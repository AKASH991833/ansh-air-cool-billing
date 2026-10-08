"""
Audit Trail - Log all important operations
Tracks who did what and when across the application
"""
from datetime import datetime
from database.db_connection import DatabaseConnection
from utils.session_manager import get_session
from utils.app_settings import get_setting


class AuditLogger:
    """Log and retrieve audit events"""

    ACTIONS = {
        'LOGIN': 'Login',
        'LOGOUT': 'Logout',
        'CREATE': 'Create',
        'UPDATE': 'Update',
        'DELETE': 'Delete',
        'RESTORE': 'Restore',
        'PAYMENT': 'Payment',
        'EXPORT': 'Export',
        'PRINT': 'Print',
        'BACKUP': 'Backup',
        'SETTINGS': 'Settings',
        'PASSWORD_CHANGE': 'Password Change',
        'USERNAME_CHANGE': 'Username Change',
    }

    @staticmethod
    def log(action, entity_type, entity_id=None, details=None):
        """Log an audit event"""
        try:
            session = get_session()
            user = session.get_current_user()
            user_id = user.get('id') if user else None
            username = user.get('username', 'Unknown') if user else 'System'

            db = DatabaseConnection()
            db.execute_query(
                "INSERT INTO audit_log (user_id, username, action, entity_type, entity_id, details) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (user_id, username, action, entity_type, entity_id, details)
            )
        except Exception as e:
            print(f"[AUDIT] Failed to log: {e}")

    @staticmethod
    def get_logs(limit=100, action=None, entity_type=None, user_id=None):
        """Get audit logs with optional filters"""
        db = DatabaseConnection()
        query = "SELECT * FROM audit_log WHERE 1=1"
        params = []
        if action:
            query += " AND action = %s"
            params.append(action)
        if entity_type:
            query += " AND entity_type = %s"
            params.append(entity_type)
        if user_id:
            query += " AND user_id = %s"
            params.append(user_id)
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        return db.execute_query(query, params, fetch_all=True) or []


def log_login(user_data):
    AuditLogger.log('LOGIN', 'User', user_data.get('id'), f"User {user_data.get('username')} logged in")


def log_logout(user_data):
    AuditLogger.log('LOGOUT', 'User', user_data.get('id'), f"User {user_data.get('username')} logged out")


def log_create(entity_type, entity_id, details=None):
    AuditLogger.log('CREATE', entity_type, entity_id, details)


def log_update(entity_type, entity_id, details=None):
    AuditLogger.log('UPDATE', entity_type, entity_id, details)


def log_delete(entity_type, entity_id, details=None):
    AuditLogger.log('DELETE', entity_type, entity_id, details)


def log_payment(invoice_id, amount, mode):
    symbol = get_setting("currency_symbol", "₹")
    AuditLogger.log('PAYMENT', 'Invoice', invoice_id, f"Payment {symbol}{amount} via {mode}")


def log_password_change(user_id):
    AuditLogger.log('PASSWORD_CHANGE', 'User', user_id, "Password changed")


def log_backup(path):
    AuditLogger.log('BACKUP', 'Database', None, f"Backup created: {path}")


def log_settings_change(details):
    AuditLogger.log('SETTINGS', 'AppSettings', None, details)
