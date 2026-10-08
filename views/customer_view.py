"""
Customer View - Enterprise CRM-style Customer Management
Clean white theme with modern UI/UX
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea,
    QSizePolicy, QSplitter, QMessageBox, QMenu, QDialog, QDialogButtonBox,
    QFormLayout, QTextEdit, QFileDialog, QGridLayout, QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect, QSpacerItem, QComboBox
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, Property, QUrl
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QDesktopServices

from utils.unified_theme import UnifiedTheme
from utils.app_settings import get_setting
from utils.formatters import Formatters
from views.base_window import BaseView, MetricCard
import os

CHEVRON_ICON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "icons", "chevron_down.png"
).replace("\\", "/")

FONT_FAMILY = "'Inter', 'Segoe UI', sans-serif"

# Enterprise color tokens for white theme
ENTERPRISE_COLORS = {
    'bg': '#f8fafc',
    'card': '#ffffff',
    'card_hover': '#f8fafc',
    'primary': '#2563eb',
    'primary_light': '#eff6ff',
    'primary_border': '#bfdbfe',
    'success': '#059669',
    'success_light': '#ecfdf5',
    'success_border': '#a7f3d0',
    'warning': '#d97706',
    'warning_light': '#fffbeb',
    'warning_border': '#fde68a',
    'danger': '#dc2626',
    'danger_light': '#fef2f2',
    'danger_border': '#fecaca',
    'info': '#0284c7',
    'info_light': '#f0f9ff',
    'info_border': '#bae6fd',
    'text': '#0f172a',
    'text_secondary': '#475569',
    'text_muted': '#94a3b8',
    'border': '#e2e8f0',
    'border_light': '#f1f5f9',
    'divider': '#e2e8f0',
    'table_header': '#f8fafc',
    'table_stripe': '#fafbfd',
    'shadow': 'rgba(15, 23, 42, 0.08)',
    'shadow_hover': 'rgba(15, 23, 42, 0.12)',
}


class EnterpriseCard(QFrame):
    """Enterprise card with subtle shadow and hover effect"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_card()

    def _setup_card(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ENTERPRISE_COLORS['card']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 12px;
            }}
        """)


class StatCard(QFrame):
    """Enterprise stat card with icon and value"""

    def __init__(self, label, value, icon, color, parent=None):
        super().__init__(parent)
        self._label = label
        self._value = value
        self._icon = icon
        self._color = color
        self._setup_ui()

    def _setup_ui(self):
        self.setMinimumHeight(88)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {ENTERPRISE_COLORS['card']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 12px;
            }}
            QFrame:hover {{
                border-color: {self._color}40;
                background-color: {self._color}04;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        icon_box = QFrame()
        icon_box.setFixedSize(44, 44)
        icon_box.setStyleSheet(f"""
            QFrame {{
                background-color: {self._color}12;
                border: 1px solid {self._color}25;
                border-radius: 12px;
            }}
        """)
        icon_l = QVBoxLayout(icon_box)
        icon_l.setContentsMargins(0, 0, 0, 0)
        icon_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl = QLabel(self._icon)
        icon_lbl.setStyleSheet(f"font-size: 18pt; background: transparent; color: {self._color};")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_l.addWidget(icon_lbl)
        layout.addWidget(icon_box)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self._value_lbl = QLabel(self._value)
        self._value_lbl.setStyleSheet(f"""
            font-size: 22pt; font-weight: 700;
            color: {ENTERPRISE_COLORS['text']};
            background: transparent;
            font-family: {FONT_FAMILY};
        """)
        text_col.addWidget(self._value_lbl)
        self._label_lbl = QLabel(self._label)
        self._label_lbl.setStyleSheet(f"""
            font-size: 9pt;
            color: {ENTERPRISE_COLORS['text_muted']};
            font-weight: 500;
            background: transparent;
            font-family: {FONT_FAMILY};
        """)
        text_col.addWidget(self._label_lbl)
        layout.addLayout(text_col)
        layout.addStretch()

    def update_value(self, value):
        self._value_lbl.setText(str(value))


class StatusBadge(QLabel):
    """Modern status badge"""

    STYLES = {
        'paid': ('#059669', '#ecfdf5', '#a7f3d0'),
        'pending': '#d97706',
        'partial': '#0284c7',
        'overdue': '#dc2626',
        'active': '#059669',
        'info': '#0284c7',
    }

    def __init__(self, text, status_type="info", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(24)

        config = self.STYLES.get(status_type, self.STYLES['info'])
        if isinstance(config, tuple):
            text_color, bg_color, border_color = config
        else:
            text_color = config
            bg_color = f"{config}12"
            border_color = f"{config}40"

        self.setStyleSheet(f"""
            background-color: {bg_color};
            color: {text_color};
            border: 1px solid {border_color};
            border-radius: 6px;
            padding: 3px 12px;
            font-size: 8pt;
            font-weight: 600;
            font-family: {FONT_FAMILY};
        """)


class TimelineNode(QFrame):
    """Activity timeline node with enterprise styling"""

    def __init__(self, event_type, date_str, description, is_first, is_last, parent=None):
        super().__init__(parent)
        self._event_type = event_type
        self._date_str = date_str
        self._description = description
        self._is_first = is_first
        self._is_last = is_last
        self._setup_ui()

    def _setup_ui(self):
        type_config = {
            'invoice': {'color': '#2563eb', 'bg': '#eff6ff', 'border': '#bfdbfe', 'icon': '📋', 'label': 'INVOICE'},
            'amc': {'color': '#7c3aed', 'bg': '#f5f3ff', 'border': '#c4b5fd', 'icon': '🛡️', 'label': 'AMC'},
            'log': {'color': '#059669', 'bg': '#ecfdf5', 'border': '#a7f3d0', 'icon': '🔧', 'label': 'SERVICE'},
        }
        cfg = type_config.get(self._event_type, {'color': '#64748b', 'bg': '#f8fafc', 'border': '#e2e8f0', 'icon': '📌', 'label': 'EVENT'})

        self.setStyleSheet("background: transparent; border: none;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        indicator_col = QVBoxLayout()
        indicator_col.setSpacing(0)
        indicator_col.setAlignment(Qt.AlignmentFlag.AlignTop)

        if not self._is_first:
            line_top = QFrame()
            line_top.setFixedSize(2, 12)
            line_top.setStyleSheet(f"background-color: {cfg['border']}; border: none;")
            indicator_col.addWidget(line_top, alignment=Qt.AlignmentFlag.AlignHCenter)
        else:
            sp = QFrame()
            sp.setFixedHeight(12)
            sp.setStyleSheet("background: transparent; border: none;")
            indicator_col.addWidget(sp, alignment=Qt.AlignmentFlag.AlignHCenter)

        dot_frame = QFrame()
        dot_frame.setFixedSize(40, 40)
        dot_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {cfg['bg']};
                border: 2px solid {cfg['border']};
                border-radius: 20px;
            }}
        """)
        dot_layout = QVBoxLayout(dot_frame)
        dot_layout.setContentsMargins(0, 0, 0, 0)
        dot_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dot_icon = QLabel(cfg['icon'])
        dot_icon.setStyleSheet("font-size: 13pt; background: transparent;")
        dot_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dot_layout.addWidget(dot_icon)
        indicator_col.addWidget(dot_frame, alignment=Qt.AlignmentFlag.AlignHCenter)

        if not self._is_last:
            line_bottom = QFrame()
            line_bottom.setFixedSize(2, 12)
            line_bottom.setStyleSheet(f"background-color: {cfg['border']}; border: none;")
            indicator_col.addWidget(line_bottom, alignment=Qt.AlignmentFlag.AlignHCenter)
        else:
            sp2 = QFrame()
            sp2.setFixedHeight(12)
            sp2.setStyleSheet("background: transparent; border: none;")
            indicator_col.addWidget(sp2, alignment=Qt.AlignmentFlag.AlignHCenter)

        layout.addLayout(indicator_col)

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {ENTERPRISE_COLORS['card']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 10px;
            }}
            QFrame:hover {{
                background-color: {cfg['bg']};
                border: 1px solid {cfg['border']};
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(6)

        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        badge = QLabel(cfg['label'])
        badge.setStyleSheet(f"""
            font-size: 8pt; font-weight: 600;
            color: {cfg['color']};
            background-color: {cfg['bg']};
            border: 1px solid {cfg['border']};
            border-radius: 4px;
            padding: 3px 10px;
            font-family: {FONT_FAMILY};
        """)
        header_row.addWidget(badge)
        header_row.addStretch()

        date_lbl = QLabel(self._date_str)
        date_lbl.setStyleSheet(f"""
            font-size: 8.5pt;
            color: {ENTERPRISE_COLORS['text_muted']};
            background: transparent;
            font-family: {FONT_FAMILY};
        """)
        header_row.addWidget(date_lbl)
        card_layout.addLayout(header_row)

        desc_lbl = QLabel(self._description)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(f"""
            font-size: 10pt;
            color: {ENTERPRISE_COLORS['text']};
            background: transparent;
            font-family: {FONT_FAMILY};
        """)
        card_layout.addWidget(desc_lbl)

        layout.addWidget(card, 1)


class CustomerView(BaseView):
    """Enterprise CRM-style customer management view"""

    def __init__(self):
        super().__init__()
        self.selected_customer_id = None
        self.customer_list = []
        self._setup_ui()
        self.load_customers()

    def update_theme_colors(self):
        colors = self.theme_manager.get_colors()
        self.theme_manager.apply_palette(self)
        self.setStyleSheet(self.theme_manager.get_main_stylesheet())
        if hasattr(self, 'customer_table'):
            self._style_table(self.customer_table)
        if hasattr(self, 'invoices_table'):
            self._style_table(self.invoices_table)
        self.load_customers()

    def _style_table(self, table):
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {ENTERPRISE_COLORS['card']};
                color: {ENTERPRISE_COLORS['text']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 10px;
                gridline-color: {ENTERPRISE_COLORS['border_light']};
                selection-background-color: {ENTERPRISE_COLORS['primary_light']};
                selection-color: {ENTERPRISE_COLORS['primary']};
                outline: none;
                alternate-background-color: {ENTERPRISE_COLORS['table_stripe']};
                font-size: 10pt;
                font-family: {FONT_FAMILY};
            }}
            QTableWidget::item {{
                padding: 14px 12px;
                border: none;
                color: {ENTERPRISE_COLORS['text']};
                background-color: transparent;
                border-bottom: 1px solid {ENTERPRISE_COLORS['border_light']};
            }}
            QTableWidget::item:selected {{
                background-color: {ENTERPRISE_COLORS['primary_light']};
                color: {ENTERPRISE_COLORS['primary']};
                border-left: 3px solid {ENTERPRISE_COLORS['primary']};
            }}
            QTableWidget::item:hover {{
                background-color: {ENTERPRISE_COLORS['primary_light']}80;
            }}
            QTableWidget::item:alternate {{
                background-color: {ENTERPRISE_COLORS['table_stripe']};
                border-bottom: 1px solid {ENTERPRISE_COLORS['border_light']};
            }}
            QTableWidget::item:alternate:selected {{
                background-color: {ENTERPRISE_COLORS['primary_light']};
                color: {ENTERPRISE_COLORS['primary']};
                border-left: 3px solid {ENTERPRISE_COLORS['primary']};
            }}
            QTableWidget::item:alternate:hover {{
                background-color: {ENTERPRISE_COLORS['primary_light']}80;
            }}
            QHeaderView::section {{
                background-color: {ENTERPRISE_COLORS['table_header']};
                color: {ENTERPRISE_COLORS['text_muted']};
                padding: 14px 12px;
                border: none;
                border-bottom: 2px solid {ENTERPRISE_COLORS['divider']};
                border-right: 1px solid {ENTERPRISE_COLORS['border_light']};
                font-weight: 600;
                font-size: 8.5pt;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                font-family: {FONT_FAMILY};
            }}
            QHeaderView::section:first {{
                border-top-left-radius: 10px;
            }}
            QHeaderView::section:last {{
                border-top-right-radius: 10px;
                border-right: none;
            }}
            QHeaderView::section:hover {{
                background-color: {ENTERPRISE_COLORS['card_hover']};
                color: {ENTERPRISE_COLORS['text']};
            }}
        """)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(24)

        self._create_header(main_layout)
        self._create_controls(main_layout)
        self._create_kpi_cards(main_layout)
        self._create_content(main_layout)

    def _create_header(self, layout):
        header = QFrame()
        header.setStyleSheet("background: transparent; border: none;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)

        icon_frame = QFrame()
        icon_frame.setFixedSize(52, 52)
        icon_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {ENTERPRISE_COLORS['primary']}, stop:1 #1d4ed8);
                border-radius: 14px;
            }}
        """)
        icon_l = QVBoxLayout(icon_frame)
        icon_l.setContentsMargins(0, 0, 0, 0)
        icon_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl = QLabel("👥")
        icon_lbl.setStyleSheet("font-size: 22pt; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_l.addWidget(icon_lbl)
        hl.addWidget(icon_frame)
        hl.addSpacing(18)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        title = QLabel("Customer Management")
        title.setStyleSheet(f"""
            font-size: 26pt;
            font-weight: 700;
            color: {ENTERPRISE_COLORS['text']};
            letter-spacing: -0.5px;
            background: transparent;
            font-family: {FONT_FAMILY};
        """)
        text_col.addWidget(title)
        subtitle = QLabel("View, manage, and track all service customers")
        subtitle.setStyleSheet(f"""
            font-size: 11pt;
            color: {ENTERPRISE_COLORS['text_muted']};
            background: transparent;
            font-family: {FONT_FAMILY};
        """)
        text_col.addWidget(subtitle)
        hl.addLayout(text_col)
        hl.addStretch()

        layout.addWidget(header)

    def _create_controls(self, layout):
        control_frame = EnterpriseCard()
        control_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {ENTERPRISE_COLORS['card']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 14px;
                padding: 4px;
            }}
        """)

        cl = QHBoxLayout(control_frame)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(16)

        search_container = QFrame()
        search_container.setStyleSheet(f"""
            QFrame {{
                background-color: {ENTERPRISE_COLORS['bg']};
                border: 2px solid {ENTERPRISE_COLORS['border']};
                border-radius: 10px;
            }}
            QFrame:hover {{
                border-color: {ENTERPRISE_COLORS['primary']}60;
            }}
        """)
        sl = QHBoxLayout(search_container)
        sl.setContentsMargins(16, 2, 16, 2)
        sl.setSpacing(10)

        search_icon = QLabel("🔍")
        search_icon.setStyleSheet(f"font-size: 14pt; background: transparent; color: {ENTERPRISE_COLORS['text_muted']};")
        sl.addWidget(search_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name, mobile, email, or address...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMinimumWidth(380)
        self.search_input.setMaximumHeight(42)
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(200)
        self._search_timer.timeout.connect(self.load_customers)
        self.search_input.textChanged.connect(lambda: self._search_timer.start())
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent; border: none;
                color: {ENTERPRISE_COLORS['text']};
                font-size: 10.5pt;
                padding: 0px;
                font-family: {FONT_FAMILY};
            }}
            QLineEdit::placeholder {{
                color: {ENTERPRISE_COLORS['text_muted']};
                font-style: normal;
            }}
        """)
        sl.addWidget(self.search_input)
        cl.addWidget(search_container)

        self.customer_filter_combo = QComboBox()
        self.customer_filter_combo.addItems(["All Customers", "Pending Balance Only", "Active AMC Only"])
        self.customer_filter_combo.setMinimumHeight(42)
        self.customer_filter_combo.setMinimumWidth(180)
        self.customer_filter_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.customer_filter_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {ENTERPRISE_COLORS['bg']};
                color: {ENTERPRISE_COLORS['text']};
                border: 2px solid {ENTERPRISE_COLORS['border']};
                border-radius: 10px;
                padding: 6px 32px 6px 14px;
                font-size: 9.5pt;
                font-weight: 600;
                font-family: {FONT_FAMILY};
            }}
            QComboBox:hover {{
                border-color: {ENTERPRISE_COLORS['primary']}60;
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
            QComboBox QAbstractItemView {{
                background-color: {ENTERPRISE_COLORS['card']};
                color: {ENTERPRISE_COLORS['text']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                selection-background-color: {ENTERPRISE_COLORS['primary_light']};
                selection-color: {ENTERPRISE_COLORS['primary']};
                padding: 6px;
            }}
        """)
        self.customer_filter_combo.currentIndexChanged.connect(self.load_customers)
        cl.addWidget(self.customer_filter_combo)

        cl.addStretch()

        add_btn = QPushButton("  ➕ Add Customer")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self.add_customer)
        add_btn.setMinimumHeight(42)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #059669, stop:1 #047857);
                color: #fff; border: none; border-radius: 10px;
                padding: 10px 24px; font-weight: 600; font-size: 10pt;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #10b981, stop:1 #059669);
            }}
            QPushButton:pressed {{
                background: #047857;
            }}
        """)
        cl.addWidget(add_btn)

        export_btn = QPushButton("  📤 Export")
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.clicked.connect(self.export_customers)
        export_btn.setMinimumHeight(42)
        export_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {ENTERPRISE_COLORS['primary']};
                border: 2px solid {ENTERPRISE_COLORS['primary']}40;
                border-radius: 10px;
                padding: 10px 22px;
                font-weight: 600; font-size: 10pt;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['primary_light']};
                border: 2px solid {ENTERPRISE_COLORS['primary']};
            }}
            QPushButton:pressed {{
                background-color: {ENTERPRISE_COLORS['primary']}20;
            }}
        """)
        cl.addWidget(export_btn)

        layout.addWidget(control_frame)

    def _create_kpi_cards(self, layout):
        cards_frame = QFrame()
        cards_frame.setStyleSheet("background: transparent; border: none;")

        cards_layout = QHBoxLayout(cards_frame)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(16)

        kpi_data = [
            ('total_customers', 'Total Customers', '0', '👥', ENTERPRISE_COLORS['primary']),
            ('total_services', 'Total Services', '0', '🔧', ENTERPRISE_COLORS['success']),
            ('total_revenue', 'Total Revenue', '₹0', '💰', ENTERPRISE_COLORS['warning']),
            ('total_pending', 'Pending Amount', '₹0', '📋', ENTERPRISE_COLORS['danger']),
        ]

        self.cust_summary_labels = {}
        for key, label, default, icon, color in kpi_data:
            card = StatCard(label, default, icon, color)
            cards_layout.addWidget(card)
            self.cust_summary_labels[key] = card

        layout.addWidget(cards_frame)

    def _update_summary_bar(self):
        total = len(self.customer_list)
        svc = sum(c['total_services'] for c in self.customer_list)
        rev = sum(float(c.get('total_amount') or 0) for c in self.customer_list)
        pen = sum(float(c.get('pending_amount') or 0) for c in self.customer_list)

        if hasattr(self, 'cust_summary_labels'):
            self.cust_summary_labels['total_customers'].update_value(str(total))
            self.cust_summary_labels['total_services'].update_value(str(svc))
            self.cust_summary_labels['total_revenue'].update_value(f'₹{rev:,.0f}')
            self.cust_summary_labels['total_pending'].update_value(f'₹{pen:,.0f}')

    def _create_content(self, layout):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(8)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {ENTERPRISE_COLORS['border']};
                border-radius: 4px;
                margin: 8px 0px;
            }}
            QSplitter::handle:hover {{
                background-color: {ENTERPRISE_COLORS['primary']}60;
            }}
        """)

        left_pane = self._create_customer_list()
        splitter.addWidget(left_pane)

        right_pane = self._create_customer_details()
        splitter.addWidget(right_pane)

        splitter.setStretchFactor(0, 65)
        splitter.setStretchFactor(1, 35)
        splitter.setSizes([680, 380])

        layout.addWidget(splitter, 1)

    def _create_customer_list(self):
        pane = EnterpriseCard()
        pane.setStyleSheet(f"""
            QFrame {{
                background-color: {ENTERPRISE_COLORS['card']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 14px;
            }}
        """)

        layout = QVBoxLayout(pane)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(16)

        header_row = QHBoxLayout()
        header_row.setSpacing(12)
        hdr_icon = QFrame()
        hdr_icon.setFixedSize(36, 36)
        hdr_icon.setStyleSheet(f"""
            QFrame {{
                background-color: {ENTERPRISE_COLORS['primary_light']};
                border: 1px solid {ENTERPRISE_COLORS['primary_border']};
                border-radius: 10px;
            }}
        """)
        hi_l = QVBoxLayout(hdr_icon)
        hi_l.setContentsMargins(0, 0, 0, 0)
        hi_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hi_lbl = QLabel("📋")
        hi_lbl.setStyleSheet("font-size: 14pt; background: transparent;")
        hi_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hi_l.addWidget(hi_lbl)
        header_row.addWidget(hdr_icon)

        hdr_label = QLabel("All Customers")
        hdr_label.setStyleSheet(f"""
            font-size: 16pt; font-weight: 700;
            color: {ENTERPRISE_COLORS['text']};
            letter-spacing: -0.3px;
            background: transparent;
            font-family: {FONT_FAMILY};
        """)
        header_row.addWidget(hdr_label)

        count_badge = QFrame()
        count_badge.setFixedSize(32, 32)
        count_badge.setStyleSheet(f"""
            QFrame {{
                background-color: {ENTERPRISE_COLORS['primary_light']};
                border-radius: 16px;
                border: 1px solid {ENTERPRISE_COLORS['primary_border']};
            }}
        """)
        bl = QVBoxLayout(count_badge)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label = QLabel("0")
        self.count_label.setStyleSheet(f"""
            font-size: 10pt; font-weight: 700;
            color: {ENTERPRISE_COLORS['primary']};
            background: transparent;
            font-family: {FONT_FAMILY};
        """)
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bl.addWidget(self.count_label)
        header_row.addWidget(count_badge)
        header_row.addStretch()
        layout.addLayout(header_row)

        self.customer_table = QTableWidget()
        self.customer_table.setColumnCount(6)
        self.customer_table.setHorizontalHeaderLabels([
            'Customer Name', 'Mobile', 'Services', 'Total (₹)', 'Pending (₹)', 'Last Visit'
        ])

        h = self.customer_table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 6):
            h.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        self.customer_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.customer_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.customer_table.setAlternatingRowColors(True)
        self.customer_table.verticalHeader().setVisible(False)
        self.customer_table.itemSelectionChanged.connect(self.on_customer_select)
        self.customer_table.cellDoubleClicked.connect(self.on_customer_double_click)
        self.customer_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customer_table.customContextMenuRequested.connect(self._on_customer_context_menu)

        self._style_table(self.customer_table)

        layout.addWidget(self.customer_table)
        return pane

    def _create_customer_details(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setObjectName("detailsScroll")
        scroll.setStyleSheet(f"""
            QScrollArea#detailsScroll {{
                background-color: {ENTERPRISE_COLORS['card']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 14px;
            }}
            QScrollBar:vertical {{
                background-color: {ENTERPRISE_COLORS['bg']}; width: 6px;
                border-radius: 3px; margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {ENTERPRISE_COLORS['border']};
                border-radius: 3px; min-height: 30px; margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {ENTERPRISE_COLORS['text_muted']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        cl = QVBoxLayout(content_widget)
        cl.setContentsMargins(24, 24, 24, 24)
        cl.setSpacing(0)

        # Profile Header
        avatar_frame = QFrame()
        avatar_frame.setFixedSize(80, 80)
        avatar_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {ENTERPRISE_COLORS['primary']}, stop:1 #1d4ed8);
                border-radius: 24px;
            }}
        """)
        al = QVBoxLayout(avatar_frame)
        al.setContentsMargins(0, 0, 0, 0)
        al.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_label = QLabel("?")
        self.avatar_label.setStyleSheet(f"""
            font-size: 32pt; font-weight: 700;
            color: #ffffff; background: transparent;
        """)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        al.addWidget(self.avatar_label)

        profile_top = QHBoxLayout()
        profile_top.addWidget(avatar_frame)
        profile_top.addSpacing(18)

        profile_info = QVBoxLayout()
        profile_info.setSpacing(6)

        name_status_row = QHBoxLayout()
        name_status_row.setSpacing(12)
        self.customer_name_label = QLabel("Select a Customer")
        self.customer_name_label.setStyleSheet(f"""
            font-size: 20pt; font-weight: 700;
            color: {ENTERPRISE_COLORS['text']};
            letter-spacing: -0.3px;
            background: transparent;
            font-family: {FONT_FAMILY};
        """)
        name_status_row.addWidget(self.customer_name_label)
        self.status_badge = StatusBadge("Active", "active")
        self.status_badge.hide()
        name_status_row.addWidget(self.status_badge)
        name_status_row.addStretch()
        profile_info.addLayout(name_status_row)

        hint = QLabel("Click a customer from the list to view details")
        hint.setStyleSheet(f"""
            font-size: 10pt;
            color: {ENTERPRISE_COLORS['text_muted']};
            background: transparent;
            font-family: {FONT_FAMILY};
        """)
        profile_info.addWidget(hint)
        profile_top.addLayout(profile_info)
        profile_top.addStretch()
        cl.addLayout(profile_top)
        cl.addSpacing(28)

        # Contact Section
        cl.addWidget(self._make_section_divider("Contact Information"))
        cl.addSpacing(14)

        self.customer_mobile_label = QLabel("---")
        self.customer_email_label = QLabel("---")
        self.customer_address_label = QLabel("---")
        contact_data = [
            ("📱", "Mobile Number", self.customer_mobile_label),
            ("✉️", "Email Address", self.customer_email_label),
            ("📍", "Address", self.customer_address_label),
        ]
        self.customer_address_label.setWordWrap(True)

        for icon, label, value_label in contact_data:
            row = QHBoxLayout()
            row.setSpacing(14)
            ic = QFrame()
            ic.setFixedSize(36, 36)
            ic.setStyleSheet(f"""
                QFrame {{
                    background-color: {ENTERPRISE_COLORS['primary_light']};
                    border-radius: 10px;
                }}
            """)
            il = QVBoxLayout(ic)
            il.setContentsMargins(0, 0, 0, 0)
            il.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ibl = QLabel(icon)
            ibl.setStyleSheet("font-size: 13pt; background: transparent;")
            ibl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            il.addWidget(ibl)
            row.addWidget(ic)
            tc = QVBoxLayout()
            tc.setSpacing(2)
            tl = QLabel(label.upper())
            tl.setStyleSheet(f"""
                font-size: 8pt;
                color: {ENTERPRISE_COLORS['text_muted']};
                font-weight: 600;
                letter-spacing: 0.8px;
                background: transparent;
                font-family: {FONT_FAMILY};
            """)
            tc.addWidget(tl)
            value_label.setStyleSheet(f"""
                font-size: 11pt;
                color: {ENTERPRISE_COLORS['text']};
                background: transparent;
                font-family: {FONT_FAMILY};
            """)
            tc.addWidget(value_label)
            row.addLayout(tc)
            row.addStretch()
            cl.addLayout(row)
            cl.addSpacing(10)

        cl.addSpacing(24)

        # Statistics Section (2x2 grid)
        cl.addWidget(self._make_section_divider("Customer Statistics"))
        cl.addSpacing(14)

        stats_grid = QFrame()
        stats_grid.setStyleSheet("background: transparent; border: none;")
        sgl = QGridLayout(stats_grid)
        sgl.setContentsMargins(0, 0, 0, 0)
        sgl.setSpacing(10)

        stat_items = [
            ("Total Invoices", "0", "📄", ENTERPRISE_COLORS['primary']),
            ("Total Revenue", "₹0", "💰", ENTERPRISE_COLORS['warning']),
            ("Pending Amount", "₹0", "📋", ENTERPRISE_COLORS['danger']),
            ("Last Service", "---", "🔧", ENTERPRISE_COLORS['success']),
        ]
        self.stat_value_labels = []
        for idx, (label, val, icon, color) in enumerate(stat_items):
            sc = QFrame()
            sc.setStyleSheet(f"""
                QFrame {{
                    background-color: {ENTERPRISE_COLORS['card']};
                    border: 1px solid {ENTERPRISE_COLORS['border']};
                    border-radius: 10px;
                }}
                QFrame:hover {{
                    background-color: {color}08;
                    border: 1px solid {color}30;
                }}
            """)
            scl = QHBoxLayout(sc)
            scl.setContentsMargins(12, 10, 12, 10)
            scl.setSpacing(10)
            sif = QFrame()
            sif.setFixedSize(34, 34)
            sif.setStyleSheet(f"""
                QFrame {{
                    background-color: {color}12;
                    border-radius: 10px;
                    border: 1px solid {color}25;
                }}
            """)
            sil = QVBoxLayout(sif)
            sil.setContentsMargins(0, 0, 0, 0)
            sil.setAlignment(Qt.AlignmentFlag.AlignCenter)
            si_lbl = QLabel(icon)
            si_lbl.setStyleSheet(f"font-size: 13pt; background: transparent; color: {color};")
            si_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sil.addWidget(si_lbl)
            scl.addWidget(sif)
            svl = QVBoxLayout()
            svl.setSpacing(2)
            vl = QLabel(val)
            vl.setStyleSheet(f"""
                font-size: 16pt; font-weight: 700;
                color: {color}; background: transparent;
                font-family: {FONT_FAMILY};
            """)
            svl.addWidget(vl)
            self.stat_value_labels.append(vl)
            ll = QLabel(label)
            ll.setStyleSheet(f"""
                font-size: 8pt;
                color: {ENTERPRISE_COLORS['text_muted']};
                font-weight: 600;
                background: transparent;
                font-family: {FONT_FAMILY};
            """)
            svl.addWidget(ll)
            scl.addLayout(svl)
            scl.addStretch()
            sgl.addWidget(sc, idx // 2, idx % 2)

        cl.addWidget(stats_grid)
        cl.addSpacing(24)

        # Installed AC Equipment Profile Section
        cl.addWidget(self._make_section_divider("Installed AC Equipment Profile"))
        cl.addSpacing(14)

        self.equipment_container = QFrame()
        self.installed_equipment_card = self.equipment_container
        self.equipment_container.setStyleSheet(f"""
            QFrame {{
                background-color: {ENTERPRISE_COLORS['bg']};
                border: 1px dashed {ENTERPRISE_COLORS['border']};
                border-radius: 10px;
            }}
        """)
        self.equipment_layout = QVBoxLayout(self.equipment_container)
        self.equipment_layout.setContentsMargins(14, 12, 14, 12)
        self.equipment_layout.setSpacing(8)

        self.no_equipment_lbl = QLabel("❄️ No registered AC units on file")
        self.equipment_details_label = self.no_equipment_lbl
        self.no_equipment_lbl.setStyleSheet(f"""
            font-size: 9pt; color: {ENTERPRISE_COLORS['text_muted']};
            font-family: {FONT_FAMILY};
        """)
        self.equipment_layout.addWidget(self.no_equipment_lbl)
        cl.addWidget(self.equipment_container)
        cl.addSpacing(24)

        # Quick Actions
        cl.addWidget(self._make_section_divider("Quick Actions"))
        cl.addSpacing(14)

        btn_frame = QFrame()
        btn_frame.setStyleSheet("background: transparent; border: none;")
        bl = QHBoxLayout(btn_frame)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(10)

        actions = [
            ("  💬  WhatsApp", "#16a34a", self._whatsapp_customer, False),
            ("  ✏️  Edit", ENTERPRISE_COLORS['primary'], self.edit_customer, False),
            ("  📒  Ledger", ENTERPRISE_COLORS['info'], self._show_ledger, True),
            ("  ➕  Invoice", ENTERPRISE_COLORS['success'], self.new_invoice_for_customer, False),
            ("  🗑️  Delete", ENTERPRISE_COLORS['danger'], self.delete_customer, True),
        ]

        for text, color, callback, is_outline in actions:
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(36)
            btn.clicked.connect(callback)
            if is_outline:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {color};
                        border: 1.5px solid {color}50;
                        border-radius: 8px;
                        padding: 8px 14px;
                        font-weight: 600;
                        font-size: 9pt;
                        font-family: {FONT_FAMILY};
                    }}
                    QPushButton:hover {{
                        background-color: {color}12;
                        border: 1.5px solid {color};
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color};
                        color: #fff;
                        border: none;
                        border-radius: 8px;
                        padding: 8px 16px;
                        font-weight: 600;
                        font-size: 9pt;
                        font-family: {FONT_FAMILY};
                    }}
                    QPushButton:hover {{
                        background-color: {color}dd;
                    }}
                """)
            bl.addWidget(btn)

        bl.addStretch()
        cl.addWidget(btn_frame)
        cl.addSpacing(24)

        # Service History
        cl.addWidget(self._make_section_divider("Service History"))
        cl.addSpacing(14)

        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(7)
        self.invoices_table.setHorizontalHeaderLabels([
            'Invoice', 'Date', 'Amount', 'Advance', 'Balance', 'Status', 'Actions'
        ])

        hdr = self.invoices_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 7):
            hdr.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        self.invoices_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.invoices_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.invoices_table.setAlternatingRowColors(True)
        self.invoices_table.verticalHeader().setVisible(False)
        self.invoices_table.setMinimumHeight(160)
        self.invoices_table.setMaximumHeight(280)
        self.invoices_table.cellDoubleClicked.connect(self.on_invoice_double_click)

        self._style_table(self.invoices_table)

        cl.addWidget(self.invoices_table)
        cl.addSpacing(24)

        # Activity Timeline
        cl.addWidget(self._make_section_divider("Activity Timeline"))
        cl.addSpacing(14)

        self.timeline_widget = QFrame()
        self.timeline_widget.setStyleSheet(f"""
            QFrame {{
                background-color: {ENTERPRISE_COLORS['bg']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 12px;
            }}
        """)
        tl = QVBoxLayout(self.timeline_widget)
        tl.setContentsMargins(16, 14, 16, 14)
        tl.setSpacing(0)

        self.timeline_scroll = QScrollArea()
        self.timeline_scroll.setWidgetResizable(True)
        self.timeline_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.timeline_scroll.setMinimumHeight(200)
        self.timeline_scroll.setMaximumHeight(340)
        self.timeline_scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{
                background: transparent; width: 5px;
                border-radius: 2px; margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {ENTERPRISE_COLORS['border']};
                border-radius: 2px; min-height: 20px; margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {ENTERPRISE_COLORS['text_muted']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

        self.timeline_content = QWidget()
        self.timeline_content.setStyleSheet("background: transparent;")
        self.timeline_content_layout = QVBoxLayout(self.timeline_content)
        self.timeline_content_layout.setSpacing(0)
        self.timeline_content_layout.setContentsMargins(0, 0, 0, 0)

        no_data = QLabel("Select a customer to view activity timeline")
        no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_data.setStyleSheet(f"""
            color: {ENTERPRISE_COLORS['text_muted']};
            padding: 40px;
            font-size: 10.5pt;
            background: transparent;
            font-family: {FONT_FAMILY};
        """)
        self.timeline_content_layout.addWidget(no_data)
        self.timeline_content_layout.addStretch()

        self.timeline_scroll.setWidget(self.timeline_content)
        tl.addWidget(self.timeline_scroll)
        cl.addWidget(self.timeline_widget)
        cl.addStretch()

        scroll.setWidget(content_widget)
        return scroll

    def _make_section_divider(self, title):
        frame = QFrame()
        frame.setStyleSheet("background: transparent; border: none;")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        label = QLabel(title.upper())
        label.setStyleSheet(f"""
            font-size: 8.5pt; font-weight: 700;
            color: {ENTERPRISE_COLORS['text_muted']};
            letter-spacing: 1.5px;
            background: transparent;
            font-family: {FONT_FAMILY};
        """)
        layout.addWidget(label)
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"""
            background-color: {ENTERPRISE_COLORS['divider']};
            border: none;
        """)
        layout.addWidget(line, 1)
        return frame

    def load_customers(self):
        self.run_in_thread(self._load_customers_thread, self._update_customer_list)

    def _load_customers_thread(self):
        from database.db_connection import DatabaseContext
        search_term = self.search_input.text().strip()
        filter_mode = "All Customers"
        if hasattr(self, 'customer_filter_combo'):
            filter_mode = self.customer_filter_combo.currentText()

        with DatabaseContext() as db:
            query = """
            SELECT c.id, c.name, c.mobile, c.email, c.address, c.landmark,
                DATE(c.created_at) as created_date,
                COUNT(i.id) as total_services,
                COALESCE(SUM(i.total_amount), 0) as total_amount,
                COALESCE(SUM(i.balance_amount), 0) as pending_amount,
                MAX(DATE(i.created_at)) as last_visit
            FROM customers c
            LEFT JOIN invoices i ON i.customer_id = c.id AND i.is_active = TRUE
            WHERE c.is_active = TRUE
            """
            params = []
            if search_term:
                query += " AND (c.name LIKE %s OR c.mobile LIKE %s OR c.email LIKE %s OR c.address LIKE %s)"
                params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])

            if filter_mode == "Active AMC Only":
                query += " AND c.id IN (SELECT customer_id FROM amc_contracts WHERE is_active = 1 AND end_date >= DATE('now'))"

            query += """
            GROUP BY c.id, c.name, c.mobile, c.email, c.address, c.landmark, c.created_at
            """

            if filter_mode == "Pending Balance Only":
                query += " HAVING pending_amount > 0"

            query += " ORDER BY c.name"
            return db.execute_query(query, params, fetch_all=True)

    def _update_customer_list(self, customers):
        self.customer_list = customers or []
        self._update_summary_bar()
        self.count_label.setText(str(len(self.customer_list)))

        self.customer_table.setUpdatesEnabled(False)
        try:
            self.customer_table.setRowCount(len(self.customer_list))
            for row, customer in enumerate(self.customer_list):
                last_visit = Formatters.format_date(customer.get('last_visit')) or 'Never'

                name_item = QTableWidgetItem(customer['name'])
                name_item.setData(Qt.ItemDataRole.UserRole, customer['id'])
                f = QFont()
                f.setWeight(QFont.Weight.DemiBold)
                f.setFamily('Inter')
                name_item.setFont(f)
                self.customer_table.setItem(row, 0, name_item)
                self.customer_table.setItem(row, 1, QTableWidgetItem(customer['mobile']))

                svc_item = QTableWidgetItem(str(customer['total_services']))
                svc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.customer_table.setItem(row, 2, svc_item)

                total_item = QTableWidgetItem(f"₹{customer['total_amount']:,.2f}")
                total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.customer_table.setItem(row, 3, total_item)

                pending_item = QTableWidgetItem(f"₹{customer['pending_amount']:,.2f}")
                pending_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                pending_item.setForeground(QColor(ENTERPRISE_COLORS['danger'] if customer['pending_amount'] > 0 else ENTERPRISE_COLORS['success']))
                self.customer_table.setItem(row, 4, pending_item)

                visit_item = QTableWidgetItem(last_visit)
                visit_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.customer_table.setItem(row, 5, visit_item)
        finally:
            self.customer_table.setUpdatesEnabled(True)

    def on_customer_select(self):
        selected_rows = self.customer_table.selectedItems()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        customer = self.customer_list[row]
        self.selected_customer_id = customer['id']
        self.load_customer_details(customer['id'])

    def load_customer_details(self, customer_id):
        self.run_in_thread(
            self._load_customer_details_thread,
            self._update_customer_details,
            None, customer_id
        )

    def _load_customer_details_thread(self, customer_id):
        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            query = """
            SELECT c.*,
                (SELECT COUNT(*) FROM invoices i WHERE i.customer_id = c.id AND i.is_active = TRUE) as total_services,
                (SELECT COALESCE(SUM(i.total_amount), 0) FROM invoices i WHERE i.customer_id = c.id AND i.is_active = TRUE) as total_amount,
                (SELECT COALESCE(SUM(i.balance_amount), 0) FROM invoices i WHERE i.customer_id = c.id AND i.is_active = TRUE) as pending_amount,
                (SELECT MAX(DATE(i.created_at)) FROM invoices i WHERE i.customer_id = c.id AND i.is_active = TRUE) as last_service
            FROM customers c WHERE c.id = %s
            """
            customer = db.execute_query(query, (customer_id,), fetch_one=True)

            query = """
            SELECT i.id, i.invoice_number, DATE(i.created_at) as invoice_date,
                i.total_amount, i.advance_payment, i.balance_amount,
                i.payment_status, i.payment_mode
            FROM invoices i WHERE i.customer_id = %s AND i.is_active = TRUE
            ORDER BY i.created_at DESC LIMIT 20
            """
            invoices = db.execute_query(query, (customer_id,), fetch_all=True)

            timeline_query = """
            SELECT 'invoice' as type, i.created_at as event_date,
                   CONCAT('Invoice #', i.invoice_number, ' - ₹', i.total_amount) as event_desc,
                   i.created_at as sort_date
            FROM invoices i WHERE i.customer_id = %s AND i.is_active = TRUE
            UNION ALL
            SELECT 'amc' as type, a.created_at as event_date,
                   CONCAT('AMC ', a.contract_type, ' created - ₹', a.contract_amount) as event_desc,
                   a.created_at as sort_date
            FROM amc_contracts a WHERE a.customer_id = %s AND a.is_active = TRUE
            ORDER BY sort_date DESC LIMIT 50
            """
            timeline = db.execute_query(timeline_query, (customer_id, customer_id), fetch_all=True)

            equip_query = """
            SELECT DISTINCT
                COALESCE(b.brand_name, 'AC Unit') as brand,
                COALESCE(i.ac_type, 'Split') as ac_type,
                COALESCE(i.ton_capacity, '1.5 Ton') as capacity,
                COALESCE(i.ac_inverter, 'Inverter') as inverter,
                MAX(DATE(i.created_at)) as last_serviced
            FROM invoices i
            LEFT JOIN ac_brands b ON b.id = i.ac_brand_id
            WHERE i.customer_id = %s AND i.is_active = TRUE AND (i.ac_type != '' OR i.ac_brand_id IS NOT NULL)
            GROUP BY b.brand_name, i.ac_type, i.ton_capacity, i.ac_inverter
            ORDER BY last_serviced DESC LIMIT 5
            """
            equipment = db.execute_query(equip_query, (customer_id,), fetch_all=True) or []
            if not equipment:
                amc_equip_query = """
                SELECT
                    COALESCE(u.ac_brand, 'AC Unit') as brand,
                    COALESCE(u.ac_type, 'Split') as ac_type,
                    COALESCE(u.capacity_tonnage, '1.5 Ton') as capacity,
                    'Standard' as inverter,
                    DATE(a.start_date) as last_serviced
                FROM amc_units u
                JOIN amc_contracts a ON a.id = u.contract_id
                WHERE a.customer_id = %s AND a.is_active = TRUE LIMIT 5
                """
                equipment = db.execute_query(amc_equip_query, (customer_id,), fetch_all=True) or []

            return {'customer': customer, 'invoices': invoices, 'timeline': timeline, 'equipment': equipment}

    def _update_customer_details(self, data):
        customer = data['customer']
        invoices = data['invoices']
        timeline = data.get('timeline', [])
        equipment = data.get('equipment', [])
        if not customer:
            return

        name = customer['name']
        initial = name[0].upper() if name else '?'
        self.avatar_label.setText(initial)
        self.customer_name_label.setText(name)

        if customer.get('total_amount', 0) > 0:
            self.status_badge.setText("Active")
            self.status_badge.show()
        else:
            self.status_badge.hide()

        self.customer_mobile_label.setText(customer['mobile'] or '---')
        self.customer_email_label.setText(customer['email'] if customer['email'] else "No email on record")

        address_parts = []
        if customer['address']:
            address_parts.append(customer['address'])
        if customer['landmark']:
            address_parts.append(f"Landmark: {customer['landmark']}")
        self.customer_address_label.setText(" | ".join(address_parts) if address_parts else "No address on record")

        self._update_stat_widget(0, str(customer['total_services']))
        self._update_stat_widget(1, f"₹{customer['total_amount']:,.2f}")
        self._update_stat_widget(2, f"₹{customer['pending_amount']:,.2f}")
        self._update_stat_widget(3, Formatters.format_date(customer.get('last_service')) or "Never")

        # Update AC Equipment profile
        if hasattr(self, 'equipment_layout'):
            while self.equipment_layout.count():
                child = self.equipment_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            if not equipment:
                no_eq = QLabel("❄️ No registered AC units on file (added automatically on invoice/AMC)")
                no_eq.setStyleSheet(f"font-size: 8.5pt; color: {ENTERPRISE_COLORS['text_muted']}; font-family: {FONT_FAMILY};")
                self.equipment_layout.addWidget(no_eq)
            else:
                for eq in equipment:
                    row_frame = QFrame()
                    row_frame.setStyleSheet(f"""
                        QFrame {{
                            background-color: {ENTERPRISE_COLORS['card']};
                            border: 1px solid {ENTERPRISE_COLORS['border']};
                            border-radius: 8px;
                        }}
                    """)
                    rl = QHBoxLayout(row_frame)
                    rl.setContentsMargins(10, 8, 10, 8)
                    rl.setSpacing(10)

                    ic = QLabel("❄️")
                    ic.setStyleSheet("font-size: 12pt; background: transparent;")
                    rl.addWidget(ic)

                    info_col = QVBoxLayout()
                    info_col.setSpacing(2)
                    brand_cap = f"{eq.get('brand', 'AC')} • {eq.get('capacity', '1.5 Ton')} {eq.get('ac_type', 'Split')}"
                    eq_name = QLabel(brand_cap)
                    eq_name.setStyleSheet(f"font-size: 9.5pt; font-weight: 600; color: {ENTERPRISE_COLORS['text']}; font-family: {FONT_FAMILY}; background: transparent;")
                    info_col.addWidget(eq_name)

                    sub_text = f"Tech: {eq.get('inverter', 'Standard')} | Last Serviced: {Formatters.format_date(eq.get('last_serviced')) or 'Recent'}"
                    sub = QLabel(sub_text)
                    sub.setStyleSheet(f"font-size: 8pt; color: {ENTERPRISE_COLORS['text_muted']}; font-family: {FONT_FAMILY}; background: transparent;")
                    info_col.addWidget(sub)
                    rl.addLayout(info_col)
                    rl.addStretch()

                    badge = QLabel("ACTIVE UNIT")
                    badge.setStyleSheet(f"""
                        font-size: 7.5pt; font-weight: 700;
                        color: {ENTERPRISE_COLORS['info']};
                        background-color: {ENTERPRISE_COLORS['info_light']};
                        border: 1px solid {ENTERPRISE_COLORS['info_border']};
                        border-radius: 4px; padding: 2px 6px;
                    """)
                    rl.addWidget(badge)
                    self.equipment_layout.addWidget(row_frame)

        self._render_timeline(timeline)

        self.invoices_table.setRowCount(0)
        for inv in invoices:
            row = self.invoices_table.rowCount()
            self.invoices_table.insertRow(row)
            self.invoices_table.setItem(row, 0, QTableWidgetItem(inv['invoice_number']))

            di = QTableWidgetItem(Formatters.format_date(inv.get('invoice_date')))
            di.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.invoices_table.setItem(row, 1, di)

            for col, key in [(2, 'total_amount'), (3, 'advance_payment'), (4, 'balance_amount')]:
                item = QTableWidgetItem(f"₹{inv[key]:,.2f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.invoices_table.setItem(row, col, item)

            bal = self.invoices_table.item(row, 4)
            bal.setForeground(QColor(ENTERPRISE_COLORS['danger'] if inv['balance_amount'] > 0 else ENTERPRISE_COLORS['success']))

            status = inv['payment_status']
            si = QTableWidgetItem(status)
            si.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.invoices_table.setItem(row, 5, si)
            ai = QTableWidgetItem("👁  ⬇  ✏️")
            ai.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.invoices_table.setItem(row, 6, ai)

    def _update_stat_widget(self, index, value):
        if hasattr(self, 'stat_value_labels') and index < len(self.stat_value_labels):
            self.stat_value_labels[index].setText(value)

    def _render_timeline(self, timeline):
        while self.timeline_content_layout.count():
            item = self.timeline_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not timeline:
            no_data = QLabel("No activity recorded for this customer")
            no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_data.setStyleSheet(f"""
                color: {ENTERPRISE_COLORS['text_muted']};
                padding: 40px;
                font-size: 10.5pt;
                background: transparent;
                font-family: {FONT_FAMILY};
            """)
            self.timeline_content_layout.addWidget(no_data)
            self.timeline_content_layout.addStretch()
            return

        for idx, event in enumerate(timeline):
            event_type = event['type']
            date_str = Formatters.format_date(event.get('event_date'), '%d %b %Y')
            desc = event['event_desc'] or ''
            node = TimelineNode(event_type, date_str, desc, idx == 0, idx == len(timeline) - 1)
            self.timeline_content_layout.addWidget(node)

        self.timeline_content_layout.addStretch()

    def on_customer_double_click(self, row, col):
        item = self.customer_table.item(row, 0)
        if item:
            self.load_customer_details(item.data(Qt.ItemDataRole.UserRole))

    def on_invoice_double_click(self, row, col):
        menu = QMenu(self)
        menu.addAction("View Invoice", lambda: self.view_invoice(row))
        menu.addAction("Download PDF", lambda: self.download_invoice_pdf(row))
        menu.addAction("Edit Invoice", lambda: self.edit_invoice(row))
        item = self.invoices_table.item(row, col)
        if item:
            rect = self.invoices_table.visualItemRect(item)
            menu.exec(self.invoices_table.viewport().mapToGlobal(rect.topLeft()))

    def view_invoice(self, row):
        self.show_success_message("View invoice feature - coming soon")

    def download_invoice_pdf(self, row):
        self.show_success_message("Download PDF feature - coming soon")

    def edit_invoice(self, row):
        self.show_success_message("Edit invoice feature - coming soon")

    def _whatsapp_customer(self):
        """Open WhatsApp web / app with customized message for selected customer"""
        if not self.selected_customer_id:
            self.show_warning_message("Please select a customer first")
            return
        mobile = self.customer_mobile_label.text().strip()
        clean_phone = "".join(filter(str.isdigit, mobile))
        if not clean_phone or len(clean_phone) < 10:
            self.show_warning_message("Customer does not have a valid mobile number on file")
            return
        if len(clean_phone) == 10:
            clean_phone = "91" + clean_phone

        cust_name = self.customer_name_label.text()
        from utils.app_settings import get_setting
        shop_name = get_setting("company_name", "AC Care Services")

        pending_str = self.stat_value_labels[2].text() if len(self.stat_value_labels) > 2 else "₹0"
        import urllib.parse
        if "₹0" not in pending_str and pending_str != "₹0.00":
            msg = f"Hello {cust_name},\nThis is a friendly reminder from {shop_name} regarding your pending service balance of {pending_str}. Please settle the payment at your convenience.\nThank you!"
        else:
            msg = f"Hello {cust_name},\nGreetings from {shop_name}! We hope your AC cooling is performing smoothly. Feel free to contact us whenever you need routine filter maintenance or service.\nThank you!"

        url = f"https://wa.me/{clean_phone}?text={urllib.parse.quote(msg)}"
        QDesktopServices.openUrl(QUrl(url))

    def _show_ledger(self):
        if not self.selected_customer_id:
            self.show_warning_message("Please select a customer")
            return
        from views.customer_ledger_dialog import CustomerLedgerDialog
        dialog = CustomerLedgerDialog(self.selected_customer_id, self)
        dialog.exec()

    def show_customer_detail(self, customer_id):
        self.selected_customer_id = customer_id
        self.load_customer_details(customer_id)
        for row in range(self.customer_table.rowCount()):
            item = self.customer_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == customer_id:
                self.customer_table.selectRow(row)
                break

    def add_customer(self):
        dialog = AddCustomerDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_customers()
            self.show_success_message("Customer added successfully")

    def edit_customer(self):
        if not self.selected_customer_id:
            self.show_warning_message("Please select a customer to edit")
            return
        dialog = EditCustomerDialog(self.selected_customer_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_customers()
            if self.selected_customer_id:
                self.load_customer_details(self.selected_customer_id)
            self.show_success_message("Customer updated successfully")

    def delete_customer(self):
        if not self.selected_customer_id:
            self.show_warning_message("Please select a customer to delete")
            return
        if self.show_question("Are you sure you want to delete this customer?"):
            from controllers.customer_controller import CustomerController
            from database.db_connection import DatabaseConnection
            db = DatabaseConnection()
            controller = CustomerController(db)
            controller.delete_customer(self.selected_customer_id)
            self.selected_customer_id = None
            self.load_customers()
            self.show_success_message("Customer deleted successfully")

    def new_invoice_for_customer(self):
        if not self.selected_customer_id:
            self.show_warning_message("Please select a customer")
            return
        selected_rows = self.customer_table.selectedItems()
        customer_data = None
        if selected_rows:
            row = selected_rows[0].row()
            if row < len(self.customer_list):
                customer_data = self.customer_list[row]
        if not customer_data:
            for c in self.customer_list:
                if c.get('id') == self.selected_customer_id:
                    customer_data = c
                    break

        self._open_invoice_for_customer(customer_data)

    def _open_invoice_for_customer(self, cust):
        """Switch to Invoice View and pass pre-filled customer data"""
        parent = self.parent()
        while parent:
            if hasattr(parent, '_show_invoice'):
                parent._show_invoice(cust)
                return
            parent = parent.parent()

    def _on_customer_context_menu(self, pos):
        """Context menu for right clicking a customer row"""
        item = self.customer_table.itemAt(pos)
        if not item:
            return
        row = item.row()
        if row < 0 or row >= len(self.customer_list):
            return
        cust = self.customer_list[row]
        self.selected_customer_id = cust.get('id')
        self.customer_table.selectRow(row)

        menu = QMenu(self)
        inv_act = menu.addAction("➕  Create Invoice")
        inv_act.triggered.connect(lambda: self._open_invoice_for_customer(cust))
        edit_act = menu.addAction("✏️  Edit Customer")
        edit_act.triggered.connect(self.edit_customer)
        ledger_act = menu.addAction("📒  Customer Ledger")
        ledger_act.triggered.connect(self._show_ledger)
        menu.addSeparator()
        wa_act = menu.addAction("📱  Send WhatsApp Message")
        wa_act.triggered.connect(self.send_whatsapp_message)
        menu.exec(self.customer_table.viewport().mapToGlobal(pos))

    def send_whatsapp_message(self):
        try:
            from utils.whatsapp_helper import WhatsAppHelper
            if not self.selected_customer_id:
                self.show_warning_message("Please select a customer first")
                return
            from database.db_connection import DatabaseContext
            with DatabaseContext() as db:
                query = "SELECT * FROM customers WHERE id = %s"
                customer = db.execute_query(query, (self.selected_customer_id,), fetch_one=True)
            if not customer:
                self.show_warning_message("Customer not found")
                return
            customer_name = customer['name']
            customer_mobile = customer['mobile']
            if not customer_mobile:
                self.show_warning_message("Customer mobile number not available")
                return
            from PySide6.QtWidgets import QDialog as QD, QVBoxLayout as QVL, QPushButton as QPB, QLabel as QLBL
            dialog = QD(self)
            dialog.setWindowTitle("Select WhatsApp Message")
            dialog.setMinimumWidth(420)
            dialog.setStyleSheet(f"""
                QDialog {{
                    background-color: {ENTERPRISE_COLORS['card']};
                    border-radius: 14px;
                }}
            """)
            layout = QVL()
            layout.setContentsMargins(24, 24, 24, 24)
            layout.setSpacing(12)
            whatsapp_green = "#25D366"
            whatsapp_dark = "#128C7E"
            title = QLBL(f"📱 Send message to: {customer_name}")
            title.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {whatsapp_green};")
            layout.addWidget(title)
            subtitle = QLBL("Choose a message template:")
            subtitle.setStyleSheet(f"font-size: 11pt; color: {ENTERPRISE_COLORS['text_secondary']};")
            layout.addWidget(subtitle)
            templates = [
                ("🙏 Greeting", 'greeting'), ("✅ Service Confirmed", 'service_confirm'),
                ("💳 Payment Reminder", 'payment_reminder'), ("🌟 Thank You", 'thank_you'),
                ("⭐ Feedback Request", 'feedback_request'),
            ]
            for btn_text, template_key in templates:
                btn = QPB(btn_text)
                btn.setMinimumHeight(40)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {whatsapp_green}; color: white; border: none;
                        padding: 12px 18px; border-radius: 8px; font-weight: bold;
                        text-align: left; font-size: 10pt;
                    }}
                    QPushButton:hover {{ background-color: {whatsapp_dark}; }}
                """)
                btn.clicked.connect(lambda checked, key=template_key:
                                   self._send_template_and_close(dialog, key, customer_mobile, customer_name))
                layout.addWidget(btn)
            dialog.setLayout(layout)
            dialog.exec()
        except Exception as e:
            self.show_error_message(f"Error: {str(e)}")

    def _send_template_and_close(self, dialog, template_key, phone, name):
        try:
            from utils.whatsapp_helper import WhatsAppHelper
            data = {
                'phone': phone, 'name': name, 'service_type': get_setting('service_types', 'AC Service,Installation,Repair,Gas Refilling,AMC Visit,AC Rent Delivery,AC Rent Pickup,Other').split(',')[0],
                'location': 'Mumbai', 'amount': '0', 'invoice_number': 'INV-XXXX',
                'date': 'DD/MM/YYYY', 'expiry_date': 'DD/MM/YYYY',
            }
            success = WhatsAppHelper.send_template(template_key, **data)
            if success:
                self.show_success_message(f"✅ WhatsApp opened for '{template_key}' message")
            else:
                self.show_warning_message("Failed to open WhatsApp")
            dialog.accept()
        except Exception as e:
            self.show_error_message(f"Error: {str(e)}")

    def export_customers(self):
        if not self.customer_list:
            self.show_warning_message("No customer data to export.")
            return
        from utils.excel_helper import ExcelExporter
        from datetime import datetime
        rows = []
        total_services = total_amount = total_pending = 0
        for cust in self.customer_list:
            last_visit = Formatters.format_date(cust.get('last_visit')) or 'Never'
            svc = int(cust.get('total_services', 0) or 0)
            amt = float(cust.get('total_amount', 0) or 0)
            pen = float(cust.get('pending_amount', 0) or 0)
            rows.append([cust['name'], cust['mobile'], svc, amt, pen, last_visit])
            total_services += svc
            total_amount += amt
            total_pending += pen
        headers = ['Name', 'Mobile', 'Total Services', 'Total Amount', 'Pending Amount', 'Last Visit']
        number_cols = {3, 4, 5}
        top_n = rows[:15]
        charts_data = [{
            'type': 'bar', 'title': 'Top Customers by Revenue',
            'categories': [r[0][:20] for r in top_n],
            'values': [('Total Amount', [r[3] for r in top_n]), ('Pending', [r[4] for r in top_n])],
            'y_axis': 'Amount (₹)'
        }] if top_n else None
        wb = ExcelExporter.build_excel(
            sheet_title='Customers', title_text='Customer Report',
            subtitle_text=f'Total: {len(rows)} customers | Generated: {datetime.now().strftime("%d-%m-%Y %H:%M")}',
            headers=headers, rows=rows,
            total_row=['', '', total_services, total_amount, total_pending, ''],
            number_cols=number_cols,
            kpis=[('Total Customers', len(rows)), ('Total Services', total_services),
                  ('Total Revenue', total_amount), ('Pending Amount', total_pending),
                  ('Avg Revenue/Customer', total_services and total_amount / total_services),
                  ('Collection Rate', f'{total_amount and (total_amount - total_pending) / total_amount * 100:.1f}%')],
            charts_data=charts_data
        )
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Customers Report",
            f"Customers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel Files (*.xlsx)"
        )
        if filepath:
            try:
                wb.save(filepath)
                self.show_success_message(f"Customer report exported: {filepath}")
            except Exception as e:
                self.show_error_message(f"Export failed: {str(e)}")

    def refresh_data(self):
        self.load_customers()


class AddCustomerDialog(QDialog):
    """Enterprise-styled Add Customer dialog"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Customer")
        self.setMinimumWidth(520)
        self.setMinimumHeight(480)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {ENTERPRISE_COLORS['card']};
            }}
            QLabel {{
                background: transparent;
                color: {ENTERPRISE_COLORS['text']};
                font-family: {FONT_FAMILY};
            }}
            QLineEdit, QTextEdit {{
                background-color: {ENTERPRISE_COLORS['bg']};
                color: {ENTERPRISE_COLORS['text']};
                border: 2px solid {ENTERPRISE_COLORS['border']};
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 10.5pt;
                font-family: {FONT_FAMILY};
            }}
            QLineEdit:hover, QTextEdit:hover {{
                border-color: {ENTERPRISE_COLORS['primary']}60;
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border: 2px solid {ENTERPRISE_COLORS['primary']};
                background-color: {ENTERPRISE_COLORS['card']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(20)

        header = QLabel("Add New Customer")
        header.setStyleSheet(f"""
            font-size: 20pt; font-weight: 700;
            color: {ENTERPRISE_COLORS['text']};
            font-family: {FONT_FAMILY};
        """)
        layout.addWidget(header)

        subtitle = QLabel("Fill in the customer details below")
        subtitle.setStyleSheet(f"""
            font-size: 10pt;
            color: {ENTERPRISE_COLORS['text_muted']};
            font-family: {FONT_FAMILY};
        """)
        layout.addWidget(subtitle)

        layout.addSpacing(10)

        form = QFormLayout()
        form.setSpacing(16)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter customer name")
        self.name_input.setMinimumHeight(44)
        form.addRow(self._create_label("Customer Name *"), self.name_input)

        self.mobile_input = QLineEdit()
        self.mobile_input.setPlaceholderText("Enter mobile number")
        self.mobile_input.setMinimumHeight(44)
        form.addRow(self._create_label("Mobile Number *"), self.mobile_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter email address (optional)")
        self.email_input.setMinimumHeight(44)
        form.addRow(self._create_label("Email Address"), self.email_input)

        self.address_input = QTextEdit()
        self.address_input.setPlaceholderText("Enter full address")
        self.address_input.setMaximumHeight(90)
        form.addRow(self._create_label("Address"), self.address_input)

        self.landmark_input = QLineEdit()
        self.landmark_input.setPlaceholderText("Enter nearby landmark (optional)")
        self.landmark_input.setMinimumHeight(44)
        form.addRow(self._create_label("Landmark"), self.landmark_input)

        layout.addLayout(form)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(44)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ENTERPRISE_COLORS['bg']};
                color: {ENTERPRISE_COLORS['text_secondary']};
                border: 2px solid {ENTERPRISE_COLORS['border']};
                border-radius: 10px;
                padding: 10px 28px;
                font-weight: 600; font-size: 10pt;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['card_hover']};
                border-color: {ENTERPRISE_COLORS['text_muted']};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        btn_layout.addStretch()

        save_btn = QPushButton("  💾  Save Customer")
        save_btn.setMinimumHeight(44)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #059669, stop:1 #047857);
                color: #fff; border: none; border-radius: 10px;
                padding: 10px 28px; font-weight: 600; font-size: 10pt;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #10b981, stop:1 #059669);
            }}
        """)
        save_btn.clicked.connect(self._validate_and_accept)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _create_label(self, text):
        label = QLabel(text)
        label.setStyleSheet(f"""
            font-size: 9pt; font-weight: 600;
            color: {ENTERPRISE_COLORS['text_secondary']};
            font-family: {FONT_FAMILY};
        """)
        return label

    def _mark_field_invalid(self, widget, invalid=True):
        if invalid:
            if not hasattr(self, '_saved_styles'):
                self._saved_styles = {}
            if widget not in self._saved_styles:
                self._saved_styles[widget] = widget.styleSheet()
            widget.setStyleSheet(f"""
                border: 2px solid {ENTERPRISE_COLORS['danger']};
                background-color: {ENTERPRISE_COLORS['danger_light']};
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 10.5pt;
                font-family: {FONT_FAMILY};
            """)
        else:
            if hasattr(self, '_saved_styles') and widget in self._saved_styles:
                widget.setStyleSheet(self._saved_styles[widget])
            else:
                widget.setStyleSheet(f"""
                    background-color: {ENTERPRISE_COLORS['bg']};
                    border: 2px solid {ENTERPRISE_COLORS['border']};
                    border-radius: 10px;
                    padding: 12px 16px;
                    font-size: 10.5pt;
                    font-family: {FONT_FAMILY};
                """)

    def _validate_and_accept(self):
        valid = True
        name = self.name_input.text().strip()
        mobile = self.mobile_input.text().strip()
        if not name:
            self._mark_field_invalid(self.name_input); valid = False
        else:
            self._mark_field_invalid(self.name_input, False)
        if not mobile:
            self._mark_field_invalid(self.mobile_input); valid = False
        else:
            self._mark_field_invalid(self.mobile_input, False)
        if not valid:
            QMessageBox.warning(self, "Validation", "Name and Mobile are required")
            return
        from controllers.customer_controller import CustomerController
        from database.db_connection import DatabaseConnection
        db = DatabaseConnection()
        controller = CustomerController(db)
        controller.add_customer(
            name=name, mobile=mobile,
            email=self.email_input.text().strip() or None,
            address=self.address_input.toPlainText().strip() or None,
            landmark=self.landmark_input.text().strip() or None
        )
        self.accept()


class EditCustomerDialog(QDialog):
    """Enterprise-styled Edit Customer dialog"""

    def __init__(self, customer_id, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.setWindowTitle("Edit Customer")
        self.setMinimumWidth(520)
        self.setMinimumHeight(480)
        self._setup_ui()
        self._load_customer()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {ENTERPRISE_COLORS['card']};
            }}
            QLabel {{
                background: transparent;
                color: {ENTERPRISE_COLORS['text']};
                font-family: {FONT_FAMILY};
            }}
            QLineEdit, QTextEdit {{
                background-color: {ENTERPRISE_COLORS['bg']};
                color: {ENTERPRISE_COLORS['text']};
                border: 2px solid {ENTERPRISE_COLORS['border']};
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 10.5pt;
                font-family: {FONT_FAMILY};
            }}
            QLineEdit:hover, QTextEdit:hover {{
                border-color: {ENTERPRISE_COLORS['primary']}60;
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border: 2px solid {ENTERPRISE_COLORS['primary']};
                background-color: {ENTERPRISE_COLORS['card']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(20)

        header = QLabel("Edit Customer")
        header.setStyleSheet(f"""
            font-size: 20pt; font-weight: 700;
            color: {ENTERPRISE_COLORS['text']};
            font-family: {FONT_FAMILY};
        """)
        layout.addWidget(header)

        subtitle = QLabel("Update customer information")
        subtitle.setStyleSheet(f"""
            font-size: 10pt;
            color: {ENTERPRISE_COLORS['text_muted']};
            font-family: {FONT_FAMILY};
        """)
        layout.addWidget(subtitle)

        layout.addSpacing(10)

        form = QFormLayout()
        form.setSpacing(16)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter customer name")
        self.name_input.setMinimumHeight(44)
        form.addRow(self._create_label("Customer Name *"), self.name_input)

        self.mobile_input = QLineEdit()
        self.mobile_input.setPlaceholderText("Enter mobile number")
        self.mobile_input.setMinimumHeight(44)
        form.addRow(self._create_label("Mobile Number *"), self.mobile_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter email address (optional)")
        self.email_input.setMinimumHeight(44)
        form.addRow(self._create_label("Email Address"), self.email_input)

        self.address_input = QTextEdit()
        self.address_input.setPlaceholderText("Enter full address")
        self.address_input.setMaximumHeight(90)
        form.addRow(self._create_label("Address"), self.address_input)

        self.landmark_input = QLineEdit()
        self.landmark_input.setPlaceholderText("Enter nearby landmark (optional)")
        self.landmark_input.setMinimumHeight(44)
        form.addRow(self._create_label("Landmark"), self.landmark_input)

        layout.addLayout(form)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(44)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ENTERPRISE_COLORS['bg']};
                color: {ENTERPRISE_COLORS['text_secondary']};
                border: 2px solid {ENTERPRISE_COLORS['border']};
                border-radius: 10px;
                padding: 10px 28px;
                font-weight: 600; font-size: 10pt;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['card_hover']};
                border-color: {ENTERPRISE_COLORS['text_muted']};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        btn_layout.addStretch()

        save_btn = QPushButton("  💾  Update Customer")
        save_btn.setMinimumHeight(44)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2563eb, stop:1 #1d4ed8);
                color: #fff; border: none; border-radius: 10px;
                padding: 10px 28px; font-weight: 600; font-size: 10pt;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
            }}
        """)
        save_btn.clicked.connect(self._validate_and_accept)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _create_label(self, text):
        label = QLabel(text)
        label.setStyleSheet(f"""
            font-size: 9pt; font-weight: 600;
            color: {ENTERPRISE_COLORS['text_secondary']};
            font-family: {FONT_FAMILY};
        """)
        return label

    def _load_customer(self):
        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            query = "SELECT * FROM customers WHERE id = %s"
            customer = db.execute_query(query, (self.customer_id,), fetch_one=True)
            if customer:
                self.name_input.setText(customer['name'])
                self.mobile_input.setText(customer['mobile'])
                self.email_input.setText(customer.get('email') or '')
                self.address_input.setText(customer.get('address') or '')
                self.landmark_input.setText(customer.get('landmark') or '')

    def _mark_field_invalid(self, widget, invalid=True):
        if invalid:
            if not hasattr(self, '_saved_styles'):
                self._saved_styles = {}
            if widget not in self._saved_styles:
                self._saved_styles[widget] = widget.styleSheet()
            widget.setStyleSheet(f"""
                border: 2px solid {ENTERPRISE_COLORS['danger']};
                background-color: {ENTERPRISE_COLORS['danger_light']};
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 10.5pt;
                font-family: {FONT_FAMILY};
            """)
        else:
            if hasattr(self, '_saved_styles') and widget in self._saved_styles:
                widget.setStyleSheet(self._saved_styles[widget])
            else:
                widget.setStyleSheet(f"""
                    background-color: {ENTERPRISE_COLORS['bg']};
                    border: 2px solid {ENTERPRISE_COLORS['border']};
                    border-radius: 10px;
                    padding: 12px 16px;
                    font-size: 10.5pt;
                    font-family: {FONT_FAMILY};
                """)

    def _validate_and_accept(self):
        valid = True
        name = self.name_input.text().strip()
        mobile = self.mobile_input.text().strip()
        if not name:
            self._mark_field_invalid(self.name_input); valid = False
        else:
            self._mark_field_invalid(self.name_input, False)
        if not mobile:
            self._mark_field_invalid(self.mobile_input); valid = False
        else:
            self._mark_field_invalid(self.mobile_input, False)
        if not valid:
            QMessageBox.warning(self, "Validation", "Name and Mobile are required")
            return
        from controllers.customer_controller import CustomerController
        from database.db_connection import DatabaseConnection
        db = DatabaseConnection()
        controller = CustomerController(db)
        controller.update_customer(
            customer_id=self.customer_id, name=name, mobile=mobile,
            email=self.email_input.text().strip() or None,
            address=self.address_input.toPlainText().strip() or None,
            landmark=self.landmark_input.text().strip() or None
        )
        self.accept()