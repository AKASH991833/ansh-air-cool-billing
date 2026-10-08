"""
Unified Theme - Dynamic Theme Management (Dark/Light)
Enterprise-grade Qt theme for AC Service Billing Software.

This module is the single source of truth for the application's look & feel.
Every view applies `get_main_stylesheet()` (via BaseView), so upgrading this
file upgrades the entire application UI at once — no business logic changes.
"""
from config import COLORS, FONTS
from PySide6.QtGui import QPalette, QColor
import threading
import os

FONT_FAMILY = "'Segoe UI', 'Inter', Arial, sans-serif"


class UnifiedTheme:
    """Unified theme manager with dynamic mode support"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.current_mode = 'light'
        self.load_theme_mode()
        self._initialized = True

    def load_theme_mode(self):
        """Load preferred theme mode - permanently locked to enterprise light mode"""
        self.current_mode = 'light'
        return self.current_mode

    @classmethod
    def get_colors(cls):
        """Get colors for current theme mode (static accessor)"""
        instance = cls()
        mode = instance.current_mode if instance.current_mode in COLORS else 'light'
        return COLORS.get(mode, COLORS['light'])

    @classmethod
    def apply_palette(cls, widget):
        """Apply QPalette colors to a widget for proper theme support"""
        colors = cls.get_colors()
        palette = QPalette()

        # Base colors
        palette.setColor(QPalette.ColorRole.Window, QColor(colors['bg']))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(colors['fg']))
        palette.setColor(QPalette.ColorRole.Base, QColor(colors['card_bg']))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors['alt_row']))
        palette.setColor(QPalette.ColorRole.Text, QColor(colors['fg']))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(colors['primary']))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors['bg'] if colors['bg'].startswith('#f') or colors['bg'] == '#f1f5f9' else '#ffffff'))
        palette.setColor(QPalette.ColorRole.Button, QColor(colors['card_bg']))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors['fg']))
        palette.setColor(QPalette.ColorRole.BrightText, QColor('#ffffff'))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(colors['card_bg']))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(colors['fg']))

        # Disabled colors
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(colors['muted']))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(colors['muted']))

        widget.setPalette(palette)

        # Style refresh
        if hasattr(widget, 'style'):
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    @classmethod
    def apply_table_theme(cls, table):
        """Apply theme specifically to QTableWidget"""
        colors = cls.get_colors()
        cls.apply_palette(table)
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {colors['card_bg']};
                color: {colors['fg']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                gridline-color: {colors['table_border']};
                selection-background-color: {colors['primary']};
                selection-color: #ffffff;
                alternate-background-color: {colors['table_stripe']};
                font-family: {FONT_FAMILY};
            }}
            QTableWidget::item {{
                padding: 8px 10px;
                border-bottom: 1px solid {colors['border_light']};
            }}
            QTableWidget::item:selected {{
                background-color: {colors['primary']};
                color: #ffffff;
            }}
            QHeaderView::section {{
                background-color: {colors['table_header']};
                color: {colors['fg']};
                padding: 10px 12px;
                border: none;
                border-bottom: 2px solid {colors['border']};
                font-weight: bold;
                font-size: 9pt;
            }}
        """)

    @classmethod
    def get_main_stylesheet(cls):
        """Get the full enterprise-grade global stylesheet based on current mode"""
        colors = cls.get_colors()
        c = colors
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        chevron_path = os.path.join(base_dir, "assets", "icons", "chevron_down.png").replace("\\", "/")
        chevron_dark = os.path.join(base_dir, "assets", "icons", "chevron_down_dark.png").replace("\\", "/")
        arrow_icon = chevron_dark if cls().current_mode == 'dark' else chevron_path

        return f"""
        /* ══════════════════════════════════════════════════════════════════
           GLOBAL FRAME & TYPOGRAPHY
           ══════════════════════════════════════════════════════════════════ */
        QMainWindow, QWidget {{
            background-color: {c['bg']};
            color: {c['fg']};
            font-family: {FONT_FAMILY};
            font-size: 10pt;
        }}

        QLabel {{
            background: transparent;
            color: {c['fg']};
        }}

        /* ── Typography helpers ── */
        QLabel#headingLabel, QLabel#titleLabel {{
            font-size: 18pt;
            font-weight: 700;
            color: {c['fg']};
            letter-spacing: -0.3px;
        }}
        QLabel#subheadingLabel, QLabel#subtitleLabel {{
            font-size: 10pt;
            color: {c['fg_soft']};
        }}
        QLabel#sectionLabel {{
            font-size: 12pt;
            font-weight: 700;
            color: {c['fg']};
            border-bottom: 2px solid {c['border']};
            padding-bottom: 6px;
        }}
        QLabel#inputLabel {{
            font-size: 8pt;
            font-weight: 700;
            color: {c['secondary']};
            letter-spacing: 0.8px;
        }}

        /* ── Cards / panels ── */
        QFrame#cardFrame, QFrame#modernCard, QFrame#kpiCard, QFrame#metricCardContainer {{
            background-color: {c['card_bg']};
            border: 1px solid {c['border']};
            border-radius: 10px;
        }}
        QFrame#filterBar, QFrame#controlFrame {{
            background-color: {c['card_bg']};
            border: 1px solid {c['border']};
            border-radius: 10px;
        }}
        QFrame#toast {{
            background-color: {c['fg']};
            color: {c['bg']};
            border-radius: 8px;
        }}

        /* ══════════════════════════════════════════════════════════════════
           SIDEBAR
           ══════════════════════════════════════════════════════════════════ */
        QFrame#sidebarFrame {{
            background-color: {c['sidebar']};
            border: none;
            border-right: 1px solid {c['border']};
        }}

        QPushButton#sidebarButton {{
            background-color: transparent;
            color: {c['fg_soft']};
            border: none;
            border-radius: 8px;
            padding: 10px 14px;
            font-weight: 500;
            font-family: {FONT_FAMILY};
            font-size: 10pt;
            text-align: left;
        }}
        QPushButton#sidebarButton:hover {{
            background-color: {c['hover']};
            color: {c['fg']};
        }}
        QPushButton#sidebarButton:checked {{
            background-color: {c['primary_soft']};
            color: {c['primary']};
            font-weight: 700;
        }}
        QPushButton#sidebarButton:focus {{ outline: none; }}

        /* Sidebar child labels inherit the button state colors */
        QPushButton#sidebarButton QLabel {{
            color: {c['fg_soft']};
            background: transparent;
        }}
        QPushButton#sidebarButton:hover QLabel {{ color: {c['fg']}; }}
        QPushButton#sidebarButton:checked QLabel {{ color: {c['primary']}; }}

        /* ══════════════════════════════════════════════════════════════════
           HEADER & STATUS BAR
           ══════════════════════════════════════════════════════════════════ */
        QFrame#headerFrame {{
            background-color: {c['card_bg']};
            border: none;
            border-bottom: 1px solid {c['border']};
        }}
        QStatusBar#statusBarFrame, QStatusBar {{
            background-color: {c['card_bg']};
            color: {c['fg']};
            border-top: 1px solid {c['border']};
            font-size: 9pt;
        }}

        /* ══════════════════════════════════════════════════════════════════
           BUTTONS — enterprise variants
           ══════════════════════════════════════════════════════════════════ */
        QPushButton {{
            background-color: {c['primary']};
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-family: {FONT_FAMILY};
            font-size: 9.5pt;
            font-weight: 600;
            min-height: 32px;
        }}
        QPushButton:hover {{ background-color: {c['primary_hover']}; }}
        QPushButton:pressed {{ background-color: {c['primary_hover']}; }}
        QPushButton:disabled {{
            background-color: {c['border']};
            color: {c['muted']};
        }}

        /* Primary action (explicit) */
        QPushButton#primaryButton {{ background-color: {c['primary']}; color: #ffffff; }}
        QPushButton#primaryButton:hover {{ background-color: {c['primary_hover']}; }}

        /* Secondary / outlined */
        QPushButton#secondaryButton {{
            background-color: transparent;
            color: {c['fg']};
            border: 1px solid {c['border']};
        }}
        QPushButton#secondaryButton:hover {{
            background-color: {c['hover']};
            border-color: {c['primary']};
            color: {c['primary']};
        }}

        /* Success */
        QPushButton#successButton {{ background-color: {c['success']}; color: #ffffff; }}
        QPushButton#successButton:hover {{ background-color: #15803d; }}

        /* Danger */
        QPushButton#dangerButton {{ background-color: {c['danger']}; color: #ffffff; }}
        QPushButton#dangerButton:hover {{ background-color: #b91c1c; }}

        /* Top Header + New Invoice Standout Button */
        QPushButton#newInvoiceHeaderBtn {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c['primary']}, stop:1 {c['primary_hover']});
            color: #ffffff;
            border: 1px solid {c['primary']};
            border-radius: 8px;
            padding: 8px 18px;
            font-size: 10pt;
            font-weight: 700;
            letter-spacing: 0.3px;
        }}
        QPushButton#newInvoiceHeaderBtn:hover {{
            background: {c['primary_hover']};
            border-color: #93c5fd;
        }}
        QPushButton#newInvoiceHeaderBtn:pressed {{
            background: {c['primary']};
        }}

        /* WhatsApp Direct Button - 1-Click Action */
        QPushButton#whatsappDirectBtn, QPushButton#whatsappBtn, QPushButton.whatsappButton {{
            background-color: #25D366;
            color: #ffffff;
            border: 1px solid #22c55e;
            border-radius: 8px;
            padding: 8px 18px;
            font-size: 10pt;
            font-weight: 700;
        }}
        QPushButton#whatsappDirectBtn:hover, QPushButton#whatsappBtn:hover, QPushButton.whatsappButton:hover {{
            background-color: #128C7E;
            border-color: #16a34a;
        }}
        QPushButton#whatsappDirectBtn:pressed, QPushButton#whatsappBtn:pressed, QPushButton.whatsappButton:pressed {{
            background-color: #075E54;
        }}

        /* Status Badges */
        QLabel#badgePaid {{
            background-color: #dcfce7;
            color: #15803d;
            border: 1px solid #86efac;
            border-radius: 6px;
            padding: 3px 10px;
            font-weight: 700;
            font-size: 8.5pt;
        }}
        QLabel#badgePending {{
            background-color: #fee2e2;
            color: #b91c1c;
            border: 1px solid #fca5a5;
            border-radius: 6px;
            padding: 3px 10px;
            font-weight: 700;
            font-size: 8.5pt;
        }}
        QLabel#badgePartial {{
            background-color: #fef3c7;
            color: #b45309;
            border: 1px solid #fcd34d;
            border-radius: 6px;
            padding: 3px 10px;
            font-weight: 700;
            font-size: 8.5pt;
        }}

        /* Icon-only / subtle button */
        QPushButton#iconButton {{
            background-color: {c['hover']};
            color: {c['fg']};
            border: 1px solid {c['border']};
            border-radius: 6px;
            padding: 6px 10px;
            min-width: 32px;
            min-height: 32px;
        }}
        QPushButton#iconButton:hover {{
            background-color: {c['primary_soft']};
            border-color: {c['primary']};
            color: {c['primary']};
        }}

        /* ══════════════════════════════════════════════════════════════════
           INPUTS
           ══════════════════════════════════════════════════════════════════ */
        QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit {{
            background-color: {c['card_bg']};
            color: {c['fg']};
            border: 1px solid {c['border']};
            border-radius: 6px;
            padding: 8px 10px;
            font-family: {FONT_FAMILY};
            font-size: 10pt;
            selection-background-color: {c['primary']};
            selection-color: #ffffff;
        }}
        QLineEdit:hover, QComboBox:hover, QDateEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover,
        QTextEdit:hover, QPlainTextEdit:hover {{
            border-color: {c['primary']};
        }}
        QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,
        QTextEdit:focus, QPlainTextEdit:focus {{
            border: 1.5px solid {c['primary']};
        }}
        QLineEdit:disabled, QComboBox:disabled, QDateEdit:disabled, QSpinBox:disabled,
        QDoubleSpinBox:disabled, QTextEdit:disabled {{ background-color: {c['border_light']}; color: {c['muted']}; }}

        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 26px;
            border: none;
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
        }}
        QComboBox::down-arrow {{
            image: url("{arrow_icon}");
            width: 12px;
            height: 12px;
            margin-right: 7px;
        }}
        QComboBox::down-arrow:on {{
            top: 1px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {c['card_bg']};
            color: {c['fg']};
            border: 1px solid {c['border']};
            border-radius: 6px;
            selection-background-color: {c['primary']};
            selection-color: #ffffff;
            outline: none;
            padding: 4px;
        }}

        QDateEdit::drop-down, QSpinBox::up-button, QSpinBox::down-button,
        QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
            border: none;
            background: transparent;
            width: 20px;
        }}

        /* ══════════════════════════════════════════════════════════════════
           TABLES
           ══════════════════════════════════════════════════════════════════ */
        QTableWidget, QTableView {{
            background-color: {c['card_bg']};
            color: {c['fg']};
            border: 1px solid {c['table_border']};
            border-radius: 8px;
            gridline-color: {c['table_border']};
            alternate-background-color: {c['table_stripe']};
            font-family: {FONT_FAMILY};
            font-size: 10pt;
        }}
        QTableWidget::item {{
            padding: 6px 10px;
            border-bottom: 1px solid {c['border_light']};
        }}
        QTableWidget::item:selected {{
            background-color: {c['primary']};
            color: #ffffff;
        }}
        QTableWidget::item:hover {{ background-color: {c['hover']}; }}

        QHeaderView::section {{
            background-color: {c['table_header']};
            color: {c['fg_soft']};
            padding: 10px 12px;
            border: none;
            border-bottom: 2px solid {c['border']};
            font-family: {FONT_FAMILY};
            font-size: 9pt;
            font-weight: 700;
        }}
        QHeaderView::section:hover {{ color: {c['primary']}; }}

        /* ══════════════════════════════════════════════════════════════════
           TABS
           ══════════════════════════════════════════════════════════════════ */
        QTabWidget::pane {{
            border: 1px solid {c['border']};
            border-radius: 8px;
            background-color: {c['card_bg']};
            top: -1px;
        }}
        QTabBar::tab {{
            background-color: transparent;
            color: {c['fg_soft']};
            padding: 9px 18px;
            font-family: {FONT_FAMILY};
            font-size: 10pt;
            font-weight: 500;
            border: none;
            border-bottom: 2px solid transparent;
        }}
        QTabBar::tab:hover {{ color: {c['primary']}; }}
        QTabBar::tab:selected {{
            color: {c['primary']};
            border-bottom: 2px solid {c['primary']};
            font-weight: 700;
        }}

        /* ══════════════════════════════════════════════════════════════════
           SCROLLBARS
           ══════════════════════════════════════════════════════════════════ */
        QScrollBar:vertical {{
            background: transparent;
            border: none;
            border-radius: 4px;
            width: 10px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical {{
            background: {c['border']};
            border-radius: 4px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{ background: {c['muted']}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}

        QScrollBar:horizontal {{
            background: transparent;
            border: none;
            border-radius: 4px;
            height: 10px;
            margin: 2px;
        }}
        QScrollBar::handle:horizontal {{
            background: {c['border']};
            border-radius: 4px;
            min-width: 24px;
        }}
        QScrollBar::handle:horizontal:hover {{ background: {c['muted']}; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}

        /* ══════════════════════════════════════════════════════════════════
           CHECKBOX / RADIO / GROUP BOX
           ══════════════════════════════════════════════════════════════════ */
        QCheckBox, QRadioButton {{
            color: {c['fg']};
            font-size: 10pt;
            spacing: 8px;
        }}
        QCheckBox::indicator, QRadioButton::indicator {{
            width: 17px;
            height: 17px;
            border: 1px solid {c['border']};
            border-radius: 4px;
            background-color: {c['card_bg']};
        }}
        QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
            background-color: {c['primary']};
            border-color: {c['primary']};
        }}
        QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
            border-color: {c['primary']};
        }}

        QGroupBox {{
            font-weight: 600;
            font-size: 10.5pt;
            border: 1px solid {c['border']};
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 14px;
            background-color: {c['card_bg']};
            color: {c['fg']};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 12px;
            padding: 0 6px;
            color: {c['primary']};
        }}

        /* ══════════════════════════════════════════════════════════════════
           DIALOGS, MENUS, MESSAGE BOXES, TOOLTIPS
           ══════════════════════════════════════════════════════════════════ */
        QDialog {{
            background-color: {c['bg']};
            color: {c['fg']};
        }}
        QMenu {{
            background-color: {c['card_bg']};
            color: {c['fg']};
            border: 1px solid {c['border']};
            border-radius: 8px;
            padding: 6px;
        }}
        QMenu::item {{
            padding: 8px 24px 8px 12px;
            border-radius: 6px;
            font-size: 10pt;
        }}
        QMenu::item:selected {{ background-color: {c['primary']}; color: #ffffff; }}
        QMenu::separator {{ height: 1px; background: {c['border']}; margin: 6px 10px; }}

        QMessageBox {{
            background-color: {c['card_bg']};
            color: {c['fg']};
        }}
        QMessageBox QLabel {{ color: {c['fg']}; font-size: 10pt; }}

        QToolTip {{
            background-color: #0f172a;
            color: #ffffff;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 9pt;
            font-weight: 500;
        }}

        /* ══════════════════════════════════════════════════════════════════
           MISC
           ══════════════════════════════════════════════════════════════════ */
        QProgressBar {{
            background-color: {c['border_light']};
            border: none;
            border-radius: 5px;
            text-align: center;
            color: {c['fg']};
            height: 12px;
            font-size: 8pt;
        }}
        QProgressBar::chunk {{
            background-color: {c['primary']};
            border-radius: 5px;
        }}
        QSplitter::handle {{ background-color: {c['border']}; width: 1px; }}
        QListWidget {{
            background-color: {c['card_bg']};
            color: {c['fg']};
            border: 1px solid {c['border']};
            border-radius: 8px;
            padding: 4px;
        }}
        QListWidget::item {{
            padding: 8px 10px;
            border-radius: 6px;
        }}
        QListWidget::item:selected {{ background-color: {c['primary']}; color: #ffffff; }}
        QListWidget::item:hover {{ background-color: {c['hover']}; }}

        QScrollArea {{ background: transparent; border: none; }}
        QStackedWidget {{ background: transparent; }}
        """

    @classmethod
    def get_login_stylesheet(cls):
        """Specialized enterprise stylesheet for the login screen"""
        c = cls.get_colors()
        return f"""
        QWidget {{
            background-color: {c['bg']};
            color: {c['fg']};
            font-family: {FONT_FAMILY};
        }}
        QLabel {{
            background: transparent;
        }}
        QLabel#loginTitle {{
            font-size: 22pt;
            font-weight: 800;
            color: {c['fg']};
            letter-spacing: -0.5px;
        }}
        QLabel#loginSubtitle {{
            font-size: 10pt;
            color: {c['fg_soft']};
        }}
        QLabel#inputLabel {{
            font-size: 8pt;
            font-weight: 700;
            color: {c['secondary']};
            letter-spacing: 1px;
        }}
        QFrame#loginCard {{
            background-color: {c['card_bg']};
            border: 1px solid {c['border']};
            border-radius: 18px;
        }}
        QLineEdit {{
            background-color: {c['card_bg']};
            color: {c['fg']};
            border: 1px solid {c['border']};
            border-radius: 10px;
            padding: 12px 16px;
            font-size: 10.5pt;
        }}
        QLineEdit:focus {{
            border: 1.5px solid {c['primary']};
        }}
        QLineEdit:hover {{ border-color: {c['primary']}; }}
        QPushButton#loginButton {{
            background-color: {c['primary']};
            color: #ffffff;
            border: none;
            border-radius: 10px;
            padding: 14px;
            font-size: 10.5pt;
            font-weight: 700;
            letter-spacing: 1px;
        }}
        QPushButton#loginButton:hover {{ background-color: {c['primary_hover']}; }}
        QPushButton#loginButton:pressed {{ background-color: {c['primary_hover']}; }}
        QPushButton#loginButton:disabled {{
            background-color: {c['border']};
            color: {c['muted']};
        }}
        QPushButton#togglePasswordBtn {{
            background-color: {c['hover']};
            color: {c['fg']};
            border: 1px solid {c['border']};
            border-radius: 10px;
            font-size: 13pt;
        }}
        QPushButton#togglePasswordBtn:hover {{
            background-color: {c['primary_soft']};
            border-color: {c['primary']};
            color: {c['primary']};
        }}
        QCheckBox {{
            color: {c['fg_soft']};
            font-size: 9.5pt;
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 5px;
            border: 1px solid {c['border']};
            background-color: {c['card_bg']};
        }}
        QCheckBox::indicator:checked {{
            background-color: {c['primary']};
            border-color: {c['primary']};
        }}
        QLabel#errorLabel {{
            color: {c['danger']};
            font-size: 9pt;
            background-color: {c['danger_soft']};
            border-radius: 8px;
            padding: 10px 14px;
            border: 1px solid {c['danger']}55;
            font-weight: 500;
        }}
        QLabel#footerLabel {{
            color: {c['muted']};
            font-size: 8pt;
        }}
        """
