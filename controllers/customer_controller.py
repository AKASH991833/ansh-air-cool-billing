"""
Customer controller
"""

class CustomerController:
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_all_customers(self, search_term=None):
        """Get all customers with optional search"""
        query = """
        SELECT 
            c.id, c.name, c.mobile, c.email, c.address, c.landmark,
            DATE(c.created_at) as created_date,
            COALESCE(inv.total_services, 0) as total_services,
            COALESCE(inv.total_amount, 0) as total_amount,
            COALESCE(inv.pending_amount, 0) as pending_amount,
            inv.last_visit as last_visit
        FROM customers c
        LEFT JOIN (
            SELECT 
                customer_id,
                COUNT(*) as total_services,
                COALESCE(SUM(total_amount), 0) as total_amount,
                COALESCE(SUM(balance_amount), 0) as pending_amount,
                MAX(DATE(created_at)) as last_visit
            FROM invoices
            WHERE is_active = TRUE
            GROUP BY customer_id
        ) inv ON c.id = inv.customer_id
        WHERE c.is_active = TRUE
        """
        
        params = []
        if search_term:
            query += " AND (c.name LIKE %s OR c.mobile LIKE %s OR c.address LIKE %s)"
            params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])
        
        query += " ORDER BY c.name"
        
        return self.db.execute_query(query, params, fetch_all=True)
    
    def get_customer_by_id(self, customer_id):
        """Get customer by ID"""
        query = """
        SELECT 
            c.*,
            COALESCE(inv.total_services, 0) as total_services,
            COALESCE(inv.total_amount, 0) as total_amount,
            COALESCE(inv.pending_amount, 0) as pending_amount,
            inv.last_service as last_service
        FROM customers c
        LEFT JOIN (
            SELECT 
                customer_id,
                COUNT(*) as total_services,
                COALESCE(SUM(total_amount), 0) as total_amount,
                COALESCE(SUM(balance_amount), 0) as pending_amount,
                MAX(DATE(created_at)) as last_service
            FROM invoices
            WHERE is_active = TRUE
            GROUP BY customer_id
        ) inv ON c.id = inv.customer_id
        WHERE c.id = %s
        """
        return self.db.execute_query(query, (customer_id,), fetch_one=True)
    
    def get_customer_invoices(self, customer_id):
        """Get customer invoices"""
        query = """
        SELECT 
            i.id, i.invoice_number, DATE(i.created_at) as invoice_date,
            i.total_amount, i.advance_payment, i.balance_amount,
            i.payment_status, i.payment_mode
        FROM invoices i
        WHERE i.customer_id = %s AND i.is_active = TRUE
        ORDER BY i.created_at DESC
        LIMIT 20
        """
        return self.db.execute_query(query, (customer_id,), fetch_all=True)
    
    def add_customer(self, name, mobile, email=None, address=None, landmark=None):
        """Add new customer"""
        from utils.formatters import Formatters
        from utils.validators import Validators

        valid, msg = Validators.validate_customer_data(name, mobile, email, address)
        if not valid:
            return None, msg

        name = Formatters.format_title(name)
        if address:
            address = Formatters.format_title(address)
        if landmark:
            landmark = Formatters.format_title(landmark)

        query = """
        INSERT INTO customers (name, mobile, email, address, landmark, is_active)
        VALUES (%s, %s, %s, %s, %s, TRUE)
        """
        customer_id = self.db.execute_query(query, (name, mobile, email, address, landmark))
        return customer_id, "Customer added successfully"
    
    def update_customer(self, customer_id, name, mobile, email=None, address=None, landmark=None):
        """Update customer"""
        from utils.formatters import Formatters
        from utils.validators import Validators

        valid, msg = Validators.validate_customer_data(name, mobile, email, address)
        if not valid:
            return False, msg

        name = Formatters.format_title(name)
        if address:
            address = Formatters.format_title(address)
        if landmark:
            landmark = Formatters.format_title(landmark)

        query = """
        UPDATE customers 
        SET name = %s, mobile = %s, email = %s, address = %s, landmark = %s, updated_at = NOW()
        WHERE id = %s
        """
        self.db.execute_query(query, (name, mobile, email, address, landmark, customer_id))
        return True, "Customer updated successfully"
    
    def delete_customer(self, customer_id):
        """Soft delete customer"""
        query = "UPDATE customers SET is_active = FALSE WHERE id = %s"
        self.db.execute_query(query, (customer_id,))
        try:
            from utils.audit import log_delete
            log_delete('Customer', customer_id)
        except Exception as audit_err:
            import logging
            logging.getLogger(__name__).warning(f"Audit log failed for delete customer {customer_id}: {audit_err}")
        return True
