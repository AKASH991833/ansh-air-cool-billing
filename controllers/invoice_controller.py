"""
Invoice controller
"""
from datetime import datetime, timedelta
from decimal import Decimal

class InvoiceController:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def _get_setting(self, key, default=''):
        try:
            result = self.db.execute_query(
                "SELECT setting_value FROM app_settings WHERE setting_key = %s",
                (key,), fetch_one=True
            )
            return result['setting_value'] if result else default
        except Exception:
            return default

    def _validate_totals(self, invoice_data, tolerance=0.5):
        """Recalculate totals from items and compare with provided values.
        Logs validation failures and rejects inconsistent data."""
        items = invoice_data.get('items', [])
        totals = invoice_data.get('totals', {})
        if not items:
            return

        discount_before_gst = self._get_setting('discount_before_gst', 'false').lower() == 'true'

        # Recalculate subtotal from items
        calculated_subtotal = sum(float(item.get('amount', 0)) for item in items)

        provided_subtotal = float(totals.get('subtotal', 0))
        if abs(calculated_subtotal - provided_subtotal) > tolerance:
            import logging
            logging.getLogger(__name__).warning(
                f"Subtotal mismatch: calculated={calculated_subtotal}, provided={provided_subtotal}"
            )
            raise ValueError(
                f"Subtotal mismatch: calculated {calculated_subtotal:.2f}, "
                f"provided {provided_subtotal:.2f}"
            )

        def _is_percentage(dt):
            return dt in ('%', 'percentage')

        # Recalculate GST (on discounted subtotal if discount_before_gst mode)
        gst_percentage = float(totals.get('gst_percentage', 0))
        if discount_before_gst:
            discount_value_for_gst = float(totals.get('discount_value', 0))
            discount_type_for_gst = totals.get('discount_type', '')
            temp_disc = 0.0
            if _is_percentage(discount_type_for_gst):
                temp_disc = calculated_subtotal * discount_value_for_gst / 100.0
            else:
                temp_disc = discount_value_for_gst
            gst_base = calculated_subtotal - temp_disc
            if gst_base < 0:
                gst_base = 0.0
            calculated_gst = gst_base * gst_percentage / 100.0
        else:
            calculated_gst = calculated_subtotal * gst_percentage / 100.0
        provided_gst = float(totals.get('gst_amount', 0))
        if abs(calculated_gst - provided_gst) > tolerance:
            import logging
            logging.getLogger(__name__).warning(
                f"GST amount mismatch: calculated={calculated_gst}, provided={provided_gst}"
            )
            raise ValueError(
                f"GST amount mismatch: calculated {calculated_gst:.2f}, "
                f"provided {provided_gst:.2f}"
            )

        # Recalculate discount
        discount_type = totals.get('discount_type', '')
        discount_value = float(totals.get('discount_value', 0))
        if _is_percentage(discount_type):
            if discount_before_gst:
                calculated_discount = calculated_subtotal * discount_value / 100.0
            else:
                calculated_discount = (calculated_subtotal + calculated_gst) * discount_value / 100.0
        elif discount_value > 0:
            calculated_discount = discount_value
        else:
            calculated_discount = 0.0
        provided_discount = float(totals.get('discount_amount', 0))
        if abs(calculated_discount - provided_discount) > tolerance:
            import logging
            logging.getLogger(__name__).warning(
                f"Discount amount mismatch: calculated={calculated_discount}, provided={provided_discount}"
            )
            raise ValueError(
                f"Discount amount mismatch: calculated {calculated_discount:.2f}, "
                f"provided {provided_discount:.2f}"
            )

        # Recalculate total
        calculated_total = calculated_subtotal + calculated_gst - calculated_discount
        provided_total = float(totals.get('total_amount', 0))
        if abs(calculated_total - provided_total) > tolerance:
            import logging
            logging.getLogger(__name__).warning(
                f"Total amount mismatch: calculated={calculated_total}, provided={provided_total}"
            )
            raise ValueError(
                f"Total amount mismatch: calculated {calculated_total:.2f}, "
                f"provided {provided_total:.2f}"
            )

        import logging
        logging.getLogger(__name__).info(
            f"Totals validated OK: subtotal={calculated_subtotal:.2f}, "
            f"gst={calculated_gst:.2f}, discount={calculated_discount:.2f}, "
            f"total={calculated_total:.2f}"
        )

    def create_invoice(self, invoice_data):
        """Create a new invoice with transaction support"""
        # Ensure connection exists
        if not hasattr(self.db, 'connection') or not self.db.connection:
            return None, "Database connection not available"

        # Begin immediate transaction to prevent duplicate invoice numbers
        # under concurrent access. SQLite will acquire an exclusive lock now.
        self.db.begin_transaction()
        
        totals = invoice_data.get('totals', {})

        # Server-side total validation
        self._validate_totals(invoice_data)
        
        try:
            # 1. Get or create customer
            customer_id = self._get_or_create_customer(invoice_data['customer'])
            if not customer_id:
                self.db.rollback()
                return None, "Failed to create customer"

            # 2. Get AC brand ID
            ac_brand_id = self._get_ac_brand_id(invoice_data['ac_details']['brand'])

            # 3. Get technician ID
            technician_id = self._get_technician_id(invoice_data['technician'])

            # 4. Create invoice
            invoice_id = self._create_invoice_record(
                customer_id, ac_brand_id, technician_id, invoice_data
            )

            if not invoice_id:
                self.db.connection.rollback()
                return None, "Failed to create invoice"

            # 5. Create invoice items
            self._create_invoice_items(invoice_id, invoice_data['items'])

            # 6. Update stock for parts
            self._update_stock(invoice_data['items'])

            # Commit transaction
            self.db.commit()
            # Audit log
            try:
                from utils.audit import log_create
                total_amount = totals.get('total_amount', 0)
                log_create('Invoice', invoice_id, f"Invoice {invoice_data['invoice_number']} created - ₹{total_amount}")
            except Exception as audit_err:
                import logging
                logging.getLogger(__name__).warning(f"Audit log failed for invoice {invoice_id}: {audit_err}")
            return invoice_id, None

        except Exception as e:
            # Rollback on error
            try:
                if getattr(self.db, '_transaction_active', False):
                    self.db.rollback()
            except Exception as rb_err:
                import logging
                logging.getLogger(__name__).warning(f"Create invoice rollback failed: {rb_err}")
            return None, f"Error creating invoice: {str(e)}"
        
    
    def _get_or_create_customer(self, customer_data):
        """Get existing customer or create new using centralized queries"""
        from utils.formatters import Formatters
        from database.queries import Queries
        from utils.validators import Validators

        # Validate customer data before any DB operation
        valid, msg = Validators.validate_customer_data(
            customer_data.get('name', ''),
            customer_data.get('mobile', ''),
            customer_data.get('email', ''),
            customer_data.get('address', '')
        )
        if not valid:
            raise ValueError(msg)

        # Format customer data
        customer_data['name'] = Formatters.format_title(customer_data['name'])
        if customer_data['address']:
            customer_data['address'] = Formatters.format_title(customer_data['address'])
        if customer_data['landmark']:
            customer_data['landmark'] = Formatters.format_title(customer_data['landmark'])

        # Check if customer exists by mobile (using Queries)
        existing = self.db.execute_query(Queries.get_customer_by_mobile(), (customer_data['mobile'],), fetch_one=True)

        if existing:
            update_query = """
            UPDATE customers 
            SET name = %s, email = %s, address = %s, landmark = %s, pincode = %s, updated_at = NOW()
            WHERE id = %s
            """
            self.db.execute_query(update_query, (
                customer_data['name'],
                customer_data['email'],
                customer_data['address'],
                customer_data['landmark'],
                customer_data.get('pincode', ''),
                existing['id']
            ))
            return existing['id']
        else:
            query = Queries.insert_customer()
            return self.db.execute_query(query, (
                customer_data['name'],
                customer_data['mobile'],
                customer_data['email'],
                customer_data['address'],
                customer_data['landmark']
            ))
    
    def _get_ac_brand_id(self, brand_name):
        """Get AC brand ID, create if doesn't exist"""
        from utils.formatters import Formatters
        from database.queries import Queries

        if not brand_name:
            return None

        brand_name = Formatters.format_title(brand_name)

        # Get existing brand
        query = "SELECT id FROM ac_brands WHERE brand_name = %s AND is_active = TRUE"
        existing = self.db.execute_query(query, (brand_name,), fetch_one=True)

        if existing:
            return existing['id']
        else:
            # Create new brand (using Queries)
            query = Queries.insert_ac_brand()
            return self.db.execute_query(query, (brand_name,))
    
    def _get_technician_id(self, technician_val):
        """Extract or resolve technician ID from int, dict, or string"""
        if not technician_val:
            return None

        if isinstance(technician_val, int):
            return technician_val

        if isinstance(technician_val, dict) and 'id' in technician_val:
            try:
                return int(technician_val['id'])
            except Exception:
                pass

        technician_str = str(technician_val).strip()
        if not technician_str:
            return None

        # Format "44: Name" or pure digit string "44"
        if ':' in technician_str:
            try:
                return int(technician_str.split(':')[0].strip())
            except Exception:
                pass

        if technician_str.isdigit():
            return int(technician_str)

        # Lookup by name
        try:
            row = self.db.execute_query(
                "SELECT id FROM technicians WHERE name = %s AND is_active = TRUE LIMIT 1",
                (technician_str,),
                fetch_one=True
            )
            if row:
                return row['id']
        except Exception:
            pass

        return None
    
    def _create_invoice_record(self, customer_id, ac_brand_id, technician_id, invoice_data):
        """Create invoice record in database"""
        from utils.formatters import Formatters

        notes = invoice_data['notes']
        if notes:
            notes = Formatters.format_sentence(notes)

        # VALIDATION: Technician must be assigned
        if not technician_id:
            raise ValueError("Technician assignment is required. Please select a technician.")

        # FIRST: Ensure invoice number exists and check if already taken
        if not invoice_data.get('invoice_number'):
            invoice_data['invoice_number'] = Formatters.generate_invoice_number(self.db)

        # BEGIN IMMEDIATE at method start ensures exclusive lock, so no race condition.
        existing = None
        for attempt in range(5):
            check_query = "SELECT id FROM invoices WHERE invoice_number = %s"
            existing = self.db.execute_query(check_query, (invoice_data['invoice_number'],), fetch_one=True)
            if existing:
                invoice_data['invoice_number'] = Formatters.generate_invoice_number(self.db)
            else:
                break

        query = """
        INSERT INTO invoices (
            invoice_number, customer_id, ac_brand_id, ac_type, ton_capacity,
            ac_inverter, star_rating,
            technician_id, subtotal, gst_percentage,
            gst_amount, discount_type, discount_value, discount_amount,
            total_amount, advance_payment, balance_amount,
            payment_mode, payment_status, notes, is_active
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
        """

        ac_details = invoice_data.get('ac_details', {})
        totals = invoice_data.get('totals', {})
        payment = invoice_data.get('payment', {})

        ac_inverter = ac_details.get('ac_inverter') or ac_details.get('inverter_type', 'No')
        star_rating = ac_details.get('star_rating', 'N/A')
        disc_type = totals.get('discount_type', 'percent')
        disc_val = totals.get('discount_value', 0)
        disc_amt = totals.get('discount_amount', 0)

        return self.db.execute_query(query, (
            invoice_data['invoice_number'],
            customer_id,
            ac_brand_id,
            ac_details.get('type', ''),
            ac_details.get('ton', ''),
            ac_inverter,
            star_rating,
            technician_id,
            totals.get('subtotal', 0),
            totals.get('gst_percentage', 0),
            totals.get('gst_amount', 0),
            disc_type, disc_val, disc_amt,
            totals.get('total_amount', 0),
            totals.get('advance_payment', 0),
            totals.get('balance_amount', 0),
            payment.get('mode', 'Cash'),
            payment.get('status', 'Pending'),
            notes
        ))
    
    def _create_invoice_items(self, invoice_id, items):
        """Create invoice items in database"""
        if not items:
            return
        
        query = """
        INSERT INTO invoice_items (invoice_id, item_type, service_id, part_id, description, quantity, rate, amount)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        params = []
        for item in items:
            itype = item.get('type', 'service')
            item_id = item.get('item_id') or item.get('service_id') or item.get('part_id')
            service_id = item_id if itype == 'service' else None
            part_id = item_id if itype == 'part' else None
            desc = item.get('description') or item.get('name', '')
            
            params.append((
                invoice_id,
                itype,
                service_id,
                part_id,
                desc,
                item.get('quantity', 1),
                item.get('rate', 0.0),
                item.get('amount', 0.0)
            ))
        
        self.db.execute_many(query, params)
    
    def _update_stock(self, items):
        """Update stock quantity for parts"""
        for item in items:
            if item.get('type') == 'part':
                part_id = item.get('item_id') or item.get('part_id')
                qty = item.get('quantity', 0)
                if part_id:
                    query = "UPDATE parts SET stock_quantity = stock_quantity - %s WHERE id = %s AND stock_quantity >= %s"
                    self.db.execute_query(query, (qty, part_id, qty))
    
    def get_invoice(self, invoice_id):
        """Get invoice by ID"""
        query = """
        SELECT 
            i.*,
            c.name as customer_name, c.mobile, c.email, c.address, c.landmark,
            ab.brand_name,
            t.name as technician_name, t.mobile as technician_mobile
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        LEFT JOIN ac_brands ab ON i.ac_brand_id = ab.id
        LEFT JOIN technicians t ON i.technician_id = t.id
        WHERE i.id = %s AND i.is_active = TRUE
        """
        return self.db.execute_query(query, (invoice_id,), fetch_one=True)
    
    def get_invoice_items(self, invoice_id):
        """Get invoice items"""
        query = """
        SELECT 
            ii.*,
            COALESCE(s.service_name, p.part_name) as item_name,
            s.service_name,
            p.part_name
        FROM invoice_items ii
        LEFT JOIN services s ON ii.service_id = s.id
        LEFT JOIN parts p ON ii.part_id = p.id
        WHERE ii.invoice_id = %s
        """
        return self.db.execute_query(query, (invoice_id,), fetch_all=True)
    
    def search_invoices(self, search_term=None, from_date=None, to_date=None, limit=100):
        """Search invoices with filters"""
        query = """
        SELECT 
            i.id, i.invoice_number, DATE(i.created_at) as invoice_date,
            c.name as customer_name, c.mobile,
            i.total_amount, i.advance_payment, i.balance_amount,
            i.payment_status, i.payment_mode
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        WHERE i.is_active = TRUE
        """
        
        conditions = []
        params = []
        
        if search_term:
            conditions.append("(c.name LIKE %s OR c.mobile LIKE %s OR i.invoice_number LIKE %s)")
            params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])
        
        if from_date:
            conditions.append("i.created_at >= %s")
            params.append(from_date)
        
        if to_date:
            conditions.append("i.created_at < %s")
            to_dt = datetime.strptime(str(to_date)[:10], '%Y-%m-%d') if isinstance(to_date, str) else datetime.combine(to_date, datetime.min.time())
            params.append((to_dt + timedelta(days=1)).strftime('%Y-%m-%d'))
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        query += " ORDER BY i.created_at DESC LIMIT %s"
        params.append(limit)
        
        return self.db.execute_query(query, params, fetch_all=True)
    
    def update_invoice_payment(self, invoice_id, amount, payment_mode, notes=None):
        """Update invoice payment"""
        try:
            # Get current invoice
            invoice = self.get_invoice(invoice_id)
            if not invoice:
                return False, "Invoice not found"
            
            # Calculate new balance
            new_balance = invoice['balance_amount'] - amount
            
            # Update payment status
            if new_balance <= 0:
                payment_status = 'Paid'
                new_balance = 0
            elif amount > 0:
                payment_status = 'Partial'
            else:
                payment_status = invoice['payment_status']
            
            # Update invoice
            query = """
            UPDATE invoices 
            SET advance_payment = advance_payment + %s,
                balance_amount = %s,
                payment_status = %s,
                payment_mode = %s,
                updated_at = NOW()
            WHERE id = %s
            """
            self.db.execute_query(query, (
                amount,
                new_balance,
                payment_status,
                payment_mode,
                invoice_id
            ))
            
            # Record payment
            if amount > 0:
                payment_query = """
                INSERT INTO payments (invoice_id, amount, payment_mode, notes)
                VALUES (%s, %s, %s, %s)
                """
                self.db.execute_query(payment_query, (
                    invoice_id,
                    amount,
                    payment_mode,
                    notes
                ))
            
            return True, "Payment updated successfully"
            
        except Exception as e:
            return False, f"Error updating payment: {str(e)}"
    
    def delete_invoice(self, invoice_id):
        """Soft delete invoice with stock restoration"""
        try:
            # Restore stock for parts before deleting
            parts_query = """
            SELECT ii.part_id, ii.quantity
            FROM invoice_items ii
            WHERE ii.invoice_id = %s AND ii.item_type = 'part'
            """
            parts = self.db.execute_query(parts_query, (invoice_id,), fetch_all=True)
            if parts:
                for part in parts:
                    self.db.execute_query(
                        "UPDATE parts SET stock_quantity = stock_quantity + %s WHERE id = %s",
                        (part['quantity'], part['part_id'])
                    )

            # Soft delete invoice
            query = "UPDATE invoices SET is_active = FALSE WHERE id = %s"
            self.db.execute_query(query, (invoice_id,))
            try:
                from utils.audit import log_delete
                log_delete('Invoice', invoice_id, "Invoice deleted")
            except Exception as audit_err:
                import logging
                logging.getLogger(__name__).warning(f"Audit log failed for delete invoice {invoice_id}: {audit_err}")
            return True, "Invoice deleted successfully"
        except Exception as e:
            return False, f"Error deleting invoice: {str(e)}"
    
    def update_invoice(self, invoice_id, invoice_data):
        """Update existing invoice with lock check"""
        try:
            # Server-side total validation
            self._validate_totals(invoice_data)

            check_lock_query = """
            SELECT id, payment_status, is_active 
            FROM invoices 
            WHERE id = %s
            """
            invoice_check = self.db.execute_query(check_lock_query, (invoice_id,), fetch_one=True)
            
            if not invoice_check:
                return None, "Invoice not found"
            
            if not invoice_check['is_active']:
                return None, "Invoice has been deleted"
            
            if invoice_check['payment_status'].lower() in ('paid', 'cancelled'):
                return None, f"Cannot modify {invoice_check['payment_status']} invoice. Only 'draft' and 'final' invoices can be edited."
            
            customer_id = self._get_or_create_customer(invoice_data['customer'])
            if not customer_id:
                return None, "Failed to update customer"

            ac_brand_id = self._get_ac_brand_id(invoice_data['ac_details']['brand'])
            technician_id = self._get_technician_id(invoice_data['technician'])

            # Get old invoice items to restore stock
            old_items_query = """
            SELECT ii.part_id, ii.quantity FROM invoice_items ii
            JOIN parts p ON ii.part_id = p.id
            WHERE ii.invoice_id = %s AND ii.item_type = 'part'
            """
            old_items = self.db.execute_query(old_items_query, (invoice_id,), fetch_all=True)

            success = self._update_invoice_record(
                invoice_id, customer_id, ac_brand_id, technician_id, invoice_data
            )
            if not success:
                raise Exception("Failed to update invoice record")

            # Restore old stock
            for item in (old_items or []):
                self.db.execute_query(
                    "UPDATE parts SET stock_quantity = stock_quantity + %s WHERE id = %s",
                    (item['quantity'], item['part_id'])
                )

            # Delete old invoice items
            self.db.execute_query("DELETE FROM invoice_items WHERE invoice_id = %s", (invoice_id,))

            # Create new invoice items
            self._create_invoice_items(invoice_id, invoice_data['items'])

            # Deduct new stock
            self._update_stock(invoice_data['items'])

            self.db.connection.commit()
            return invoice_id, None
        except Exception as e:
            try:
                self.db.connection.rollback()
            except Exception:
                pass
            return None, f"Error updating invoice: {str(e)}"
    
    def _update_invoice_record(self, invoice_id, customer_id, ac_brand_id, technician_id, invoice_data):
        """Update invoice record in database"""
        from utils.formatters import Formatters

        notes = invoice_data['notes']
        if notes:
            notes = Formatters.format_sentence(notes)

        query = """
        UPDATE invoices SET
            customer_id = %s, ac_brand_id = %s, ac_type = %s, star_rating = %s,
            ton_capacity = %s, ac_inverter = %s, technician_id = %s, subtotal = %s, 
            gst_percentage = %s, gst_amount = %s, discount_type = %s, discount_value = %s,
            discount_amount = %s, total_amount = %s, advance_payment = %s, 
            balance_amount = %s, payment_mode = %s, payment_status = %s, notes = %s,
            updated_at = NOW()
        WHERE id = %s
        """
        
        ac_details = invoice_data.get('ac_details', {})
        totals = invoice_data.get('totals', {})
        payment = invoice_data.get('payment', {})
        
        ac_inverter = ac_details.get('ac_inverter') or ac_details.get('inverter_type', 'No')
        
        self.db.execute_query(query, (
            customer_id,
            ac_brand_id,
            ac_details.get('type', ''),
            ac_details.get('star_rating', 'N/A'),
            ac_details.get('ton', ''),
            ac_inverter,
            technician_id,
            totals.get('subtotal', 0),
            totals.get('gst_percentage', 0),
            totals.get('gst_amount', 0),
            totals.get('discount_type', 'percent'),
            totals.get('discount_value', 0),
            totals.get('discount_amount', 0),
            totals.get('total_amount', 0),
            totals.get('advance_payment', 0),
            totals.get('balance_amount', 0),
            payment.get('mode', 'Cash'),
            payment.get('status', 'Pending'),
            notes,
            invoice_id
        ))
        
        return True