"""
Settings View - PySide6 Settings and Master Data Management
Professional settings interface with profile, shop details, and master data
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea,
    QSizePolicy, QTabWidget, QComboBox, QDoubleSpinBox, QSpinBox,
    QTextEdit, QFormLayout, QMessageBox, QDialog, QButtonGroup,
    QDialogButtonBox, QCheckBox, QRadioButton, QTimeEdit, QGroupBox,
    QLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QCursor, QBrush, QColor, QKeySequence

from utils.unified_theme import UnifiedTheme
from utils.app_settings import get_setting
from views.base_window import BaseView
import os

CHEVRON_ICON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "icons", "chevron_down.png"
).replace("\\", "/")



def clear_invoice_pdf_cache():
    """Purge stale generated invoice PDFs so that any changes to shop details/settings reflect immediately"""
    try:
        from config import PDF_DIR
        import glob
        for f in glob.glob(os.path.join(str(PDF_DIR), "*.pdf")):
            try:
                os.remove(f)
            except Exception:
                pass
    except Exception:
        pass


class QWidgetWrapper(QWidget):
    """Simple wrapper class for QWidget layouts"""
    def __init__(self, layout):
        super().__init__()
        self.setLayout(layout)


class SettingsView(BaseView):
    """Settings and master data management view"""
    
    # Signal emitted when settings are saved
    settings_saved = Signal()

    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data

        self._setup_ui()
        self.load_user_profile()
        self.load_application_settings()

    def load_application_settings(self):
        """Load application settings from DB and update UI with robust error handling"""
        print("[SETTINGS_VIEW] Loading settings from DB...")
        from controllers.settings_controller import SettingsController
        from database.db_connection import DatabaseConnection
        
        try:
            db = DatabaseConnection()
            sc = SettingsController(db)
            settings = sc.get_application_settings()
            
            if hasattr(self, 'invoice_prefix_input'):
                self.invoice_prefix_input.setText(str(settings.get('invoice_prefix', 'INV')))
            if hasattr(self, 'invoice_start_spin'):
                self.invoice_start_spin.setValue(int(settings.get('starting_invoice_number', 1001)))
            if hasattr(self, 'gst_spin'):
                self.gst_spin.setValue(float(settings.get('default_gst_percentage') or 18.0))
            
            if hasattr(self, 'opening_time'):
                from PySide6.QtCore import QTime
                ot = QTime.fromString(settings.get('opening_time', '09:00'), "HH:mm")
                if ot.isValid(): self.opening_time.setTime(ot)
                
            if hasattr(self, 'closing_time'):
                from PySide6.QtCore import QTime
                ct = QTime.fromString(settings.get('closing_time', '20:00'), "HH:mm")
                if ct.isValid(): self.closing_time.setTime(ct)
                
            if hasattr(self, 'terms_input'):
                self.terms_input.setPlainText(settings.get('terms_conditions', '1. Goods once sold will not be taken back.\n2. Warranty as per company policy.\n3. Payment due within 7 days.\n4. Service warranty only on selected parts.'))
            if hasattr(self, 'thanks_note_input'):
                self.thanks_note_input.setText(settings.get('thank_you_note', 'Thank you for your business!'))
            if hasattr(self, 'watermark_input'):
                self.watermark_input.setText(settings.get('invoice_watermark', 'INVOICE'))
            if hasattr(self, 'default_notes_input'):
                self.default_notes_input.setText(settings.get('default_notes', 'All Work Done'))
            if hasattr(self, 'app_name_input'):
                self.app_name_input.setText(settings.get('app_name', 'AC Service Billing'))
            if hasattr(self, 'shop_type_combo'):
                st = settings.get('shop_type', 'AC Service')
                idx = self.shop_type_combo.findText(st)
                if idx >= 0:
                    self.shop_type_combo.setCurrentIndex(idx)
            if hasattr(self, 'company_name_input'):
                self.company_name_input.setText(settings.get('company_name', 'Your Company Name'))
            if hasattr(self, 'currency_input'):
                self.currency_input.setText(settings.get('currency_symbol', '\u20b9'))
            if hasattr(self, 'date_format_input'):
                self.date_format_input.setText(settings.get('date_format', 'dd-MM-yyyy'))
            if hasattr(self, 'smtp_server_input'):
                self.smtp_server_input.setText(settings.get('smtp_server', 'smtp.gmail.com'))
            if hasattr(self, 'smtp_port_input'):
                self.smtp_port_input.setText(settings.get('smtp_port', '587'))
            if hasattr(self, 'smtp_username_input'):
                self.smtp_username_input.setText(settings.get('smtp_username', ''))
            if hasattr(self, 'smtp_password_input'):
                self.smtp_password_input.setText(settings.get('smtp_password', ''))
            if hasattr(self, 'smtp_from_email_input'):
                self.smtp_from_email_input.setText(settings.get('smtp_from_email', 'your@email.com'))
            if hasattr(self, 'smtp_from_name_input'):
                self.smtp_from_name_input.setText(settings.get('smtp_from_name', 'Your Company Name'))
            if hasattr(self, 'email_subject_input'):
                self.email_subject_input.setText(settings.get('email_subject', 'Invoice #{invoice_number} - {company_name}'))
            if hasattr(self, 'email_body_input'):
                self.email_body_input.setPlainText(settings.get('email_body', 'Dear {customer_name},\n\nPlease find attached invoice #{invoice_number}.\n\nThank you for your business!\n{company_name}'))

            if hasattr(self, 'service_types_input'):
                self.service_types_input.setText(settings.get('service_types', 'AC Service,Installation,Repair,Gas Refilling,AMC Visit,AC Rent Delivery,AC Rent Pickup,Other'))
            if hasattr(self, 'ac_types_input'):
                self.ac_types_input.setText(settings.get('ac_types', 'Split,Window,Cassette,Tower,Other'))
            if hasattr(self, 'ac_ton_capacities_input'):
                self.ac_ton_capacities_input.setText(settings.get('ac_ton_capacities', '1.0,1.5,2.0,3.0,Other'))
            if hasattr(self, 'ac_inverter_options_input'):
                self.ac_inverter_options_input.setText(settings.get('ac_inverter_options', 'No,Yes'))
            if hasattr(self, 'star_ratings_input'):
                self.star_ratings_input.setText(settings.get('star_ratings', 'N/A,1,2,3,4,5'))
                
            print(f"[SETTINGS_VIEW] Successfully applied {len(settings)} settings to UI")
        except Exception as e:
            print(f"[ERROR] Failed to apply settings to UI: {e}")

    def update_theme_colors(self):
        """Update theme colors for proper dark theme support"""
        colors = self.theme_manager.get_colors()
        
        # Apply QPalette colors
        self.theme_manager.apply_palette(self)
        
        # Apply stylesheet
        self.setStyleSheet(self.theme_manager.get_main_stylesheet())
        
        # Apply theme directly to table for proper alternating colors
        if hasattr(self, 'master_table'):
            self.theme_manager.apply_table_theme(self.master_table)
        
        # Refresh data
        self.load_user_profile()

    # ── Enterprise Design Tokens ─────────────────────────────────────
    S = {
        'bg':        '#f8fafc',
        'card':      '#ffffff',
        'border':    '#e2e8f0',
        'border_lt': '#f1f5f9',
        'primary':   '#2563eb',
        'primary_lt':'#eff6ff',
        'text':      '#0f172a',
        'text2':     '#475569',
        'muted':     '#64748b',
        'success':   '#059669',
        'success_lt':'#dcfce7',
        'warning':   '#d97706',
        'warning_lt':'#fef3c7',
        'danger':    '#dc2626',
        'danger_lt': '#fee2e2',
        'hover':     '#f1f5f9',
    }

    def _setup_ui(self):
        """Setup enterprise settings UI with left-sidebar navigation."""
        S = self.S
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setStyleSheet(f"background:{S['bg']};")

        # ── Page header strip ───────────────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(72)
        header.setStyleSheet(f"""
            QFrame {{
                background: {S['card']};
                border-bottom: 1px solid {S['border']};
            }}
        """)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(28, 0, 28, 0)
        hl.setSpacing(14)

        icon_lbl = QLabel("\u2699\ufe0f")
        icon_lbl.setStyleSheet("font-size: 24pt; background: transparent;")
        hl.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        h1 = QLabel("Settings")
        h1.setStyleSheet(f"font-size: 18pt; font-weight: 800; color: {S['text']}; background: transparent;")
        title_col.addWidget(h1)
        sub = QLabel("Configure profile, shop details, invoice settings and more")
        sub.setStyleSheet(f"font-size: 9pt; color: {S['muted']}; background: transparent;")
        title_col.addWidget(sub)
        hl.addLayout(title_col)
        hl.addStretch()
        root.addWidget(header)

        # ── Body: sidebar + content ───────────────────────────────────────────────
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        # Left navigation sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(210)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background: {S['card']};
                border-right: 1px solid {S['border']};
            }}
        """)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(10, 20, 10, 20)
        sb_layout.setSpacing(3)

        # Section label above nav
        nav_lbl = QLabel("SETTINGS")
        nav_lbl.setStyleSheet(f"""
            font-size: 7pt; font-weight: 800; letter-spacing: 1.5px;
            color: {S['muted']}; background: transparent; padding: 0 6px 8px 6px;
        """)
        sb_layout.addWidget(nav_lbl)

        nav_items = [
            ("\U0001f464", "User Profile",     0),
            ("\U0001f3ea", "Shop Details",     1),
            ("\u2699\ufe0f",  "Application",      2),
            ("\U0001f4ca", "Master Data",      3),
            ("\u2328\ufe0f",  "Shortcuts",        4),
            ("\U0001f310", "Language",         5),
            ("\U0001f4be", "Backup & Restore", 6),
        ]

        self._nav_btns = {}
        self._content_stack = None   # set below

        for icon, label, idx in nav_items:
            btn = QPushButton(f"  {icon}  {label}")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(40)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {S['text2']};
                    border: none;
                    border-left: 3px solid transparent;
                    border-radius: 0;
                    padding: 0 10px;
                    font-size: 9.5pt;
                    font-weight: 500;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background: {S['primary_lt']};
                    color: {S['primary']};
                    border-left: 3px solid {S['primary']}40;
                }}
                QPushButton:checked {{
                    background: {S['primary_lt']};
                    color: {S['primary']};
                    font-weight: 700;
                    border-left: 3px solid {S['primary']};
                }}
            """)
            btn.clicked.connect(lambda checked, i=idx: self._switch_settings_section(i))
            sb_layout.addWidget(btn)
            self._nav_btns[idx] = btn

        sb_layout.addStretch()

        # Version badge
        ver = QLabel("AC Service Billing v2.0")
        ver.setStyleSheet(f"""
            font-size: 7.5pt; color: {S['muted']};
            background: transparent; padding: 4px;
        """)
        ver.setAlignment(Qt.AlignCenter)
        sb_layout.addWidget(ver)
        body.addWidget(sidebar)

        # Right content stacked widget
        from PySide6.QtWidgets import QStackedWidget
        self._content_stack = QStackedWidget()
        self._content_stack.setStyleSheet(f"background: {S['bg']};")

        self.user_tab       = self._create_user_profile_tab()
        self.shop_tab       = self._create_shop_details_tab()
        self.app_tab        = self._create_app_settings_tab()
        self.master_tab     = self._create_master_data_tab()
        self.shortcuts_tab  = self._create_shortcuts_tab()
        self.language_tab   = self._create_language_tab()
        self.backup_tab     = self._create_backup_tab()

        for tab in [self.user_tab, self.shop_tab, self.app_tab, self.master_tab,
                    self.shortcuts_tab, self.language_tab,
                    self.backup_tab]:
            self._content_stack.addWidget(tab)

        body.addWidget(self._content_stack, 1)
        root.addLayout(body, 1)

        # Activate first section
        self._switch_settings_section(0)

    def _switch_settings_section(self, index: int):
        """Switch content area and update sidebar active highlight."""
        if self._content_stack:
            self._content_stack.setCurrentIndex(index)
        for idx, btn in self._nav_btns.items():
            btn.setChecked(idx == index)
    
    def _make_styled_group(self, title, colors=None, description=None):
        """White card container for a settings section."""
        S = self.S
        frame = QFrame()
        frame.setObjectName("settingsCard")
        frame.setStyleSheet(f"""
            QFrame#settingsCard {{
                background: {S['card']};
                border: 1px solid {S['border']};
                border-radius: 10px;
            }}
            QLabel {{
                background: transparent;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(8)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"font-size: 11pt; font-weight: 700; color: {S['text']}; background: transparent; border: none;")
        layout.addWidget(title_lbl)

        if description:
            desc_lbl = QLabel(description)
            desc_lbl.setWordWrap(True)
            desc_lbl.setStyleSheet(
                f"font-size: 8.5pt; color: {S['muted']}; background: transparent; border: none; margin-bottom: 2px;")
            layout.addWidget(desc_lbl)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {S['border']}; border: none; max-height: 1px; margin: 4px 0;")
        layout.addWidget(sep)
        return frame

    def _make_section_scroll(self):
        """Create a standard scrollable page wrapper with consistent padding."""
        S = self.S
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"border: none; background: {S['bg']};")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content.setStyleSheet(f"background: {S['bg']};")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)
        scroll.setWidget(content)
        return scroll, layout

    def _make_styled_line_input(self, placeholder=""):
        S = self.S
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setFixedHeight(38)
        inp.setStyleSheet(f"""
            QLineEdit {{
                background: {S['card']};
                color: {S['text']};
                border: 1px solid {S['border']};
                border-radius: 8px;
                padding: 0 12px;
                font-size: 10pt;
            }}
            QLineEdit:focus {{
                border: 2px solid {S['primary']};
                background: #fafcff;
            }}
            QLineEdit:hover {{
                border-color: #94a3b8;
            }}
        """)
        return inp

    def _make_styled_text_edit(self, height=80):
        S = self.S
        te = QTextEdit()
        te.setMinimumHeight(height)
        te.setMaximumHeight(height + 40)
        te.setStyleSheet(f"""
            QTextEdit {{
                background: {S['card']};
                color: {S['text']};
                border: 1px solid {S['border']};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 10pt;
            }}
            QTextEdit:focus {{
                border: 2px solid {S['primary']};
                background: #fafcff;
            }}
        """)
        return te

    def _make_styled_form_row(self, label_text, widget):
        S = self.S
        row = QVBoxLayout()
        row.setSpacing(5)
        lbl = QLabel(label_text)
        lbl.setStyleSheet(
            f"font-weight: 600; font-size: 9.5pt; color: {S['text2']}; background: transparent;")
        row.addWidget(lbl)
        if isinstance(widget, QLayout):
            row.addLayout(widget)
        else:
            row.addWidget(widget)
        return row

    def _make_gradient_btn(self, text, color1, color2, color_hover1, color_hover2, icon=""):
        btn = QPushButton(f"{icon}  {text}" if icon else text)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setFixedHeight(40)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {color1};
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 0 24px;
                font-size: 9.5pt;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {color_hover1};
            }}
            QPushButton:pressed {{
                background: {color2};
            }}
        """)
        return btn


    def _create_user_profile_tab(self):
        """User Profile section — enterprise 2-column layout."""
        S = self.S
        scroll, layout = self._make_section_scroll()

        # ── User Information card ──────────────────────────────────────────
        info_card = self._make_styled_group(
            "User Information", description="Your login identity and personal contact details")

        # Avatar row
        username_str = self.user_data.get('username', 'User')
        avatar_row = QHBoxLayout()
        avatar_row.setSpacing(16)
        avatar = QLabel(username_str[:2].upper())
        avatar.setFixedSize(56, 56)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"""
            background: {S['primary']};
            color: #ffffff;
            border-radius: 28px;
            font-size: 16pt;
            font-weight: 800;
        """)
        avatar_row.addWidget(avatar)
        av_info = QVBoxLayout()
        av_info.setSpacing(2)
        av_info.addWidget(QLabel(f"<b style='font-size:11pt;color:{S['text']}'>{username_str}</b>"))
        badge = QLabel("Administrator" if self.user_data.get('role', 'admin').lower() in ('admin','administrator') else "Staff")
        badge.setStyleSheet(f"""
            background: {S['primary']}20; color: {S['primary']};
            border: 1px solid {S['primary']}40;
            border-radius: 10px; padding: 2px 10px;
            font-size: 8pt; font-weight: 700;
        """)
        badge.setFixedHeight(20)
        badge.setAlignment(Qt.AlignCenter)
        av_info.addWidget(badge)
        avatar_row.addLayout(av_info)
        avatar_row.addStretch()
        # Status chip
        active_chip = QLabel("● Active")
        active_chip.setStyleSheet(
            f"color: {S['success']}; font-weight: 700; font-size: 10pt; background: transparent;")
        avatar_row.addWidget(active_chip)
        info_card.layout().addLayout(avatar_row)

        # 2-column grid
        grid = QHBoxLayout()
        grid.setSpacing(16)
        col1 = QVBoxLayout()
        col1.setSpacing(14)
        col2 = QVBoxLayout()
        col2.setSpacing(14)

        self.username_label = QLabel(username_str)
        self.username_label.setStyleSheet(
            f"font-weight: 700; font-size: 10pt; color: {S['primary']}; "
            f"background: {S['primary']}10; border: 1px solid {S['primary']}30; "
            "border-radius: 6px; padding: 8px 12px;")
        col1.addLayout(self._make_styled_form_row("Username (read-only):", self.username_label))

        self.full_name_input = self._make_styled_line_input("Enter full name")
        col2.addLayout(self._make_styled_form_row("Full Name:", self.full_name_input))

        self.email_input = self._make_styled_line_input("Enter email address")
        col1.addLayout(self._make_styled_form_row("Email Address:", self.email_input))

        self.phone_input = self._make_styled_line_input("Enter phone number")
        col2.addLayout(self._make_styled_form_row("Phone Number:", self.phone_input))

        grid.addLayout(col1, 1)
        grid.addLayout(col2, 1)
        info_card.layout().addLayout(grid)

        # Action buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()
        chg_user_btn = self._make_gradient_btn("Change Username", "#8b5cf6", "#7c3aed", "#a78bfa", "#8b5cf6")
        chg_user_btn.clicked.connect(self._show_change_username_dialog)
        btn_row.addWidget(chg_user_btn)
        chg_pw_btn = self._make_gradient_btn("Change Password", "#d97706", "#b45309", "#f59e0b", "#d97706")
        chg_pw_btn.clicked.connect(self._show_change_password_dialog)
        btn_row.addWidget(chg_pw_btn)
        save_btn = self._make_gradient_btn("Save Profile", "#059669", "#047857", "#10b981", "#059669", "✓")
        save_btn.clicked.connect(self.save_user_profile)
        btn_row.addWidget(save_btn)
        info_card.layout().addLayout(btn_row)

        layout.addWidget(info_card)
        layout.addStretch()
        return scroll

    
    def _create_shop_details_tab(self):
        """Shop Details section — enterprise 2-column card layout."""
        S = self.S
        scroll, layout = self._make_section_scroll()

        # ── Business Information card ──────────────────────────────────────
        shop_card = self._make_styled_group(
            "Business Information",
            description="This information appears on every invoice and receipt")
        grid = QHBoxLayout()
        grid.setSpacing(16)
        c1 = QVBoxLayout()
        c1.setSpacing(14)
        c2 = QVBoxLayout()
        c2.setSpacing(14)

        self.shop_name_input = self._make_styled_line_input("e.g. Cool Air Services")
        c1.addLayout(self._make_styled_form_row("Shop Name *:", self.shop_name_input))

        self.shop_phone_input = self._make_styled_line_input("+91 9876543210")
        c2.addLayout(self._make_styled_form_row("Phone Number:", self.shop_phone_input))

        self.shop_email_input = self._make_styled_line_input("info@yourshop.com")
        c1.addLayout(self._make_styled_form_row("Email Address:", self.shop_email_input))

        self.tagline_input = self._make_styled_line_input("AC Sales & Service Management")
        c2.addLayout(self._make_styled_form_row("Tagline:", self.tagline_input))

        self.gst_input = self._make_styled_line_input("e.g. 27ABCDE1234F1Z5")
        c1.addLayout(self._make_styled_form_row("GST Number:", self.gst_input))

        self.services_input = self._make_styled_line_input("Sales | Installation | AMC | Repair")
        c2.addLayout(self._make_styled_form_row("Services Offered:", self.services_input))

        grid.addLayout(c1, 1)
        grid.addLayout(c2, 1)
        shop_card.layout().addLayout(grid)

        # Address — full width
        self.address_input = self._make_styled_text_edit(80)
        shop_card.layout().addLayout(self._make_styled_form_row("Address *:", self.address_input))
        layout.addWidget(shop_card)

        # ── Owner Details card ─────────────────────────────────────────────
        owner_card = self._make_styled_group(
            "Owner Details",
            description="Contact details for the business owner")
        ow_grid = QHBoxLayout()
        ow_grid.setSpacing(16)
        ow1 = QVBoxLayout()
        ow1.setSpacing(14)
        ow2 = QVBoxLayout()
        ow2.setSpacing(14)

        self.owner_name_input = self._make_styled_line_input("Enter owner name")
        ow1.addLayout(self._make_styled_form_row("Owner Name *:", self.owner_name_input))

        self.owner_phone_input = self._make_styled_line_input("+91 9876543210")
        ow2.addLayout(self._make_styled_form_row("Owner Phone:", self.owner_phone_input))

        ow_grid.addLayout(ow1, 1)
        ow_grid.addLayout(ow2, 1)
        owner_card.layout().addLayout(ow_grid)
        layout.addWidget(owner_card)

        # ── Logo card ─────────────────────────────────────────────────────
        logo_card = self._make_styled_group(
            "Shop Logo",
            description="Your logo appears on invoices, receipts and all reports")
        logo_h = QHBoxLayout()
        logo_h.setSpacing(20)

        self.logo_preview = QLabel("\U0001f3ea")
        self.logo_preview.setFixedSize(90, 90)
        self.logo_preview.setAlignment(Qt.AlignCenter)
        self.logo_preview.setStyleSheet(f"""
            font-size: 32pt;
            border: 2px dashed {S['border']};
            border-radius: 10px;
            background: {S['bg']};
        """)
        logo_h.addWidget(self.logo_preview)

        logo_r = QVBoxLayout()
        logo_r.setSpacing(8)
        self.logo_path_label = QLabel("No custom logo selected — using default emoji")
        self.logo_path_label.setStyleSheet(
            f"color: {S['muted']}; font-size: 9pt; background: transparent;")
        logo_r.addWidget(self.logo_path_label)
        browse_btn = self._make_gradient_btn("Browse & Upload Logo", S['primary'], "#1d4ed8", "#3b82f6", S['primary'], "\U0001f4c1")
        browse_btn.clicked.connect(self._browse_logo)
        logo_r.addWidget(browse_btn)
        remove_btn = self._make_gradient_btn("Remove Custom Logo", S['danger'], "#b91c1c", "#ef4444", S['danger'], "\U0001f5d1")
        remove_btn.clicked.connect(self._remove_logo)
        logo_r.addWidget(remove_btn)
        logo_r.addStretch()
        logo_h.addLayout(logo_r)
        logo_h.addStretch()
        logo_card.layout().addLayout(logo_h)
        layout.addWidget(logo_card)

        # Save button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        save_btn = self._make_gradient_btn("Save Shop Details", "#059669", "#047857", "#10b981", "#059669", "\U0001f4be")
        save_btn.clicked.connect(self.save_shop_details)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)
        layout.addStretch()
        return scroll

    
    def _create_app_settings_tab(self):
        """Application Settings - enterprise layout with organized cards."""
        S = self.S
        scroll, layout = self._make_section_scroll()

        spin_style = f"""
            QSpinBox, QDoubleSpinBox, QTimeEdit, QComboBox {{
                background: {S['card']}; color: {S['text']};
                border: 1px solid {S['border']}; border-radius: 8px;
                padding: 0 10px; font-size: 10pt; min-height: 38px;
            }}
            QSpinBox:focus, QDoubleSpinBox:focus, QTimeEdit:focus, QComboBox:focus {{
                border: 2px solid {S['primary']};
            }}
            QSpinBox::up-button, QDoubleSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::down-button {{
                border: none; background: transparent;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                border: none;
                width: 28px;
            }}
            QComboBox::down-arrow {{
                image: url("{CHEVRON_ICON_PATH}");
                width: 12px;
                height: 12px;
                margin-right: 8px;
            }}
        """

        # Invoice Settings card
        inv_card = self._make_styled_group(
            "Invoice Settings",
            description="Invoice numbering, GST rate, and printed invoice text")
        inv_grid = QHBoxLayout()
        inv_grid.setSpacing(16)
        iv1 = QVBoxLayout(); iv1.setSpacing(14)
        iv2 = QVBoxLayout(); iv2.setSpacing(14)

        self.invoice_prefix_input = self._make_styled_line_input("INV")
        iv1.addLayout(self._make_styled_form_row("Invoice Prefix:", self.invoice_prefix_input))

        self.invoice_start_spin = QSpinBox()
        self.invoice_start_spin.setRange(1, 999999)
        self.invoice_start_spin.setValue(1001)
        self.invoice_start_spin.setStyleSheet(spin_style)
        iv2.addLayout(self._make_styled_form_row("Starting Number:", self.invoice_start_spin))

        self.gst_spin = QDoubleSpinBox()
        self.gst_spin.setRange(0, 100)
        self.gst_spin.setValue(18.0)
        self.gst_spin.setSuffix("%")
        self.gst_spin.setStyleSheet(spin_style)
        iv1.addLayout(self._make_styled_form_row("GST Percentage:", self.gst_spin))

        self.thanks_note_input = self._make_styled_line_input("Thank you for your business!")
        iv2.addLayout(self._make_styled_form_row("Thank You Note:", self.thanks_note_input))

        self.watermark_input = self._make_styled_line_input("INVOICE")
        iv1.addLayout(self._make_styled_form_row("Watermark Text:", self.watermark_input))

        self.default_notes_input = self._make_styled_line_input("All Work Done")
        iv2.addLayout(self._make_styled_form_row("Default Notes:", self.default_notes_input))

        inv_grid.addLayout(iv1, 1)
        inv_grid.addLayout(iv2, 1)
        inv_card.layout().addLayout(inv_grid)

        self.terms_input = self._make_styled_text_edit(100)
        self.terms_input.setPlainText(
            "1. Goods once sold will not be taken back.\n"
            "2. Warranty as per company policy.\n"
            "3. Payment due within 7 days.\n"
            "4. Service warranty only on selected parts.")
        inv_card.layout().addLayout(self._make_styled_form_row("Terms & Conditions:", self.terms_input))
        layout.addWidget(inv_card)

        # Company & Branding card
        co_card = self._make_styled_group(
            "Company & Branding",
            description="Application name, company identity and display format")
        co_grid = QHBoxLayout()
        co_grid.setSpacing(16)
        cg1 = QVBoxLayout(); cg1.setSpacing(14)
        cg2 = QVBoxLayout(); cg2.setSpacing(14)

        self.app_name_input = self._make_styled_line_input("AC Service Billing")
        cg1.addLayout(self._make_styled_form_row("App Name:", self.app_name_input))

        self.company_name_input = self._make_styled_line_input("Your Company Name")
        cg2.addLayout(self._make_styled_form_row("Company Name:", self.company_name_input))

        self.shop_type_combo = QComboBox()
        self.shop_type_combo.addItems(["AC Service", "General Service", "Electronics", "Mobile", "Other"])
        self.shop_type_combo.setStyleSheet(spin_style)
        cg1.addLayout(self._make_styled_form_row("Shop Type:", self.shop_type_combo))

        self.currency_input = self._make_styled_line_input()
        self.currency_input.setText("\u20b9")
        self.currency_input.setMaxLength(5)
        cg2.addLayout(self._make_styled_form_row("Currency Symbol:", self.currency_input))

        self.date_format_input = self._make_styled_line_input("dd-MM-yyyy")
        cg1.addLayout(self._make_styled_form_row("Date Format:", self.date_format_input))

        co_grid.addLayout(cg1, 1)
        co_grid.addLayout(cg2, 1)
        co_card.layout().addLayout(co_grid)
        layout.addWidget(co_card)

        # Business Hours card
        hrs_card = self._make_styled_group(
            "Business Hours",
            description="Shop opening and closing times shown on invoices")
        hrs_grid = QHBoxLayout()
        hrs_grid.setSpacing(16)
        h1 = QVBoxLayout(); h1.setSpacing(14)
        h2 = QVBoxLayout(); h2.setSpacing(14)

        self.opening_time = QTimeEdit()
        self.opening_time.setStyleSheet(spin_style)
        h1.addLayout(self._make_styled_form_row("Opening Time:", self.opening_time))

        self.closing_time = QTimeEdit()
        self.closing_time.setStyleSheet(spin_style)
        h2.addLayout(self._make_styled_form_row("Closing Time:", self.closing_time))

        hrs_grid.addLayout(h1, 1)
        hrs_grid.addLayout(h2, 1)
        hrs_card.layout().addLayout(hrs_grid)
        layout.addWidget(hrs_card)

        # SMTP / Email card
        smtp_card = self._make_styled_group(
            "SMTP / Email Settings",
            description="Server details for sending invoices by email")
        sg_grid = QHBoxLayout()
        sg_grid.setSpacing(16)
        sg1 = QVBoxLayout(); sg1.setSpacing(14)
        sg2 = QVBoxLayout(); sg2.setSpacing(14)

        self.smtp_server_input = self._make_styled_line_input("smtp.gmail.com")
        sg1.addLayout(self._make_styled_form_row("SMTP Server:", self.smtp_server_input))

        self.smtp_port_input = self._make_styled_line_input("587")
        sg2.addLayout(self._make_styled_form_row("SMTP Port:", self.smtp_port_input))

        self.smtp_username_input = self._make_styled_line_input("your@email.com")
        sg1.addLayout(self._make_styled_form_row("SMTP Username:", self.smtp_username_input))

        self.smtp_password_input = self._make_styled_line_input("Password")
        self.smtp_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        smtp_pw_h = QHBoxLayout()
        smtp_pw_h.setSpacing(6)
        smtp_pw_h.addWidget(self.smtp_password_input, 1)
        self.smtp_eye_btn = QPushButton("\U0001f441")
        self.smtp_eye_btn.setCheckable(True)
        self.smtp_eye_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.smtp_eye_btn.setFixedSize(38, 38)
        self.smtp_eye_btn.setStyleSheet(f"""
            QPushButton {{
                background: {S['card']}; color: {S['muted']};
                border: 1px solid {S['border']}; border-radius: 8px;
            }}
            QPushButton:hover {{ border-color: {S['primary']}; color: {S['primary']}; }}
        """)
        def toggle_smtp_eye(checked):
            self.smtp_password_input.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)
        self.smtp_eye_btn.toggled.connect(toggle_smtp_eye)
        smtp_pw_h.addWidget(self.smtp_eye_btn)
        pw_lbl = QLabel("SMTP Password:")
        pw_lbl.setStyleSheet(f"font-weight: 600; font-size: 9.5pt; color: {S['text2']}; background: transparent;")
        pw_col = QVBoxLayout()
        pw_col.setSpacing(5)
        pw_col.addWidget(pw_lbl)
        pw_col.addLayout(smtp_pw_h)
        sg2.addLayout(pw_col)

        self.smtp_from_email_input = self._make_styled_line_input("your@email.com")
        sg1.addLayout(self._make_styled_form_row("From Email:", self.smtp_from_email_input))

        self.smtp_from_name_input = self._make_styled_line_input("Your Company")
        sg2.addLayout(self._make_styled_form_row("From Name:", self.smtp_from_name_input))

        sg_grid.addLayout(sg1, 1)
        sg_grid.addLayout(sg2, 1)
        smtp_card.layout().addLayout(sg_grid)

        self.email_subject_input = self._make_styled_line_input("Invoice #{invoice_number} - {company_name}")
        smtp_card.layout().addLayout(self._make_styled_form_row("Email Subject:", self.email_subject_input))

        self.email_body_input = self._make_styled_text_edit(90)
        self.email_body_input.setPlainText(
            "Dear {customer_name},\n\nPlease find attached invoice #{invoice_number}.\n\nThank you!\n{company_name}")
        smtp_card.layout().addLayout(self._make_styled_form_row("Email Body:", self.email_body_input))
        layout.addWidget(smtp_card)

        # Dropdown Options card
        dd_card = self._make_styled_group(
            "Dropdown Options",
            description="Comma-separated values used in dropdowns across the app")
        dd_grid = QHBoxLayout()
        dd_grid.setSpacing(16)
        dd1 = QVBoxLayout(); dd1.setSpacing(14)
        dd2 = QVBoxLayout(); dd2.setSpacing(14)

        self.service_types_input = self._make_styled_line_input(
            "AC Service,Installation,Repair,Gas Refilling,AMC Visit,Other")
        dd1.addLayout(self._make_styled_form_row("Service Types:", self.service_types_input))

        self.ac_types_input = self._make_styled_line_input("Split,Window,Cassette,Tower,Other")
        dd2.addLayout(self._make_styled_form_row("AC Types:", self.ac_types_input))

        self.ac_ton_capacities_input = self._make_styled_line_input("1.0,1.5,2.0,3.0,Other")
        dd1.addLayout(self._make_styled_form_row("AC Ton Capacities:", self.ac_ton_capacities_input))

        self.ac_inverter_options_input = self._make_styled_line_input("No,Yes")
        dd2.addLayout(self._make_styled_form_row("Inverter Options:", self.ac_inverter_options_input))

        self.star_ratings_input = self._make_styled_line_input("N/A,1,2,3,4,5")
        dd1.addLayout(self._make_styled_form_row("Star Ratings:", self.star_ratings_input))

        dd_grid.addLayout(dd1, 1)
        dd_grid.addLayout(dd2, 1)
        dd_card.layout().addLayout(dd_grid)
        layout.addWidget(dd_card)

        # Database status card
        db_card = self._make_styled_group("Database Status")
        db_h = QHBoxLayout()
        db_h.setSpacing(10)
        db_dot = QLabel("\u25cf")
        db_dot.setStyleSheet(f"font-size: 14pt; color: {S['success']}; background: transparent;")
        db_h.addWidget(db_dot)
        db_txt = QLabel("Database Connected  \u00b7  Engine: SQLite  \u00b7  Mode: WAL (High Performance)")
        db_txt.setStyleSheet(f"color: {S['text2']}; font-size: 10pt; background: transparent;")
        db_h.addWidget(db_txt)
        db_h.addStretch()
        db_card.layout().addLayout(db_h)
        layout.addWidget(db_card)

        # Save button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        app_save_btn = self._make_gradient_btn(
            "Save Application Settings", S['primary'], "#1d4ed8", "#3b82f6", S['primary'], "\U0001f4be")
        app_save_btn.clicked.connect(self.save_application_settings)
        btn_row.addWidget(app_save_btn)
        layout.addLayout(btn_row)
        layout.addStretch()
        return scroll


    def save_application_settings(self):
        """Save application settings from UI to DB"""
        settings = {
            'invoice_prefix': self.invoice_prefix_input.text().strip(),
            'starting_invoice_number': self.invoice_start_spin.value(),
            'default_gst_percentage': self.gst_spin.value(),
            'opening_time': self.opening_time.time().toString("HH:mm"),
            'closing_time': self.closing_time.time().toString("HH:mm"),
            'terms_conditions': self.terms_input.toPlainText().strip(),
            'thank_you_note': self.thanks_note_input.text().strip(),
            'invoice_watermark': self.watermark_input.text().strip(),
            'default_notes': self.default_notes_input.text().strip(),
            'app_name': self.app_name_input.text().strip(),
            'shop_type': self.shop_type_combo.currentText(),
            'company_name': self.company_name_input.text().strip(),
            'currency_symbol': self.currency_input.text().strip(),
            'date_format': self.date_format_input.text().strip(),
            'smtp_server': self.smtp_server_input.text().strip(),
            'smtp_port': self.smtp_port_input.text().strip(),
            'smtp_username': self.smtp_username_input.text().strip(),
            'smtp_password': self.smtp_password_input.text().strip(),
            'smtp_from_email': self.smtp_from_email_input.text().strip(),
            'smtp_from_name': self.smtp_from_name_input.text().strip(),
            'email_subject': self.email_subject_input.text().strip(),
            'email_body': self.email_body_input.toPlainText().strip(),
            'service_types': self.service_types_input.text().strip(),
            'ac_types': self.ac_types_input.text().strip(),
            'ac_ton_capacities': self.ac_ton_capacities_input.text().strip(),
            'ac_inverter_options': self.ac_inverter_options_input.text().strip(),
            'star_ratings': self.star_ratings_input.text().strip(),
        }
        
        from controllers.settings_controller import SettingsController
        from database.db_connection import DatabaseConnection
        
        db = DatabaseConnection()
        sc = SettingsController(db)
        success, message = sc.save_application_settings(settings)
        
        if success:
            clear_invoice_pdf_cache()
            self.show_success_message(message)
            from utils.app_settings import invalidate_cache
            invalidate_cache()   # Clear in-process settings cache
            from utils.event_bus import get_event_bus
            get_event_bus().emit_settings_updated(settings)
            self.settings_saved.emit()
        else:
            self.show_error_message(message)

    
    def _make_styled_combo(self, items, width=200):
        colors = self.theme_manager.get_colors()
        combo = QComboBox()
        combo.addItems(items)
        combo.setMinimumWidth(width)
        combo.setStyleSheet(f"""
            QComboBox {{
                background: {colors['card_bg']};
                color: {colors['fg']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 9pt;
                min-height: 18px;
            }}
            QComboBox:hover {{
                border-color: #3b82f680;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                border: none;
                width: 28px;
            }}
            QComboBox::down-arrow {{
                image: url("{CHEVRON_ICON_PATH}");
                width: 12px;
                height: 12px;
                margin-right: 6px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {colors['card_bg']};
                color: {colors['fg']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                padding: 4px;
                selection-background-color: #3b82f6;
                selection-color: #ffffff;
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 6px 12px;
                border-radius: 4px;
            }}
        """)
        return combo

    def _create_master_data_tab(self):
        """Create master data management tab - Enterprise Catalog Studio"""
        S = self.S
        scroll, layout = self._make_section_scroll()
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(14)

        # ── 1. Top Header & Action Controls Strip ─────────────────────────────
        header_card = QFrame()
        header_card.setStyleSheet(f"""
            QFrame {{
                background: {S['card']};
                border: 1px solid {S['border']};
                border-radius: 10px;
                padding: 12px 18px;
            }}
        """)
        hl = QHBoxLayout(header_card)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(14)

        # Title & Subtitle
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        h_title = QLabel("📋  Master Data Catalog")
        h_title.setStyleSheet(f"font-size: 13pt; font-weight: 800; color: {S['text']}; background: transparent;")
        title_col.addWidget(h_title)

        h_sub = QLabel("Central catalog of services, parts pricing, AC brands, and system reference lookups.")
        h_sub.setStyleSheet(f"font-size: 8.5pt; color: {S['muted']}; background: transparent;")
        title_col.addWidget(h_sub)
        hl.addLayout(title_col)

        hl.addStretch()

        # Refresh button (always visible at top)
        refresh_btn = QPushButton("🔄  Refresh")
        refresh_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        refresh_btn.setFixedHeight(36)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                color: #334155;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 0 16px;
                font-size: 8.5pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #f8fafc;
                border-color: #94a3b8;
            }
        """)
        refresh_btn.clicked.connect(self._load_master_data)
        hl.addWidget(refresh_btn)

        # Prominent Add New button (always visible at top right)
        self.master_add_btn = QPushButton("➕  Add Service")
        self.master_add_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.master_add_btn.setFixedHeight(36)
        self.master_add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {S['primary']};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
                font-size: 9pt;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: #1d4ed8;
            }}
            QPushButton:pressed {{
                background: #1e40af;
            }}
        """)
        self.master_add_btn.clicked.connect(self._add_master_item)
        hl.addWidget(self.master_add_btn)

        layout.addWidget(header_card)

        # ── 2. Category Switcher Bar (Interactive Pills + Search) ──────────────
        categories_card = QFrame()
        categories_card.setStyleSheet(f"""
            QFrame {{
                background: {S['card']};
                border: 1px solid {S['border']};
                border-radius: 10px;
                padding: 12px 16px;
            }}
        """)
        cat_layout = QVBoxLayout(categories_card)
        cat_layout.setContentsMargins(0, 0, 0, 0)
        cat_layout.setSpacing(10)

        # Pills Row
        pills_row = QHBoxLayout()
        pills_row.setSpacing(8)
        pills_row.setContentsMargins(0, 0, 0, 0)

        self.master_pills = {}
        pill_items = [
            ("🛠️ Services", "Services"),
            ("📦 Parts", "Parts"),
            ("🏷️ AC Brands", "AC Brands"),
            ("❄️ AC Types", "AC Types"),
            ("⚖️ AC Tonnage", "AC Tonnage"),
            ("⭐ Star Ratings", "Star Ratings"),
            ("📏 Units", "Inventory Units"),
            ("👷 Tech Statuses", "Technician Statuses"),
            ("💳 Payment Modes", "Payment Modes"),
        ]

        for label, cat_key in pill_items:
            pill = QPushButton(label)
            pill.setCheckable(True)
            pill.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            pill.setFixedHeight(32)
            pill.setStyleSheet("""
                QPushButton {
                    background: #f1f5f9;
                    color: #475569;
                    border: 1px solid #e2e8f0;
                    border-radius: 16px;
                    padding: 0 14px;
                    font-size: 8.5pt;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #e2e8f0;
                    color: #0f172a;
                }
                QPushButton:checked {
                    background: #2563eb;
                    color: #ffffff;
                    border: 1px solid #1d4ed8;
                    font-weight: 700;
                }
            """)
            pill.clicked.connect(lambda checked, k=cat_key: self._on_master_pill_clicked(k))
            pills_row.addWidget(pill)
            self.master_pills[cat_key] = pill

        pills_row.addStretch()
        cat_layout.addLayout(pills_row)

        # Toolbar Row (Data Type Dropdown, Search Input, Record Count Badge)
        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)
        filter_row.setContentsMargins(0, 0, 0, 0)

        # Synced Combo Box
        self.master_type_combo = self._make_styled_combo([
            "Services", "Parts", "AC Brands", "AC Types",
            "AC Tonnage", "Star Ratings", "Inventory Units",
            "Technician Statuses", "Payment Modes"
        ])
        self.master_type_combo.setMinimumWidth(180)
        self.master_type_combo.setFixedHeight(36)
        self.master_type_combo.currentTextChanged.connect(self._on_master_type_changed)
        filter_row.addWidget(self.master_type_combo)

        # Search Bar
        self.master_search = QLineEdit()
        self.master_search.setPlaceholderText("🔍  Filter records by name, description, rate...")
        self.master_search.setClearButtonEnabled(True)
        self.master_search.setMinimumWidth(320)
        self.master_search.setFixedHeight(36)
        self.master_search.setStyleSheet(f"""
            QLineEdit {{
                background: #f8fafc;
                color: {S['text']};
                border: 1px solid {S['border']};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 9pt;
            }}
            QLineEdit:focus {{
                border: 1.5px solid {S['primary']};
                background: #ffffff;
            }}
        """)
        self.master_search.textChanged.connect(self._filter_master_table)
        filter_row.addWidget(self.master_search)

        filter_row.addStretch()

        # Record count badge
        self.master_count_label = QLabel("0 active records")
        self.master_count_label.setStyleSheet("""
            background: #eff6ff;
            color: #1e40af;
            border: 1px solid #bfdbfe;
            border-radius: 12px;
            padding: 4px 14px;
            font-size: 8.5pt;
            font-weight: 700;
        """)
        filter_row.addWidget(self.master_count_label)
        cat_layout.addLayout(filter_row)

        layout.addWidget(categories_card)

        # ── 3. Table Container ──────────────────────────────────────────────────
        table_container = QFrame()
        table_container.setStyleSheet(f"""
            QFrame {{
                background: {S['card']};
                border: 1px solid {S['border']};
                border-radius: 10px;
                padding: 0px;
            }}
        """)
        table_container_layout = QVBoxLayout(table_container)
        table_container_layout.setContentsMargins(0, 0, 0, 0)
        table_container_layout.setSpacing(0)

        self.master_table = QTableWidget()
        self.master_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.master_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.master_table.setAlternatingRowColors(True)
        self.master_table.verticalHeader().setVisible(False)
        self.master_table.verticalHeader().setDefaultSectionSize(46)
        self.master_table.setShowGrid(True)
        self.master_table.setGridStyle(Qt.PenStyle.SolidLine)
        self.master_table.setSortingEnabled(True)
        self.master_table.setMinimumHeight(440)
        self.master_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #ffffff;
                color: #0f172a;
                border: none;
                gridline-color: #e2e8f0;
                selection-background-color: #eff6ff;
                selection-color: #0f172a;
                alternate-background-color: #f8fafc;
                font-family: 'Segoe UI', sans-serif;
                font-size: 9pt;
            }}
            QTableWidget::item {{
                padding: 6px 12px;
                border-bottom: 1px solid #e2e8f0;
            }}
            QTableWidget::item:selected {{
                background: #eff6ff;
                color: #0f172a;
            }}
            QTableWidget::item:hover {{
                background: #f1f5f9;
            }}
            QHeaderView::section {{
                background: #f1f5f9;
                color: #334155;
                padding: 10px 12px;
                border: none;
                border-bottom: 2px solid #cbd5e1;
                border-right: 1px solid #e2e8f0;
                font-weight: 700;
                font-size: 8.5pt;
                letter-spacing: 0.3px;
            }}
            QHeaderView::section:last {{
                border-right: none;
            }}
        """)

        table_container_layout.addWidget(self.master_table)
        layout.addWidget(table_container, 1)

        # Set initial pill state and trigger load
        self._on_master_pill_clicked("Services")

        return scroll

    def _on_master_pill_clicked(self, cat_key):
        """Update active pill, button label and combo box"""
        for k, pill in getattr(self, 'master_pills', {}).items():
            pill.setChecked(k == cat_key)
        if hasattr(self, 'master_type_combo'):
            idx = self.master_type_combo.findText(cat_key)
            if idx >= 0 and self.master_type_combo.currentIndex() != idx:
                self.master_type_combo.blockSignals(True)
                self.master_type_combo.setCurrentIndex(idx)
                self.master_type_combo.blockSignals(False)
        if hasattr(self, 'master_add_btn'):
            singular = cat_key[:-1] if cat_key.endswith('s') else cat_key
            self.master_add_btn.setText(f"➕  Add {singular}")
        self._load_master_data()

    def _on_master_type_changed(self, text):
        """Handle master data type dropdown change"""
        for k, pill in getattr(self, 'master_pills', {}).items():
            pill.setChecked(k == text)
        if hasattr(self, 'master_add_btn'):
            singular = text[:-1] if text.endswith('s') else text
            self.master_add_btn.setText(f"➕  Add {singular}")
        self._load_master_data()

    def load_user_profile(self):
        """Load user profile data"""
        self.full_name_input.setText(self.user_data.get('full_name', ''))
        self.email_input.setText(self.user_data.get('email', ''))
        self.phone_input.setText(self.user_data.get('phone', ''))
        
        # Load shop details
        self.run_in_thread(
            self._load_shop_details_thread,
            self._update_shop_details
        )
    
    def _load_shop_details_thread(self):
        """Load shop details in background"""
        from controllers.auth_controller import AuthController
        from database.db_connection import DatabaseConnection
        
        db = DatabaseConnection()
        auth = AuthController(db)
        return auth.get_shop_details()
    
    def _update_shop_details(self, shop_details):
        """Update shop details UI"""
        if shop_details:
            self.shop_name_input.setText(shop_details.get('shop_name', ''))
            self.address_input.setText(shop_details.get('address', ''))
            self.shop_phone_input.setText(shop_details.get('phone', ''))
            self.shop_email_input.setText(shop_details.get('email', ''))
            self.tagline_input.setText(shop_details.get('tagline', ''))
            self.services_input.setText(shop_details.get('services', ''))
            self.gst_input.setText(shop_details.get('gst_number', ''))
            self.owner_name_input.setText(shop_details.get('owner_name', ''))
            self.owner_phone_input.setText(shop_details.get('owner_phone', ''))
            logo = shop_details.get('logo_path', '') or ''
            from utils.logo_helper import get_logo_path
            logo_display = logo if logo and os.path.exists(logo) else get_logo_path()
            self._update_logo_preview(logo_display)
            if logo and os.path.exists(logo):
                self.logo_path_label.setText(f"Logo: {os.path.basename(logo)}")
            else:
                self.logo_path_label.setText("Default logo (no custom logo set)")
        
        # Load master data
        self._load_master_data()
    
    def save_user_profile(self):
        """Save user profile with session refresh and real-time update"""
        full_name = self.full_name_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()

        if not full_name:
            self.show_warning_message("Full name is required")
            return

        from controllers.auth_controller import AuthController
        from database.db_connection import DatabaseConnection
        from utils.event_bus import get_event_bus

        db = DatabaseConnection()
        auth = AuthController(db)
        result = auth.update_profile(
            self.user_data.get('id'),
            full_name, email, phone
        )

        # Handle new 3-tuple return value (success, message, updated_user)
        if len(result) == 3:
            success, message, updated_user = result
        else:
            success, message = result
            updated_user = None

        if success:
            # Update local user_data with new values
            self.user_data['full_name'] = full_name
            self.user_data['email'] = email
            self.user_data['phone'] = phone

            # Update from DB response if available
            if updated_user:
                self.user_data.update(updated_user)

            # Refresh the input fields to show updated data
            self.full_name_input.setText(full_name)
            self.email_input.setText(email)
            self.phone_input.setText(phone)

            # CRITICAL: Refresh session manager with updated user data
            from utils.session_manager import get_session
            session = get_session()
            if session:
                session.refresh_session(self.user_data)
                print(f"[SESSION] Session refreshed after profile update")

            # Emit real-time update via event bus
            event_bus = get_event_bus()
            event_bus.emit_user_profile_updated(self.user_data)

            self.show_success_message(message)
            print(f"[DEBUG] Profile saved - emitting signal")
            self.settings_saved.emit()  # Emit signal to notify other views
        else:
            self.show_error_message(message)
    
    def _show_change_username_dialog(self):
        """Show change username dialog"""
        from views.settings_view import ChangeUsernameDialog
        dialog = ChangeUsernameDialog(self.user_data.get('id'), self)
        if dialog.exec():
            new_username = dialog.new_username_input.text().strip()
            # Refresh the username label after successful change
            self.username_label.setText(new_username)
            # Update local user data
            self.user_data['username'] = new_username
            
            # Refresh session to persist this in memory
            from utils.session_manager import get_session
            session = get_session()
            if session:
                session.refresh_session(self.user_data)
                
            self.settings_saved.emit()
    
    def _show_change_password_dialog(self):
        """Show change password dialog"""
        from views.settings_view import ChangePasswordDialog
        dialog = ChangePasswordDialog(self.user_data.get('id'), self)
        dialog.exec()
    
    def _browse_logo(self):
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Shop Logo", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            from utils.logo_helper import save_uploaded_logo
            saved_path = save_uploaded_logo(file_path)
            self._update_logo_preview(saved_path)
            self.logo_path_label.setText(f"Logo: {os.path.basename(file_path)}")
            self._logo_updated = True

    def _remove_logo(self):
        logo_storage = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'data', 'custom_logo.png'
        )
        if os.path.exists(logo_storage):
            os.remove(logo_storage)
        self.logo_preview.clear()
        self.logo_preview.setText("No Logo")
        self.logo_path_label.setText("No custom logo selected (default will be used)")
        self._logo_updated = True

    def _update_logo_preview(self, path):
        from PySide6.QtGui import QPixmap
        if path and os.path.exists(path):
            pixmap = QPixmap(path).scaled(
                90, 90,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.logo_preview.setPixmap(pixmap)
        else:
            self.logo_preview.clear()
            self.logo_preview.setText("No Logo")

    def save_shop_details(self):
        """Save shop details with real-time update"""
        shop_name = self.shop_name_input.text().strip()
        address = self.address_input.toPlainText().strip()
        owner_name = self.owner_name_input.text().strip()

        if not shop_name or not address or not owner_name:
            self.show_warning_message("Shop Name, Address, and Owner Name are required")
            return

        logo_path = ''
        if getattr(self, '_logo_updated', False):
            from utils.logo_helper import LOGO_STORAGE, CUSTOM_LOGO_NAME
            custom = os.path.join(str(LOGO_STORAGE), CUSTOM_LOGO_NAME)
            if os.path.exists(custom):
                logo_path = custom
            self._logo_updated = False

        shop_data = {
            'shop_name': shop_name,
            'address': address,
            'phone': self.shop_phone_input.text().strip(),
            'email': self.shop_email_input.text().strip(),
            'tagline': self.tagline_input.text().strip(),
            'services': self.services_input.text().strip(),
            'gst_number': self.gst_input.text().strip(),
            'owner_name': owner_name,
            'owner_phone': self.owner_phone_input.text().strip(),
            'logo_path': logo_path
        }

        from controllers.auth_controller import AuthController
        from database.db_connection import DatabaseConnection
        from utils.event_bus import get_event_bus

        db = DatabaseConnection()
        auth = AuthController(db)
        success, message = auth.update_shop_details(shop_data)

        if success:
            clear_invoice_pdf_cache()
            # Emit real-time update via event bus
            event_bus = get_event_bus()
            event_bus.emit_shop_details_updated(shop_data)

            self.show_success_message(message)
            print(f"[DEBUG] Shop settings saved - emitting signal")
            # Reload shop details to ensure UI shows updated data
            self.run_in_thread(
                self._load_shop_details_thread,
                self._update_shop_details
            )
            self.settings_saved.emit()  # Emit signal to notify other views
        else:
            self.show_error_message(message)
    
    def create_backup(self):
        """Create database backup"""
        self.show_success_message("Backup created successfully")
    
    def restore_backup(self):
        """Restore from backup"""
        self.show_warning_message("Restore feature - use with caution")
    
    def _load_master_data(self):
        """Load master data based on selected type"""
        master_type = self.master_type_combo.currentText()

        if hasattr(self, 'master_search'):
            self.master_search.blockSignals(True)
            self.master_search.clear()
            self.master_search.blockSignals(False)

        self.run_in_thread(
            self._load_master_data_thread,
            self._update_master_table,
            None,  # on_error - use default handler
            master_type
        )

    def _filter_master_table(self, text):
        """Filter master data rows across all visible data columns"""
        text = (text or '').strip().lower()
        self.master_table.setSortingEnabled(False)
        visible = 0
        total = self.master_table.rowCount()
        col_count = self.master_table.columnCount()

        for row in range(total):
            match = not text
            if text:
                for col in range(col_count - 1):  # exclude actions column
                    item = self.master_table.item(row, col)
                    if item and text in item.text().lower():
                        match = True
                        break
            self.master_table.setRowHidden(row, not match)
            if match:
                visible += 1

        if hasattr(self, 'master_count_label'):
            if text:
                self.master_count_label.setText(f"{visible} of {total} records")
            else:
                self.master_count_label.setText(f"{total} active record{'s' if total != 1 else ''}")
        self.master_table.setSortingEnabled(True)

    def _load_master_data_thread(self, master_type):
        """Load master data in background with complete rich columns"""
        from database.db_connection import DatabaseContext

        with DatabaseContext() as db:
            if master_type == "Services":
                return db.execute_query(
                    "SELECT id, service_name as name, description, default_rate as rate, is_active FROM services WHERE is_active = TRUE ORDER BY id ASC",
                    fetch_all=True
                )
            elif master_type == "Parts":
                return db.execute_query(
                    "SELECT id, part_name as name, category, stock_quantity, unit, default_rate as rate, is_active FROM parts WHERE is_active = TRUE ORDER BY id ASC",
                    fetch_all=True
                )
            elif master_type == "AC Brands":
                return db.execute_query(
                    "SELECT id, brand_name as name, created_at, is_active FROM ac_brands WHERE is_active = TRUE ORDER BY id ASC",
                    fetch_all=True
                )
            elif master_type == "AC Types":
                return db.execute_query("SELECT id, type_name as name, is_active FROM ac_types WHERE is_active = TRUE ORDER BY id ASC", fetch_all=True)
            elif master_type == "AC Tonnage":
                return db.execute_query("SELECT id, capacity_value as name, is_active FROM ac_capacities WHERE is_active = TRUE ORDER BY id ASC", fetch_all=True)
            elif master_type == "Star Ratings":
                return db.execute_query("SELECT id, star_label as name, is_active FROM ac_stars WHERE is_active = TRUE ORDER BY id ASC", fetch_all=True)
            elif master_type == "Inventory Units":
                return db.execute_query("SELECT id, unit_name as name, is_active FROM inventory_units WHERE is_active = TRUE ORDER BY id ASC", fetch_all=True)
            elif master_type == "Technician Statuses":
                return db.execute_query("SELECT id, status_name as name, is_active FROM technician_statuses WHERE is_active = TRUE ORDER BY id ASC", fetch_all=True)
            elif master_type == "Payment Modes":
                return db.execute_query(
                    "SELECT id, mode_name as name, created_at, is_active FROM payment_modes WHERE is_active = TRUE ORDER BY id ASC",
                    fetch_all=True
                )
        return []

    def _update_master_table(self, data):
        """Update master data table with adaptive columns and enterprise styling"""
        master_type = self.master_type_combo.currentText()
        self.master_table.setSortingEnabled(False)
        self.master_table.setRowCount(0)

        currency_symbol = get_setting("currency_symbol", "₹")

        # Determine column layout based on master_type
        if master_type == "Services":
            cols = ['#', 'Service Name', 'Scope / Description', 'Standard Rate (₹)', 'Status', 'Actions']
            col_widths = [65, 230, 320, 160, 110, 170]
        elif master_type == "Parts":
            cols = ['#', 'Part Name', 'Category', 'Stock Available', 'Unit Rate (₹)', 'Status', 'Actions']
            col_widths = [65, 240, 160, 130, 150, 110, 170]
        elif master_type == "AC Brands":
            cols = ['#', 'Brand Name', 'Created Date', 'Status', 'Actions']
            col_widths = [65, 280, 160, 120, 170]
        else:
            cols = ['#', 'Catalog Item / Value', 'Status', 'Actions']
            col_widths = [65, 360, 130, 170]

        self.master_table.setColumnCount(len(cols))
        self.master_table.setHorizontalHeaderLabels(cols)

        # Column sizing
        header = self.master_table.horizontalHeader()
        for i, w in enumerate(col_widths):
            self.master_table.setColumnWidth(i, w)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        # Stretch description or main item column
        stretch_col = 2 if master_type == "Services" else 1
        header.setSectionResizeMode(stretch_col, QHeaderView.ResizeMode.Stretch)

        for item in (data or []):
            row = self.master_table.rowCount()
            self.master_table.insertRow(row)

            # Column 0: ID
            id_item = QTableWidgetItem(str(item['id']))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            id_item.setForeground(QBrush(QColor('#64748b')))
            id_item.setFont(QFont("Segoe UI", 9))
            self.master_table.setItem(row, 0, id_item)

            actions_col = 3

            if master_type == "Services":
                # Name
                name_item = QTableWidgetItem(str(item.get('name') or ''))
                name_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                name_item.setForeground(QBrush(QColor('#0f172a')))
                self.master_table.setItem(row, 1, name_item)

                # Scope / Description
                desc = item.get('description') or 'Standard Service'
                desc_item = QTableWidgetItem(str(desc))
                desc_item.setFont(QFont("Segoe UI", 8.5))
                desc_item.setForeground(QBrush(QColor('#475569')))
                self.master_table.setItem(row, 2, desc_item)

                # Rate
                rate = float(item.get('rate') or 0.0)
                rate_item = QTableWidgetItem(f"{currency_symbol} {rate:,.2f}")
                rate_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                rate_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                rate_item.setForeground(QBrush(QColor('#0284c7')))
                self.master_table.setItem(row, 3, rate_item)

                # Status
                status_item = QTableWidgetItem("● Active")
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                status_item.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                status_item.setForeground(QBrush(QColor('#15803d')))
                self.master_table.setItem(row, 4, status_item)

                actions_col = 5

            elif master_type == "Parts":
                # Part Name
                name_item = QTableWidgetItem(str(item.get('name') or ''))
                name_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                name_item.setForeground(QBrush(QColor('#0f172a')))
                self.master_table.setItem(row, 1, name_item)

                # Category
                cat = item.get('category') or 'General'
                cat_item = QTableWidgetItem(str(cat))
                cat_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                cat_item.setFont(QFont("Segoe UI", 8.5))
                cat_item.setForeground(QBrush(QColor('#334155')))
                self.master_table.setItem(row, 2, cat_item)

                # Stock Available
                stock = item.get('stock_quantity') or 0
                unit = item.get('unit') or 'Pcs'
                stock_item = QTableWidgetItem(f"{stock} {unit}")
                stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                stock_item.setFont(QFont("Segoe UI", 8.5, QFont.Weight.Bold))
                stock_item.setForeground(QBrush(QColor('#047857') if stock > 0 else QColor('#b91c1c')))
                self.master_table.setItem(row, 3, stock_item)

                # Unit Rate
                rate = float(item.get('rate') or 0.0)
                rate_item = QTableWidgetItem(f"{currency_symbol} {rate:,.2f}")
                rate_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                rate_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                rate_item.setForeground(QBrush(QColor('#0284c7')))
                self.master_table.setItem(row, 4, rate_item)

                # Status
                status_item = QTableWidgetItem("● Active")
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                status_item.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                status_item.setForeground(QBrush(QColor('#15803d')))
                self.master_table.setItem(row, 5, status_item)

                actions_col = 6

            elif master_type == "AC Brands":
                # Brand Name
                name_item = QTableWidgetItem(str(item.get('name') or ''))
                name_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                name_item.setForeground(QBrush(QColor('#0f172a')))
                self.master_table.setItem(row, 1, name_item)

                # Created Date
                created = str(item.get('created_at') or '')[:10]
                if created and '-' in created:
                    parts = created.split('-')
                    if len(parts) == 3 and len(parts[0]) == 4:
                        created = f"{parts[2]}-{parts[1]}-{parts[0]}"
                date_item = QTableWidgetItem(created or '—')
                date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                date_item.setFont(QFont("Segoe UI", 8.5))
                date_item.setForeground(QBrush(QColor('#475569')))
                self.master_table.setItem(row, 2, date_item)

                # Status
                status_item = QTableWidgetItem("● Active")
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                status_item.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                status_item.setForeground(QBrush(QColor('#15803d')))
                self.master_table.setItem(row, 3, status_item)

                actions_col = 4

            else:
                # Name / Value
                name_item = QTableWidgetItem(str(item.get('name') or ''))
                name_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                name_item.setForeground(QBrush(QColor('#0f172a')))
                self.master_table.setItem(row, 1, name_item)

                # Status
                status_item = QTableWidgetItem("● Active")
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                status_item.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                status_item.setForeground(QBrush(QColor('#15803d')))
                self.master_table.setItem(row, 2, status_item)

                actions_col = 3

            # Actions widget
            actions_widget = QWidget()
            actions_widget.setStyleSheet("background: transparent;")
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 0, 4, 0)
            actions_layout.setSpacing(8)
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            curr_id = item['id']

            edit_btn = QPushButton("✏️ Edit")
            edit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            edit_btn.setFixedSize(76, 28)
            edit_btn.setStyleSheet("""
                QPushButton {
                    background: #eff6ff;
                    color: #1d4ed8;
                    border: 1px solid #bfdbfe;
                    border-radius: 5px;
                    font-size: 8.5pt;
                    font-weight: 600;
                    padding: 0;
                }
                QPushButton:hover {
                    background: #2563eb;
                    color: #ffffff;
                    border: 1px solid #2563eb;
                }
            """)
            edit_btn.clicked.connect(lambda checked, cid=curr_id: self._edit_master_item(cid))
            actions_layout.addWidget(edit_btn)

            delete_btn = QPushButton("🗑️ Delete")
            delete_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            delete_btn.setFixedSize(78, 28)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background: #fef2f2;
                    color: #b91c1c;
                    border: 1px solid #fecaca;
                    border-radius: 5px;
                    font-size: 8.5pt;
                    font-weight: 600;
                    padding: 0;
                }
                QPushButton:hover {
                    background: #dc2626;
                    color: #ffffff;
                    border: 1px solid #dc2626;
                }
            """)
            delete_btn.clicked.connect(lambda checked, cid=curr_id: self._delete_master_item(cid))
            actions_layout.addWidget(delete_btn)

            self.master_table.setCellWidget(row, actions_col, actions_widget)
            self.master_table.setRowHeight(row, 44)

        if hasattr(self, 'master_count_label'):
            count = self.master_table.rowCount()
            self.master_count_label.setText(f"{count} active item{'s' if count != 1 else ''}")

        self.master_table.setSortingEnabled(True)

    def _add_master_item(self):
        """Add new master item with real-time update"""
        master_type = self.master_type_combo.currentText()
        dialog = AddMasterItemDialog(master_type, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_master_data()
            singular = master_type[:-1] if master_type.endswith('s') else master_type
            self.show_success_message(f"{singular} added successfully")
            # Emit real-time update
            from utils.event_bus import get_event_bus
            event_bus = get_event_bus()
            event_bus.emit_master_data_updated(master_type)

    def _edit_master_item(self, item_id):
        """Edit master item with real-time update"""
        master_type = self.master_type_combo.currentText()
        dialog = EditMasterItemDialog(master_type, item_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_master_data()
            singular = master_type[:-1] if master_type.endswith('s') else master_type
            self.show_success_message(f"{singular} updated successfully")
            # Emit real-time update
            from utils.event_bus import get_event_bus
            event_bus = get_event_bus()
            event_bus.emit_master_data_updated(master_type)

    def _delete_master_item(self, item_id):
        """Delete master item with real-time update and safety recovery"""
        master_type = self.master_type_combo.currentText()
        singular = master_type[:-1] if master_type.endswith('s') else master_type

        if self.show_question(f"Are you sure you want to delete this {singular}?\n\nIt will be safely moved to Deleted Items and can be restored anytime."):
            from database.db_connection import DatabaseContext

            with DatabaseContext() as db:
                if master_type == "Services":
                    db.execute_query("UPDATE services SET is_active = FALSE WHERE id = %s", (item_id,))
                elif master_type == "Parts":
                    db.execute_query("UPDATE parts SET is_active = FALSE WHERE id = %s", (item_id,))
                elif master_type == "AC Brands":
                    db.execute_query("UPDATE ac_brands SET is_active = FALSE WHERE id = %s", (item_id,))
                elif master_type == "AC Types":
                    db.execute_query("UPDATE ac_types SET is_active = FALSE WHERE id = %s", (item_id,))
                elif master_type == "AC Tonnage":
                    db.execute_query("UPDATE ac_capacities SET is_active = FALSE WHERE id = %s", (item_id,))
                elif master_type == "Star Ratings":
                    db.execute_query("UPDATE ac_stars SET is_active = FALSE WHERE id = %s", (item_id,))
                elif master_type == "Inventory Units":
                    db.execute_query("UPDATE inventory_units SET is_active = FALSE WHERE id = %s", (item_id,))
                elif master_type == "Technician Statuses":
                    db.execute_query("UPDATE technician_statuses SET is_active = FALSE WHERE id = %s", (item_id,))
                elif master_type == "Payment Modes":
                    db.execute_query("UPDATE payment_modes SET is_active = FALSE WHERE id = %s", (item_id,))

            self._load_master_data()
            self.show_success_message(f"{singular} deleted successfully (recoverable in Deleted Items)")
            # Emit real-time update
            from utils.event_bus import get_event_bus
            event_bus = get_event_bus()
            event_bus.emit_master_data_updated(master_type)
    
    def refresh_data(self):
        """Refresh settings data"""
        self.load_user_profile()


    def _create_shortcuts_tab(self):
        """Create keyboard shortcuts customization tab - enterprise card and table layout."""
        from utils.shortcut_manager import get_shortcut_manager, DEFAULT_SHORTCUTS
        from PySide6.QtGui import QKeySequence

        S = self.S
        scroll, layout = self._make_section_scroll()

        # Info card
        info_card = self._make_styled_group(
            "Keyboard Shortcuts",
            description="Accelerate your workflow with quick keyboard shortcuts. Double-click or click Edit to change a key combination.")
        layout.addWidget(info_card)

        # Toolbar card: search & filter
        tb_card = self._make_styled_group("Shortcut Directory")
        tb_l = QHBoxLayout()
        tb_l.setSpacing(14)

        search_col = QVBoxLayout()
        search_col.setSpacing(4)
        search_lbl = QLabel("Search Shortcuts")
        search_lbl.setStyleSheet(f"font-weight: 600; font-size: 9pt; color: {S['text2']}; background: transparent;")
        search_col.addWidget(search_lbl)

        self._shortcut_search = QLineEdit()
        self._shortcut_search.setPlaceholderText("Type action name or key (e.g. Invoice, Ctrl+N)...")
        self._shortcut_search.setClearButtonEnabled(True)
        self._shortcut_search.setMinimumWidth(280)
        self._shortcut_search.setStyleSheet(f"""
            QLineEdit {{
                background: {S['bg']};
                color: {S['text']};
                border: 1px solid {S['border']};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 9.5pt;
            }}
            QLineEdit:focus {{
                border: 1px solid {S['primary']};
            }}
        """)
        search_col.addWidget(self._shortcut_search)
        tb_l.addLayout(search_col)
        tb_l.addStretch()

        reset_btn = QPushButton("↺  Reset All to Defaults")
        reset_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        reset_btn.setFixedHeight(38)
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {S['text2']};
                border: 1px solid {S['border']};
                border-radius: 6px;
                padding: 0 16px;
                font-size: 9pt;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {S['hover']};
                border-color: {S['text2']};
            }}
        """)
        reset_btn.clicked.connect(self._on_shortcut_reset)
        tb_l.addWidget(reset_btn, alignment=Qt.AlignmentFlag.AlignBottom)

        tb_card.layout().addLayout(tb_l)
        layout.addWidget(tb_card)

        # Shortcuts table container
        table_container = QFrame()
        table_container.setStyleSheet(f"""
            QFrame {{
                background: {S['card']};
                border: 1px solid {S['border']};
                border-radius: 8px;
            }}
        """)
        tc_layout = QVBoxLayout(table_container)
        tc_layout.setContentsMargins(0, 0, 0, 0)
        tc_layout.setSpacing(0)

        self.shortcut_mgr = get_shortcut_manager()
        shortcuts = self.shortcut_mgr.get_all_shortcuts()

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Action", "Shortcut Key", "Description", "Customize"])
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(46)
        table.setShowGrid(True)
        table.setGridStyle(Qt.PenStyle.SolidLine)
        table.setSortingEnabled(True)
        table.setMinimumHeight(380)

        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #ffffff;
                color: #1a1a1a;
                border: none;
                gridline-color: #e2e8f0;
                selection-background-color: #eff6ff;
                selection-color: #1a1a1a;
                font-family: 'Segoe UI', sans-serif;
                font-size: 10pt;
            }}
            QTableWidget::item {{
                padding: 8px 14px;
                border-bottom: 1px solid #e2e8f0;
                border-right: 1px solid #e2e8f0;
            }}
            QTableWidget::item:selected {{
                background: #eff6ff;
                color: #1a1a1a;
            }}
            QTableWidget::item:hover {{
                background: #f8fafc;
            }}
            QHeaderView::section {{
                background: #f8fafc;
                color: #334155;
                padding: 11px 14px;
                border: none;
                border-bottom: 2px solid #cbd5e1;
                border-right: 1px solid #e2e8f0;
                font-weight: 700;
                font-size: 9pt;
            }}
            QHeaderView::section:last {{
                border-right: none;
            }}
        """)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, 180)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(1, 150)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(3, 120)

        action_names = {
            'new_invoice': 'New Invoice',
            'search': 'Search Customers',
            'refresh': 'Refresh Data',
            'dashboard': 'Open Dashboard',
            'customers': 'Open Customers',
            'settings': 'Open Settings',
            'print': 'Print Invoice',
            'daily_logs': 'Open Daily Logs',
            'technicians': 'Open Technicians',
            'invoice_mgmt': 'Manage Invoices',
            'amc': 'AMC Contracts',
        }
        desc_texts = {
            'new_invoice': 'Create a new customer invoice',
            'search': 'Focus customer search bar',
            'refresh': 'Refresh current view & data',
            'dashboard': 'Switch to dashboard overview',
            'customers': 'Switch to customer directory',
            'settings': 'Open system settings window',
            'print': 'Print current invoice receipt',
            'daily_logs': 'Open daily work and cost logs register',
            'technicians': 'Open technician management view',
            'invoice_mgmt': 'View & search all historical invoices',
            'amc': 'Manage annual maintenance contracts',
        }

        self._shortcut_table = table
        self._shortcut_keys = list(shortcuts.keys())

        table.setRowCount(len(self._shortcut_keys))
        for i, name in enumerate(self._shortcut_keys):
            sc = shortcuts[name]

            # Col 0: Action Name
            act_item = QTableWidgetItem(action_names.get(name, name))
            act_item.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
            act_item.setForeground(QBrush(QColor('#0f172a')))
            table.setItem(i, 0, act_item)

            # Col 1: Key Combination (badge style)
            key_text = sc.get('key', '')
            key_item = QTableWidgetItem(f"  {key_text}  " if key_text else "—")
            key_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            key_item.setForeground(QBrush(QColor('#2563eb')))
            key_item.setBackground(QBrush(QColor('#eff6ff')))
            key_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            table.setItem(i, 1, key_item)

            # Col 2: Description
            desc_item = QTableWidgetItem(desc_texts.get(name, ''))
            desc_item.setForeground(QBrush(QColor('#475569')))
            table.setItem(i, 2, desc_item)

            # Col 3: Edit Action Button - modern enterprise pill button
            btn_widget = QWidget()
            btn_widget.setStyleSheet("background: transparent;")
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            edit_btn = QPushButton("✏️ Edit")
            edit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            edit_btn.setFixedSize(82, 30)
            edit_btn.setStyleSheet("""
                QPushButton {
                    background: #eff6ff;
                    color: #2563eb;
                    border: 1px solid #bfdbfe;
                    border-radius: 6px;
                    font-size: 9pt;
                    font-weight: 600;
                    padding: 0;
                    min-height: 30px;
                    max-height: 30px;
                }
                QPushButton:hover {
                    background: #2563eb;
                    color: #ffffff;
                    border: 1px solid #2563eb;
                }
                QPushButton:pressed {
                    background: #1d4ed8;
                    color: #ffffff;
                }
            """)
            edit_btn.clicked.connect(lambda checked, r=i: self._on_shortcut_edit(r, 1))
            btn_layout.addWidget(edit_btn)
            table.setCellWidget(i, 3, btn_widget)
            table.setRowHeight(i, 48)

        def filter_shortcuts(text):
            query = text.lower().strip()
            for r in range(table.rowCount()):
                match = False
                for c in (0, 1, 2):
                    item = table.item(r, c)
                    if item and query in item.text().lower():
                        match = True
                        break
                table.setRowHidden(r, not match)

        self._shortcut_search.textChanged.connect(filter_shortcuts)
        table.cellDoubleClicked.connect(self._on_shortcut_edit)
        tc_layout.addWidget(table)
        layout.addWidget(table_container)

        layout.addStretch()
        return scroll

    def _on_shortcut_edit(self, row, col):
        """Handle shortcut edit with a polished enterprise key-capture modal."""
        if row < 0 or row >= len(self._shortcut_keys):
            return
        name = self._shortcut_keys[row]
        current = self._shortcut_table.item(row, 1).text().strip()

        class KeyCaptureEdit(QLineEdit):
            """Line edit that records the pressed key combination"""
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setReadOnly(True)
                self.setPlaceholderText("Press new key combination on keyboard...")
                self.setAlignment(Qt.AlignCenter)
                self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

            def keyPressEvent(self, event):
                key = event.key()
                if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
                    event.accept()
                    return
                seq = QKeySequence(int(event.modifiers()) | key)
                if not seq.isEmpty():
                    self.setText(seq.toString(QKeySequence.SequenceFormat.NativeText))
                event.accept()

        S = self.S
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Keyboard Shortcut")
        dialog.setFixedWidth(460)
        dialog.setStyleSheet(f"background: {S['card']};")

        lay = QVBoxLayout(dialog)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        title_lbl = QLabel(f"⌨️  Change Shortcut: {name.replace('_', ' ').title()}")
        title_lbl.setStyleSheet(f"font-size: 13pt; font-weight: 700; color: {S['text']}; background: transparent;")
        lay.addWidget(title_lbl)

        hint_lbl = QLabel("Click inside the box below and press the desired shortcut combination on your keyboard (e.g. Ctrl+Shift+N or F5).")
        hint_lbl.setWordWrap(True)
        hint_lbl.setStyleSheet(f"color: {S['text2']}; font-size: 9pt; background: transparent; line-height: 1.4;")
        lay.addWidget(hint_lbl)

        cap = KeyCaptureEdit()
        if current and current != "—":
            cap.setText(current)
        cap.setFixedHeight(50)
        cap.setStyleSheet(f"""
            QLineEdit {{
                background: {S['bg']};
                color: {S['primary']};
                border: 2px dashed {S['primary']}80;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13pt;
                font-weight: 700;
            }}
            QLineEdit:focus {{
                border: 2px solid {S['primary']};
                background: {S['primary_lt']};
            }}
        """)
        lay.addWidget(cap)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.setFixedHeight(38)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {S['text2']};
                border: 1px solid {S['border']}; border-radius: 6px;
                padding: 0 20px; font-size: 9.5pt; font-weight: 600;
            }}
            QPushButton:hover {{ background: {S['hover']}; }}
        """)
        cancel_btn.clicked.connect(dialog.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save Shortcut")
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_btn.setFixedHeight(38)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {S['primary']}; color: #ffffff;
                border: none; border-radius: 6px;
                padding: 0 22px; font-size: 9.5pt; font-weight: 700;
            }}
            QPushButton:hover {{ background: #1d4ed8; }}
        """)
        save_btn.clicked.connect(dialog.accept)
        btn_row.addWidget(save_btn)
        lay.addLayout(btn_row)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_key = cap.text().strip()
            if not new_key:
                self.show_error_message("Invalid key sequence")
                return
            seq = QKeySequence(new_key)
            if seq.isEmpty():
                self.show_error_message("Invalid key sequence")
                return
            self.shortcut_mgr.save_shortcut(name, new_key)
            item = self._shortcut_table.item(row, 1)
            item.setText(f"  {new_key}  ")
            item.setForeground(QBrush(QColor('#2563eb')))
            item.setBackground(QBrush(QColor('#eff6ff')))
            self.show_success_message(f"Shortcut for '{name.replace('_', ' ').title()}' updated to {new_key}.")

    def _on_shortcut_reset(self):
        """Reset all shortcuts to defaults"""
        if self.show_question("Reset all shortcuts to default values?"):
            from utils.shortcut_manager import get_shortcut_manager
            mgr = get_shortcut_manager()
            mgr.reset_to_defaults()
            shortcuts = mgr.get_all_shortcuts()
            for i, name in enumerate(self._shortcut_keys):
                if name in shortcuts:
                    item = self._shortcut_table.item(i, 1)
                    key_text = shortcuts[name].get('key', '')
                    item.setText(f"  {key_text}  " if key_text else "—")
                    item.setForeground(QBrush(QColor('#2563eb')))
                    item.setBackground(QBrush(QColor('#eff6ff')))
            self.show_success_message("All shortcuts have been reset to factory defaults.")

    def _create_language_tab(self):
        """Create language & regional localization tab - enterprise layout."""
        S = self.S
        scroll, layout = self._make_section_scroll()

        # Language selection card
        lang_card = self._make_styled_group(
            "Application Language",
            description="Select interface language for all menus, forms, receipts, and system dialogs")

        self.lang_group = QButtonGroup(self)

        lang_options_layout = QVBoxLayout()
        lang_options_layout.setSpacing(12)

        # English Card
        en_frame = QFrame()
        en_frame.setStyleSheet(f"""
            QFrame {{
                background: {S['bg']};
                border: 1px solid {S['border']};
                border-radius: 8px;
                padding: 12px 16px;
            }}
            QFrame:hover {{
                border-color: {S['primary']};
            }}
        """)
        en_hl = QHBoxLayout(en_frame)
        en_hl.setContentsMargins(10, 8, 10, 8)
        en_hl.setSpacing(14)

        en_radio = QRadioButton()
        en_radio.setStyleSheet(f"""
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
            }}
        """)
        en_radio.setProperty('lang_code', 'en')
        self.lang_group.addButton(en_radio, 0)
        en_hl.addWidget(en_radio)

        en_text_col = QVBoxLayout()
        en_text_col.setSpacing(2)
        en_title = QLabel("English (Default)")
        en_title.setStyleSheet(f"font-size: 11pt; font-weight: 700; color: {S['text']}; background: transparent;")
        en_text_col.addWidget(en_title)
        en_sub = QLabel("Standard international business terminology for billing, receipts and invoices.")
        en_sub.setStyleSheet(f"font-size: 8.5pt; color: {S['text2']}; background: transparent;")
        en_text_col.addWidget(en_sub)
        en_hl.addLayout(en_text_col, 1)

        en_badge = QLabel("EN")
        en_badge.setStyleSheet(f"background: {S['primary_lt']}; color: {S['primary']}; font-weight: 800; font-size: 9pt; border-radius: 4px; padding: 4px 8px;")
        en_hl.addWidget(en_badge)
        lang_options_layout.addWidget(en_frame)

        # Hindi Card
        hi_frame = QFrame()
        hi_frame.setStyleSheet(f"""
            QFrame {{
                background: {S['bg']};
                border: 1px solid {S['border']};
                border-radius: 8px;
                padding: 12px 16px;
            }}
            QFrame:hover {{
                border-color: {S['primary']};
            }}
        """)
        hi_hl = QHBoxLayout(hi_frame)
        hi_hl.setContentsMargins(10, 8, 10, 8)
        hi_hl.setSpacing(14)

        hi_radio = QRadioButton()
        hi_radio.setStyleSheet(f"""
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
            }}
        """)
        hi_radio.setProperty('lang_code', 'hi')
        self.lang_group.addButton(hi_radio, 1)
        hi_hl.addWidget(hi_radio)

        hi_text_col = QVBoxLayout()
        hi_text_col.setSpacing(2)
        hi_title = QLabel("हिन्दी (Hindi)")
        hi_title.setStyleSheet(f"font-size: 11pt; font-weight: 700; color: {S['text']}; background: transparent;")
        hi_text_col.addWidget(hi_title)
        hi_sub = QLabel("पूर्ण हिन्दी स्थानीयकरण — भारतीय उपयोगकर्ताओं एवं क्षेत्रीय स्टाफ के लिए उपयुक्त।")
        hi_sub.setStyleSheet(f"font-size: 8.5pt; color: {S['text2']}; background: transparent;")
        hi_text_col.addWidget(hi_sub)
        hi_hl.addLayout(hi_text_col, 1)

        hi_badge = QLabel("HI")
        hi_badge.setStyleSheet(f"background: {S['warning_lt']}; color: {S['warning']}; font-weight: 800; font-size: 9pt; border-radius: 4px; padding: 4px 8px;")
        hi_hl.addWidget(hi_badge)
        lang_options_layout.addWidget(hi_frame)

        lang_card.layout().addLayout(lang_options_layout)
        layout.addWidget(lang_card)

        # Set current language
        from utils.language import current_language
        curr_lang = current_language()
        if curr_lang == 'hi':
            hi_radio.setChecked(True)
        else:
            en_radio.setChecked(True)

        # Live Dynamic Translation Preview Card
        preview_card = self._make_styled_group(
            "Live Interface Preview",
            description="Dynamic preview demonstrating how key system labels appear in the selected language")

        preview_grid = QGridLayout()
        preview_grid.setHorizontalSpacing(16)
        preview_grid.setVerticalSpacing(10)

        preview_terms = [
            ("Dashboard", "dashboard"),
            ("Customers", "customers"),
            ("Invoice", "invoice"),
            ("Settings", "settings"),
            ("Total Revenue", "total_revenue"),
            ("Services Done", "services_done"),
        ]

        self._preview_labels = {}
        for idx, (label_title, key) in enumerate(preview_terms):
            row = idx // 2
            col = (idx % 2) * 2

            title_lbl = QLabel(f"{label_title}:")
            title_lbl.setStyleSheet(f"font-weight: 600; font-size: 9pt; color: {S['text2']}; background: transparent;")
            preview_grid.addWidget(title_lbl, row, col)

            val_lbl = QLabel()
            val_lbl.setStyleSheet(f"""
                background: {S['bg']};
                color: {S['text']};
                font-weight: 700;
                font-size: 9.5pt;
                border: 1px solid {S['border']};
                border-radius: 6px;
                padding: 6px 12px;
            """)
            preview_grid.addWidget(val_lbl, row, col + 1)
            self._preview_labels[key] = val_lbl

        preview_card.layout().addLayout(preview_grid)
        layout.addWidget(preview_card)

        def update_preview():
            from utils.language import _, get_language_manager
            lang = 'hi' if hi_radio.isChecked() else 'en'
            mgr = get_language_manager()
            old_lang = mgr.get_language()
            mgr.set_language(lang)
            for k, lbl in self._preview_labels.items():
                lbl.setText(_(k))
            mgr.set_language(old_lang)

        en_radio.toggled.connect(lambda: update_preview())
        hi_radio.toggled.connect(lambda: update_preview())
        update_preview()

        # Save action button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        save_lang_btn = self._make_gradient_btn(
            "Save Language Setting", S['primary'], "#1d4ed8", "#3b82f6", S['primary'], "✓")
        save_lang_btn.clicked.connect(self._on_language_save)
        btn_row.addWidget(save_lang_btn)
        layout.addLayout(btn_row)

        layout.addStretch()
        return scroll

    def _on_language_save(self):
        """Save selected language with confirmation"""
        selected = self.lang_group.checkedButton()
        if not selected:
            return
        lang_code = selected.property('lang_code')
        from utils.language import set_language, get_language_manager
        mgr = get_language_manager()
        if mgr.set_language(lang_code):
            lang_name = "हिन्दी (Hindi)" if lang_code == 'hi' else "English"
            self.show_success_message(f"Application language set to {lang_name}.\nPlease restart the application for all window titles and menus to take full effect.")
        else:
            self.show_error_message("Failed to save language setting.")

    def _create_backup_tab(self):
        """Create Backup & Restore tab - enterprise administration view."""
        import os
        from controllers.settings_controller import SettingsController
        from database.db_connection import DatabaseConnection

        S = self.S
        scroll, layout = self._make_section_scroll()

        # System Health & Status card
        health_card = self._make_styled_group(
            "System Data Health & Storage",
            description="Active database status, storage health and previous backup records")

        health_l = QVBoxLayout()
        health_l.setSpacing(12)

        # Status row
        status_h = QHBoxLayout()
        status_h.setSpacing(10)
        status_dot = QLabel("●")
        status_dot.setStyleSheet(f"font-size: 14pt; color: {S['success']}; background: transparent;")
        status_h.addWidget(status_dot)
        status_text = QLabel("Database Engine: SQLite  ·  Journal Mode: WAL (High Concurrency & Crash Resilient)")
        status_text.setStyleSheet(f"font-weight: 700; font-size: 10pt; color: {S['text']}; background: transparent;")
        status_h.addWidget(status_text)
        status_h.addStretch()
        health_l.addLayout(status_h)

        # Info metrics row
        metrics_grid = QHBoxLayout()
        metrics_grid.setSpacing(14)

        # Metric 1: Last backup
        m1 = QFrame()
        m1.setStyleSheet(f"background: {S['bg']}; border: 1px solid {S['border']}; border-radius: 8px; padding: 12px 16px;")
        m1_l = QVBoxLayout(m1)
        m1_l.setSpacing(4)
        m1_sub = QLabel("LAST CREATED BACKUP")
        m1_sub.setStyleSheet(f"font-size: 7.5pt; font-weight: 800; color: {S['muted']}; letter-spacing: 1px;")
        m1_l.addWidget(m1_sub)
        self.backup_info_label = QLabel("Scanning backups...")
        self.backup_info_label.setStyleSheet(f"font-size: 10.5pt; font-weight: 700; color: {S['text']};")
        m1_l.addWidget(self.backup_info_label)
        metrics_grid.addWidget(m1, 1)

        # Metric 2: Backups folder
        m2 = QFrame()
        m2.setStyleSheet(f"background: {S['bg']}; border: 1px solid {S['border']}; border-radius: 8px; padding: 12px 16px;")
        m2_l = QVBoxLayout(m2)
        m2_l.setSpacing(4)
        m2_sub = QLabel("BACKUP DIRECTORY")
        m2_sub.setStyleSheet(f"font-size: 7.5pt; font-weight: 800; color: {S['muted']}; letter-spacing: 1px;")
        m2_l.addWidget(m2_sub)
        backups_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
        dir_lbl = QLabel(f"📁 {backups_dir}")
        dir_lbl.setStyleSheet(f"font-size: 9pt; font-weight: 600; color: {S['text2']};")
        m2_l.addWidget(dir_lbl)
        metrics_grid.addWidget(m2, 1)

        health_l.addLayout(metrics_grid)
        health_card.layout().addLayout(health_l)
        layout.addWidget(health_card)

        # Create Backup Card
        backup_card = self._make_styled_group(
            "Create System Backup",
            description="Export a complete snapshot of all customers, invoices, items, technician logs, and configuration to an encrypted JSON backup file")
        bc_l = QVBoxLayout()
        bc_l.setSpacing(14)

        bc_desc = QLabel(
            "Backups are completely self-contained and allow seamless restoration in case of hardware failure, machine migration, or data corruption.")
        bc_desc.setWordWrap(True)
        bc_desc.setStyleSheet(f"color: {S['text2']}; font-size: 9pt; background: transparent;")
        bc_l.addWidget(bc_desc)

        bc_btn_row = QHBoxLayout()
        bc_btn_row.setSpacing(12)
        create_backup_btn = self._make_gradient_btn(
            "Create Full System Backup Now", "#059669", "#047857", "#10b981", "#059669", "📤")
        create_backup_btn.setFixedHeight(44)
        create_backup_btn.clicked.connect(self._do_backup)
        bc_btn_row.addWidget(create_backup_btn)

        open_folder_btn = QPushButton("📁  Open Backup Folder")
        open_folder_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        open_folder_btn.setFixedHeight(44)
        open_folder_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {S['text2']};
                border: 1px solid {S['border']};
                border-radius: 6px;
                padding: 0 18px;
                font-size: 9.5pt;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {S['hover']};
                border-color: {S['text2']};
            }}
        """)
        def open_dir():
            try:
                os.makedirs(backups_dir, exist_ok=True)
                os.startfile(backups_dir)
            except Exception as e:
                self.show_error_message(f"Could not open directory: {e}")
        open_folder_btn.clicked.connect(open_dir)
        bc_btn_row.addWidget(open_folder_btn)
        bc_btn_row.addStretch()
        bc_l.addLayout(bc_btn_row)

        backup_card.layout().addLayout(bc_l)
        layout.addWidget(backup_card)

        # Restore Card
        restore_card = self._make_styled_group(
            "Restore Database",
            description="Restore all system records from a previously exported backup archive")
        rc_l = QVBoxLayout()
        rc_l.setSpacing(14)

        # Warning Callout
        warn_box = QFrame()
        warn_box.setStyleSheet(f"""
            QFrame {{
                background: #fef2f2;
                border: 1px solid #fecaca;
                border-left: 4px solid #ef4444;
                border-radius: 6px;
                padding: 12px 16px;
            }}
        """)
        wb_layout = QVBoxLayout(warn_box)
        wb_layout.setSpacing(4)
        wb_title = QLabel("⚠️ Caution: Data Overwrite Warning")
        wb_title.setStyleSheet("font-weight: 800; font-size: 9.5pt; color: #b91c1c; background: transparent;")
        wb_layout.addWidget(wb_title)
        wb_text = QLabel("Restoring will completely overwrite the active database with data from the backup archive. Make sure you have created an up-to-date backup before initiating a restore operation.")
        wb_text.setWordWrap(True)
        wb_text.setStyleSheet("font-size: 9pt; color: #7f1d1d; background: transparent;")
        wb_layout.addWidget(wb_text)
        rc_l.addWidget(warn_box)

        restore_btn = self._make_gradient_btn(
            "Select Backup File to Restore...", "#d97706", "#b45309", "#f59e0b", "#d97706", "📥")
        restore_btn.setFixedHeight(44)
        restore_btn.clicked.connect(self._do_restore)
        rc_l.addWidget(restore_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        restore_card.layout().addLayout(rc_l)
        layout.addWidget(restore_card)

        self._update_backup_info()
        layout.addStretch()
        return scroll

    def _update_backup_info(self):
        """Update last backup timestamp and status display"""
        import os, glob, datetime
        backups_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
        if os.path.exists(backups_dir):
            files = glob.glob(os.path.join(backups_dir, '*.json'))
            if files:
                latest = max(files, key=os.path.getmtime)
                size = os.path.getsize(latest)
                mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(latest))
                self.backup_info_label.setText(
                    f"{os.path.basename(latest)} ({size/1024:.1f} KB) · {mod_time.strftime('%d-%b-%Y %I:%M %p')}")
            else:
                self.backup_info_label.setText("No backups found yet")
        else:
            self.backup_info_label.setText("Backups directory not yet initialized")

    def _do_backup(self):
        """Execute full backup"""
        from controllers.settings_controller import SettingsController
        from database.db_connection import DatabaseConnection
        db = DatabaseConnection()
        sc = SettingsController(db)
        try:
            path = sc.create_backup()
            self._update_backup_info()
            self.show_success_message(f"Backup created successfully!\n\nSaved to:\n{path}")
        except Exception as e:
            self.show_error_message(f"Backup failed: {str(e)}")

    def _do_restore(self):
        """Execute restore with security confirmations"""
        from PySide6.QtWidgets import QFileDialog
        from controllers.settings_controller import SettingsController
        from database.db_connection import DatabaseConnection

        if not self.show_question(
            "RESTORE SYSTEM DATA\n\nThis operation will OVERWRITE all current database records.\n"
            "Are you absolutely sure you want to proceed?"
        ):
            return
        if not self.show_question(
            "FINAL CONFIRMATION\n\nExisting data will be replaced by the backup.\n"
            "This action cannot be undone. Continue?"
        ):
            return

        path, _ = QFileDialog.getOpenFileName(
            self, "Select Backup File", "", "Backup Files (*.json);;All Files (*.*)")
        if not path:
            return

        try:
            db = DatabaseConnection()
            sc = SettingsController(db)
            sc.restore_backup(path)
            self.show_success_message("Database restored successfully from backup! System will now refresh.")
            self.settings_saved.emit()
        except Exception as e:
            self.show_error_message(f"Restore failed: {str(e)}")


class ProfileSettingsView(SettingsView):
    """Profile settings view - opens Settings with profile section focused"""
    def __init__(self, user_data, parent=None):
        super().__init__(user_data)
        self._switch_settings_section(0)


class ChangePasswordDialog(QDialog):
    """Enterprise modal for changing user password"""

    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle("Change Password")
        self.setFixedWidth(460)
        S = SettingsView.S
        self.setStyleSheet(f"background: {S['card']};")
        self._setup_ui()

    def _setup_ui(self):
        """Setup dialog UI"""
        S = SettingsView.S
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title_lbl = QLabel("🔑  Change Password")
        title_lbl.setStyleSheet(f"font-size: 14pt; font-weight: 700; color: {S['text']}; background: transparent;")
        layout.addWidget(title_lbl)

        input_style = f"""
            QLineEdit {{
                background: {S['bg']};
                color: {S['text']};
                border: 1px solid {S['border']};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 10pt;
            }}
            QLineEdit:focus {{
                border: 1px solid {S['primary']};
            }}
        """
        eye_style = f"""
            QPushButton {{
                background: {S['bg']};
                border: 1px solid {S['border']};
                border-radius: 6px;
                font-size: 9pt;
                color: {S['text2']};
            }}
            QPushButton:hover {{
                color: {S['primary']};
                border-color: {S['primary']};
            }}
        """

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Current Password
        self.current_password_input = QLineEdit()
        self.current_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.current_password_input.setPlaceholderText("Enter current password")
        self.current_password_input.setFixedHeight(38)
        self.current_password_input.setStyleSheet(input_style)

        current_pw_layout = QHBoxLayout()
        current_pw_layout.setSpacing(6)
        current_pw_layout.addWidget(self.current_password_input, 1)
        self.current_eye_btn = QPushButton("Show")
        self.current_eye_btn.setFixedSize(54, 38)
        self.current_eye_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.current_eye_btn.setCheckable(True)
        self.current_eye_btn.setStyleSheet(eye_style)
        def toggle_current(checked):
            self.current_password_input.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)
            self.current_eye_btn.setText("Hide" if checked else "Show")
        self.current_eye_btn.toggled.connect(toggle_current)
        current_pw_layout.addWidget(self.current_eye_btn)

        lbl = QLabel("Current Password *")
        lbl.setStyleSheet(f"font-weight: 600; font-size: 9.5pt; color: {S['text2']}; background: transparent;")
        form.addRow(lbl, current_pw_layout)

        # New Password
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setPlaceholderText("Enter new password (min 8 chars)")
        self.new_password_input.setFixedHeight(38)
        self.new_password_input.setStyleSheet(input_style)

        new_pw_layout = QHBoxLayout()
        new_pw_layout.setSpacing(6)
        new_pw_layout.addWidget(self.new_password_input, 1)
        self.new_eye_btn = QPushButton("Show")
        self.new_eye_btn.setFixedSize(54, 38)
        self.new_eye_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_eye_btn.setCheckable(True)
        self.new_eye_btn.setStyleSheet(eye_style)
        def toggle_new(checked):
            self.new_password_input.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)
            self.new_eye_btn.setText("Hide" if checked else "Show")
        self.new_eye_btn.toggled.connect(toggle_new)
        new_pw_layout.addWidget(self.new_eye_btn)

        lbl2 = QLabel("New Password *")
        lbl2.setStyleSheet(f"font-weight: 600; font-size: 9.5pt; color: {S['text2']}; background: transparent;")
        form.addRow(lbl2, new_pw_layout)

        # Confirm Password
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setPlaceholderText("Re-enter new password to verify")
        self.confirm_password_input.setFixedHeight(38)
        self.confirm_password_input.setStyleSheet(input_style)

        confirm_pw_layout = QHBoxLayout()
        confirm_pw_layout.setSpacing(6)
        confirm_pw_layout.addWidget(self.confirm_password_input, 1)
        self.confirm_eye_btn = QPushButton("Show")
        self.confirm_eye_btn.setFixedSize(54, 38)
        self.confirm_eye_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.confirm_eye_btn.setCheckable(True)
        self.confirm_eye_btn.setStyleSheet(eye_style)
        def toggle_confirm(checked):
            self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)
            self.confirm_eye_btn.setText("Hide" if checked else "Show")
        self.confirm_eye_btn.toggled.connect(toggle_confirm)
        confirm_pw_layout.addWidget(self.confirm_eye_btn)

        lbl3 = QLabel("Confirm Password *")
        lbl3.setStyleSheet(f"font-weight: 600; font-size: 9.5pt; color: {S['text2']}; background: transparent;")
        form.addRow(lbl3, confirm_pw_layout)

        layout.addLayout(form)

        # Password rules helper
        req_box = QFrame()
        req_box.setStyleSheet(f"background: {S['bg']}; border: 1px solid {S['border']}; border-radius: 6px; padding: 10px;")
        req_l = QVBoxLayout(req_box)
        req_l.setSpacing(2)
        req_title = QLabel("Password Strength Rules:")
        req_title.setStyleSheet(f"font-weight: 700; font-size: 8.5pt; color: {S['text']}; background: transparent;")
        req_l.addWidget(req_title)
        req_sub = QLabel("• Minimum 8 characters\n• At least 1 uppercase & 1 lowercase letter\n• At least 1 number & 1 special symbol (!@#$%...)")
        req_sub.setStyleSheet(f"font-size: 8pt; color: {S['text2']}; background: transparent;")
        req_l.addWidget(req_sub)
        layout.addWidget(req_box)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.setFixedHeight(38)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {S['text2']};
                border: 1px solid {S['border']}; border-radius: 6px;
                padding: 0 18px; font-size: 9.5pt; font-weight: 600;
            }}
            QPushButton:hover {{ background: {S['hover']}; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        ok_btn = QPushButton("Change Password")
        ok_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        ok_btn.setFixedHeight(38)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: {S['primary']}; color: #ffffff;
                border: none; border-radius: 6px;
                padding: 0 20px; font-size: 9.5pt; font-weight: 700;
            }}
            QPushButton:hover {{ background: #1d4ed8; }}
        """)
        ok_btn.clicked.connect(self._validate_and_accept)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

    def _validate_and_accept(self):
        """Validate and change password"""
        current = self.current_password_input.text()
        new = self.new_password_input.text()
        confirm = self.confirm_password_input.text()

        if not current or not new or not confirm:
            QMessageBox.warning(self, "Validation", "All password fields are required.")
            return

        if new != confirm:
            QMessageBox.warning(self, "Validation", "New passwords do not match.")
            return

        from controllers.auth_controller import AuthController
        from database.db_connection import DatabaseConnection

        is_valid, message = AuthController.validate_password_strength(new)
        if not is_valid:
            QMessageBox.warning(self, "Password Validation", message)
            return

        db = DatabaseConnection()
        auth = AuthController(db)
        success, msg = auth.change_password(self.user_id, current, new)

        if success:
            self.accept()
            QMessageBox.information(self, "Success", msg)
        else:
            QMessageBox.critical(self, "Error", msg)


class ChangeUsernameDialog(QDialog):
    """Enterprise modal for changing username"""

    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle("Change Username")
        self.setFixedWidth(460)
        S = SettingsView.S
        self.setStyleSheet(f"background: {S['card']};")
        self._setup_ui()

    def _setup_ui(self):
        """Setup dialog UI"""
        S = SettingsView.S
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title_lbl = QLabel("👤  Change Username")
        title_lbl.setStyleSheet(f"font-size: 14pt; font-weight: 700; color: {S['text']}; background: transparent;")
        layout.addWidget(title_lbl)

        info_box = QFrame()
        info_box.setStyleSheet(f"background: {S['warning_lt']}; border: 1px solid #fde68a; border-radius: 6px; padding: 10px 14px;")
        ib_layout = QVBoxLayout(info_box)
        ib_layout.setSpacing(2)
        info_label = QLabel("Notice: Changing your username will update your login credentials immediately. Remember your new username.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {S['warning']}; font-size: 8.5pt; font-weight: 600; background: transparent;")
        ib_layout.addWidget(info_label)
        layout.addWidget(info_box)

        input_style = f"""
            QLineEdit {{
                background: {S['bg']};
                color: {S['text']};
                border: 1px solid {S['border']};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 10pt;
            }}
            QLineEdit:focus {{
                border: 1px solid {S['primary']};
            }}
        """

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # New Username
        self.new_username_input = QLineEdit()
        self.new_username_input.setPlaceholderText("Enter new username")
        self.new_username_input.setFixedHeight(38)
        self.new_username_input.setStyleSheet(input_style)
        lbl1 = QLabel("New Username *")
        lbl1.setStyleSheet(f"font-weight: 600; font-size: 9.5pt; color: {S['text2']}; background: transparent;")
        form.addRow(lbl1, self.new_username_input)

        # Password to confirm
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter current password to authorize")
        self.password_input.setFixedHeight(38)
        self.password_input.setStyleSheet(input_style)

        pw_layout = QHBoxLayout()
        pw_layout.setSpacing(6)
        pw_layout.addWidget(self.password_input, 1)

        self.eye_btn = QPushButton("Show")
        self.eye_btn.setFixedSize(54, 38)
        self.eye_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.eye_btn.setCheckable(True)
        self.eye_btn.setStyleSheet(f"""
            QPushButton {{
                background: {S['bg']};
                border: 1px solid {S['border']};
                border-radius: 6px;
                font-size: 9pt;
                color: {S['text2']};
            }}
            QPushButton:hover {{
                color: {S['primary']};
                border-color: {S['primary']};
            }}
        """)
        def toggle_eye(checked):
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)
            self.eye_btn.setText("Hide" if checked else "Show")
        self.eye_btn.toggled.connect(toggle_eye)
        pw_layout.addWidget(self.eye_btn)

        lbl2 = QLabel("Current Password *")
        lbl2.setStyleSheet(f"font-weight: 600; font-size: 9.5pt; color: {S['text2']}; background: transparent;")
        form.addRow(lbl2, pw_layout)

        layout.addLayout(form)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.setFixedHeight(38)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {S['text2']};
                border: 1px solid {S['border']}; border-radius: 6px;
                padding: 0 18px; font-size: 9.5pt; font-weight: 600;
            }}
            QPushButton:hover {{ background: {S['hover']}; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        ok_btn = QPushButton("Update Username")
        ok_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        ok_btn.setFixedHeight(38)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background: {S['primary']}; color: #ffffff;
                border: none; border-radius: 6px;
                padding: 0 20px; font-size: 9.5pt; font-weight: 700;
            }}
            QPushButton:hover {{ background: #1d4ed8; }}
        """)
        ok_btn.clicked.connect(self._validate_and_accept)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

    def _validate_and_accept(self):
        """Validate and change username"""
        new_username = self.new_username_input.text().strip()
        password = self.password_input.text()

        if not new_username or not password:
            QMessageBox.warning(self, "Validation", "All fields are required.")
            return

        if len(new_username) < 3:
            QMessageBox.warning(self, "Validation", "Username must be at least 3 characters.")
            return

        from controllers.auth_controller import AuthController
        from database.db_connection import DatabaseConnection

        db = DatabaseConnection()
        auth = AuthController(db)
        success, msg = auth.change_username(self.user_id, new_username, password)

        if success:
            self.accept()
            QMessageBox.information(self, "Success", msg)
        else:
            QMessageBox.critical(self, "Error", msg)


class AddMasterItemDialog(QDialog):
    """Enterprise modal for adding master data items"""

    def __init__(self, master_type, parent=None):
        super().__init__(parent)
        self.master_type = master_type
        S = SettingsView.S
        singular = master_type[:-1] if master_type.endswith('s') else master_type
        self.setWindowTitle(f"Add New {singular}")
        self.setFixedWidth(460)
        self.setModal(True)
        self.setStyleSheet(f"background-color: {S['card']};")
        self._setup_ui()

    def _setup_ui(self):
        """Setup dialog UI"""
        S = SettingsView.S
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)

        singular = self.master_type[:-1] if self.master_type.endswith('s') else self.master_type

        # Header
        title_lbl = QLabel(f"➕  Add New {singular}")
        title_lbl.setStyleSheet(f"font-size: 13pt; font-weight: 800; color: {S['text']}; background: transparent;")
        layout.addWidget(title_lbl)

        subtitle_lbl = QLabel(f"Create a new entry in master catalog: {self.master_type}")
        subtitle_lbl.setStyleSheet(f"font-size: 8.5pt; color: {S['muted']}; background: transparent; margin-top: -10px;")
        layout.addWidget(subtitle_lbl)

        # Form card
        form_frame = QFrame()
        form_frame.setStyleSheet(f"""
            QFrame {{
                background: {S['bg']};
                border: 1px solid {S['border']};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        form = QFormLayout(form_frame)
        form.setSpacing(12)
        form.setContentsMargins(0, 0, 0, 0)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Name / Title input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(f"Enter {singular.lower()} name...")
        self.name_input.setFixedHeight(36)
        self.name_input.setStyleSheet(f"""
            QLineEdit {{
                background: #ffffff;
                color: {S['text']};
                border: 1px solid {S['border']};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 9.5pt;
            }}
            QLineEdit:focus {{
                border: 1.5px solid {S['primary']};
            }}
        """)
        name_label = QLabel("Name *")
        name_label.setStyleSheet(f"font-weight: 600; font-size: 9pt; color: {S['text2']}; background: transparent;")
        form.addRow(name_label, self.name_input)

        self.currency_symbol = get_setting("currency_symbol", "₹")

        # Specific fields for Services
        if self.master_type == "Services":
            self.rate_input = QDoubleSpinBox()
            self.rate_input.setRange(0, 999999)
            self.rate_input.setPrefix(self.currency_symbol + " ")
            self.rate_input.setFixedHeight(36)
            self.rate_input.setStyleSheet(f"""
                QDoubleSpinBox {{
                    background: #ffffff;
                    color: {S['text']};
                    border: 1px solid {S['border']};
                    border-radius: 6px;
                    padding: 0 12px;
                    font-size: 9.5pt;
                }}
                QDoubleSpinBox:focus {{
                    border: 1.5px solid {S['primary']};
                }}
            """)
            rate_label = QLabel("Standard Rate")
            rate_label.setStyleSheet(f"font-weight: 600; font-size: 9pt; color: {S['text2']}; background: transparent;")
            form.addRow(rate_label, self.rate_input)

            self.desc_input = QLineEdit()
            self.desc_input.setPlaceholderText("e.g. Indoor & outdoor split unit servicing...")
            self.desc_input.setFixedHeight(36)
            self.desc_input.setStyleSheet(f"""
                QLineEdit {{
                    background: #ffffff;
                    color: {S['text']};
                    border: 1px solid {S['border']};
                    border-radius: 6px;
                    padding: 0 12px;
                    font-size: 9.5pt;
                }}
                QLineEdit:focus {{
                    border: 1.5px solid {S['primary']};
                }}
            """)
            desc_label = QLabel("Description")
            desc_label.setStyleSheet(f"font-weight: 600; font-size: 9pt; color: {S['text2']}; background: transparent;")
            form.addRow(desc_label, self.desc_input)

        # Specific fields for Parts
        elif self.master_type == "Parts":
            self.cat_input = QLineEdit()
            self.cat_input.setPlaceholderText("e.g. Pipes, Gas, Electrical, Motor...")
            self.cat_input.setFixedHeight(36)
            self.cat_input.setStyleSheet(f"""
                QLineEdit {{
                    background: #ffffff;
                    color: {S['text']};
                    border: 1px solid {S['border']};
                    border-radius: 6px;
                    padding: 0 12px;
                    font-size: 9.5pt;
                }}
                QLineEdit:focus {{
                    border: 1.5px solid {S['primary']};
                }}
            """)
            cat_label = QLabel("Category")
            cat_label.setStyleSheet(f"font-weight: 600; font-size: 9pt; color: {S['text2']}; background: transparent;")
            form.addRow(cat_label, self.cat_input)

            self.rate_input = QDoubleSpinBox()
            self.rate_input.setRange(0, 999999)
            self.rate_input.setPrefix(self.currency_symbol + " ")
            self.rate_input.setFixedHeight(36)
            self.rate_input.setStyleSheet(f"""
                QDoubleSpinBox {{
                    background: #ffffff;
                    color: {S['text']};
                    border: 1px solid {S['border']};
                    border-radius: 6px;
                    padding: 0 12px;
                    font-size: 9.5pt;
                }}
                QDoubleSpinBox:focus {{
                    border: 1.5px solid {S['primary']};
                }}
            """)
            rate_label = QLabel("Unit Rate")
            rate_label.setStyleSheet(f"font-weight: 600; font-size: 9pt; color: {S['text2']}; background: transparent;")
            form.addRow(rate_label, self.rate_input)

            self.stock_input = QSpinBox()
            self.stock_input.setRange(0, 99999)
            self.stock_input.setValue(0)
            self.stock_input.setFixedHeight(36)
            self.stock_input.setStyleSheet(f"""
                QSpinBox {{
                    background: #ffffff;
                    color: {S['text']};
                    border: 1px solid {S['border']};
                    border-radius: 6px;
                    padding: 0 12px;
                    font-size: 9.5pt;
                }}
                QSpinBox:focus {{
                    border: 1.5px solid {S['primary']};
                }}
            """)
            stock_label = QLabel("Stock Qty")
            stock_label.setStyleSheet(f"font-weight: 600; font-size: 9pt; color: {S['text2']}; background: transparent;")
            form.addRow(stock_label, self.stock_input)

            self.unit_input = QLineEdit()
            self.unit_input.setPlaceholderText("e.g. Pcs, Mtr, Kg, Set...")
            self.unit_input.setText("Pcs")
            self.unit_input.setFixedHeight(36)
            self.unit_input.setStyleSheet(f"""
                QLineEdit {{
                    background: #ffffff;
                    color: {S['text']};
                    border: 1px solid {S['border']};
                    border-radius: 6px;
                    padding: 0 12px;
                    font-size: 9.5pt;
                }}
                QLineEdit:focus {{
                    border: 1.5px solid {S['primary']};
                }}
            """)
            unit_label = QLabel("Unit")
            unit_label.setStyleSheet(f"font-weight: 600; font-size: 9pt; color: {S['text2']}; background: transparent;")
            form.addRow(unit_label, self.unit_input)

        layout.addWidget(form_frame)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.setFixedHeight(36)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {S['text2']};
                border: 1px solid {S['border']};
                border-radius: 6px;
                padding: 0 20px;
                font-size: 9pt;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {S['hover']};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Entry")
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_btn.setFixedHeight(36)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {S['primary']};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 0 22px;
                font-size: 9pt;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: #1d4ed8;
            }}
        """)
        save_btn.clicked.connect(self._validate_and_accept)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _validate_and_accept(self):
        """Validate and save new master item"""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Name cannot be empty.")
            return

        from database.db_connection import DatabaseContext

        with DatabaseContext() as db:
            try:
                if self.master_type == "Services":
                    rate = self.rate_input.value()
                    desc = self.desc_input.text().strip() if hasattr(self, 'desc_input') else ''
                    db.execute_query(
                        "INSERT INTO services (service_name, default_rate, description) VALUES (%s, %s, %s)",
                        (name, rate, desc)
                    )
                elif self.master_type == "Parts":
                    rate = self.rate_input.value()
                    cat = self.cat_input.text().strip() if hasattr(self, 'cat_input') else 'General'
                    stock = self.stock_input.value() if hasattr(self, 'stock_input') else 0
                    unit = self.unit_input.text().strip() if hasattr(self, 'unit_input') else 'Pcs'
                    db.execute_query(
                        "INSERT INTO parts (part_name, category, default_rate, stock_quantity, unit) VALUES (%s, %s, %s, %s, %s)",
                        (name, cat, rate, stock, unit)
                    )
                elif self.master_type == "AC Brands":
                    db.execute_query("INSERT INTO ac_brands (brand_name) VALUES (%s)", (name,))
                elif self.master_type == "AC Types":
                    db.execute_query("INSERT INTO ac_types (type_name) VALUES (%s)", (name,))
                elif self.master_type == "AC Tonnage":
                    db.execute_query("INSERT INTO ac_capacities (capacity_value) VALUES (%s)", (name,))
                elif self.master_type == "Star Ratings":
                    db.execute_query("INSERT INTO ac_stars (star_label) VALUES (%s)", (name,))
                elif self.master_type == "Inventory Units":
                    db.execute_query("INSERT INTO inventory_units (unit_name) VALUES (%s)", (name,))
                elif self.master_type == "Technician Statuses":
                    db.execute_query("INSERT INTO technician_statuses (status_name) VALUES (%s)", (name,))
                elif self.master_type == "Payment Modes":
                    db.execute_query("INSERT INTO payment_modes (mode_name) VALUES (%s)", (name,))

                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to add item: {str(e)}")


class EditMasterItemDialog(QDialog):
    """Enterprise modal for editing master data items"""

    def __init__(self, master_type, item_id, parent=None):
        super().__init__(parent)
        self.master_type = master_type
        self.item_id = item_id
        S = SettingsView.S
        singular = master_type[:-1] if master_type.endswith('s') else master_type
        self.setWindowTitle(f"Edit {singular}")
        self.setFixedWidth(460)
        self.setModal(True)
        self.setStyleSheet(f"background-color: {S['card']};")

        self._setup_ui()
        self._load_item()

    def _setup_ui(self):
        """Setup dialog UI"""
        S = SettingsView.S
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)

        singular = self.master_type[:-1] if self.master_type.endswith('s') else self.master_type

        # Header
        title_lbl = QLabel(f"✏️  Edit {singular}")
        title_lbl.setStyleSheet(f"font-size: 13pt; font-weight: 800; color: {S['text']}; background: transparent;")
        layout.addWidget(title_lbl)

        subtitle_lbl = QLabel(f"Update record #{self.item_id} in {self.master_type}")
        subtitle_lbl.setStyleSheet(f"font-size: 8.5pt; color: {S['muted']}; background: transparent; margin-top: -10px;")
        layout.addWidget(subtitle_lbl)

        # Form card
        form_frame = QFrame()
        form_frame.setStyleSheet(f"""
            QFrame {{
                background: {S['bg']};
                border: 1px solid {S['border']};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        form = QFormLayout(form_frame)
        form.setSpacing(12)
        form.setContentsMargins(0, 0, 0, 0)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter name...")
        self.name_input.setFixedHeight(36)
        self.name_input.setStyleSheet(f"""
            QLineEdit {{
                background: #ffffff;
                color: {S['text']};
                border: 1px solid {S['border']};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 9.5pt;
            }}
            QLineEdit:focus {{
                border: 1.5px solid {S['primary']};
            }}
        """)
        name_label = QLabel("Name *")
        name_label.setStyleSheet(f"font-weight: 600; font-size: 9pt; color: {S['text2']}; background: transparent;")
        form.addRow(name_label, self.name_input)

        self.currency_symbol = get_setting("currency_symbol", "₹")

        # Specific fields for Services
        if self.master_type == "Services":
            self.rate_input = QDoubleSpinBox()
            self.rate_input.setRange(0, 999999)
            self.rate_input.setPrefix(self.currency_symbol + " ")
            self.rate_input.setFixedHeight(36)
            self.rate_input.setStyleSheet(f"""
                QDoubleSpinBox {{
                    background: #ffffff;
                    color: {S['text']};
                    border: 1px solid {S['border']};
                    border-radius: 6px;
                    padding: 0 12px;
                    font-size: 9.5pt;
                }}
                QDoubleSpinBox:focus {{
                    border: 1.5px solid {S['primary']};
                }}
            """)
            rate_label = QLabel("Standard Rate")
            rate_label.setStyleSheet(f"font-weight: 600; font-size: 9pt; color: {S['text2']}; background: transparent;")
            form.addRow(rate_label, self.rate_input)

            self.desc_input = QLineEdit()
            self.desc_input.setPlaceholderText("e.g. Indoor & outdoor split unit servicing...")
            self.desc_input.setFixedHeight(36)
            self.desc_input.setStyleSheet(f"""
                QLineEdit {{
                    background: #ffffff;
                    color: {S['text']};
                    border: 1px solid {S['border']};
                    border-radius: 6px;
                    padding: 0 12px;
                    font-size: 9.5pt;
                }}
                QLineEdit:focus {{
                    border: 1.5px solid {S['primary']};
                }}
            """)
            desc_label = QLabel("Description")
            desc_label.setStyleSheet(f"font-weight: 600; font-size: 9pt; color: {S['text2']}; background: transparent;")
            form.addRow(desc_label, self.desc_input)

        # Specific fields for Parts
        elif self.master_type == "Parts":
            self.cat_input = QLineEdit()
            self.cat_input.setPlaceholderText("e.g. Pipes, Gas, Electrical, Motor...")
            self.cat_input.setFixedHeight(36)
            self.cat_input.setStyleSheet(f"""
                QLineEdit {{
                    background: #ffffff;
                    color: {S['text']};
                    border: 1px solid {S['border']};
                    border-radius: 6px;
                    padding: 0 12px;
                    font-size: 9.5pt;
                }}
                QLineEdit:focus {{
                    border: 1.5px solid {S['primary']};
                }}
            """)
            cat_label = QLabel("Category")
            cat_label.setStyleSheet(f"font-weight: 600; font-size: 9pt; color: {S['text2']}; background: transparent;")
            form.addRow(cat_label, self.cat_input)

            self.rate_input = QDoubleSpinBox()
            self.rate_input.setRange(0, 999999)
            self.rate_input.setPrefix(self.currency_symbol + " ")
            self.rate_input.setFixedHeight(36)
            self.rate_input.setStyleSheet(f"""
                QDoubleSpinBox {{
                    background: #ffffff;
                    color: {S['text']};
                    border: 1px solid {S['border']};
                    border-radius: 6px;
                    padding: 0 12px;
                    font-size: 9.5pt;
                }}
                QDoubleSpinBox:focus {{
                    border: 1.5px solid {S['primary']};
                }}
            """)
            rate_label = QLabel("Unit Rate")
            rate_label.setStyleSheet(f"font-weight: 600; font-size: 9pt; color: {S['text2']}; background: transparent;")
            form.addRow(rate_label, self.rate_input)

            self.stock_input = QSpinBox()
            self.stock_input.setRange(0, 99999)
            self.stock_input.setValue(0)
            self.stock_input.setFixedHeight(36)
            self.stock_input.setStyleSheet(f"""
                QSpinBox {{
                    background: #ffffff;
                    color: {S['text']};
                    border: 1px solid {S['border']};
                    border-radius: 6px;
                    padding: 0 12px;
                    font-size: 9.5pt;
                }}
                QSpinBox:focus {{
                    border: 1.5px solid {S['primary']};
                }}
            """)
            stock_label = QLabel("Stock Qty")
            stock_label.setStyleSheet(f"font-weight: 600; font-size: 9pt; color: {S['text2']}; background: transparent;")
            form.addRow(stock_label, self.stock_input)

            self.unit_input = QLineEdit()
            self.unit_input.setPlaceholderText("e.g. Pcs, Mtr, Kg, Set...")
            self.unit_input.setFixedHeight(36)
            self.unit_input.setStyleSheet(f"""
                QLineEdit {{
                    background: #ffffff;
                    color: {S['text']};
                    border: 1px solid {S['border']};
                    border-radius: 6px;
                    padding: 0 12px;
                    font-size: 9.5pt;
                }}
                QLineEdit:focus {{
                    border: 1.5px solid {S['primary']};
                }}
            """)
            unit_label = QLabel("Unit")
            unit_label.setStyleSheet(f"font-weight: 600; font-size: 9pt; color: {S['text2']}; background: transparent;")
            form.addRow(unit_label, self.unit_input)

        layout.addWidget(form_frame)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.setFixedHeight(36)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {S['text2']};
                border: 1px solid {S['border']};
                border-radius: 6px;
                padding: 0 20px;
                font-size: 9pt;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {S['hover']};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Changes")
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_btn.setFixedHeight(36)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {S['primary']};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 0 22px;
                font-size: 9pt;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: #1d4ed8;
            }}
        """)
        save_btn.clicked.connect(self._validate_and_accept)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _load_item(self):
        """Load item data"""
        from database.db_connection import DatabaseContext

        with DatabaseContext() as db:
            if self.master_type == "Services":
                item = db.execute_query(
                    "SELECT service_name, default_rate, description FROM services WHERE id = %s",
                    (self.item_id,),
                    fetch_one=True
                )
            elif self.master_type == "Parts":
                item = db.execute_query(
                    "SELECT part_name, category, default_rate, stock_quantity, unit FROM parts WHERE id = %s",
                    (self.item_id,),
                    fetch_one=True
                )
            elif self.master_type == "AC Brands":
                item = db.execute_query(
                    "SELECT brand_name FROM ac_brands WHERE id = %s",
                    (self.item_id,),
                    fetch_one=True
                )
            elif self.master_type == "AC Types":
                item = db.execute_query("SELECT type_name FROM ac_types WHERE id = %s", (self.item_id,), fetch_one=True)
            elif self.master_type == "AC Tonnage":
                item = db.execute_query("SELECT capacity_value FROM ac_capacities WHERE id = %s", (self.item_id,), fetch_one=True)
            elif self.master_type == "Star Ratings":
                item = db.execute_query("SELECT star_label FROM ac_stars WHERE id = %s", (self.item_id,), fetch_one=True)
            elif self.master_type == "Inventory Units":
                item = db.execute_query("SELECT unit_name FROM inventory_units WHERE id = %s", (self.item_id,), fetch_one=True)
            elif self.master_type == "Technician Statuses":
                item = db.execute_query("SELECT status_name FROM technician_statuses WHERE id = %s", (self.item_id,), fetch_one=True)
            elif self.master_type == "Payment Modes":
                item = db.execute_query(
                    "SELECT mode_name FROM payment_modes WHERE id = %s",
                    (self.item_id,),
                    fetch_one=True
                )
            else:
                item = None

            if item:
                self.name_input.setText(
                    item.get('service_name') or item.get('part_name') or
                    item.get('brand_name') or item.get('type_name') or
                    item.get('capacity_value') or item.get('star_label') or
                    item.get('unit_name') or item.get('status_name') or
                    item.get('mode_name', '')
                )
                if hasattr(self, 'rate_input') and item.get('default_rate') is not None:
                    self.rate_input.setValue(float(item.get('default_rate') or 0.0))
                if hasattr(self, 'desc_input') and item.get('description'):
                    self.desc_input.setText(str(item.get('description') or ''))
                if hasattr(self, 'cat_input') and item.get('category'):
                    self.cat_input.setText(str(item.get('category') or ''))
                if hasattr(self, 'stock_input') and item.get('stock_quantity') is not None:
                    self.stock_input.setValue(int(item.get('stock_quantity') or 0))
                if hasattr(self, 'unit_input') and item.get('unit'):
                    self.unit_input.setText(str(item.get('unit') or 'Pcs'))

    def _validate_and_accept(self):
        """Validate and save item"""
        name = self.name_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation Error", "Name cannot be empty.")
            return

        from database.db_connection import DatabaseContext

        with DatabaseContext() as db:
            try:
                if self.master_type == "Services":
                    rate = self.rate_input.value()
                    desc = self.desc_input.text().strip() if hasattr(self, 'desc_input') else ''
                    db.execute_query(
                        "UPDATE services SET service_name = %s, default_rate = %s, description = %s WHERE id = %s",
                        (name, rate, desc, self.item_id)
                    )
                elif self.master_type == "Parts":
                    rate = self.rate_input.value()
                    cat = self.cat_input.text().strip() if hasattr(self, 'cat_input') else 'General'
                    stock = self.stock_input.value() if hasattr(self, 'stock_input') else 0
                    unit = self.unit_input.text().strip() if hasattr(self, 'unit_input') else 'Pcs'
                    db.execute_query(
                        "UPDATE parts SET part_name = %s, category = %s, default_rate = %s, stock_quantity = %s, unit = %s WHERE id = %s",
                        (name, cat, rate, stock, unit, self.item_id)
                    )
                elif self.master_type == "AC Brands":
                    db.execute_query("UPDATE ac_brands SET brand_name = %s WHERE id = %s", (name, self.item_id))
                elif self.master_type == "AC Types":
                    db.execute_query("UPDATE ac_types SET type_name = %s WHERE id = %s", (name, self.item_id))
                elif self.master_type == "AC Tonnage":
                    db.execute_query("UPDATE ac_capacities SET capacity_value = %s WHERE id = %s", (name, self.item_id))
                elif self.master_type == "Star Ratings":
                    db.execute_query("UPDATE ac_stars SET star_label = %s WHERE id = %s", (name, self.item_id))
                elif self.master_type == "Inventory Units":
                    db.execute_query("UPDATE inventory_units SET unit_name = %s WHERE id = %s", (name, self.item_id))
                elif self.master_type == "Technician Statuses":
                    db.execute_query("UPDATE technician_statuses SET status_name = %s WHERE id = %s", (name, self.item_id))
                elif self.master_type == "Payment Modes":
                    db.execute_query("UPDATE payment_modes SET mode_name = %s WHERE id = %s", (name, self.item_id))

                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to update item: {str(e)}")
