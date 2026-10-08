"""
Utilities module for AC Service Billing Software

PERFORMANCE NOTE: Heavy optional dependencies (openpyxl, numpy, etc.) are NOT
imported here at module-level. They are lazily imported only when first used.
This reduces cold-start import time by ~1.7 seconds.
"""
# ── Always-needed lightweight utilities ──────────────────────────────────────
from .validators import Validators
from .formatters import Formatters
from .session_manager import SessionManager, get_session, is_user_logged_in, get_current_user, logout_user
from .unified_theme import UnifiedTheme
from .language import LanguageManager
from .logger import get_loggers, log_database_query
from .audit import AuditLogger, log_login, log_logout
from .event_bus import EventBus
from .shortcut_manager import ShortcutManager

# ── Lazy imports (imported on first access, not at startup) ──────────────────
# The following are heavy and only needed on specific user actions:
#   ExcelExporter     → openpyxl + numpy  (~1.7s)
#   PDFGenerator      → ProfessionalInvoiceGenerator → WeasyPrint / Qt WebEngine
#   WhatsAppHelper    → webbrowser
#   invoice_html_template → jinja2 / heavy string processing
# Use `from utils.excel_helper import ExcelExporter` directly in the callsite.

def __getattr__(name):
    """Lazy-load heavy modules only when first accessed via `from utils import X`."""
    lazy_map = {
        'PDFGenerator': ('utils.pdf_generator', 'PDFGenerator'),
        'ProfessionalInvoiceGenerator': ('utils.professional_invoice_generator', 'ProfessionalInvoiceGenerator'),
        'ExcelExporter': ('utils.excel_helper', 'ExcelExporter'),
        'WhatsAppHelper': ('utils.whatsapp_helper', 'WhatsAppHelper'),
        'generate_invoice_html': ('utils.invoice_html_template', 'generate_invoice_html'),
        'QuickCustomerSearch': ('utils.search_widget', 'QuickCustomerSearch'),
        'BarChartWidget': ('utils.chart_widgets', 'BarChartWidget'),
        'PieChartWidget': ('utils.chart_widgets', 'PieChartWidget'),
        'HorizontalBarChartWidget': ('utils.chart_widgets', 'HorizontalBarChartWidget'),
    }
    if name in lazy_map:
        module_path, attr = lazy_map[name]
        import importlib
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    raise AttributeError(f"module 'utils' has no attribute {name!r}")


__all__ = [
    'PDFGenerator',
    'Validators',
    'Formatters',
    'SessionManager',
    'get_session',
    'is_user_logged_in',
    'get_current_user',
    'logout_user',
    'ProfessionalInvoiceGenerator',
    'UnifiedTheme',
    'LanguageManager',
    'get_loggers',
    'log_database_query',
    'AuditLogger',
    'log_login',
    'log_logout',
    'QuickCustomerSearch',
    'BarChartWidget',
    'PieChartWidget',
    'HorizontalBarChartWidget',
    'ExcelExporter',
    'WhatsAppHelper',
    'EventBus',
    'ShortcutManager',
    'generate_invoice_html',
]
