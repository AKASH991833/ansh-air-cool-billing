"""
Technician controller
"""
from datetime import datetime, timedelta
from utils.logger import logger

class TechnicianController:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_technicians_summary(self, start_date=None, end_date=None):
        """Get technicians with work summary"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        if isinstance(end_date, str):
            end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end_date_dt = end_date
        end_date_plus = (end_date_dt + timedelta(days=1)).strftime('%Y-%m-%d')

        if isinstance(start_date, str):
            start_date_str = start_date
        else:
            start_date_str = start_date.strftime('%Y-%m-%d')

        query = """
        SELECT 
            t.id,
            t.name,
            t.mobile,
            COUNT(i.id) as services_done,
            COALESCE(SUM(i.advance_payment), 0) as amount_collected,
            COALESCE(SUM(i.balance_amount), 0) as pending_amount
        FROM technicians t
        LEFT JOIN invoices i ON t.id = i.technician_id
            AND i.is_active = TRUE
            AND i.created_at >= %s AND i.created_at < %s
        WHERE t.is_active = TRUE
        GROUP BY t.id, t.name, t.mobile
        ORDER BY t.name
        """
        
        return self.db.execute_query(query, (start_date_str, end_date_plus), fetch_all=True)
    
    def get_technician_profile(self, technician_id):
        """Get technician profile with statistics"""
        query = """
        SELECT 
            t.*,
            COALESCE(inv.total_services, 0) as total_services,
            COALESCE(inv.total_revenue, 0) as total_revenue,
            COALESCE(inv.amount_collected, 0) as amount_collected,
            COALESCE(inv.pending_amount, 0) as pending_amount
        FROM technicians t
        LEFT JOIN (
            SELECT 
                technician_id,
                COUNT(*) as total_services,
                COALESCE(SUM(total_amount), 0) as total_revenue,
                COALESCE(SUM(advance_payment), 0) as amount_collected,
                COALESCE(SUM(balance_amount), 0) as pending_amount
            FROM invoices
            WHERE is_active = TRUE AND technician_id IS NOT NULL
            GROUP BY technician_id
        ) inv ON t.id = inv.technician_id
        WHERE t.id = %s
        """
        
        profile = self.db.execute_query(query, (technician_id,), fetch_one=True)
        
        if not profile:
            return None
        
        commission_earned = float(profile.get('total_revenue') or 0) * (float(profile.get('commission_rate') or 0) / 100)
        profile['commission_earned'] = commission_earned

        return profile
    
    def get_work_summary(self, technician_id, start_date, end_date):
        """Get daily work summary for technician"""
        if isinstance(end_date, str):
            end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end_date_dt = end_date
        end_date_plus = (end_date_dt + timedelta(days=1)).strftime('%Y-%m-%d')

        if isinstance(start_date, str):
            start_date_str = start_date
        else:
            start_date_str = start_date.strftime('%Y-%m-%d')

        # Daily summary
        daily_query = """
        SELECT 
            DATE(i.created_at) as work_date,
            COUNT(*) as services_done,
            COALESCE(SUM(i.advance_payment), 0) as amount_collected,
            COALESCE(SUM(i.balance_amount), 0) as pending_amount,
            GROUP_CONCAT(DISTINCT c.name SEPARATOR ', ') as customers_served
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        WHERE i.technician_id = %s
        AND i.is_active = TRUE
        AND i.created_at >= %s AND i.created_at < %s
        GROUP BY DATE(i.created_at)
        ORDER BY work_date DESC
        """
        
        daily_summary = self.db.execute_query(daily_query, (technician_id, start_date_str, end_date_plus), fetch_all=True)
        
        # Statistics
        stats_query = """
        SELECT 
            COUNT(DISTINCT DATE(i.created_at)) as days_worked,
            COUNT(*) as total_services,
            COALESCE(SUM(i.advance_payment), 0) as total_collected,
            COALESCE(SUM(i.balance_amount), 0) as total_pending
        FROM invoices i
        WHERE i.technician_id = %s
        AND i.is_active = TRUE
        AND i.created_at >= %s AND i.created_at < %s
        """
        
        stats = self.db.execute_query(stats_query, (technician_id, start_date_str, end_date_plus), fetch_one=True)
        
        return {
            'daily_summary': daily_summary,
            'statistics': stats or {
                'days_worked': 0,
                'total_services': 0,
                'total_collected': 0,
                'total_pending': 0
            }
        }
    
    def get_service_history(self, technician_id, start_date, end_date):
        """Get service history for technician"""
        if isinstance(end_date, str):
            end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end_date_dt = end_date
        end_date_plus = (end_date_dt + timedelta(days=1)).strftime('%Y-%m-%d')

        if isinstance(start_date, str):
            start_date_str = start_date
        else:
            start_date_str = start_date.strftime('%Y-%m-%d')

        query = """
        SELECT 
            i.id as invoice_id,
            i.invoice_number,
            DATE(i.created_at) as work_date,
            c.name as customer_name,
            c.mobile,
            i.total_amount,
            i.payment_status,
            i.payment_mode,
            sv.services_performed
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        LEFT JOIN (
            SELECT ii.invoice_id,
                   GROUP_CONCAT(s.service_name SEPARATOR ', ') as services_performed
            FROM invoice_items ii
            JOIN services s ON ii.service_id = s.id
            GROUP BY ii.invoice_id
        ) sv ON i.id = sv.invoice_id
        WHERE i.technician_id = %s
        AND i.is_active = TRUE
        AND i.created_at >= %s AND i.created_at < %s
        ORDER BY i.created_at DESC
        """
        
        return self.db.execute_query(query, (technician_id, start_date, end_date), fetch_all=True)
    
    def add_technician(self, name, mobile, email=None, address=None, commission_rate=10):
        """Add new technician"""
        from utils.formatters import Formatters
        from utils.validators import Validators

        valid, msg = Validators.validate_name(name)
        if not valid:
            raise ValueError(msg)
        valid, msg = Validators.validate_mobile(mobile)
        if not valid:
            raise ValueError(msg)
        if email:
            valid, msg = Validators.validate_email(email)
            if not valid:
                raise ValueError(msg)

        name = Formatters.format_title(name)
        if address:
            address = Formatters.format_title(address)

        query = """
        INSERT INTO technicians (name, mobile, email, address, commission_rate, is_active)
        VALUES (%s, %s, %s, %s, %s, TRUE)
        """
        
        try:
            tech_id = self.db.execute_query(query, (name, mobile, email, address, commission_rate))
            try:
                from utils.audit import log_create
                log_create('Technician', tech_id, f"Added technician: {name}")
            except Exception as audit_err:
                logger.warning(f"Audit log failed for create technician {tech_id}: {audit_err}")
            return tech_id
        except Exception as e:
            raise Exception(f"Failed to add technician: {str(e)}")
    
    def update_technician(self, technician_id, name, mobile, email=None, address=None, commission_rate=10, is_active=True):
        """Update technician"""
        from utils.formatters import Formatters
        from utils.validators import Validators

        valid, msg = Validators.validate_name(name)
        if not valid:
            raise ValueError(msg)
        valid, msg = Validators.validate_mobile(mobile)
        if not valid:
            raise ValueError(msg)
        if email:
            valid, msg = Validators.validate_email(email)
            if not valid:
                raise ValueError(msg)

        name = Formatters.format_title(name)
        if address:
            address = Formatters.format_title(address)

        query = """
        UPDATE technicians 
        SET name = %s, mobile = %s, email = %s, address = %s, 
            commission_rate = %s, is_active = %s, updated_at = NOW()
        WHERE id = %s
        """
        
        try:
            self.db.execute_query(query, (name, mobile, email, address, commission_rate, is_active, technician_id))
            try:
                from utils.audit import log_update
                log_update('Technician', technician_id, f"Updated technician: {name}")
            except Exception as audit_err:
                logger.warning(f"Audit log failed for update technician {technician_id}: {audit_err}")
            return True
        except Exception as e:
            raise Exception(f"Failed to update technician: {str(e)}")
    
    def delete_technician(self, technician_id):
        """Soft delete technician"""
        query = "UPDATE technicians SET is_active = FALSE WHERE id = %s"
        
        try:
            self.db.execute_query(query, (technician_id,))
            try:
                from utils.audit import log_delete
                log_delete('Technician', technician_id)
            except Exception as audit_err:
                logger.warning(f"Audit log failed for delete technician {technician_id}: {audit_err}")
            return True
        except Exception as e:
            raise Exception(f"Failed to delete technician: {str(e)}")
    
    def get_technician_performance_report(self, start_date=None, end_date=None):
        """Get performance report for all technicians"""
        if not start_date:
            start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        if isinstance(end_date, str):
            end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end_date_dt = end_date
        end_date_plus = (end_date_dt + timedelta(days=1)).strftime('%Y-%m-%d')

        if isinstance(start_date, str):
            start_date_str = start_date
        else:
            start_date_str = start_date.strftime('%Y-%m-%d')

        query = """
        SELECT 
            t.id,
            t.name,
            t.mobile,
            t.commission_rate,
            COUNT(i.id) as total_services,
            COALESCE(SUM(i.total_amount), 0) as total_revenue,
            COALESCE(SUM(i.advance_payment), 0) as amount_collected,
            COALESCE(SUM(i.balance_amount), 0) as pending_amount,
            COUNT(DISTINCT DATE(i.created_at)) as days_worked,
            COALESCE(SUM(i.total_amount) / NULLIF(COUNT(i.id), 0), 0) as avg_service_value
        FROM technicians t
        LEFT JOIN invoices i ON t.id = i.technician_id
            AND i.is_active = TRUE
            AND i.created_at >= %s AND i.created_at < %s
        WHERE t.is_active = TRUE
        GROUP BY t.id, t.name, t.mobile, t.commission_rate
        ORDER BY total_revenue DESC
        """
        
        return self.db.execute_query(query, (start_date_str, end_date_plus), fetch_all=True)
    
    def assign_invoice_to_technician(self, invoice_id, technician_id):
        """Assign invoice to technician"""
        query = "UPDATE invoices SET technician_id = %s, updated_at = NOW() WHERE id = %s"
        
        try:
            self.db.execute_query(query, (technician_id, invoice_id))
            return True
        except Exception as e:
            raise Exception(f"Failed to assign invoice: {str(e)}")
    
    def get_available_technicians(self):
        """Get list of active technicians"""
        query = "SELECT id, name, mobile FROM technicians WHERE is_active = TRUE ORDER BY name"
        return self.db.execute_query(query, fetch_all=True)
    
    def calculate_commission(self, technician_id, start_date=None, end_date=None):
        """Calculate commission for technician"""
        if not start_date:
            start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        if isinstance(end_date, str):
            end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end_date_dt = end_date
        end_date_plus = (end_date_dt + timedelta(days=1)).strftime('%Y-%m-%d')

        if isinstance(start_date, str):
            start_date_str = start_date
        else:
            start_date_str = start_date.strftime('%Y-%m-%d')

        # Get technician commission rate
        tech_query = "SELECT commission_rate FROM technicians WHERE id = %s"
        tech = self.db.execute_query(tech_query, (technician_id,), fetch_one=True)
        
        if not tech:
            return 0
        
        commission_rate = tech['commission_rate']
        
        # Get total revenue for period
        revenue_query = """
        SELECT COALESCE(SUM(total_amount), 0) as total_revenue
        FROM invoices
        WHERE technician_id = %s
        AND is_active = TRUE
        AND created_at >= %s AND created_at < %s
        """
        
        revenue = self.db.execute_query(revenue_query, (technician_id, start_date_str, end_date_plus), fetch_one=True)
        
        commission = float(revenue['total_revenue']) * (float(commission_rate) / 100)
        return commission