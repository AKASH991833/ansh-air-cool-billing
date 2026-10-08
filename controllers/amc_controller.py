"""
AMC (Annual Maintenance Contract) Controller
Handles AMC contract creation, management, and billing
"""
from datetime import datetime, timedelta
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from database.queries import Queries
from utils.formatters import Formatters
import logging

logger = logging.getLogger(__name__)


class AMCController:
    def __init__(self, db_connection):
        self.db = db_connection

    def generate_amc_number(self):
        """Generate unique AMC contract number"""
        result = self.db.execute_query(Queries.get_next_amc_number(), fetch_one=True)
        max_num = result['max_num'] if result and result['max_num'] else 0
        return f"AMC{max_num + 1:04d}"

    def create_amc_contract(self, contract_data):
        """Create new AMC contract"""
        try:
            # Validate required fields
            required_fields = ['customer_id', 'contract_type', 'start_date',
                             'no_of_units', 'services_per_year', 'contract_amount']
            for field in required_fields:
                if field not in contract_data:
                    return None, f"Missing required field: {field}"

            # Generate AMC ID
            amc_id = self.generate_amc_number()

            # Calculate dates and amounts
            start_date_raw = contract_data['start_date']
            # Normalize start_date to YYYY-MM-DD for MySQL
            try:
                start_date = datetime.strptime(str(start_date_raw), '%d-%m-%Y').strftime('%Y-%m-%d')
            except ValueError:
                try:
                    start_date = datetime.strptime(str(start_date_raw), '%Y-%m-%d').strftime('%Y-%m-%d')
                except ValueError:
                    return None, f"Invalid date format: {start_date_raw}. Expected dd-mm-yyyy or yyyy-mm-dd."
            end_date = self._calculate_end_date(start_date, contract_data.get('contract_duration', 1))
            
            # Calculate renewal reminder date (30 days before expiry)
            renewal_reminder = self._calculate_end_date(start_date, contract_data.get('contract_duration', 1), days_before=30)

            # Calculate totals
            contract_amount = Decimal(str(contract_data['contract_amount']))
            gst_percent = Decimal(str(contract_data.get('gst_percent', 18)))
            gst_amount = contract_amount * gst_percent / 100
            total_amount = contract_amount + gst_amount
            advance_paid = Decimal(str(contract_data.get('advance_paid', 0)))
            balance_amount = total_amount - advance_paid

            # Determine payment status
            if balance_amount <= 0:
                payment_status = 'Paid'
            elif advance_paid > 0:
                payment_status = 'Partial'
            else:
                payment_status = 'Pending'

            # Get next due date if partial payment
            next_due_date = contract_data.get('next_due_date') if payment_status == 'Partial' else None

            # Format notes
            notes = contract_data.get('notes', '')
            if notes:
                notes = Formatters.format_sentence(notes)

            # Insert contract
            params = (
                amc_id,
                contract_data['customer_id'],
                contract_data['contract_type'],
                start_date,
                end_date,
                int(contract_data['no_of_units']),
                int(contract_data['services_per_year']),
                int(contract_data['services_per_year']),  # services_remaining = services_per_year initially
                float(contract_amount),
                float(gst_percent),
                float(total_amount),
                float(advance_paid),
                float(balance_amount),
                contract_data.get('payment_mode', 'Pending'),
                payment_status,
                next_due_date,
                'Active',
                int(contract_data.get('grace_period', 7)),
                renewal_reminder,
                notes
            )

            contract_id = self.db.execute_query(Queries.insert_amc_contract(), params)

            if not contract_id:
                return None, "Failed to create AMC contract"

            # Add units
            units = contract_data.get('units', [])
            for unit in units:
                self._add_amc_unit(contract_id, unit)

            # Auto-schedule visits - CRITICAL: This must succeed
            visit_error = None
            primary_tech_id = contract_data.get('technician_id')
            try:
                self._schedule_amc_visits(contract_id, start_date, end_date,
                                         int(contract_data['services_per_year']),
                                         technician_id=primary_tech_id)
            except Exception as e:
                visit_error = f"Visits not scheduled: {str(e)}"
                logger.error(f"AMC {contract_id}: Failed to schedule visits - {e}")

            # Return with warning if visits failed
            if visit_error:
                return contract_id, visit_error

            return contract_id, None

        except Exception as e:
            logger.error(f"Error creating AMC contract: {e}")
            return None, f"Error creating AMC contract: {str(e)}"

    def _calculate_end_date(self, start_date_str, duration_years, days_before=0):
        """Calculate contract end date or reminder date"""
        if not start_date_str:
            raise ValueError("start_date_str cannot be None")
        try:
            start_date = datetime.strptime(str(start_date_str), '%d-%m-%Y')
        except ValueError:
            try:
                start_date = datetime.strptime(str(start_date_str), '%Y-%m-%d')
            except ValueError:
                raise ValueError(f"Invalid date format: {start_date_str}. Expected dd-mm-yyyy or yyyy-mm-dd.")

        if days_before > 0:
            # Calculate reminder date
            end_date = start_date + relativedelta(years=duration_years) - timedelta(days=days_before)
        else:
            # Calculate end date
            end_date = start_date + relativedelta(years=duration_years) - timedelta(days=1)
        
        return end_date.strftime('%Y-%m-%d')

    def _add_amc_unit(self, amc_contract_id, unit_data):
        """Add AC unit to AMC contract"""
        params = (
            amc_contract_id,
            unit_data.get('brand', 'Unknown'),
            unit_data.get('ac_type', 'Split'),
            unit_data.get('ton', '1.0'),
            unit_data.get('star_rating', 'N/A'),
            unit_data.get('inverter', 'Not Specified'),
            unit_data.get('model', ''),
            unit_data.get('serial_number', ''),
            unit_data.get('indoor_location', ''),
            unit_data.get('outdoor_location', ''),
            unit_data.get('installation_date')
        )
        return self.db.execute_query(Queries.insert_amc_unit(), params)

    def _schedule_amc_visits(self, amc_contract_id, start_date_str, end_date_str, services_per_year, technician_id=None):
        """Auto-schedule AMC visits based on services per year"""
        try:
            start_date = datetime.strptime(str(start_date_str), '%Y-%m-%d')
            end_date = datetime.strptime(str(end_date_str), '%Y-%m-%d')

            total_days = (end_date - start_date).days
            interval_days = total_days // services_per_year if services_per_year > 0 else 90

            visits = []
            for i in range(1, services_per_year + 1):
                visit_date = start_date + timedelta(days=interval_days * (i - 1))
                if visit_date <= end_date:
                    next_due = (visit_date + timedelta(days=interval_days)).strftime('%Y-%m-%d') if i < services_per_year else None
                    visits.append((
                        amc_contract_id,
                        i,
                        visit_date.strftime('%Y-%m-%d'),
                        technician_id,  # primary technician if assigned, or None
                        '',  # work_done
                        '',  # parts_replaced
                        0,   # extra_charge
                        next_due,
                        'Scheduled',
                        ''
                    ))

            if visits:
                result = self.db.execute_many(Queries.insert_amc_visit(), visits)
                logger.info(f"Scheduled {len(visits)} visits for AMC contract {amc_contract_id}")
                return result
            return 0

        except Exception as e:
            # Log the error with full context
            logger.error(
                f"Failed to schedule AMC visits - "
                f"Contract: {amc_contract_id}, "
                f"Start: {start_date_str}, End: {end_date_str}, "
                f"Services/year: {services_per_year}, "
                f"Error: {e}"
            )
            # Re-raise to notify caller that visit scheduling failed
            raise

    def get_all_amc_contracts(self):
        """Get all AMC contracts"""
        return self.db.execute_query(Queries.get_all_amc_contracts(), fetch_all=True)

    def get_amc_by_customer(self, customer_id):
        """Get AMC contracts for a customer"""
        return self.db.execute_query(Queries.get_amc_by_customer_id(), (customer_id,), fetch_all=True)

    def get_amc_contract(self, contract_id):
        """Get single AMC contract by ID"""
        return self.db.execute_query(Queries.get_amc_contract_by_id(), (contract_id,), fetch_one=True)

    def search_amc_contracts(self, search_term):
        """Search AMC contracts"""
        search_pattern = f"%{search_term}%"
        return self.db.execute_query(
            Queries.search_amc_contracts(),
            (search_pattern, search_pattern, search_pattern),
            fetch_all=True
        )

    def search_customers_for_amc(self, search_term):
        """Search customers for AMC assignment"""
        search_pattern = f"%{search_term}%"
        return self.db.execute_query(
            Queries.search_customer_for_amc(),
            (search_pattern, search_pattern),
            fetch_all=True
        )

    def get_amc_units(self, amc_id):
        """Get all units for an AMC contract"""
        return self.db.execute_query(Queries.get_amc_units(), (amc_id,), fetch_all=True)

    def get_amc_visits(self, amc_id):
        """Get all visits for an AMC contract"""
        return self.db.execute_query(Queries.get_amc_visits(), (amc_id,), fetch_all=True)

    def get_upcoming_visits(self):
        """Get upcoming scheduled visits"""
        return self.db.execute_query(Queries.get_upcoming_amc_visits(), fetch_all=True)

    def add_amc_visit(self, visit_data):
        """Add a new AMC visit"""
        try:
            params = (
                visit_data['amc_id'],
                visit_data['visit_number'],
                visit_data['visit_date'],
                visit_data.get('technician_id'),
                visit_data.get('work_done', ''),
                visit_data.get('parts_replaced', ''),
                float(visit_data.get('extra_charge', 0)),
                visit_data.get('next_due_date'),
                visit_data.get('visit_status', 'Scheduled'),
                visit_data.get('notes', '')
            )
            visit_id = self.db.execute_query(Queries.insert_amc_visit(), params)
            return visit_id, None
        except Exception as e:
            return None, f"Error adding visit: {str(e)}"

    def complete_visit(self, visit_id, visit_data):
        """Complete a visit and decrement services remaining"""
        try:
            # Update visit status
            params = (
                'Completed',
                visit_data.get('work_done', ''),
                visit_data.get('parts_replaced', ''),
                float(visit_data.get('extra_charge', 0)),
                visit_data.get('next_due_date'),
                visit_data.get('notes', ''),
                visit_id
            )
            self.db.execute_query(Queries.update_visit_status(), params)

            # Get amc_id for this visit
            result = self.db.execute_query(
                "SELECT amc_id FROM amc_visits WHERE id = %s",
                (visit_id,), fetch_one=True
            )
            if result:
                amc_id = result['amc_id']
                # Get contract id from amc_id (amc_id is the contract ID in visits table)
                self.db.execute_query(Queries.update_amc_services_remaining(), (amc_id,))

                # Check if all services completed
                contract = self.get_amc_contract(amc_id)
                if contract and contract.get('services_remaining', 0) <= 0:
                    self.update_amc_status(amc_id, 'Completed')

            return True, None
        except Exception as e:
            return False, f"Error completing visit: {str(e)}"

    def update_visit_status(self, visit_id, visit_data):
        """Update visit status and details"""
        try:
            params = (
                visit_data.get('visit_status', 'Completed'),
                visit_data.get('work_done', ''),
                visit_data.get('parts_replaced', ''),
                float(visit_data.get('extra_charge', 0)),
                visit_data.get('next_due_date'),
                visit_data.get('notes', ''),
                visit_id
            )
            self.db.execute_query(Queries.update_visit_status(), params)
            return True, None
        except Exception as e:
            return False, f"Error updating visit: {str(e)}"

    def update_amc_status(self, contract_id, status):
        """Update AMC contract status"""
        try:
            self.db.execute_query(Queries.update_amc_status(), (status, contract_id))
            return True, None
        except Exception as e:
            return False, f"Error updating status: {str(e)}"

    def update_amc_payment(self, contract_id, amount, payment_mode, next_due_date=None):
        """Update AMC payment"""
        try:
            contract = self.get_amc_contract(contract_id)
            if not contract:
                return False, "Contract not found"

            new_advance = Decimal(str(contract['advance_paid'])) + Decimal(str(amount))
            new_balance = Decimal(str(contract['balance_amount'])) - Decimal(str(amount))

            if new_balance <= 0:
                payment_status = 'Paid'
                new_balance = 0
            elif amount > 0:
                payment_status = 'Partial'
            else:
                payment_status = contract['payment_status']

            self.db.execute_query(
                Queries.update_amc_payment(),
                (float(new_advance), float(new_balance), payment_status, payment_mode, next_due_date, contract_id)
            )

            return True, "Payment updated successfully"
        except Exception as e:
            return False, f"Error updating payment: {str(e)}"

    def check_expired_contracts(self):
        """Check and update expired contracts"""
        today = datetime.now().date()
        contracts = self.get_all_amc_contracts()

        expired_count = 0
        for contract in contracts:
            if not contract.get('end_date'):
                continue
            end_date = datetime.strptime(str(contract['end_date']), '%Y-%m-%d').date()
            grace_period = contract.get('grace_period', 7)
            grace_end = end_date + timedelta(days=grace_period)
            
            if grace_end < today and contract['amc_status'] == 'Active':
                self.update_amc_status(contract['id'], 'Expired')
                expired_count += 1

        return expired_count

    def get_amc_stats(self):
        """Get AMC statistics for dashboard"""
        stats = self.db.execute_query(Queries.get_amc_expiry_stats(), fetch_one=True)
        revenue = self.db.execute_query(Queries.get_amc_revenue(), fetch_one=True)

        return {
            'total_active': stats['total_active'] if stats else 0,
            'expiring_soon': stats['expiring_soon'] if stats else 0,
            'expired': stats['expired'] if stats else 0,
            'total_revenue': float(revenue['total_revenue']) if revenue else 0,
            'collected': float(revenue['collected']) if revenue else 0,
            'pending': float(revenue['pending']) if revenue else 0,
            'upcoming_visits': len(self.get_upcoming_visits())
        }

    def create_amc_invoice(self, contract_id, invoice_data):
        """Create AMC invoice"""
        try:
            contract = self.get_amc_contract(contract_id)
            if not contract:
                return None, "Contract not found"

            # Generate invoice number
            invoice_number = self._generate_amc_invoice_number()

            # Calculate amounts
            subtotal = Decimal(str(invoice_data.get('subtotal', contract['contract_amount'])))
            gst_percent = Decimal(str(invoice_data.get('gst_percent', contract['gst_percent'])))
            gst_amount = subtotal * gst_percent / 100
            total_amount = subtotal + gst_amount
            advance = Decimal(str(invoice_data.get('advance_payment', 0)))
            balance = total_amount - advance

            payment_status = 'Paid' if balance <= 0 else ('Partial' if advance > 0 else 'Pending')

            params = (
                contract_id,
                invoice_number,
                invoice_data.get('invoice_date', datetime.now().strftime('%Y-%m-%d')),
                float(subtotal),
                float(gst_percent),
                float(gst_amount),
                float(total_amount),
                float(advance),
                float(balance),
                invoice_data.get('payment_mode', 'Pending'),
                payment_status,
                invoice_data.get('notes', '')
            )

            invoice_id = self.db.execute_query(Queries.insert_amc_invoice(), params)
            return invoice_id, None

        except Exception as e:
            return None, f"Error creating invoice: {str(e)}"

    def _generate_amc_invoice_number(self):
        """Generate AMC invoice number"""
        result = self.db.execute_query(
            "SELECT MAX(CAST(SUBSTRING(invoice_number, 5) AS UNSIGNED)) as max_num FROM amc_invoices",
            fetch_one=True
        )
        max_num = result['max_num'] if result and result['max_num'] else 0
        return f"AMCI{max_num + 1:04d}"

    def get_amc_invoice(self, invoice_id):
        """Get AMC invoice details"""
        return self.db.execute_query(Queries.get_amc_invoice_details(), (invoice_id,), fetch_one=True)

    def delete_amc_contract(self, contract_id):
        """Soft delete AMC contract"""
        try:
            self.db.execute_query(
                "UPDATE amc_contracts SET is_active = FALSE, amc_status = 'Cancelled' WHERE id = %s",
                (contract_id,)
            )
            return True, None
        except Exception as e:
            return False, f"Error deleting contract: {str(e)}"

    def get_amc_for_pdf(self, contract_id):
        """Get complete AMC data for PDF generation"""
        contract = self.get_amc_contract(contract_id)
        if not contract:
            return None

        units = self.get_amc_units(contract_id)
        visits = self.get_amc_visits(contract_id)

        return {
            'contract': contract,
            'units': units,
            'visits': visits
        }

    def add_or_get_customer(self, customer_data):
        """Add new customer or get existing by mobile"""
        try:
            # Check if customer exists by mobile
            existing = self.db.execute_query(
                Queries.get_customer_by_mobile(),
                (customer_data['mobile'],),
                fetch_one=True
            )

            if existing:
                return existing['id'], None

            # Create new customer
            params = (
                Formatters.format_title(customer_data['name']),
                customer_data['mobile'],
                customer_data.get('email', ''),
                Formatters.format_title(customer_data.get('address', '')),
                Formatters.format_title(customer_data.get('landmark', ''))
            )

            customer_id = self.db.execute_query(Queries.insert_customer(), params)
            return customer_id, None

        except Exception as e:
            return None, f"Error saving customer: {str(e)}"
