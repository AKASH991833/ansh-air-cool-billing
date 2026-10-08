"""
Configuration settings for AC Service Billing Software
SQLite Edition - No server installation required
"""
import os
import sys
from pathlib import Path

# Application paths
# PyInstaller extracts read-only bundled resources to _MEIPASS. Writable data
# belongs in AppData so installed users do not need administrator permissions.
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
    RESOURCE_DIR = Path(getattr(sys, '_MEIPASS', BASE_DIR))
    APP_DATA_DIR = Path(os.getenv('APPDATA', BASE_DIR / 'data')) / 'AnshAirCool'
else:
    BASE_DIR = Path(__file__).resolve().parent
    RESOURCE_DIR = BASE_DIR
    APP_DATA_DIR = BASE_DIR / 'data'

# ============================================================================
# DATABASE CONFIGURATION - SQLite (No MySQL Required)
# ============================================================================
# SQLite file is auto-created in the app's data directory
# No server, no credentials, no installation needed
# ============================================================================

# Database file path — writable storage in AppData for frozen apps, or local data in dev
DATA_DIR = APP_DATA_DIR
DB_PATH = DATA_DIR / 'desktop_software.db'

# Create data directory if needed
try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"[WARN] Could not create data directory: {e}")

DB_CONFIG = {
    'database': str(DB_PATH),
    'timeout': 30,
    'check_same_thread': False,
    'foreign_keys': True,
}

# Database name constant
DATABASE_NAME = 'Desktop_software'

# Application settings (fallbacks - override via Settings UI/DB)
APP_NAME = "Billing System"
APP_VERSION = "1.0.0"
COMPANY_NAME = "Your Company Name"

# Invoice settings (fallbacks - override via Settings UI/DB)
INVOICE_PREFIX = "INV"
INVOICE_START_NUMBER = 1001
GST_PERCENTAGE = 18.0

# WhatsApp (fallback - configurable via Settings UI/DB)
WHATSAPP_NUMBER = ""

# File paths
LOGO_PATH = RESOURCE_DIR / "assets" / "Logo.png"
INVOICE_TEMPLATE_PATH = RESOURCE_DIR / "assets" / "invoice_template.pdf"
EXPORT_DIR = (APP_DATA_DIR / "exports") if getattr(sys, 'frozen', False) else (BASE_DIR / "exports")
PDF_DIR = (APP_DATA_DIR / "pdfs") if getattr(sys, 'frozen', False) else (BASE_DIR / "pdfs")
LOG_DIR = (APP_DATA_DIR / "logs") if getattr(sys, 'frozen', False) else (BASE_DIR / "logs")

# Create necessary directories
for directory in [DATA_DIR, EXPORT_DIR, PDF_DIR, LOG_DIR]:
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[WARN] Could not create directory {directory}: {e}")

# UI Settings - Light theme is the default for clearer reading and cleaner UI.
# Dark mode remains available as a secondary option.
# Enterprise-grade palette with semantic tokens (fg_soft, *_soft tints, table tokens).
# UI Settings - Enterprise Light Theme is the permanent application theme (Dark mode removed)
COLORS = {
    'light': {
        'bg': '#f1f5f9',            # Page background - soft slate
        'fg': '#0f172a',            # Primary text
        'fg_soft': '#334155',       # Secondary text
        'primary': '#2563eb',       # Corporate blue - primary actions
        'primary_hover': '#1d4ed8', # Primary hover
        'primary_soft': '#dbeafe',  # Subtle blue tint for hover/active rows
        'secondary': '#475569',     # Muted text / secondary actions
        'success': '#16a34a',
        'success_soft': '#dcfce7',
        'warning': '#d97706',
        'warning_soft': '#fef3c7',
        'danger': '#dc2626',
        'danger_soft': '#fee2e2',
        'info': '#0ea5e9',
        'info_soft': '#e0f2fe',
        'card_bg': '#ffffff',
        'border': '#e2e8f0',
        'border_light': '#f1f5f9',
        'hover': '#f8fafc',
        'alt_row': '#f8fafc',
        'sidebar': '#ffffff',       # Clean white sidebar, separated by border
        'header': '#ffffff',
        'accent': '#2563eb',
        'muted': '#64748b',
        'table_header': '#f8fafc',
        'table_stripe': '#fafbfd',
        'table_border': '#e2e8f0',
        'shadow': 'rgba(15, 23, 42, 0.08)'
    }
}
# Point 'dark' to 'light' for compatibility so no legacy code can trigger dark mode
COLORS['dark'] = COLORS['light']

# Font settings - ENHANCED TYPOGRAPHY
FONTS = {
    'small': ('Segoe UI', 9),
    'normal': ('Segoe UI', 10),
    'medium': ('Segoe UI', 11),
    'large': ('Segoe UI', 12),
    'heading': ('Segoe UI', 14, 'bold'),
    'title': ('Segoe UI', 18, 'bold'),
    'display': ('Segoe UI', 24, 'bold'),
    'button': ('Segoe UI', 10, 'bold'),
    'label': ('Segoe UI', 10, 'bold'),
    'data': ('Segoe UI', 10),
    'body': ('Segoe UI', 10),                 # Standard body text
    'card_title': ('Segoe UI', 13, 'bold'),   # For card headers and section titles
    'metric_value': ('Segoe UI', 28, 'bold'), # For large numbers in metric cards
    'metric_label': ('Segoe UI', 11),         # For labels below metric values
    'table_header': ('Segoe UI', 11, 'bold'), # For treeview table headers
    'table_row': ('Segoe UI', 10),            # For treeview table rows
    'fab': ('Segoe UI', 20, 'bold'),          # For the Floating Action Button text
    'subheading': ('Segoe UI', 14),           # For date and revenue trend summary
}

# WhatsApp Configuration (fallbacks - override via Settings UI/DB)
WHATSAPP_ENABLED = True
WHATSAPP_BASE_URL = f"https://wa.me/91{WHATSAPP_NUMBER}"

# SMTP Email Configuration (fallbacks - override via Settings UI/DB)
SMTP_CONFIG = {
    'server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'port': int(os.getenv('SMTP_PORT', '587')),
    'username': os.getenv('SMTP_USERNAME', ''),
    'password': os.getenv('SMTP_PASSWORD', ''),
    'use_tls': os.getenv('SMTP_USE_TLS', 'True').lower() == 'true',
    'from_email': os.getenv('SMTP_FROM_EMAIL', 'your@email.com'),
    'from_name': os.getenv('SMTP_FROM_NAME', 'Your Company Name'),
}