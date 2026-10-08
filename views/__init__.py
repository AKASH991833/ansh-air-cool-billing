"""
Views module for AC Service Billing Software - PySide6 Edition

PERFORMANCE: All view classes are lazy-loaded via __getattr__ so that Python
only imports (and JIT-compiles) a view when it is first actually used.
This cuts the startup time significantly — especially for heavy views like
CustomerView, TechnicianView, InvoiceManagementView, and ReportView.
"""

# Only the two windows needed at startup are imported eagerly:
from .login_view import LoginWindow
from .main_window import MainWindow

# Legacy / compat aliases available without lazy loading
MainView = MainWindow

def __getattr__(name):
    """Lazy-load any view by name on first access."""
    _lazy = {
        'EnhancedDashboardView': ('.enhanced_dashboard_view', 'EnhancedDashboardView'),
        'DashboardView':         ('.enhanced_dashboard_view', 'EnhancedDashboardView'),
        'InvoiceView':           ('.invoice_view',            'InvoiceView'),
        'CustomerView':          ('.customer_view',           'CustomerView'),
        'AMCView':               ('.amc_view',                'AMCView'),
        'TechnicianView':        ('.technician_view',         'TechnicianView'),
        'SettingsView':          ('.settings_view',           'SettingsView'),
        'ProfileSettingsView':   ('.settings_view',           'ProfileSettingsView'),
        'ChangePasswordDialog':  ('.settings_view',           'ChangePasswordDialog'),
        'ChangePasswordView':    ('.settings_view',           'ChangePasswordDialog'),
        'MasterDataView':        ('.settings_view',           'SettingsView'),
        'InvoiceManagementView': ('.invoice_management_view', 'InvoiceManagementView'),
        'DailyLogView':          ('.daily_log_view',          'DailyLogView'),
        'InventoryView':         ('.inventory_view',          'InventoryView'),
        'ReportView':            ('.report_view',             'ReportView'),
        'DeletedItemsView':      ('.deleted_items_view',      'DeletedItemsView'),
        'EditInvoiceDialog':     ('.edit_invoice_dialog',     'EditInvoiceDialog'),
        'EmailInvoiceDialog':    ('.email_invoice_dialog',    'EmailInvoiceDialog'),
        'CustomerLedgerDialog':  ('.customer_ledger_dialog',  'CustomerLedgerDialog'),
        'WhatsAppShareDialog':   ('.whatsapp_share_dialog',   'WhatsAppShareDialog'),
    }
    if name in _lazy:
        rel_module, attr = _lazy[name]
        import importlib
        mod = importlib.import_module(rel_module, package=__name__)
        return getattr(mod, attr)
    raise AttributeError(f"module 'views' has no attribute {name!r}")


__all__ = [
    'LoginWindow',
    'MainWindow',
    'MainView',
    'DashboardView',
    'EnhancedDashboardView',
    'InvoiceView',
    'CustomerView',
    'AMCView',
    'TechnicianView',
    'InvoiceManagementView',
    'DailyLogView',
    'InventoryView',
    'ReportView',
    'DeletedItemsView',
    'SettingsView',
    'MasterDataView',
    'ProfileSettingsView',
    'ChangePasswordDialog',
    'ChangePasswordView',
    'EditInvoiceDialog',
    'EmailInvoiceDialog',
    'CustomerLedgerDialog',
    'WhatsAppShareDialog',
]