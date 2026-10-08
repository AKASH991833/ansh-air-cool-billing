"""
Invoice View — Executive Studio Invoice Creator & Editor
Modern single-screen split-studio UX with live bill recalculation,
instant customer autofill, quick-pick item chips, inline quantity counters,
and 1-click settlement actions (Save, Print, WhatsApp).
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea,
    QComboBox, QDoubleSpinBox, QSpinBox, QTextEdit, QMessageBox, QMenu,
    QCheckBox, QGridLayout, QAbstractItemView, QListWidget, QListWidgetItem,
    QSizePolicy, QButtonGroup, QRadioButton, QStackedWidget, QScrollBar
)
from PySide6.QtCore import Qt, QDate, QTimer, QPropertyAnimation, QEasingCurve, Property, QEvent
from PySide6.QtGui import QColor, QShortcut, QKeySequence, QFont, QCursor
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import os

from utils.unified_theme import UnifiedTheme
from utils.app_settings import get_setting
from views.base_window import BaseView

CHEVRON_ICON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "icons", "chevron_down.png"
).replace("\\", "/")

ENTERPRISE_COLORS = {
    'bg': '#f8fafc',
    'card': '#ffffff',
    'card_hover': '#f1f5f9',
    'border': '#e2e8f0',
    'border_light': '#f1f5f9',
    'primary': '#2563eb',
    'primary_hover': '#1d4ed8',
    'primary_light': '#eff6ff',
    'primary_border': '#bfdbfe',
    'text': '#0f172a',
    'text_muted': '#64748b',
    'text_secondary': '#475569',
    'success': '#059669',
    'success_light': '#ecfdf5',
    'success_border': '#a7f3d0',
    'warning': '#d97706',
    'warning_light': '#fffbeb',
    'warning_border': '#fde68a',
    'danger': '#dc2626',
    'danger_light': '#fef2f2',
    'danger_border': '#fca5a5',
    'info': '#0284c7',
    'info_light': '#f0f9ff',
    'info_border': '#bae6fd',
    'divider': '#e2e8f0',
    'table_header': '#f8fafc',
    'table_stripe': '#fbfcfe',
}

_C = ENTERPRISE_COLORS
C = _C['primary']
C_HOVER = _C['primary_hover']
C_DIM = _C['primary_light']
GREEN = _C['success']
RED = _C['danger']
AMBER = _C['warning']
WHITE = _C['text']
DARK = _C['bg']
CARD = _C['card']
BORDER = _C['border']
MUTED = _C['text_muted']
SECONDARY = _C['text_secondary']


class ToastNotification(QFrame):
    def __init__(self, parent, message, type="warning"):
        super().__init__(parent)
        self.setObjectName("toast")
        colors = {
            "warning": (AMBER, f"{AMBER}18", "⚠️"),
            "error": (RED, f"{RED}18", "❌"),
            "success": (GREEN, f"{GREEN}18", "✅"),
            "info": (C, f"{C}18", "ℹ️"),
        }
        fg, bg, icon_char = colors.get(type, colors["warning"])
        self.setStyleSheet(f"""
            QFrame#toast {{
                background: #ffffff;
                border: 1.5px solid {fg};
                border-left: 6px solid {fg};
                border-radius: 8px;
                padding: 8px 14px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)
        icon = QLabel(icon_char)
        icon.setStyleSheet("font-size: 15px; background: transparent;")
        layout.addWidget(icon)
        msg = QLabel(message)
        msg.setStyleSheet(f"color: {ENTERPRISE_COLORS['text']}; font-size: 12px; font-weight: 600; background: transparent;")
        msg.setWordWrap(True)
        layout.addWidget(msg, 1)

        self.setFixedWidth(400)
        self.adjustSize()
        self.show()
        QTimer.singleShot(3500, self._fade_out)

    def _fade_out(self):
        self.deleteLater()

    def showEvent(self, event):
        super().showEvent(event)
        parent = self.parent()
        if parent:
            pw = parent.width()
            self.move(pw - self.width() - 24, 70)


class InvoiceView(BaseView):
    _next_item_id = 1

    def __init__(self):
        super().__init__()
        self.invoice_items = []
        self._customer_cache = []
        self._skip_search = False
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._do_customer_search)
        self.services_list = []
        self.parts_list = []
        self._search_items = []
        self._selected_search_item = None
        self._search_ignore_next = False
        self._recent_items = []
        self._search_arrow_idx = -1
        self._undo_item = None
        self._category_filter = 'all'
        self.ac_brands_list = []
        self.technicians_list = []
        self.customer_id = None
        self.item_search_input = None
        self.search_popup = None
        self._payment_status_manually_set = False
        self._setting_status_programmatically = False
        self._save_in_progress = False

        self._setup_ui()
        self.load_master_data()
        self._connect_event_bus()
        self._setup_shortcuts()
        self._setup_tab_order()

    def _tc(self):
        return self.theme_manager.get_colors()

    def _next_id(self):
        nid = InvoiceView._next_item_id
        InvoiceView._next_item_id += 1
        return nid

    def _connect_event_bus(self):
        try:
            from utils.event_bus import get_event_bus
            self.event_bus = get_event_bus()
            self.event_bus.master_data_updated.connect(self._on_master_data_updated)
        except Exception:
            pass

    def _on_master_data_updated(self, data_type):
        self.load_master_data()

    def _setup_shortcuts(self):
        # Keyboard productivity shortcuts
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self._save_invoice)
        QShortcut(QKeySequence("Ctrl+P"), self).activated.connect(self._save_and_print_invoice)
        QShortcut(QKeySequence("Alt+W"), self).activated.connect(self._direct_whatsapp_share)
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self._clear_form)
        QShortcut(QKeySequence("Alt+I"), self).activated.connect(lambda: self.item_search_input.setFocus())
        QShortcut(QKeySequence("Alt+C"), self).activated.connect(lambda: self.customer_name_input.setFocus())
        QShortcut(QKeySequence("Return"), self).activated.connect(self._shortcut_enter)

    def _shortcut_enter(self):
        focused = self.focusWidget()
        if focused is self.item_search_input:
            self._on_search_return()
            return
        if focused is self.item_qty_spin:
            self.item_rate_spin.setFocus()
            return
        if focused is self.item_rate_spin:
            self._add_current_item()
            return

    def _setup_tab_order(self):
        QWidget.setTabOrder(self.customer_name_input, self.customer_mobile_input)
        QWidget.setTabOrder(self.customer_mobile_input, self.customer_address_input)
        QWidget.setTabOrder(self.customer_address_input, self.customer_email_input)
        QWidget.setTabOrder(self.customer_email_input, self.customer_pincode_input)
        QWidget.setTabOrder(self.customer_pincode_input, self.ac_brand_combo)
        QWidget.setTabOrder(self.ac_brand_combo, self.ac_type_combo)
        QWidget.setTabOrder(self.ac_type_combo, self.ac_ton_combo)
        QWidget.setTabOrder(self.ac_ton_combo, self.ac_inverter_combo)
        QWidget.setTabOrder(self.ac_inverter_combo, self.ac_star_combo)
        QWidget.setTabOrder(self.ac_star_combo, self.item_search_input)
        QWidget.setTabOrder(self.item_search_input, self.advance_input)
        QWidget.setTabOrder(self.advance_input, self.technician_combo)
        QWidget.setTabOrder(self.technician_combo, self.payment_mode_combo)
        QWidget.setTabOrder(self.payment_mode_combo, self.payment_status_combo)
        QWidget.setTabOrder(self.payment_status_combo, self.notes_input)

    def show_warning_message(self, message, title="Warning"):
        parent = self.window() if self.window() else self
        ToastNotification(parent, message, "warning")

    def show_success_message(self, message, title="Success"):
        parent = self.window() if self.window() else self
        ToastNotification(parent, message, "success")

    def show_error_message(self, message, title="Error"):
        parent = self.window() if self.window() else self
        ToastNotification(parent, message, "error")

    def update_theme_colors(self):
        colors = self._tc()
        self.setStyleSheet(f"background: {colors['bg']};")
        self.theme_manager.apply_palette(self)
        if hasattr(self, 'items_table'):
            self._rebuild_table()

    # ──────────────────────────────────────────────────────────────────
    # UI SETUP — Executive 2-Column Split Studio
    # ──────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        self.currency_symbol = get_setting("currency_symbol", "₹")
        c = self._tc()
        self.setStyleSheet(f"background: {c['bg']};")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Top Header (compact) ──
        root_layout.addWidget(self._build_top_header())

        # ── Main 2-Column Studio (no horizontal scroll) ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(f"""
            QScrollArea {{ background: {c['bg']}; border: none; }}
            QScrollBar:vertical {{ background: transparent; width: 6px; }}
            QScrollBar::handle:vertical {{ background: {c['border']}; border-radius: 3px; min-height: 25px; }}
            QScrollBar::handle:vertical:hover {{ background: {c['muted']}; }}
            QScrollBar:horizontal {{ height: 0px; }}
        """)

        # Outer wrapper enforces no overflow
        outer = QWidget()
        outer.setStyleSheet(f"background: {c['bg']};")
        outer_lay = QHBoxLayout(outer)
        outer_lay.setContentsMargins(14, 10, 14, 10)
        outer_lay.setSpacing(12)

        # LEFT column — stretches to fill available space
        left_col = QVBoxLayout()
        left_col.setSpacing(10)
        left_col.addWidget(self._build_customer_ac_card())
        left_col.addWidget(self._build_item_cart_card(), 1)
        outer_lay.addLayout(left_col, 1)

        # RIGHT sidebar — fixed 300px width
        right_panel = QWidget()
        right_panel.setFixedWidth(300)
        right_panel.setStyleSheet("background: transparent;")
        right_lay = QVBoxLayout(right_panel)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(10)
        right_lay.addWidget(self._build_bill_slip_card())
        right_lay.addWidget(self._build_settlement_card())
        right_lay.addWidget(self._build_actions_card())
        right_lay.addStretch()
        outer_lay.addWidget(right_panel, 0)

        scroll.setWidget(outer)
        root_layout.addWidget(scroll, 1)

    def _build_top_header(self):
        c = self._tc()
        hdr = QFrame()
        hdr.setObjectName("invoiceStudioHeader")
        hdr.setStyleSheet(f"""
            QFrame#invoiceStudioHeader {{
                background: {c['card_bg']};
                border-bottom: 1px solid {c['border']};
            }}
        """)
        hdr.setFixedHeight(48)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(16, 0, 16, 0)
        hl.setSpacing(10)

        # Icon + Title
        icon_lbl = QLabel("🧾")
        icon_lbl.setStyleSheet(f"font-size: 14pt; background: {c['primary']}15; border-radius: 6px; padding: 2px 6px;")
        icon_lbl.setFixedSize(32, 32)
        icon_lbl.setAlignment(Qt.AlignCenter)
        hl.addWidget(icon_lbl)

        t_lbl = QLabel("New Invoice Studio")
        t_lbl.setStyleSheet(f"font-size: 11pt; font-weight: 800; color: {c['fg']}; letter-spacing: -0.2px;")
        hl.addWidget(t_lbl)

        sub_lbl = QLabel("— Fast Billing Workspace")
        sub_lbl.setStyleSheet(f"font-size: 8pt; color: {c['muted']}; font-weight: 500;")
        hl.addWidget(sub_lbl)
        hl.addStretch()

        # Date badge
        date_badge = QLabel(f"📅  {datetime.now().strftime('%d %b, %Y')}")
        date_badge.setStyleSheet(f"""
            background: {c['hover']}; color: {c['fg']};
            border: 1px solid {c['border']}; border-radius: 5px;
            padding: 4px 10px; font-size: 8.5pt; font-weight: 600;
        """)
        hl.addWidget(date_badge)

        # Reset Button
        self.btn_reset_draft = QPushButton("🔄  New / Reset")
        self.btn_reset_draft.setToolTip("Reset Draft (Ctrl+N)")
        self.btn_reset_draft.setCursor(Qt.PointingHandCursor)
        self.btn_reset_draft.setFixedHeight(30)
        self.btn_reset_draft.setStyleSheet(f"""
            QPushButton {{
                background: {c['hover']}; color: {c['muted']};
                border: 1px solid {c['border']}; border-radius: 5px;
                padding: 0 12px; font-size: 8pt; font-weight: 600;
            }}
            QPushButton:hover {{ color: {RED}; border-color: {RED}50; background: {RED}10; }}
        """)
        self.btn_reset_draft.clicked.connect(self._clear_form)
        hl.addWidget(self.btn_reset_draft)

        return hdr

    def _build_customer_ac_card(self):
        c = self._tc()
        card = QFrame()
        card.setObjectName("custAcCard")
        card.setStyleSheet(f"""
            QFrame#custAcCard {{
                background: {c['card_bg']};
                border: 1px solid {c['border']};
                border-radius: 10px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(8)

        # ─ Header ─
        hdr_row = QHBoxLayout()
        hdr_row.setSpacing(6)
        ic = QLabel("👤")
        ic.setStyleSheet("font-size: 11pt;")
        hdr_row.addWidget(ic)
        title = QLabel("Customer & AC Details")
        title.setStyleSheet(f"font-size: 10pt; font-weight: 700; color: {c['fg']};")
        hdr_row.addWidget(title)
        hdr_row.addStretch()
        self.cust_status_badge = QLabel("🔵 New Customer")
        self.cust_status_badge.setStyleSheet(f"""
            background: {c['primary']}15; color: {c['primary']};
            border: 1px solid {c['primary']}30; border-radius: 5px;
            padding: 2px 8px; font-size: 7.5pt; font-weight: 700;
        """)
        hdr_row.addWidget(self.cust_status_badge)
        layout.addLayout(hdr_row)

        # Thin divider
        div = QFrame(); div.setFrameShape(QFrame.HLine)
        div.setStyleSheet(f"background: {c['border']}; max-height: 1px;")
        layout.addWidget(div)

        # ─ Customer Fields: 2-column grid ─
        grid = QGridLayout()
        grid.setSpacing(6)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        grid.setColumnMinimumWidth(0, 70)
        grid.setColumnMinimumWidth(2, 70)

        # Row 0: Name | Mobile
        grid.addWidget(self._lbl("Full Name *"), 0, 0)
        self.customer_name_input = QLineEdit()
        self.customer_name_input.setPlaceholderText("Customer full name...")
        self.customer_name_input.setFixedHeight(30)
        self._style_input(self.customer_name_input)
        grid.addWidget(self.customer_name_input, 0, 1)

        grid.addWidget(self._lbl("Mobile *"), 0, 2)
        self.customer_mobile_input = QLineEdit()
        self.customer_mobile_input.setPlaceholderText("10-digit mobile")
        self.customer_mobile_input.setFixedHeight(30)
        self._style_input(self.customer_mobile_input)
        grid.addWidget(self.customer_mobile_input, 0, 3)

        # Row 1: Address | Email + PIN
        grid.addWidget(self._lbl("Address"), 1, 0)
        self.customer_address_input = QLineEdit()
        self.customer_address_input.setPlaceholderText("Street, Landmark...")
        self.customer_address_input.setFixedHeight(30)
        self._style_input(self.customer_address_input)
        grid.addWidget(self.customer_address_input, 1, 1)

        grid.addWidget(self._lbl("Email / PIN"), 1, 2)
        email_pin = QHBoxLayout()
        email_pin.setSpacing(4)
        self.customer_email_input = QLineEdit()
        self.customer_email_input.setPlaceholderText("Email (optional)")
        self.customer_email_input.setFixedHeight(30)
        self._style_input(self.customer_email_input)
        email_pin.addWidget(self.customer_email_input, 3)
        self.customer_pincode_input = QLineEdit()
        self.customer_pincode_input.setPlaceholderText("PIN")
        self.customer_pincode_input.setFixedHeight(30)
        self.customer_pincode_input.setMaximumWidth(65)
        self._style_input(self.customer_pincode_input)
        email_pin.addWidget(self.customer_pincode_input, 1)
        grid.addLayout(email_pin, 1, 3)

        layout.addLayout(grid)

        # Autocomplete dropdown
        self.customer_dropdown = QListWidget()
        self.customer_dropdown.setMaximumHeight(120)
        self.customer_dropdown.setStyleSheet(f"""
            QListWidget {{
                background: {c['card_bg']}; border: 1.5px solid {c['primary']};
                border-radius: 7px; padding: 3px; color: {c['fg']}; font-size: 8.5pt;
            }}
            QListWidget::item {{ padding: 5px 8px; border-radius: 4px; }}
            QListWidget::item:hover {{ background: {c['primary']}20; color: {c['primary']}; }}
            QListWidget::item:selected {{ background: {c['primary']}; color: #ffffff; }}
        """)
        self.customer_dropdown.hide()
        self.customer_dropdown.itemClicked.connect(self._on_customer_selected)
        layout.addWidget(self.customer_dropdown)

        self.customer_name_input.textChanged.connect(self._on_customer_search_text)
        self.customer_mobile_input.textChanged.connect(self._on_customer_search_text)

        # ─ AC Unit Strip (grid layout, not horizontal overflow) ─
        shop_type = get_setting('shop_type', 'AC Service')
        ac_strip = QFrame()
        ac_strip.setStyleSheet(f"""
            QFrame {{
                background: {c['hover']};
                border: 1px solid {c['border']};
                border-radius: 7px;
            }}
        """)
        ac_outer = QHBoxLayout(ac_strip)
        ac_outer.setContentsMargins(10, 5, 10, 5)
        ac_outer.setSpacing(6)

        ac_title = QLabel("❄️ AC:")
        ac_title.setStyleSheet(f"font-weight: 700; color: {c['fg']}; font-size: 8.5pt;")
        ac_title.setFixedWidth(30)
        ac_outer.addWidget(ac_title)

        self.ac_brand_combo = QComboBox()
        self.ac_brand_combo.addItem("Brand", "")
        self.ac_brand_combo.setFixedHeight(26)
        self._style_combo(self.ac_brand_combo)
        ac_outer.addWidget(self.ac_brand_combo, 2)

        self.ac_ton_combo = QComboBox()
        self.ac_ton_combo.addItems(get_setting('ac_ton_capacities', '1.0,1.5,2.0,3.0,Other').split(','))
        self.ac_ton_combo.setFixedHeight(26)
        self._style_combo(self.ac_ton_combo)
        ac_outer.addWidget(self.ac_ton_combo, 1)

        self.ac_type_combo = QComboBox()
        self.ac_type_combo.addItems(get_setting('ac_types', 'Split,Window,Cassette,Tower,Other').split(','))
        self.ac_type_combo.setFixedHeight(26)
        self._style_combo(self.ac_type_combo)
        ac_outer.addWidget(self.ac_type_combo, 1)

        self.ac_inverter_combo = QComboBox()
        self.ac_inverter_combo.addItems(get_setting('ac_inverter_options', 'No,Yes').split(','))
        self.ac_inverter_combo.setFixedHeight(26)
        self._style_combo(self.ac_inverter_combo)
        ac_outer.addWidget(self.ac_inverter_combo, 1)

        self.ac_star_combo = QComboBox()
        self.ac_star_combo.addItems(get_setting('star_ratings', 'N/A,1,2,3,4,5').split(','))
        self.ac_star_combo.setFixedHeight(26)
        self._style_combo(self.ac_star_combo)
        ac_outer.addWidget(self.ac_star_combo, 1)

        layout.addWidget(ac_strip)
        ac_strip.setVisible(shop_type == 'AC Service')

        return card

    # ──────────────────────────────────────────────────────────────────
    # SECTION B: SERVICE & SPARE PARTS CART
    # ──────────────────────────────────────────────────────────────────
    def _build_item_cart_card(self):
        c = self._tc()
        card = QFrame()
        card.setObjectName("itemCartCard")
        card.setStyleSheet(f"""
            QFrame#itemCartCard {{
                background: {c['card_bg']};
                border: 1px solid {c['border']};
                border-radius: 10px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(8)

        # Header Row
        hdr_row = QHBoxLayout()
        hdr_row.setSpacing(6)
        ic = QLabel("🛠️")
        ic.setStyleSheet("font-size: 11pt;")
        hdr_row.addWidget(ic)
        title = QLabel("Billable Services & Spare Parts")
        title.setStyleSheet(f"font-size: 10pt; font-weight: 700; color: {c['fg']};")
        hdr_row.addWidget(title)
        hdr_row.addStretch()
        self.item_total_label = QLabel("0 Items  |  ₹ 0.00")
        self.item_total_label.setStyleSheet(f"""
            background: {c['primary']}15; color: {c['primary']};
            border: 1px solid {c['primary']}30; border-radius: 12px;
            padding: 3px 10px; font-size: 8pt; font-weight: 700;
        """)
        hdr_row.addWidget(self.item_total_label)
        layout.addLayout(hdr_row)

        div = QFrame(); div.setFrameShape(QFrame.HLine)
        div.setStyleSheet(f"background: {c['border']}; max-height: 1px;")
        layout.addWidget(div)

        # ─ Search + Add Row ─
        search_row = QHBoxLayout()
        search_row.setSpacing(6)

        self.item_category_combo = QComboBox()
        self.item_category_combo.addItems(["All Items", "Services", "Parts"])
        self.item_category_combo.setFixedWidth(90)
        self.item_category_combo.setFixedHeight(32)
        self._style_combo(self.item_category_combo)
        self.item_category_combo.currentTextChanged.connect(
            lambda: self._on_search_text_changed(self.item_search_input.text()))
        search_row.addWidget(self.item_category_combo)

        self.item_search_input = QLineEdit()
        self.item_search_input.setPlaceholderText("🔍  Search service or part (Alt+I)...")
        self.item_search_input.setFixedHeight(32)
        self.item_search_input.setStyleSheet(f"""
            QLineEdit {{
                background: #ffffff; color: {c['fg']};
                border: 1px solid {c['border']}; border-radius: 6px;
                padding: 0 10px; font-size: 9pt;
            }}
            QLineEdit:focus {{ border: 1.5px solid {c['primary']}; }}
        """)
        self.item_search_input.textChanged.connect(self._on_search_text_changed)
        self.item_search_input.returnPressed.connect(self._on_search_return)
        self.item_search_input.installEventFilter(self)
        search_row.addWidget(self.item_search_input, 1)

        # Qty
        qty_lbl = QLabel("Qty:")
        qty_lbl.setStyleSheet(f"font-size: 8pt; font-weight: 600; color: {c['muted']};")
        search_row.addWidget(qty_lbl)
        self.item_qty_spin = QSpinBox()
        self.item_qty_spin.setRange(1, 9999)
        self.item_qty_spin.setValue(1)
        self.item_qty_spin.setFixedWidth(50)
        self.item_qty_spin.setFixedHeight(32)
        self.item_qty_spin.setAlignment(Qt.AlignCenter)
        self._style_spin(self.item_qty_spin)
        search_row.addWidget(self.item_qty_spin)

        # Rate
        rate_lbl = QLabel("Rate:")
        rate_lbl.setStyleSheet(f"font-size: 8pt; font-weight: 600; color: {c['muted']};")
        search_row.addWidget(rate_lbl)
        self.item_rate_spin = QDoubleSpinBox()
        self.item_rate_spin.setRange(0, 999999)
        self.item_rate_spin.setPrefix(self.currency_symbol + " ")
        self.item_rate_spin.setDecimals(2)
        self.item_rate_spin.setFixedWidth(95)
        self.item_rate_spin.setFixedHeight(32)
        self._style_spin(self.item_rate_spin)
        search_row.addWidget(self.item_rate_spin)

        # Add button
        self.btn_add_item = QPushButton("+ Add")
        self.btn_add_item.setCursor(Qt.PointingHandCursor)
        self.btn_add_item.setFixedHeight(32)
        self.btn_add_item.setFixedWidth(60)
        self.btn_add_item.setStyleSheet(f"""
            QPushButton {{
                background: {c['primary']}; color: #ffffff;
                border: none; border-radius: 6px;
                font-size: 9pt; font-weight: 700;
            }}
            QPushButton:hover {{ background: {c['primary_hover']}; }}
        """)
        self.btn_add_item.clicked.connect(self._add_current_item)
        search_row.addWidget(self.btn_add_item)

        layout.addWidget(self._wrap(search_row))

        # Hidden legacy label
        self.selected_item_label = QLabel("—")
        self.selected_item_label.hide()
        layout.addWidget(self.selected_item_label)

        # Search popup
        self.search_popup = QListWidget()
        self.search_popup.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.search_popup.setFocusPolicy(Qt.NoFocus)
        self.search_popup.setStyleSheet(f"""
            QListWidget {{
                background: #ffffff; border: 1.5px solid {c['primary']};
                border-radius: 7px; padding: 3px; font-size: 9pt; color: {c['fg']};
            }}
            QListWidget::item {{ padding: 7px 10px; border-radius: 4px; }}
            QListWidget::item:hover {{ background: {c['primary']}15; color: {c['primary']}; }}
            QListWidget::item:selected {{ background: {c['primary']}; color: #ffffff; }}
        """)
        self.search_popup.itemClicked.connect(self._on_search_item_clicked)
        self.search_popup.installEventFilter(self)
        self.search_popup.hide()

        # ─ Quick Pick chips (scrollable horizontal) ─
        chips_scroll = QScrollArea()
        chips_scroll.setFixedHeight(38)
        chips_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        chips_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        chips_scroll.setFrameShape(QFrame.NoFrame)
        chips_scroll.setStyleSheet("background: transparent;")

        chips_w = QWidget()
        chips_w.setStyleSheet("background: transparent;")
        chips_lay = QHBoxLayout(chips_w)
        chips_lay.setContentsMargins(0, 0, 0, 0)
        chips_lay.setSpacing(5)

        lbl_quick = QLabel("⚡ Quick:")
        lbl_quick.setStyleSheet(f"font-weight: 700; color: {c['primary']}; font-size: 8pt;")
        chips_lay.addWidget(lbl_quick)

        quick_picks = [
            ("🛁 Jet Service", "Jet Pump Service", 599.0, "service"),
            ("❄️ Gas R32", "Gas Refilling R32", 2500.0, "part"),
            ("❄️ Gas R410A", "Gas Refilling R410A", 2800.0, "part"),
            ("⚡ Capacitor", "Capacitor 45uF", 450.0, "part"),
            ("🛠️ Install", "AC Installation Split", 1200.0, "service"),
            ("🔧 Uninstall", "AC Uninstallation", 600.0, "service"),
            ("💡 PCB Repair", "PCB Board Repair", 1500.0, "service"),
            ("⚙️ Fan Motor", "AC Fan Motor", 1800.0, "part"),
        ]
        for icon_lbl, item_name, rate, it_type in quick_picks:
            btn = QPushButton(f"{icon_lbl} ₹{rate:,.0f}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(26)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {c['hover']}; color: {c['fg']};
                    border: 1px solid {c['border']}; border-radius: 10px;
                    padding: 0 8px; font-size: 7.5pt; font-weight: 600;
                }}
                QPushButton:hover {{ background: {c['primary']}; color: #ffffff; border-color: {c['primary']}; }}
            """)
            btn.clicked.connect(lambda ch, n=item_name, r=rate, t=it_type: self._on_quick_chip_clicked(n, r, t))
            chips_lay.addWidget(btn)
        chips_lay.addStretch()
        chips_scroll.setWidget(chips_w)
        layout.addWidget(chips_scroll)

        # ─ Items Table ─
        self.items_table = self._build_items_table()

        self.items_empty_label = QLabel("📦  Cart empty — search above or tap Quick Pick to add items")
        self.items_empty_label.setAlignment(Qt.AlignCenter)
        self.items_empty_label.setStyleSheet(f"""
            background: {c['hover']}; color: {c['muted']};
        """)
        self.items_empty_label.setMinimumHeight(140)

        self.items_table_stack = QStackedWidget()
        self.items_table_stack.addWidget(self.items_table)
        self.items_table_stack.addWidget(self.items_empty_label)
        self.items_table_stack.setCurrentIndex(1)
        layout.addWidget(self.items_table_stack, 1)

        return card

    def _build_items_table(self):
        c = self._tc()
        table = QTableWidget()
        headers = ['#', 'Type', 'Item Description', 'Quantity', 'Rate', 'Amount', 'Action']
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setShowGrid(False)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setMinimumHeight(180)
        table.setStyleSheet(f"""
            QTableWidget {{
                background: #ffffff;
                border: 1px solid {c['border']};
                border-radius: 8px;
                gridline-color: transparent;
            }}
            QHeaderView::section {{
                background: {c['hover']};
                color: {c['muted']};
                padding: 9px 8px;
                border: none;
                border-bottom: 1.5px solid {c['border']};
                font-weight: 700;
                font-size: 8pt;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            QTableWidget::item {{
                padding: 6px 10px;
                color: {c['fg']};
                border-bottom: 1px solid {c['border_light']};
                font-size: 9pt;
            }}
            QTableWidget::item:selected {{
                background: {c['primary']}15;
                color: {c['fg']};
            }}
        """)
        h = table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.Interactive)
        table.setColumnWidth(0, 36)
        table.setColumnWidth(1, 80)
        table.setColumnWidth(3, 110)
        table.setColumnWidth(4, 90)
        table.setColumnWidth(5, 100)
        table.setColumnWidth(6, 60)
        h.setSectionResizeMode(2, QHeaderView.Stretch)
        return table

    # ──────────────────────────────────────────────────────────────────
    # SECTION C: RIGHT RAIL — LIVE BILL SLIP & SUMMARY
    # ──────────────────────────────────────────────────────────────────
    def _build_bill_slip_card(self):
        c = self._tc()
        card = QFrame()
        card.setObjectName("billSlipCard")
        card.setStyleSheet(f"""
            QFrame#billSlipCard {{
                background: {c['card_bg']};
                border: 1px solid {c['border']};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # Header
        hdr = QHBoxLayout()
        ic = QLabel("🧾")
        ic.setStyleSheet("font-size: 12pt;")
        hdr.addWidget(ic)
        t = QLabel("Bill Slip & Taxation")
        t.setStyleSheet(f"font-size: 10pt; font-weight: 700; color: {c['fg']};")
        hdr.addWidget(t)
        hdr.addStretch()
        layout.addLayout(hdr)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet(f"background: {c['border']}; max-height: 1px;")
        layout.addWidget(div)

        # Subtotal Row
        sub_h = QHBoxLayout()
        sub_lbl = QLabel("Subtotal")
        sub_lbl.setStyleSheet(f"font-size: 9pt; font-weight: 600; color: {c['muted']};")
        sub_h.addWidget(sub_lbl)
        sub_h.addStretch()
        self.subtotal_label = QLabel(f"{self.currency_symbol} 0.00")
        self.subtotal_label.setStyleSheet(f"font-size: 11pt; font-weight: 700; color: {c['fg']};")
        sub_h.addWidget(self.subtotal_label)
        layout.addLayout(sub_h)

        # ── GST Hub ──
        gst_frame = QFrame()
        gst_frame.setStyleSheet(f"""
            QFrame {{
                background: {c['hover']}; border: 1px solid {c['border']};
                border-radius: 8px; padding: 6px;
            }}
        """)
        gst_l = QVBoxLayout(gst_frame)
        gst_l.setContentsMargins(8, 6, 8, 6)
        gst_l.setSpacing(6)

        gst_top = QHBoxLayout()
        self.gst_checkbox = QCheckBox("Apply GST (Tax Invoice)")
        self.gst_checkbox.setStyleSheet(f"""
            QCheckBox {{ font-weight: 700; color: {c['fg']}; font-size: 8.5pt; }}
            QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 4px; border: 1px solid {c['border']}; }}
            QCheckBox::indicator:checked {{ background: {c['primary']}; border-color: {c['primary']}; }}
        """)
        self.gst_checkbox.stateChanged.connect(self._calculate_totals)
        gst_top.addWidget(self.gst_checkbox)
        gst_top.addStretch()

        self.gst_amount_label = QLabel(f"+ {self.currency_symbol}0.00")
        self.gst_amount_label.setStyleSheet(f"font-size: 9.5pt; font-weight: 700; color: {c['primary']};")
        gst_top.addWidget(self.gst_amount_label)
        gst_l.addLayout(gst_top)

        # GST Rate Selector
        self.gst_rate_combo = QComboBox()
        self.gst_rate_combo.addItems(["5%", "12%", "18%", "28%"])
        self.gst_rate_combo.setCurrentIndex(2)  # Default 18%
        self.gst_rate_combo.setEnabled(False)
        self.gst_rate_combo.currentIndexChanged.connect(self._calculate_totals)
        self._style_combo(self.gst_rate_combo)
        gst_l.addWidget(self.gst_rate_combo)

        layout.addWidget(gst_frame)

        # ── Discount Hub ──
        disc_frame = QFrame()
        disc_frame.setStyleSheet(f"""
            QFrame {{
                background: {c['hover']}; border: 1px solid {c['border']};
                border-radius: 8px; padding: 6px;
            }}
        """)
        disc_l = QVBoxLayout(disc_frame)
        disc_l.setContentsMargins(8, 6, 8, 6)
        disc_l.setSpacing(6)

        disc_top = QHBoxLayout()
        self.disc_checkbox = QCheckBox("Discount")
        self.disc_checkbox.setStyleSheet(f"""
            QCheckBox {{ font-weight: 700; color: {AMBER}; font-size: 8.5pt; }}
            QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 4px; border: 1px solid {c['border']}; }}
            QCheckBox::indicator:checked {{ background: {AMBER}; border-color: {AMBER}; }}
        """)
        self.disc_checkbox.stateChanged.connect(self._calculate_totals)
        disc_top.addWidget(self.disc_checkbox)
        disc_top.addStretch()

        self.disc_amount_label = QLabel(f"- {self.currency_symbol}0.00")
        self.disc_amount_label.setStyleSheet(f"font-size: 9.5pt; font-weight: 700; color: {AMBER};")
        disc_top.addWidget(self.disc_amount_label)
        disc_l.addLayout(disc_top)

        disc_inputs = QHBoxLayout()
        disc_inputs.setSpacing(6)

        self.disc_type_combo = QComboBox()
        self.disc_type_combo.addItems(["%", self.currency_symbol])
        self.disc_type_combo.setEnabled(False)
        self.disc_type_combo.setFixedWidth(55)
        self.disc_type_combo.currentIndexChanged.connect(self._calculate_totals)
        self._style_combo(self.disc_type_combo)
        disc_inputs.addWidget(self.disc_type_combo)

        self.disc_value_spin = QDoubleSpinBox()
        self.disc_value_spin.setRange(0, 999999)
        self.disc_value_spin.setDecimals(2)
        self.disc_value_spin.setEnabled(False)
        self.disc_value_spin.valueChanged.connect(self._calculate_totals)
        self._style_spin(self.disc_value_spin)
        disc_inputs.addWidget(self.disc_value_spin, 1)

        disc_l.addLayout(disc_inputs)
        layout.addWidget(disc_frame)

        # ── Grand Total Banner ──
        total_banner = QFrame()
        total_banner.setObjectName("grandTotalBanner")
        total_banner.setStyleSheet(f"""
            QFrame#grandTotalBanner {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c['primary']}, stop:1 #1d4ed8);
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        tb_lay = QVBoxLayout(total_banner)
        tb_lay.setContentsMargins(14, 10, 14, 10)
        tb_lay.setSpacing(2)

        tb_lbl = QLabel("TOTAL PAYABLE (NET)")
        tb_lbl.setStyleSheet("font-size: 8pt; font-weight: 700; color: #ffffff; letter-spacing: 0.8px;")
        tb_lay.addWidget(tb_lbl)

        self.total_amount_label = QLabel(f"{self.currency_symbol} 0")
        self.total_amount_label.setStyleSheet("font-size: 22pt; font-weight: 800; color: #ffffff;")
        tb_lay.addWidget(self.total_amount_label)

        layout.addWidget(total_banner)

        return card

    # ──────────────────────────────────────────────────────────────────
    # SECTION D: PAYMENT & SETTLEMENT
    # ──────────────────────────────────────────────────────────────────
    def _build_settlement_card(self):
        c = self._tc()
        card = QFrame()
        card.setObjectName("settlementCard")
        card.setStyleSheet(f"""
            QFrame#settlementCard {{
                background: {c['card_bg']};
                border: 1px solid {c['border']};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # Header
        hdr = QHBoxLayout()
        ic = QLabel("💳")
        ic.setStyleSheet("font-size: 12pt;")
        hdr.addWidget(ic)
        t = QLabel("Payment & Settlement")
        t.setStyleSheet(f"font-size: 10pt; font-weight: 700; color: {c['fg']};")
        hdr.addWidget(t)
        hdr.addStretch()
        layout.addLayout(hdr)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet(f"background: {c['border']}; max-height: 1px;")
        layout.addWidget(div)

        # Advance & Balance Dual Cards
        dual_h = QHBoxLayout()
        dual_h.setSpacing(8)

        # Advance box
        adv_box = QFrame()
        adv_box.setStyleSheet(f"""
            QFrame {{
                background: {c['hover']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 6px 10px;
            }}
        """)
        abl = QVBoxLayout(adv_box)
        abl.setContentsMargins(0, 0, 0, 0)
        abl.setSpacing(2)
        al = QLabel("💵 Advance Paid")
        al.setStyleSheet(f"font-size: 7.5pt; font-weight: 700; color: {GREEN}; text-transform: uppercase;")
        abl.addWidget(al)
        self.advance_input = QDoubleSpinBox()
        self.advance_input.setRange(0, 999999)
        self.advance_input.setPrefix(self.currency_symbol + " ")
        self.advance_input.setDecimals(2)
        self.advance_input.setFixedHeight(28)
        self.advance_input.setStyleSheet(f"""
            QDoubleSpinBox {{
                background: transparent; color: {GREEN}; border: none;
                font-size: 12pt; font-weight: 800;
            }}
        """)
        self.advance_input.valueChanged.connect(self._calculate_balance)
        abl.addWidget(self.advance_input)
        dual_h.addWidget(adv_box, 1)

        # Balance box
        bal_box = QFrame()
        bal_box.setStyleSheet(f"""
            QFrame {{
                background: {c['hover']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 6px 10px;
            }}
        """)
        bbl = QVBoxLayout(bal_box)
        bbl.setContentsMargins(0, 0, 0, 0)
        bbl.setSpacing(2)
        bl = QLabel("⚖️ Balance Due")
        bl.setStyleSheet(f"font-size: 7.5pt; font-weight: 700; color: {RED}; text-transform: uppercase;")
        bbl.addWidget(bl)
        self.balance_label = QLabel(f"{self.currency_symbol} 0.00")
        self.balance_label.setStyleSheet(f"font-size: 12pt; font-weight: 800; color: {RED};")
        bbl.addWidget(self.balance_label)
        dual_h.addWidget(bal_box, 1)

        layout.addLayout(dual_h)

        # Fields: Technician & Payment Mode & Status
        grid = QGridLayout()
        grid.setSpacing(8)

        grid.addWidget(self._create_field_header("Technician"), 0, 0)
        self.technician_combo = QComboBox()
        self.technician_combo.addItem("-- Select Technician --", "")
        self._style_combo(self.technician_combo)
        grid.addWidget(self.technician_combo, 0, 1)

        grid.addWidget(self._create_field_header("Mode"), 1, 0)
        self.payment_mode_combo = QComboBox()
        self._style_combo(self.payment_mode_combo)
        grid.addWidget(self.payment_mode_combo, 1, 1)

        grid.addWidget(self._create_field_header("Status"), 2, 0)
        self.payment_status_combo = QComboBox()
        self.payment_status_combo.addItems(["Paid", "Partial", "Pending"])
        self._style_combo(self.payment_status_combo)
        self.payment_status_combo.currentTextChanged.connect(self._on_payment_status_changed)
        grid.addWidget(self.payment_status_combo, 2, 1)

        layout.addLayout(grid)

        # Notes
        layout.addWidget(self._create_field_header("Warranty & Job Remarks:"))
        self.notes_input = QTextEdit()
        self.notes_input.setText("All Work Done")
        self.notes_input.setFixedHeight(45)
        self._style_input(self.notes_input)
        layout.addWidget(self.notes_input)

        # Preset Notes Chips
        chips_h = QHBoxLayout()
        chips_h.setSpacing(4)
        preset_notes = ["30 Days Warranty", "All Tested OK", "Gas Leak Fixed"]
        for pnote in preset_notes:
            pbtn = QPushButton(f"+ {pnote}")
            pbtn.setCursor(Qt.PointingHandCursor)
            pbtn.setStyleSheet(f"""
                QPushButton {{
                    background: {c['hover']}; color: {c['muted']};
                    border: 1px solid {c['border']}; border-radius: 10px;
                    padding: 2px 8px; font-size: 7.5pt; font-weight: 600;
                }}
                QPushButton:hover {{
                    color: {c['primary']}; border-color: {c['primary']};
                }}
            """)
            pbtn.clicked.connect(lambda ch, note=pnote: self._append_note(note))
            chips_h.addWidget(pbtn)
        chips_h.addStretch()
        layout.addLayout(chips_h)

        return card

    def _append_note(self, note):
        cur = self.notes_input.toPlainText().strip()
        if not cur or cur == "All Work Done":
            self.notes_input.setText(note)
        else:
            self.notes_input.setText(f"{cur} | {note}")

    # ──────────────────────────────────────────────────────────────────
    # SECTION E: ACTION BUTTONS (SAVE / PRINT / WHATSAPP)
    # ──────────────────────────────────────────────────────────────────
    def _build_actions_card(self):
        c = self._tc()
        card = QFrame()
        card.setObjectName("actionsCard")
        card.setStyleSheet(f"""
            QFrame#actionsCard {{
                background: {c['card_bg']};
                border: 1px solid {c['border']};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # Save & Print (Primary Action)
        self.save_print_btn = QPushButton("🖨️  Save & Print Invoice")
        self.save_print_btn.setToolTip("Save and Print Invoice (Ctrl+P)")
        self.save_print_btn.setCursor(Qt.PointingHandCursor)
        self.save_print_btn.setFixedHeight(40)
        self.save_print_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {GREEN}, stop:1 #047857);
                color: #ffffff; border: none; border-radius: 8px;
                font-size: 9.5pt; font-weight: 700; letter-spacing: 0.2px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 {GREEN});
            }}
        """)
        self.save_print_btn.clicked.connect(self._save_and_print_invoice)
        layout.addWidget(self.save_print_btn)

        # Save Button
        self.save_invoice_btn = QPushButton("💾  Save Draft")
        self.save_invoice_btn.setToolTip("Save Invoice Draft (Ctrl+S)")
        self.save_invoice_btn.setCursor(Qt.PointingHandCursor)
        self.save_invoice_btn.setFixedHeight(36)
        self.save_invoice_btn.setStyleSheet(f"""
            QPushButton {{
                background: {c['primary']}; color: #ffffff;
                border: none; border-radius: 8px;
                font-size: 9pt; font-weight: 700;
            }}
            QPushButton:hover {{ background: {c['primary_hover']}; }}
        """)
        self.save_invoice_btn.clicked.connect(self._save_invoice)
        layout.addWidget(self.save_invoice_btn)

        # WhatsApp Direct Share
        self.wa_direct_btn = QPushButton("⚡  WhatsApp PDF")
        self.wa_direct_btn.setToolTip("Direct WhatsApp PDF Share (Alt+W)")
        self.wa_direct_btn.setCursor(Qt.PointingHandCursor)
        self.wa_direct_btn.setFixedHeight(36)
        self.wa_direct_btn.setStyleSheet(f"""
            QPushButton {{
                background: #25D366; color: #ffffff;
                border: none; border-radius: 8px;
                font-size: 9pt; font-weight: 700;
            }}
            QPushButton:hover {{ background: #1ebd5a; }}
        """)
        self.wa_direct_btn.clicked.connect(self._direct_whatsapp_share)
        layout.addWidget(self.wa_direct_btn)

        # Corporate PDF Preview
        self.preview_btn = QPushButton("👁️  Preview PDF")
        self.preview_btn.setToolTip("Preview Corporate PDF")
        self.preview_btn.setCursor(Qt.PointingHandCursor)
        self.preview_btn.setFixedHeight(32)
        self.preview_btn.setStyleSheet(f"""
            QPushButton {{
                background: {c['hover']}; color: {c['fg']};
                border: 1px solid {c['border']}; border-radius: 8px;
                font-size: 8.5pt; font-weight: 600;
            }}
            QPushButton:hover {{ border-color: {c['primary']}; color: {c['primary']}; }}
        """)
        self.preview_btn.clicked.connect(self._preview_invoice_pdf)
        layout.addWidget(self.preview_btn)

        return card

    # ──────────────────────────────────────────────────────────────────
    # STYLING HELPERS
    # ──────────────────────────────────────────────────────────────────
    def _create_field_header(self, text):
        c = self._tc()
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-weight: 600; color: {c['muted']}; font-size: 8.5pt;")
        return lbl

    def _lbl(self, text):
        """Compact label alias used in grid layouts."""
        c = self._tc()
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-weight: 600; color: {c['muted']}; font-size: 8pt;")
        return lbl

    def _wrap(self, layout):
        """Wrap a QLayout in a transparent QWidget."""
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        w.setLayout(layout)
        return w

    def _style_input(self, widget):
        c = self._tc()
        widget.setStyleSheet(f"""
            QLineEdit, QTextEdit {{
                background: #ffffff; color: {c['fg']};
                border: 1px solid {c['border']}; border-radius: 6px;
                padding: 6px 10px; font-size: 9pt;
            }}
            QLineEdit:focus, QTextEdit:focus {{ border: 1.5px solid {c['primary']}; }}
            QLineEdit::placeholder, QTextEdit::placeholder {{ color: {c['muted']}; }}
        """)

    def _style_combo(self, combo):
        c = self._tc()
        combo.setStyleSheet(f"""
            QComboBox {{
                background: #ffffff; color: {c['fg']};
                border: 1px solid {c['border']}; border-radius: 6px;
                padding: 5px 8px; font-size: 9pt; min-height: 22px;
            }}
            QComboBox:focus {{ border: 1.5px solid {c['primary']}; }}
            QComboBox::drop-down {{
                subcontrol-origin: padding; subcontrol-position: right center;
                width: 20px; border-left: 1px solid {c['border']};
            }}
            QComboBox::down-arrow {{
                image: url("{CHEVRON_ICON_PATH}"); width: 10px; height: 10px;
            }}
            QComboBox QAbstractItemView {{
                background: #ffffff; color: {c['fg']};
                selection-background-color: {c['primary']}15;
                selection-color: {c['primary']};
                border: 1px solid {c['border']}; border-radius: 6px;
            }}
        """)

    def _style_spin(self, spin):
        c = self._tc()
        spin.setStyleSheet(f"""
            QSpinBox, QDoubleSpinBox {{
                background: #ffffff; color: {c['fg']};
                border: 1px solid {c['border']}; border-radius: 6px;
                padding: 4px 6px; font-size: 9pt; min-height: 22px;
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{ border: 1.5px solid {c['primary']}; }}
        """)

    # ──────────────────────────────────────────────────────────────────
    # ITEM ADDITION & TABLE MANAGEMENT
    # ──────────────────────────────────────────────────────────────────
    def _add_current_item(self):
        if self._selected_search_item:
            data = self._selected_search_item
            qty = self.item_qty_spin.value()
            rate = float(self.item_rate_spin.value())
            amount = float(Decimal(str(qty)) * Decimal(str(rate)))
            name = data['name']
            unit = data.get('unit', 'pcs')
            self._add_item_to_table(self.items_table, data['type'], data['id'], name, qty, unit, rate, amount)
            self._clear_item_search()
            return

        name = self.item_search_input.text().strip()
        if name:
            qty = self.item_qty_spin.value()
            rate = float(self.item_rate_spin.value())
            amount = float(Decimal(str(qty)) * Decimal(str(rate)))
            cat = self.item_category_combo.currentText()
            item_type = 'part' if cat == 'Parts' else 'service'
            self._add_item_to_table(self.items_table, item_type, None, name, qty, 'pcs', rate, amount)
            self._clear_item_search()
        else:
            self.show_warning_message("Type an item name or pick from Quick Pick chips first")

    def _on_quick_chip_clicked(self, name, rate, it_type):
        """1-click instant addition or auto-increment in cart"""
        for it in self.invoice_items:
            if it['name'].lower() == name.lower():
                it['qty'] += 1
                it['amount'] = float(Decimal(str(it['qty'])) * Decimal(str(it['rate'])))
                self._rebuild_table()
                self._calculate_totals()
                self._update_item_total()
                self.show_success_message(f"Increased quantity of '{name}' to {it['qty']}")
                return

        amount = float(Decimal('1') * Decimal(str(rate)))
        self._add_item_to_table(self.items_table, it_type, None, name, 1, 'pcs', rate, amount)
        self.show_success_message(f"Added '{name}' to bill")

    def _add_item_to_table(self, table, item_type, item_id, name, qty, unit, rate, amount):
        uid = self._next_id()
        data = {
            'uid': uid, 'type': item_type, 'item_id': item_id,
            'name': name, 'qty': qty, 'unit': unit, 'rate': rate, 'amount': amount
        }
        self.invoice_items.append(data)
        self._rebuild_table()
        self._calculate_totals()
        self._update_item_total()

    def _rebuild_table(self):
        self.items_table.blockSignals(True)
        self.items_table.setRowCount(0)
        c = self._tc()

        for row, data in enumerate(self.invoice_items):
            self.items_table.insertRow(row)

            # 0: S.No
            n0 = QTableWidgetItem(str(row + 1))
            n0.setTextAlignment(Qt.AlignCenter)
            n0.setFlags(n0.flags() & ~Qt.ItemIsEditable)
            self.items_table.setItem(row, 0, n0)

            # 1: Type Pill
            is_svc = data['type'] == 'service'
            type_text = "SVC" if is_svc else "PART"
            type_item = QTableWidgetItem(type_text)
            type_item.setTextAlignment(Qt.AlignCenter)
            type_item.setFont(QFont("Segoe UI", 8, QFont.Bold))
            type_item.setForeground(QColor(c['primary'] if is_svc else '#7c3aed'))
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.items_table.setItem(row, 1, type_item)

            # 2: Name
            name_item = QTableWidgetItem(data['name'])
            name_item.setFont(QFont("Segoe UI", 9, QFont.DemiBold))
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.items_table.setItem(row, 2, name_item)

            # 3: Interactive Inline Qty Widget
            qty_widget = self._make_inline_qty_widget(data['uid'], data['qty'])
            self.items_table.setCellWidget(row, 3, qty_widget)

            # 4: Rate
            rate_item = QTableWidgetItem(f"{self.currency_symbol}{data['rate']:,.2f}")
            rate_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            rate_item.setFlags(rate_item.flags() & ~Qt.ItemIsEditable)
            self.items_table.setItem(row, 4, rate_item)

            # 5: Amount
            amt_item = QTableWidgetItem(f"{self.currency_symbol}{data['amount']:,.2f}")
            amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            amt_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            amt_item.setForeground(QColor(c['fg']))
            amt_item.setFlags(amt_item.flags() & ~Qt.ItemIsEditable)
            self.items_table.setItem(row, 5, amt_item)

            # 6: Remove Action
            btn_del = QPushButton("🗑️")
            btn_del.setFixedSize(28, 28)
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; border: none; border-radius: 4px; font-size: 11pt;
                }}
                QPushButton:hover {{ background: {RED}18; color: {RED}; }}
            """)
            btn_del.clicked.connect(lambda ch, u=data['uid']: self._delete_item(u, ask=False))
            del_w = QWidget()
            del_lay = QHBoxLayout(del_w)
            del_lay.setContentsMargins(0, 0, 0, 0)
            del_lay.setAlignment(Qt.AlignCenter)
            del_lay.addWidget(btn_del)
            self.items_table.setCellWidget(row, 6, del_w)

            self.items_table.setRowHeight(row, 36)

        self.items_table.blockSignals(False)

        # Toggle empty state vs table
        if self.invoice_items:
            self.items_table_stack.setCurrentIndex(0)
        else:
            self.items_table_stack.setCurrentIndex(1)

    def _make_inline_qty_widget(self, uid, current_qty):
        c = self._tc()
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(w)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(4)
        lay.setAlignment(Qt.AlignCenter)

        btn_minus = QPushButton("−")
        btn_minus.setFixedSize(22, 24)
        btn_minus.setCursor(Qt.PointingHandCursor)
        btn_minus.setStyleSheet(f"""
            QPushButton {{
                background: #ffffff; color: {c['fg']};
                border: 1px solid {c['border']}; border-radius: 4px;
                font-weight: 700; font-size: 11px;
            }}
            QPushButton:hover {{ background: {c['primary']}15; border-color: {c['primary']}; color: {c['primary']}; }}
        """)
        btn_minus.clicked.connect(lambda: self._decrement_item_qty(uid))

        lbl_qty = QLabel(str(current_qty))
        lbl_qty.setStyleSheet(f"font-weight: 700; color: {c['fg']}; font-size: 9pt; min-width: 22px;")
        lbl_qty.setAlignment(Qt.AlignCenter)

        btn_plus = QPushButton("+")
        btn_plus.setFixedSize(22, 24)
        btn_plus.setCursor(Qt.PointingHandCursor)
        btn_plus.setStyleSheet(f"""
            QPushButton {{
                background: #ffffff; color: {c['fg']};
                border: 1px solid {c['border']}; border-radius: 4px;
                font-weight: 700; font-size: 11px;
            }}
            QPushButton:hover {{ background: {c['primary']}15; border-color: {c['primary']}; color: {c['primary']}; }}
        """)
        btn_plus.clicked.connect(lambda: self._increment_item_qty(uid))

        lay.addWidget(btn_minus)
        lay.addWidget(lbl_qty)
        lay.addWidget(btn_plus)
        return w

    def _decrement_item_qty(self, uid):
        for it in self.invoice_items:
            if it['uid'] == uid:
                if it['qty'] > 1:
                    it['qty'] -= 1
                    it['amount'] = float(Decimal(str(it['qty'])) * Decimal(str(it['rate'])))
                    self._rebuild_table()
                    self._calculate_totals()
                    self._update_item_total()
                else:
                    self._delete_item(uid, ask=False)
                break

    def _increment_item_qty(self, uid):
        for it in self.invoice_items:
            if it['uid'] == uid:
                it['qty'] += 1
                it['amount'] = float(Decimal(str(it['qty'])) * Decimal(str(it['rate'])))
                self._rebuild_table()
                self._calculate_totals()
                self._update_item_total()
                break

    def _delete_item(self, uid, ask=True):
        item = next((it for it in self.invoice_items if it['uid'] == uid), None)
        if not item:
            return
        if ask:
            reply = QMessageBox.question(self, "Remove Item", f"Remove '{item['name']}' from bill?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        self.invoice_items = [it for it in self.invoice_items if it['uid'] != uid]
        self._rebuild_table()
        self._calculate_totals()
        self._update_item_total()

    def _update_item_total(self):
        total = float(sum((Decimal(str(it['amount'])) for it in self.invoice_items), Decimal('0')))
        count = len(self.invoice_items)
        self.item_total_label.setText(f"{count} Item{'s' if count != 1 else ''}  |  {self.currency_symbol} {total:,.2f}")

    def _update_items_summary(self):
        # Compatibility helper
        pass

    def _update_stepper(self, step=0):
        # Compatibility helper
        pass

    # ──────────────────────────────────────────────────────────────────
    # TOTALS, TAXATION & BALANCE CALCULATION
    # ──────────────────────────────────────────────────────────────────
    def _calculate_totals(self):
        subtotal_d = sum((Decimal(str(it['amount'])) for it in self.invoice_items), Decimal('0'))
        self.subtotal_label.setText(f"{self.currency_symbol} {float(subtotal_d):,.2f}")

        discount_before_gst = get_setting('discount_before_gst', False)

        disc_amt_d = Decimal('0')
        if self.disc_checkbox.isChecked():
            raw_type = self.disc_type_combo.currentText()
            disc_val_d = Decimal(str(self.disc_value_spin.value()))
            if raw_type == '%':
                disc_amt_d = subtotal_d * disc_val_d / Decimal('100')
            else:
                disc_amt_d = disc_val_d
            self.disc_amount_label.setText(f"- {self.currency_symbol}{float(disc_amt_d):,.2f}")
        else:
            self.disc_amount_label.setText(f"- {self.currency_symbol}0.00")

        gst_d = Decimal('0')
        if self.gst_checkbox.isChecked():
            gst_rate_val = Decimal(self.gst_rate_combo.currentText().replace('%', ''))
            base_for_gst = subtotal_d - disc_amt_d if discount_before_gst else subtotal_d
            if base_for_gst < 0:
                base_for_gst = Decimal('0')
            gst_d = base_for_gst * gst_rate_val / Decimal('100')
            self.gst_amount_label.setText(f"+ {self.currency_symbol}{float(gst_d):,.2f}")
        else:
            self.gst_amount_label.setText(f"+ {self.currency_symbol}0.00")

        if self.disc_checkbox.isChecked() and not discount_before_gst:
            total_before_disc = subtotal_d + gst_d
            raw_type = self.disc_type_combo.currentText()
            disc_val_d = Decimal(str(self.disc_value_spin.value()))
            if raw_type == '%':
                disc_amt_d = total_before_disc * disc_val_d / Decimal('100')
            else:
                disc_amt_d = disc_val_d
            self.disc_amount_label.setText(f"- {self.currency_symbol}{float(disc_amt_d):,.2f}")

        total_d = subtotal_d + gst_d - disc_amt_d
        if total_d < 0:
            total_d = Decimal('0')
        rounded_total = float(total_d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        self.total_amount_label.setText(f"{self.currency_symbol} {rounded_total:,.2f}")

        # Enable/disable controls
        self.gst_rate_combo.setEnabled(self.gst_checkbox.isChecked())
        self.disc_type_combo.setEnabled(self.disc_checkbox.isChecked())
        self.disc_value_spin.setEnabled(self.disc_checkbox.isChecked())

        self._calculate_balance()

    def _calculate_balance(self):
        total_text = self.total_amount_label.text().replace(self.currency_symbol, "").replace(",", "").strip()
        total = Decimal(total_text) if total_text else Decimal('0')
        advance = Decimal(str(self.advance_input.value()))
        balance = total - advance
        self.balance_label.setText(f"{self.currency_symbol} {float(balance):,.2f}")

        c = self._tc()
        if balance <= 0:
            self.balance_label.setStyleSheet(f"font-size: 12pt; font-weight: 800; color: {GREEN};")
            if not self._payment_status_manually_set:
                self._set_payment_status('Paid')
        elif advance > 0:
            self.balance_label.setStyleSheet(f"font-size: 12pt; font-weight: 800; color: {AMBER};")
            if not self._payment_status_manually_set:
                self._set_payment_status('Partial')
        else:
            self.balance_label.setStyleSheet(f"font-size: 12pt; font-weight: 800; color: {RED};")
            if not self._payment_status_manually_set:
                self._set_payment_status('Pending')

    def _set_payment_status(self, status):
        self._setting_status_programmatically = True
        self.payment_status_combo.setCurrentText(status)
        self._setting_status_programmatically = False

    def _on_payment_status_changed(self, text):
        if not self._setting_status_programmatically:
            self._payment_status_manually_set = True

    # ──────────────────────────────────────────────────────────────────
    # SEARCH & AUTOCOMPLETE
    # ──────────────────────────────────────────────────────────────────
    def _on_customer_search_text(self):
        if self._skip_search:
            return
        sender = self.sender()
        text = sender.text().strip() if sender else ""
        if len(text) >= 2:
            self._search_timer.start(250)
        else:
            self._search_timer.stop()
            self.customer_dropdown.hide()

    def _do_customer_search(self):
        term = self.customer_name_input.text().strip()
        mobile_term = self.customer_mobile_input.text().strip()
        params = []
        conditions = []
        if term:
            conditions.append("name LIKE %s")
            params.append(f"%{term}%")
        if mobile_term:
            conditions.append("mobile LIKE %s")
            params.append(f"%{mobile_term}%")
        if not conditions:
            self.customer_dropdown.hide()
            return

        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            results = db.execute_query(f"""
                SELECT id, name, mobile, email, address, pincode
                FROM customers WHERE is_active=TRUE AND ({' OR '.join(conditions)})
                ORDER BY name LIMIT 10
            """, params, fetch_all=True) or []

        self._customer_cache = results
        self.customer_dropdown.clear()

        # Auto-fill if mobile matches exactly
        clean_mob = mobile_term.replace('+91', '').replace(' ', '').replace('-', '')
        if clean_mob and len(clean_mob) == 10 and len(results) == 1:
            res_mob = str(results[0]['mobile'] or '').replace('+91', '').replace(' ', '').replace('-', '')
            if res_mob == clean_mob:
                self._fill_customer_details(results[0])
                return

        if results:
            for c in results:
                item = QListWidgetItem(f"👤  {c['name']}   |   📞  {c['mobile']}   |   📍  {c.get('address', '')}")
                item.setData(Qt.ItemDataRole.UserRole, c['id'])
                self.customer_dropdown.addItem(item)
            self.customer_dropdown.show()
        else:
            self.customer_dropdown.hide()

    def _on_customer_selected(self, item):
        cid = item.data(Qt.ItemDataRole.UserRole)
        customer = next((c for c in self._customer_cache if c['id'] == cid), None)
        if customer:
            self._fill_customer_details(customer)

    def _fill_customer_details(self, customer):
        self._skip_search = True
        self.customer_id = customer.get('id')
        self.customer_name_input.setText(str(customer.get('name', '') or ''))
        self.customer_mobile_input.setText(str(customer.get('mobile', '') or '').replace('+91', '').replace(' ', '').replace('-', ''))
        self.customer_address_input.setText(str(customer.get('address', '') or ''))
        self.customer_email_input.setText(str(customer.get('email', '') or ''))
        self.customer_pincode_input.setText(str(customer.get('pincode', '') or ''))
        self._skip_search = False
        self.customer_dropdown.hide()

        if hasattr(self, 'cust_status_badge'):
            self.cust_status_badge.setText(f"🟢 Registered Customer (#{self.customer_id})")
            self.cust_status_badge.setStyleSheet(f"""
                background: {GREEN}15; color: {GREEN};
                border: 1px solid {GREEN}40; border-radius: 6px;
                padding: 3px 8px; font-size: 8pt; font-weight: 700;
            """)

    def _on_search_text_changed(self, text):
        if self._search_ignore_next:
            self._search_ignore_next = False
            return
        text = text.strip()
        if len(text) < 1:
            self.search_popup.hide()
            return
        cat = self.item_category_combo.currentText()
        if cat == 'Services':
            pool = [i for i in self._search_items if i['type'] == 'service']
        elif cat == 'Parts':
            pool = [i for i in self._search_items if i['type'] == 'part']
        else:
            pool = self._search_items

        results = [i for i in pool if text.lower() in i['name'].lower()][:10]
        if not results:
            self.search_popup.hide()
            return

        self.search_popup.clear()
        for item in results:
            t = item['type'].upper()
            w = QListWidgetItem(f"[{t}] {item['name']} — {self.currency_symbol}{item['rate']:,.2f}")
            w.setData(Qt.UserRole, item)
            self.search_popup.addItem(w)

        pos = self.item_search_input.mapToGlobal(self.item_search_input.rect().bottomLeft())
        self.search_popup.move(pos)
        self.search_popup.setFixedWidth(self.item_search_input.width())
        self.search_popup.show()

    def _on_search_item_clicked(self, item):
        data = item.data(Qt.UserRole)
        self._selected_search_item = data
        self.selected_item_label.setText(f"{data['name']} ({self.currency_symbol}{data['rate']:,.2f})")
        self.item_rate_spin.setValue(data['rate'])
        self.item_qty_spin.setValue(1)
        self._search_ignore_next = True
        self.item_search_input.setText(data['name'])
        self.search_popup.hide()
        self.item_qty_spin.setFocus()

    def _on_search_return(self):
        if self.search_popup.isVisible() and self.search_popup.count() > 0:
            item = self.search_popup.item(0)
            self._on_search_item_clicked(item)
            self._add_current_item()
        elif self.item_search_input.text().strip():
            self._add_current_item()

    def _clear_item_search(self):
        self._selected_search_item = None
        self.selected_item_label.setText("—")
        self.item_search_input.clear()
        self.item_rate_spin.setValue(0)
        self.item_qty_spin.setValue(1)
        self.search_popup.hide()

    def eventFilter(self, obj, event):
        if obj is self.item_search_input and event.type() == QEvent.KeyPress:
            if self.search_popup.isVisible():
                if event.key() == Qt.Key_Down:
                    self.search_popup.setFocus()
                    self.search_popup.setCurrentRow(0)
                    return True
                elif event.key() == Qt.Key_Escape:
                    self.search_popup.hide()
                    return True
        elif obj is self.search_popup and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                item = self.search_popup.currentItem()
                if item:
                    self._on_search_item_clicked(item)
                return True
            elif event.key() == Qt.Key_Escape:
                self.search_popup.hide()
                self.item_search_input.setFocus()
                return True
        return super().eventFilter(obj, event)

    # ──────────────────────────────────────────────────────────────────
    # MASTER DATA LOADING
    # ──────────────────────────────────────────────────────────────────
    def load_master_data(self):
        self.run_in_thread(self._load_master_data_thread, self._update_master_data)

    def _load_master_data_thread(self):
        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            services = db.execute_query("SELECT id, service_name, default_rate FROM services WHERE is_active = TRUE", fetch_all=True)
            parts = db.execute_query("SELECT id, part_name, default_rate, stock_quantity, unit FROM parts WHERE is_active = TRUE", fetch_all=True)
            brands = db.execute_query("SELECT id, brand_name FROM ac_brands WHERE is_active = TRUE", fetch_all=True) if get_setting('shop_type', 'AC Service') == 'AC Service' else []
            technicians = db.execute_query("SELECT id, name FROM technicians WHERE is_active = TRUE", fetch_all=True)
            payment_modes = db.execute_query("SELECT id, mode_name FROM payment_modes WHERE is_active = TRUE", fetch_all=True)
            return {
                'services': services or [],
                'parts': parts or [],
                'brands': brands or [],
                'technicians': technicians or [],
                'payment_modes': payment_modes or []
            }

    def _update_master_data(self, data):
        self.services_list = data['services']
        self.parts_list = data['parts']
        self.ac_brands_list = data['brands']
        self.technicians_list = data['technicians']
        self._build_search_index()

        if get_setting('shop_type', 'AC Service') == 'AC Service':
            self.ac_brand_combo.blockSignals(True)
            self.ac_brand_combo.clear()
            self.ac_brand_combo.addItem("Select Brand", "")
            for b in self.ac_brands_list:
                self.ac_brand_combo.addItem(b['brand_name'], b['id'])
            self.ac_brand_combo.blockSignals(False)

        self.technician_combo.blockSignals(True)
        self.technician_combo.clear()
        self.technician_combo.addItem("-- Select Technician --", "")
        for t in self.technicians_list:
            self.technician_combo.addItem(t['name'], t['id'])
        self.technician_combo.blockSignals(False)

        self.payment_mode_combo.blockSignals(True)
        self.payment_mode_combo.clear()
        for pm in data['payment_modes']:
            self.payment_mode_combo.addItem(pm['mode_name'])
        self.payment_mode_combo.blockSignals(False)

    def _build_search_index(self):
        self._search_items = []
        for s in self.services_list:
            self._search_items.append({
                'type': 'service', 'id': s['id'], 'name': s['service_name'],
                'rate': float(s['default_rate']), 'unit': '', 'stock': None
            })
        for p in self.parts_list:
            self._search_items.append({
                'type': 'part', 'id': p['id'], 'name': p['part_name'],
                'rate': float(p['default_rate']), 'unit': p.get('unit', 'pcs'),
                'stock': p.get('stock_quantity')
            })

    # ──────────────────────────────────────────────────────────────────
    # SAVE & PRINT & WHATSAPP
    # ──────────────────────────────────────────────────────────────────
    def _validate_form(self):
        name = self.customer_name_input.text().strip()
        mobile = self.customer_mobile_input.text().strip().replace('+91', '').replace(' ', '').replace('-', '')
        if not name:
            self.show_warning_message("Please enter Customer Full Name")
            self.customer_name_input.setFocus()
            return False
        if not mobile or (len(mobile) != 10 and not mobile.startswith('0')):
            self.show_warning_message("Please enter a valid 10-digit Customer Mobile Number")
            self.customer_mobile_input.setFocus()
            return False
        if not self.invoice_items:
            self.show_warning_message("Please add at least one service or spare part to the bill")
            self.item_search_input.setFocus()
            return False
        return True

    def _save_invoice(self):
        if self._save_in_progress:
            return
        if not self._validate_form():
            return
        self._save_in_progress = True
        self.save_invoice_btn.setEnabled(False)
        self.save_invoice_btn.setText("⏳  Saving Draft...")
        try:
            res = self._execute_save_invoice()
            if res:
                inv_num = res['inv_num']
                cust_name = res['cust_name']
                self.show_success_message(f"Invoice {inv_num} saved successfully for {cust_name}!")
                self._clear_form()
                return res['inv_id']
            return None
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Unexpected error saving invoice:\n{str(e)}")
            import traceback; traceback.print_exc()
            return None
        finally:
            self._save_in_progress = False
            self.save_invoice_btn.setEnabled(True)
            self.save_invoice_btn.setText("💾   Save Invoice Draft (Ctrl+S)")

    def _save_and_print_invoice(self):
        if self._save_in_progress:
            return
        if not self._validate_form():
            return
        res = self._execute_save_invoice()
        if not res:
            return
        inv_id = res['inv_id']
        inv_num = res['inv_num']
        cust_name = res['cust_name']
        mobile = res['mobile']
        total = res['total_amount']
        advance = res['advance_payment']
        balance = res['balance_amount']
        try:
            from database.db_connection import DatabaseContext
            from utils.pdf_invoice_generator import PDFInvoiceGenerator
            from utils.formatters import Formatters

            with DatabaseContext() as db:
                inv = db.execute_query(
                    "SELECT i.*, c.name as customer_name, c.mobile as customer_mobile FROM invoices i JOIN customers c ON i.customer_id = c.id WHERE i.id = %s",
                    (inv_id,), fetch_one=True
                )
                items = db.execute_query(
                    "SELECT ii.*, s.service_name, p.part_name, p.unit FROM invoice_items ii LEFT JOIN services s ON ii.service_id = s.id LEFT JOIN parts p ON ii.part_id = p.id WHERE ii.invoice_id = %s",
                    (inv_id,), fetch_all=True
                )

            pdf_data = {
                'invoice_number': inv_num,
                'invoice_date': Formatters.format_date(inv.get('created_at')) or datetime.now().strftime('%d-%m-%Y'),
                'customer_name': cust_name,
                'customer_mobile': mobile,
                'customer_address': self.customer_address_input.text().strip(),
                'ac_brand': self.ac_brand_combo.currentText(),
                'ac_type': self.ac_type_combo.currentText(),
                'ton_capacity': self.ac_ton_combo.currentText(),
                'items': [{
                    'description': (it.get('description') or it.get('service_name') or it.get('part_name') or 'Service'),
                    'quantity': it.get('quantity', 1),
                    'rate': float(it.get('rate') or 0),
                    'amount': float(it.get('amount') or 0),
                    'unit': it.get('unit', 'pcs'),
                } for it in (items or [])],
                'subtotal': float(inv.get('subtotal') or 0),
                'gst_amount': float(inv.get('gst_amount') or 0),
                'gst_percentage': float(inv.get('gst_percentage') or 0),
                'total_amount': total,
                'paid_amount': advance,
                'balance_amount': balance,
                'payment_mode': self.payment_mode_combo.currentText(),
                'payment_status': self.payment_status_combo.currentText(),
            }

            generator = PDFInvoiceGenerator()
            pdf_path = generator.generate_invoice(pdf_data)
            self.show_success_message(f"Invoice {inv_num} saved! Sending to system printer...")
            if os.path.exists(pdf_path):
                try:
                    os.startfile(pdf_path, "print")
                except Exception:
                    os.startfile(pdf_path)
            self._clear_form()
        except Exception as e:
            self.show_error_message(f"Print error: {str(e)}")

    def _direct_whatsapp_share(self):
        if self._save_in_progress:
            return
        if not self._validate_form():
            return
        self._save_in_progress = True
        self.wa_direct_btn.setEnabled(False)
        self.wa_direct_btn.setText("⚡  Generating PDF...")
        try:
            res = self._execute_save_invoice()
            if not res:
                return

            inv_id = res['inv_id']
            inv_num = res['inv_num']
            cust_name = res['cust_name']
            mobile = res['mobile']
            total = res['total_amount']
            advance = res['advance_payment']
            balance = res['balance_amount']

            from database.db_connection import DatabaseContext
            from utils.pdf_invoice_generator import PDFInvoiceGenerator
            from utils.whatsapp_clipboard import open_direct_chat_with_message, copy_file_to_clipboard
            from utils.formatters import Formatters

            with DatabaseContext() as db:
                inv = db.execute_query(
                    "SELECT i.*, c.name as customer_name, c.mobile as customer_mobile FROM invoices i JOIN customers c ON i.customer_id = c.id WHERE i.id = %s",
                    (inv_id,), fetch_one=True
                )
                items = db.execute_query(
                    "SELECT ii.*, s.service_name, p.part_name, p.unit FROM invoice_items ii LEFT JOIN services s ON ii.service_id = s.id LEFT JOIN parts p ON ii.part_id = p.id WHERE ii.invoice_id = %s",
                    (inv_id,), fetch_all=True
                )

            pdf_data = {
                'invoice_number': inv_num,
                'invoice_date': Formatters.format_date(inv.get('created_at')) or datetime.now().strftime('%d-%m-%Y'),
                'customer_name': cust_name,
                'customer_mobile': mobile,
                'customer_address': self.customer_address_input.text().strip(),
                'ac_brand': self.ac_brand_combo.currentText(),
                'ac_type': self.ac_type_combo.currentText(),
                'ton_capacity': self.ac_ton_combo.currentText(),
                'items': [{
                    'description': (it.get('description') or it.get('service_name') or it.get('part_name') or 'Service'),
                    'quantity': it.get('quantity', 1),
                    'rate': float(it.get('rate') or 0),
                    'amount': float(it.get('amount') or 0),
                    'unit': it.get('unit', 'pcs'),
                } for it in (items or [])],
                'subtotal': float(inv.get('subtotal') or 0),
                'gst_amount': float(inv.get('gst_amount') or 0),
                'gst_percentage': float(inv.get('gst_percentage') or 0),
                'total_amount': total,
                'paid_amount': advance,
                'balance_amount': balance,
                'payment_mode': self.payment_mode_combo.currentText(),
                'payment_status': self.payment_status_combo.currentText(),
            }

            generator = PDFInvoiceGenerator()
            pdf_path = generator.generate_invoice(pdf_data)

            copy_file_to_clipboard(pdf_path)

            company = get_setting('company_name', 'Ansh Air Cool')
            wa_message = (
                f"📄 *TAX INVOICE - {inv_num}*\n\n"
                f"Namaste {cust_name} ji!\n"
                f"Thank you for choosing *{company}*.\n\n"
                f"📋 *Bill Details:*\n"
                f"• Invoice No: {inv_num}\n"
                f"• Date: {datetime.now().strftime('%d-%m-%Y')}\n"
                f"• Total Amount: ₹{total:,.2f}\n"
                f"• Advance Paid: ₹{advance:,.2f}\n"
                f"• Balance Due: ₹{balance:,.2f}\n\n"
                f"📄 Invoice PDF aapke sath attach kar diya gaya hai."
            )

            open_direct_chat_with_message(mobile, wa_message, paste_file=True, file_path=pdf_path)
            self.show_success_message(f"⚡ Invoice {inv_num} saved & WhatsApp chat opened for {cust_name}!")
            self._clear_form()

        except Exception as e:
            self.show_error_message(f"WhatsApp share error: {str(e)}")
            import traceback; traceback.print_exc()
        finally:
            self._save_in_progress = False
            self.wa_direct_btn.setEnabled(True)
            self.wa_direct_btn.setText("⚡   Direct WhatsApp PDF (Alt+W)")

    def _preview_invoice_pdf(self):
        if not self.invoice_items:
            self.show_warning_message("Please add at least one service or part to preview the bill")
            return
        try:
            from utils.pdf_invoice_generator import PDFInvoiceGenerator
            from config import PDF_DIR

            subtotal = sum((Decimal(str(it['amount'])) for it in self.invoice_items), Decimal('0'))
            gst_amt = Decimal('0')
            gst_pct = 0.0
            if self.gst_checkbox.isChecked():
                gst_pct = float(self.gst_rate_combo.currentText().replace('%', ''))
                gst_amt = subtotal * Decimal(str(gst_pct)) / Decimal('100')
            disc_amt = Decimal('0')
            if self.disc_checkbox.isChecked():
                disc_val = Decimal(str(self.disc_value_spin.value()))
                if self.disc_type_combo.currentText() == '%':
                    disc_amt = subtotal * disc_val / Decimal('100')
                else:
                    disc_amt = disc_val

            total = float(subtotal + gst_amt - disc_amt)
            adv = float(self.advance_input.value())
            bal = total - adv

            pdf_data = {
                'invoice_number': 'PREVIEW-DRAFT',
                'invoice_date': datetime.now().strftime('%d-%m-%Y'),
                'customer_name': self.customer_name_input.text().strip() or 'Valued Customer',
                'customer_mobile': self.customer_mobile_input.text().strip() or 'N/A',
                'customer_address': self.customer_address_input.text().strip(),
                'ac_brand': self.ac_brand_combo.currentText(),
                'ac_type': self.ac_type_combo.currentText(),
                'ton_capacity': self.ac_ton_combo.currentText(),
                'items': [{
                    'description': it['name'],
                    'quantity': it['qty'],
                    'rate': float(it['rate']),
                    'amount': float(it['amount']),
                    'unit': it.get('unit', 'pcs'),
                } for it in self.invoice_items],
                'subtotal': float(subtotal),
                'gst_amount': float(gst_amt),
                'gst_percentage': gst_pct,
                'total_amount': total,
                'paid_amount': adv,
                'balance_amount': bal,
                'payment_mode': self.payment_mode_combo.currentText(),
                'payment_status': self.payment_status_combo.currentText(),
            }

            generator = PDFInvoiceGenerator()
            pdf_path = generator.generate_invoice(pdf_data)
            if os.path.exists(pdf_path):
                os.startfile(pdf_path)
            self.show_success_message("Opening Invoice PDF Preview...")
        except Exception as e:
            self.show_error_message(f"Preview error: {str(e)}")

    def _execute_save_invoice(self):
        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            cust_name = self.customer_name_input.text().strip()
            mobile = self.customer_mobile_input.text().strip().replace('+91', '').replace(' ', '').replace('-', '')
            cust_address = self.customer_address_input.text().strip()
            cust_email = self.customer_email_input.text().strip()
            cust_pincode = self.customer_pincode_input.text().strip()

            if self.customer_id:
                cust_id = self.customer_id
                db.execute_query(
                    "UPDATE customers SET name=%s, mobile=%s, address=%s, email=%s, pincode=%s, updated_at=NOW() WHERE id=%s",
                    (cust_name, mobile, cust_address, cust_email, cust_pincode, cust_id)
                )
            else:
                existing = db.execute_query(
                    "SELECT id FROM customers WHERE mobile=%s AND is_active=TRUE", (mobile,), fetch_one=True
                )
                if existing:
                    cust_id = existing['id']
                    db.execute_query(
                        "UPDATE customers SET name=%s, address=%s, email=%s, pincode=%s, updated_at=NOW() WHERE id=%s",
                        (cust_name, cust_address, cust_email, cust_pincode, cust_id)
                    )
                else:
                    cust_id = db.execute_query(
                        "INSERT INTO customers (name, mobile, address, email, pincode, is_active) VALUES (%s, %s, %s, %s, %s, TRUE)",
                        (cust_name, mobile, cust_address, cust_email, cust_pincode)
                    )

            subtotal_d = sum((Decimal(str(it['amount'])) for it in self.invoice_items), Decimal('0'))
            discount_before_gst = get_setting('discount_before_gst', False)

            disc_amt_d = Decimal('0')
            disc_type = ''
            disc_val_d = Decimal('0')
            if self.disc_checkbox.isChecked():
                raw_type = self.disc_type_combo.currentText()
                disc_type = 'percentage' if raw_type == '%' else 'fixed'
                disc_val_d = Decimal(str(self.disc_value_spin.value()))
                base_for_disc = subtotal_d
                if disc_type == 'percentage':
                    disc_amt_d = base_for_disc * disc_val_d / Decimal('100')
                else:
                    disc_amt_d = disc_val_d

            gst_d = Decimal('0')
            gst_rate_used = 0
            if self.gst_checkbox.isChecked():
                gst_rate_val = Decimal(self.gst_rate_combo.currentText().replace('%', ''))
                if discount_before_gst:
                    gst_base = subtotal_d - disc_amt_d
                    if gst_base < 0:
                        gst_base = Decimal('0')
                    gst_d = gst_base * gst_rate_val / Decimal('100')
                else:
                    gst_d = subtotal_d * gst_rate_val / Decimal('100')
                gst_rate_used = float(gst_rate_val)

            if self.disc_checkbox.isChecked() and not discount_before_gst:
                total_before_disc = subtotal_d + gst_d
                if disc_type == 'percentage':
                    disc_amt_d = total_before_disc * disc_val_d / Decimal('100')
                else:
                    disc_amt_d = disc_val_d

            total_d = subtotal_d + gst_d - disc_amt_d
            if total_d < 0:
                total_d = Decimal('0')
            rounded_total = float(total_d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            advance_d = Decimal(str(self.advance_input.value()))
            balance_d = Decimal(str(rounded_total)) - advance_d

            from utils.formatters import Formatters
            inv_num = Formatters.generate_invoice_number(db)

            tech_id = self.technician_combo.currentData() if self.technician_combo.currentData() else None
            brand_id = self.ac_brand_combo.currentData() if self.ac_brand_combo.currentData() else None
            notes = self.notes_input.toPlainText().strip()

            inv_id = db.execute_query("""
                INSERT INTO invoices (
                    invoice_number, customer_id, ac_brand_id, ac_type, ton_capacity,
                    ac_inverter, star_rating,
                    technician_id, subtotal, gst_percentage,
                    gst_amount, discount_type, discount_value, discount_amount,
                    total_amount, advance_payment, balance_amount,
                    payment_mode, payment_status, notes, is_active, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, NOW())
            """, (
                inv_num, cust_id, brand_id, self.ac_type_combo.currentText(),
                self.ac_ton_combo.currentText(), self.ac_inverter_combo.currentText(),
                self.ac_star_combo.currentText(), tech_id,
                float(subtotal_d), gst_rate_used, float(gst_d),
                disc_type, float(disc_val_d), float(disc_amt_d),
                float(rounded_total), float(advance_d), float(balance_d),
                self.payment_mode_combo.currentText(),
                self.payment_status_combo.currentText(),
                notes,
            ))

            for it in self.invoice_items:
                db.execute_query("""
                    INSERT INTO invoice_items (invoice_id, item_type, service_id, part_id, description, quantity, rate, amount)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    inv_id, it['type'],
                    it['item_id'] if it['type'] == 'service' else None,
                    it['item_id'] if it['type'] == 'part' else None,
                    it.get('name', ''),
                    it['qty'], it['rate'], it['amount']
                ))
                if it['type'] == 'part' and it['item_id'] is not None:
                    db.execute_query(
                        "UPDATE parts SET stock_quantity = stock_quantity - %s WHERE id = %s AND stock_quantity >= %s",
                        (it['qty'], it['item_id'], it['qty'])
                    )

            return {
                'inv_id': inv_id,
                'inv_num': inv_num,
                'cust_id': cust_id,
                'cust_name': cust_name,
                'mobile': mobile,
                'total_amount': float(rounded_total),
                'advance_payment': float(advance_d),
                'balance_amount': float(balance_d),
            }

    # ──────────────────────────────────────────────────────────────────
    # FORM RESET & EXTERNAL INTEGRATION
    # ──────────────────────────────────────────────────────────────────
    def _clear_form(self):
        self.customer_id = None
        self._skip_search = False
        self._payment_status_manually_set = False
        self._setting_status_programmatically = False
        if hasattr(self, 'customer_dropdown'):
            self.customer_dropdown.hide()
        self.customer_name_input.clear()
        self.customer_mobile_input.clear()
        self.customer_address_input.clear()
        self.customer_email_input.clear()
        self.customer_pincode_input.clear()
        self.ac_inverter_combo.setCurrentIndex(0)
        self.ac_star_combo.setCurrentIndex(0)
        self.items_table.setRowCount(0)
        self.items_table_stack.setCurrentIndex(1)
        self.invoice_items = []
        self._clear_item_search()
        self.gst_checkbox.setChecked(False)
        self.gst_rate_combo.setCurrentIndex(2)
        self.disc_checkbox.setChecked(False)
        self.disc_type_combo.setCurrentIndex(0)
        self.disc_value_spin.setValue(0)
        self.advance_input.setValue(0)
        self.technician_combo.setCurrentIndex(0)
        self.payment_mode_combo.setCurrentIndex(0)
        self.payment_status_combo.setCurrentIndex(0)
        self.notes_input.setText(get_setting('default_notes', 'All Work Done'))
        self.subtotal_label.setText(f"{self.currency_symbol} 0.00")
        self.gst_amount_label.setText(f"+ {self.currency_symbol}0.00")
        self.disc_amount_label.setText(f"- {self.currency_symbol}0.00")
        self.total_amount_label.setText(f"{self.currency_symbol} 0")
        self.balance_label.setText(f"{self.currency_symbol} 0.00")
        self._update_item_total()

        if hasattr(self, 'cust_status_badge'):
            c = self._tc()
            self.cust_status_badge.setText("🔵 New Customer (Auto-save)")
            self.cust_status_badge.setStyleSheet(f"""
                background: {c['primary']}15; color: {c['primary']};
                border: 1px solid {c['primary']}30; border-radius: 6px;
                padding: 3px 8px; font-size: 8pt; font-weight: 700;
            """)

    def set_customer_data(self, data):
        """Pre-fill customer details from customer view or quick search"""
        if not data:
            return
        self.customer_id = data.get('id')
        if hasattr(self, 'customer_name_input'):
            self.customer_name_input.setText(str(data.get('name', '') or ''))
        if hasattr(self, 'customer_mobile_input'):
            self.customer_mobile_input.setText(str(data.get('mobile', '') or ''))
        if hasattr(self, 'customer_address_input') and data.get('address'):
            self.customer_address_input.setText(str(data.get('address', '') or ''))
        if hasattr(self, 'customer_email_input') and data.get('email'):
            self.customer_email_input.setText(str(data.get('email', '') or ''))
        if hasattr(self, 'customer_pincode_input') and data.get('pincode'):
            self.customer_pincode_input.setText(str(data.get('pincode', '') or ''))

        if hasattr(self, 'cust_status_badge'):
            self.cust_status_badge.setText(f"🟢 Customer Loaded (#{self.customer_id or 'New'})")
            self.cust_status_badge.setStyleSheet(f"""
                background: {GREEN}15; color: {GREEN};
                border: 1px solid {GREEN}40; border-radius: 6px;
                padding: 3px 8px; font-size: 8pt; font-weight: 700;
            """)

    def refresh_data(self):
        self.customer_id = None
        self._payment_status_manually_set = False
        self._setting_status_programmatically = False
        if hasattr(self, 'customer_dropdown'):
            self.customer_dropdown.hide()
        self.invoice_items = []
        self.items_table.setRowCount(0)
        self.items_table_stack.setCurrentIndex(1)
        self.load_master_data()

    def reload_ui_settings(self):
        self.currency_symbol = get_setting("currency_symbol", "₹")
        self._clear_form()
        self._rebuild_table()
