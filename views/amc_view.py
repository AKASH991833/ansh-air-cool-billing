"""
AMC View - Enterprise AMC Contract & Preventive Maintenance Management
Modern Executive White/Slate Theme with comprehensive lifecycle management
"""
import os
import urllib.parse
from datetime import datetime, timedelta
from decimal import Decimal

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea,
    QSizePolicy, QTabWidget, QComboBox, QDoubleSpinBox, QSpinBox,
    QTextEdit, QFormLayout, QMessageBox, QDateEdit, QDialog,
    QSplitter, QGroupBox, QMenu, QFileDialog, QAbstractItemView,
    QInputDialog, QGridLayout, QDialogButtonBox, QCheckBox
)
from PySide6.QtCore import Qt, QDate, Signal, QUrl
from PySide6.QtGui import QColor, QFont, QDesktopServices, QCursor

from utils.unified_theme import UnifiedTheme
from views.base_window import BaseView
from utils.app_settings import get_setting
from utils.formatters import Formatters


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHEVRON_ICON_PATH = os.path.join(BASE_DIR, "assets", "icons", "chevron_down.png").replace("\\", "/")

FONT_FAMILY = "'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif"

# Enterprise Design Tokens matching Customer, Technician, and Invoice views
ENTERPRISE_COLORS = {
    'bg': '#f8fafc',
    'card': '#ffffff',
    'card_hover': '#f8fafc',
    'primary': '#2563eb',
    'primary_hover': '#1d4ed8',
    'primary_light': '#eff6ff',
    'primary_border': '#bfdbfe',
    'success': '#059669',
    'success_hover': '#047857',
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
    'purple': '#7c3aed',
    'purple_light': '#f5f3ff',
    'purple_border': '#ddd6fe',
    'text': '#0f172a',
    'text_secondary': '#475569',
    'text_muted': '#64748b',
    'border': '#e2e8f0',
    'border_light': '#f1f5f9',
    'divider': '#e2e8f0',
    'table_header': '#f8fafc',
    'table_stripe': '#fafbfd',
    'shadow': 'rgba(15, 23, 42, 0.08)',
}


class AMCStatusBadge(QLabel):
    """Modern enterprise status badge for AMC contracts"""

    def __init__(self, status, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(24)

        status_norm = (status or "").strip().title()
        cfg = {
            'Active': (ENTERPRISE_COLORS['success'], ENTERPRISE_COLORS['success_light'], ENTERPRISE_COLORS['success_border']),
            'Expiring Soon': (ENTERPRISE_COLORS['warning'], ENTERPRISE_COLORS['warning_light'], ENTERPRISE_COLORS['warning_border']),
            'Expired': (ENTERPRISE_COLORS['danger'], ENTERPRISE_COLORS['danger_light'], ENTERPRISE_COLORS['danger_border']),
            'Completed': (ENTERPRISE_COLORS['info'], ENTERPRISE_COLORS['info_light'], ENTERPRISE_COLORS['info_border']),
            'Cancelled': (ENTERPRISE_COLORS['text_muted'], ENTERPRISE_COLORS['border_light'], ENTERPRISE_COLORS['border'])
        }
        fg, bg, brd = cfg.get(status_norm, (ENTERPRISE_COLORS['text_secondary'], ENTERPRISE_COLORS['border_light'], ENTERPRISE_COLORS['border']))
        self.setText(f"● {status_norm}")
        self.setStyleSheet(f"""
            background-color: {bg};
            color: {fg};
            border: 1px solid {brd};
            border-radius: 12px;
            padding: 1px 8px;
            font-size: 8pt;
            font-weight: 700;
            font-family: "Segoe UI", 'Inter', sans-serif;
        """)


class VisitStatusBadge(QLabel):
    """Modern enterprise badge for AMC visit schedule status"""

    def __init__(self, status, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(24)

        status_norm = (status or "").strip().title()
        cfg = {
            'Completed': (ENTERPRISE_COLORS['success'], ENTERPRISE_COLORS['success_light'], ENTERPRISE_COLORS['success_border']),
            'Scheduled': (ENTERPRISE_COLORS['primary'], ENTERPRISE_COLORS['primary_light'], ENTERPRISE_COLORS['primary_border']),
            'Overdue': (ENTERPRISE_COLORS['danger'], ENTERPRISE_COLORS['danger_light'], ENTERPRISE_COLORS['danger_border']),
            'Cancelled': (ENTERPRISE_COLORS['text_muted'], ENTERPRISE_COLORS['border_light'], ENTERPRISE_COLORS['border'])
        }
        fg, bg, brd = cfg.get(status_norm, (ENTERPRISE_COLORS['text_secondary'], ENTERPRISE_COLORS['border_light'], ENTERPRISE_COLORS['border']))
        self.setText(f"● {status_norm}")
        self.setStyleSheet(f"""
            background-color: {bg};
            color: {fg};
            border: 1px solid {brd};
            border-radius: 12px;
            padding: 1px 8px;
            font-size: 8pt;
            font-weight: 700;
            font-family: "Segoe UI", 'Inter', sans-serif;
        """)


def _make_centered_cell_widget(child_widget):
    """Wraps a widget in a centered layout container to prevent stretching or clipping"""
    container = QWidget()
    lay = QHBoxLayout(container)
    lay.setContentsMargins(2, 2, 2, 2)
    lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lay.addWidget(child_widget)
    return container


class AMCView(BaseView):
    """Enterprise AMC contract & preventive maintenance management view"""

    def __init__(self):
        super().__init__()
        self.currency_symbol = get_setting("currency_symbol", "₹")
        self.selected_customer = None
        self.amc_units = []
        self.selected_amc_id = None
        self.customer_list = []
        self.technicians_list = []
        self.amc_list = []
        self.visits_list = []

        self._setup_ui()
        self.load_amc_data()
        self.load_technicians()
        self._load_visits()
        self._search_customer()

    def update_theme_colors(self):
        """Technician & AMC sections locked to enterprise pure white theme"""
        self.setStyleSheet(f"""
            AMCView, QWidget {{
                background-color: {ENTERPRISE_COLORS['bg']};
                font-family: {FONT_FAMILY};
            }}
        """)
        self._style_white_table(self.amc_table)
        self._style_white_table(self.visits_table)
        self.load_amc_data()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            AMCView, QWidget {{
                background-color: {ENTERPRISE_COLORS['bg']};
                font-family: {FONT_FAMILY};
            }}
            QToolTip {{
                background-color: #0F172A;
                color: #FFFFFF;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 9pt;
                font-weight: 500;
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(16)

        # 1. Executive Top Header
        self._create_header(main_layout)

        # 2. Executive KPI Stat Cards (5 Cards)
        self._create_summary_bar(main_layout)

        # 3. Modern Segmented Tab Bar
        self._create_tabs(main_layout)

    # ═══════════════════════════════════════════════════════════════════════════
    # 1. EXECUTIVE TOP HEADER
    # ═══════════════════════════════════════════════════════════════════════════
    def _create_header(self, layout):
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        # Title & Subtitle
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title = QLabel("AMC CONTRACT MANAGEMENT")
        title.setObjectName("headingLabel")
        title.setStyleSheet(f"""
            font-size: 18pt;
            font-weight: 800;
            color: {ENTERPRISE_COLORS['text']};
            font-family: {FONT_FAMILY};
            letter-spacing: -0.5px;
        """)
        text_layout.addWidget(title)

        subtitle = QLabel("Annual service agreements, preventive visit schedules, equipment registry & recurring revenue")
        subtitle.setObjectName("subheadingLabel")
        subtitle.setStyleSheet(f"""
            font-size: 9.5pt;
            color: {ENTERPRISE_COLORS['text_muted']};
            font-family: {FONT_FAMILY};
        """)
        text_layout.addWidget(subtitle)
        header_layout.addLayout(text_layout)

        header_layout.addStretch()

        # Action Buttons
        self.refresh_btn = QPushButton("🔄  Refresh")
        self.refresh_btn.setToolTip("Reload contracts and visit schedules")
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setStyleSheet(self._secondary_button_style())
        self.refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(self.refresh_btn)

        self.export_excel_btn = QPushButton("📊  Export Excel")
        self.export_excel_btn.setToolTip("Export AMC contracts to styled Excel sheet with analytics")
        self.export_excel_btn.setCursor(Qt.PointingHandCursor)
        self.export_excel_btn.setStyleSheet(self._secondary_button_style())
        self.export_excel_btn.clicked.connect(self._export_amc_to_excel)
        header_layout.addWidget(self.export_excel_btn)

        self.new_contract_header_btn = QPushButton("➕  New AMC Contract")
        self.new_contract_header_btn.setToolTip("Create a new Annual Maintenance Contract")
        self.new_contract_header_btn.setCursor(Qt.PointingHandCursor)
        self.new_contract_header_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ENTERPRISE_COLORS['primary']};
                color: #ffffff;
                font-size: 10pt;
                font-weight: 700;
                font-family: {FONT_FAMILY};
                padding: 9px 18px;
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['primary_hover']};
            }}
        """)
        self.new_contract_header_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(2))
        header_layout.addWidget(self.new_contract_header_btn)

        layout.addWidget(header_widget)

    # ═══════════════════════════════════════════════════════════════════════════
    # 2. EXECUTIVE KPI STAT CARDS
    # ═══════════════════════════════════════════════════════════════════════════
    def _create_summary_bar(self, layout):
        self.summary_container = QWidget()
        self.summary_container.setStyleSheet("background: transparent;")
        cards_layout = QHBoxLayout(self.summary_container)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(14)

        metrics = [
            ('amc_total', 'TOTAL CONTRACTS', '0', ENTERPRISE_COLORS['primary'], '📄', ENTERPRISE_COLORS['primary_light'], 'Registered agreements'),
            ('amc_active', 'ACTIVE COVERAGE', '0', ENTERPRISE_COLORS['success'], '🛡️', ENTERPRISE_COLORS['success_light'], 'Currently serviced'),
            ('amc_expiring', 'EXPIRING IN 30D', '0', ENTERPRISE_COLORS['warning'], '⏳', ENTERPRISE_COLORS['warning_light'], 'Requires renewal'),
            ('amc_revenue', 'TOTAL REVENUE', f"{self.currency_symbol}0", ENTERPRISE_COLORS['text'], '💰', ENTERPRISE_COLORS['table_stripe'], 'Gross contract value'),
            ('amc_scheduled_visits', 'SCHEDULED VISITS', '0', ENTERPRISE_COLORS['purple'], '🛠️', ENTERPRISE_COLORS['purple_light'], 'Pending field visits'),
        ]

        self.amc_summary_labels = {}
        for key, label, default, val_color, icon, badge_bg, subtext in metrics:
            card = QFrame()
            card.setObjectName(f"kpiCard_{key}")
            card.setStyleSheet(f"""
                QFrame#kpiCard_{key} {{
                    background-color: #ffffff;
                    border: 1px solid {ENTERPRISE_COLORS['border']};
                    border-radius: 12px;
                }}
                QFrame#kpiCard_{key}:hover {{
                    border-color: {val_color}60;
                    background-color: #ffffff;
                }}
            """)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(16, 14, 16, 14)
            cl.setSpacing(6)

            top_row = QHBoxLayout()
            top_row.setSpacing(10)

            icon_lbl = QLabel(icon)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_lbl.setFixedSize(36, 36)
            icon_lbl.setStyleSheet(f"""
                background-color: {badge_bg};
                border-radius: 10px;
                font-size: 14pt;
            """)
            top_row.addWidget(icon_lbl)

            lbl = QLabel(label)
            lbl.setStyleSheet(f"""
                font-size: 8pt;
                font-weight: 700;
                color: {ENTERPRISE_COLORS['text_muted']};
                letter-spacing: 0.6px;
                font-family: {FONT_FAMILY};
            """)
            top_row.addWidget(lbl)
            top_row.addStretch()
            cl.addLayout(top_row)

            val_lbl = QLabel(default)
            val_lbl.setStyleSheet(f"""
                font-size: 18pt;
                font-weight: 800;
                color: {val_color};
                font-family: {FONT_FAMILY};
                margin-top: 2px;
            """)
            cl.addWidget(val_lbl)
            self.amc_summary_labels[key] = val_lbl

            sub_lbl = QLabel(subtext)
            sub_lbl.setStyleSheet(f"""
                font-size: 8pt;
                color: {ENTERPRISE_COLORS['text_muted']};
                font-family: {FONT_FAMILY};
            """)
            cl.addWidget(sub_lbl)

            cards_layout.addWidget(card)

        layout.addWidget(self.summary_container)

    # ═══════════════════════════════════════════════════════════════════════════
    # 3. SEGMENTED TABS
    # ═══════════════════════════════════════════════════════════════════════════
    def _create_tabs(self, layout):
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 12px;
                background-color: #ffffff;
                top: -1px;
            }}
            QTabBar::tab {{
                background-color: #f1f5f9;
                color: {ENTERPRISE_COLORS['text_secondary']};
                padding: 10px 22px;
                font-size: 9.5pt;
                font-weight: 700;
                font-family: {FONT_FAMILY};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 6px;
                min-width: 140px;
            }}
            QTabBar::tab:selected {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['primary']};
                border-bottom: 2px solid #ffffff;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {ENTERPRISE_COLORS['primary_light']};
                color: {ENTERPRISE_COLORS['primary']};
            }}
        """)

        # Tab 1: Contracts Directory
        self.amc_list_tab = self._create_amc_list_tab()
        self.tabs.addTab(self.amc_list_tab, "📋  All Contracts")

        # Tab 2: Visit Schedules
        self.visits_tab = self._create_visits_tab()
        self.tabs.addTab(self.visits_tab, "📅  Visit Schedules")

        # Tab 3: New Contract Studio
        self.new_contract_tab = self._create_new_contract_tab()
        self.tabs.addTab(self.new_contract_tab, "➕  New Contract Studio")

        layout.addWidget(self.tabs, 1)

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 1: ALL CONTRACTS DIRECTORY
    # ═══════════════════════════════════════════════════════════════════════════
    def _create_amc_list_tab(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(14)

        # Filters toolbar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        self.amc_search_input = QLineEdit()
        self.amc_search_input.setPlaceholderText("🔍  Search by AMC ID, customer name or phone...")
        self.amc_search_input.setClearButtonEnabled(True)
        self.amc_search_input.setStyleSheet(self._input_style())
        self.amc_search_input.textChanged.connect(self.load_amc_data)
        filter_bar.addWidget(self.amc_search_input, 3)

        status_lbl = QLabel("Status:")
        status_lbl.setStyleSheet(f"font-size: 9pt; font-weight: 600; color: {ENTERPRISE_COLORS['text_secondary']};")
        filter_bar.addWidget(status_lbl)

        self.amc_status_filter = QComboBox()
        self.amc_status_filter.addItems(["All Status", "Active", "Expiring Soon", "Expired", "Completed"])
        self.amc_status_filter.setStyleSheet(self._combo_style())
        self.amc_status_filter.currentTextChanged.connect(self.load_amc_data)
        filter_bar.addWidget(self.amc_status_filter, 1)

        type_lbl = QLabel("Type:")
        type_lbl.setStyleSheet(f"font-size: 9pt; font-weight: 600; color: {ENTERPRISE_COLORS['text_secondary']};")
        filter_bar.addWidget(type_lbl)

        self.amc_type_filter = QComboBox()
        self.amc_type_filter.addItems(["All Types", "Comprehensive", "Non-Comprehensive"])
        self.amc_type_filter.setStyleSheet(self._combo_style())
        self.amc_type_filter.currentTextChanged.connect(self.load_amc_data)
        filter_bar.addWidget(self.amc_type_filter, 1)

        layout.addLayout(filter_bar)

        # Contracts Data Table
        self.amc_table = QTableWidget()
        self.amc_table.setColumnCount(11)
        self.amc_table.setHorizontalHeaderLabels([
            'AMC ID', 'Customer Details', 'Contract Type', 'Period / Dates',
            'Units', 'Services', 'Scope / Notes', 'Total Value', 'Paid / Balance', 'Status', 'Quick Actions'
        ])
        self.amc_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.amc_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.amc_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.amc_table.verticalHeader().setVisible(False)
        self.amc_table.setShowGrid(True)
        self.amc_table.setGridStyle(Qt.PenStyle.SolidLine)
        self.amc_table.setWordWrap(True)
        self.amc_table.setAlternatingRowColors(True)

        self._style_white_table(self.amc_table)

        hdr = self.amc_table.horizontalHeader()
        hdr.setMinimumSectionSize(60)
        hdr.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(8, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(9, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(10, QHeaderView.ResizeMode.Interactive)

        self.amc_table.setColumnWidth(0, 90)
        self.amc_table.setColumnWidth(2, 115)
        self.amc_table.setColumnWidth(3, 110)
        self.amc_table.setColumnWidth(4, 75)
        self.amc_table.setColumnWidth(5, 85)
        self.amc_table.setColumnWidth(6, 115)
        self.amc_table.setColumnWidth(7, 95)
        self.amc_table.setColumnWidth(8, 110)
        self.amc_table.setColumnWidth(9, 95)
        self.amc_table.setColumnWidth(10, 165)

        self.amc_table.cellDoubleClicked.connect(self._on_amc_double_click)
        self.amc_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.amc_table.customContextMenuRequested.connect(self._show_amc_context_menu)

        layout.addWidget(self.amc_table, 1)

        # Bottom Action Bar
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        hint_lbl = QLabel("💡 Double-click any row or right-click to inspect 360° contract details & visits")
        hint_lbl.setStyleSheet(f"font-size: 8.5pt; color: {ENTERPRISE_COLORS['text_muted']}; font-family: {FONT_FAMILY};")
        bottom_bar.addWidget(hint_lbl)
        bottom_bar.addStretch()

        self.btn_action_view = QPushButton("👁️  View Details")
        self.btn_action_view.setStyleSheet(self._secondary_button_style())
        self.btn_action_view.clicked.connect(self._on_view_details_clicked)
        bottom_bar.addWidget(self.btn_action_view)

        self.btn_action_pay = QPushButton("💳  Add Payment")
        self.btn_action_pay.setStyleSheet(self._secondary_button_style())
        self.btn_action_pay.clicked.connect(self._on_add_payment_clicked)
        bottom_bar.addWidget(self.btn_action_pay)

        self.btn_action_schedule = QPushButton("📅  Schedule Visit")
        self.btn_action_schedule.setStyleSheet(self._secondary_button_style())
        self.btn_action_schedule.clicked.connect(self._on_schedule_visit_clicked)
        bottom_bar.addWidget(self.btn_action_schedule)

        self.btn_action_pdf = QPushButton("📄  Contract PDF / Form")
        self.btn_action_pdf.setToolTip("Generate, preview, print and share official AMC Agreement & Certificate PDF")
        self.btn_action_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_action_pdf.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['primary']};
                font-size: 9pt;
                font-weight: 700;
                font-family: {FONT_FAMILY};
                padding: 7px 14px;
                border-radius: 8px;
                border: 1px solid {ENTERPRISE_COLORS['primary_border']};
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['primary_light']};
            }}
        """)
        self.btn_action_pdf.clicked.connect(self._on_generate_pdf_clicked)
        bottom_bar.addWidget(self.btn_action_pdf)

        self.btn_action_wa = QPushButton("💬  WhatsApp")
        self.btn_action_wa.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                color: #059669;
                font-size: 9pt;
                font-weight: 700;
                font-family: {FONT_FAMILY};
                padding: 7px 14px;
                border-radius: 8px;
                border: 1px solid #a7f3d0;
            }}
            QPushButton:hover {{
                background-color: #ecfdf5;
                border-color: #059669;
            }}
        """)
        self.btn_action_wa.clicked.connect(self._on_whatsapp_share_clicked)
        bottom_bar.addWidget(self.btn_action_wa)

        self.btn_action_renew = QPushButton("🔄  Renew AMC")
        self.btn_action_renew.setStyleSheet(self._secondary_button_style())
        self.btn_action_renew.clicked.connect(self._on_renew_amc_clicked)
        bottom_bar.addWidget(self.btn_action_renew)

        self.btn_action_delete = QPushButton("🗑️  Delete Contract")
        self.btn_action_delete.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['danger']};
                font-size: 9pt;
                font-weight: 700;
                font-family: {FONT_FAMILY};
                padding: 7px 14px;
                border-radius: 8px;
                border: 1px solid {ENTERPRISE_COLORS['danger_border']};
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['danger_light']};
            }}
        """)
        self.btn_action_delete.clicked.connect(self._on_delete_amc_clicked)
        bottom_bar.addWidget(self.btn_action_delete)

        layout.addLayout(bottom_bar)
        return container

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 2: VISIT SCHEDULES
    # ═══════════════════════════════════════════════════════════════════════════
    def _create_visits_tab(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(14)

        # Filters toolbar
        ctrl = QHBoxLayout()
        ctrl.setSpacing(12)

        vstatus_lbl = QLabel("Filter Status:")
        vstatus_lbl.setStyleSheet(f"font-size: 9pt; font-weight: 600; color: {ENTERPRISE_COLORS['text_secondary']};")
        ctrl.addWidget(vstatus_lbl)

        self.visit_status_combo = QComboBox()
        self.visit_status_combo.addItems(["All", "Scheduled", "Completed", "Cancelled"])
        self.visit_status_combo.setStyleSheet(self._combo_style())
        self.visit_status_combo.currentTextChanged.connect(self._load_visits)
        ctrl.addWidget(self.visit_status_combo)

        ctrl.addSpacing(15)
        hint = QLabel("Track preventive maintenance visits, technician allocations, and service completions")
        hint.setStyleSheet(f"font-size: 8.5pt; color: {ENTERPRISE_COLORS['text_muted']}; font-family: {FONT_FAMILY};")
        ctrl.addWidget(hint)
        ctrl.addStretch()

        refresh_visits_btn = QPushButton("🔄  Refresh Visits")
        refresh_visits_btn.setStyleSheet(self._secondary_button_style())
        refresh_visits_btn.clicked.connect(self._load_visits)
        ctrl.addWidget(refresh_visits_btn)

        layout.addLayout(ctrl)

        # Visits Table
        self.visits_table = QTableWidget()
        self.visits_table.setColumnCount(8)
        self.visits_table.setHorizontalHeaderLabels([
            'Visit #', 'AMC Contract', 'Customer Details', 'Visit Date',
            'Assigned Technician', 'Status', 'Work / Description / Notes', 'Quick Actions'
        ])
        self.visits_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.visits_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.visits_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.visits_table.verticalHeader().setVisible(False)
        self.visits_table.setShowGrid(True)
        self.visits_table.setGridStyle(Qt.PenStyle.SolidLine)
        self.visits_table.setWordWrap(True)
        self.visits_table.setAlternatingRowColors(True)

        self._style_white_table(self.visits_table)

        hdr = self.visits_table.horizontalHeader()
        hdr.setMinimumSectionSize(70)
        hdr.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)

        self.visits_table.setColumnWidth(0, 85)
        self.visits_table.setColumnWidth(1, 110)
        self.visits_table.setColumnWidth(2, 175)
        self.visits_table.setColumnWidth(3, 125)
        self.visits_table.setColumnWidth(4, 150)
        self.visits_table.setColumnWidth(5, 110)
        self.visits_table.setColumnWidth(7, 190)

        self.visits_table.cellDoubleClicked.connect(self._on_visit_double_click)
        self.visits_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.visits_table.customContextMenuRequested.connect(self._show_visit_context_menu)

        layout.addWidget(self.visits_table, 1)

        # Bottom Action Bar for Visits
        visits_bottom = QHBoxLayout()
        visits_bottom.setSpacing(10)

        v_hint = QLabel("💡 Double-click or right-click any visit to complete, reschedule, or assign technician")
        v_hint.setStyleSheet(f"font-size: 8.5pt; color: {ENTERPRISE_COLORS['text_muted']}; font-family: {FONT_FAMILY};")
        visits_bottom.addWidget(v_hint)
        visits_bottom.addStretch()

        self.btn_visit_done = QPushButton("✓  Mark Completed")
        self.btn_visit_done.setStyleSheet(f"""
            QPushButton {{
                background-color: {ENTERPRISE_COLORS['success']};
                color: #ffffff;
                font-size: 9pt;
                font-weight: 700;
                font-family: {FONT_FAMILY};
                padding: 7px 14px;
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['success_hover']};
            }}
        """)
        self.btn_visit_done.clicked.connect(self._on_visit_complete_clicked)
        visits_bottom.addWidget(self.btn_visit_done)

        self.btn_visit_resched = QPushButton("📅  Reschedule Date")
        self.btn_visit_resched.setStyleSheet(self._secondary_button_style())
        self.btn_visit_resched.clicked.connect(self._on_visit_resched_clicked)
        visits_bottom.addWidget(self.btn_visit_resched)

        self.btn_visit_assign = QPushButton("👤  Assign Technician")
        self.btn_visit_assign.setStyleSheet(self._secondary_button_style())
        self.btn_visit_assign.clicked.connect(self._on_visit_assign_clicked)
        visits_bottom.addWidget(self.btn_visit_assign)

        self.btn_visit_wa = QPushButton("💬  WhatsApp Reminder")
        self.btn_visit_wa.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                color: #059669;
                font-size: 9pt;
                font-weight: 700;
                font-family: {FONT_FAMILY};
                padding: 7px 14px;
                border-radius: 8px;
                border: 1px solid #a7f3d0;
            }}
            QPushButton:hover {{
                background-color: #ecfdf5;
                border-color: #059669;
            }}
        """)
        self.btn_visit_wa.clicked.connect(self._on_visit_wa_clicked)
        visits_bottom.addWidget(self.btn_visit_wa)

        self.btn_visit_cancel = QPushButton("✕  Cancel Visit")
        self.btn_visit_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['danger']};
                font-size: 9pt;
                font-weight: 700;
                font-family: {FONT_FAMILY};
                padding: 7px 14px;
                border-radius: 8px;
                border: 1px solid {ENTERPRISE_COLORS['danger_border']};
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['danger_light']};
            }}
        """)
        self.btn_visit_cancel.clicked.connect(self._on_visit_cancel_clicked)
        visits_bottom.addWidget(self.btn_visit_cancel)

        layout.addLayout(visits_bottom)
        return container

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 3: NEW AMC CONTRACT STUDIO
    # ═══════════════════════════════════════════════════════════════════════════
    def _create_new_contract_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"background: {ENTERPRISE_COLORS['bg']};")

        content = QWidget()
        content.setStyleSheet(f"background: {ENTERPRISE_COLORS['bg']};")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(18, 16, 18, 20)
        layout.setSpacing(16)

        # ── 1. Top Executive Banner ──────────────────────────────────────────
        top_box = QFrame()
        top_box.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e3a8a, stop:0.5 #2563eb, stop:1 #1d4ed8);
                border-radius: 12px;
                padding: 14px 18px;
            }}
        """)
        top_layout = QHBoxLayout(top_box)
        top_layout.setContentsMargins(4, 4, 4, 4)
        top_layout.setSpacing(14)

        tb_icon = QLabel("📝")
        tb_icon.setStyleSheet("font-size: 26pt; background: transparent;")
        top_layout.addWidget(tb_icon)

        tb_text = QVBoxLayout()
        tb_text.setSpacing(2)
        tb_title = QLabel("Create Annual Maintenance Contract (AMC)")
        tb_title.setStyleSheet("font-size: 13.5pt; font-weight: 800; color: #ffffff; background: transparent; font-family: " + FONT_FAMILY + ";")
        tb_sub = QLabel("Configure customer profile, equipment registry, frequency presets, smart commercials & auto-schedule visits")
        tb_sub.setStyleSheet("font-size: 8.5pt; color: #dbeafe; background: transparent; font-family: " + FONT_FAMILY + ";")
        tb_text.addWidget(tb_title)
        tb_text.addWidget(tb_sub)
        top_layout.addLayout(tb_text)
        top_layout.addStretch()

        # Header quick button to clear/reset
        hdr_reset_btn = QPushButton("🔄  Clear Form")
        hdr_reset_btn.setCursor(Qt.PointingHandCursor)
        hdr_reset_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.18);
                color: #ffffff;
                font-size: 8.5pt;
                font-weight: 700;
                padding: 6px 14px;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.35);
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        hdr_reset_btn.clicked.connect(self._reset_new_contract_form)
        top_layout.addWidget(hdr_reset_btn)

        layout.addWidget(top_box)

        # ── Two-Column Main Grid ─────────────────────────────────────────────
        grid = QGridLayout()
        grid.setSpacing(16)

        # ── Card 1: Customer Profile & Identification ─────────────────────────
        cust_card = self._create_card("👤  Customer Profile & Service Site", "Select existing customer or quick-add new profile")
        cust_layout = QVBoxLayout(cust_card)
        cust_layout.setContentsMargins(16, 14, 16, 14)
        cust_layout.setSpacing(10)

        # Search row with Quick Add button
        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        self.customer_search_input = QLineEdit()
        self.customer_search_input.setPlaceholderText("🔍  Search customer by name, mobile, address...")
        self.customer_search_input.setClearButtonEnabled(True)
        self.customer_search_input.setStyleSheet(self._input_style())
        self.customer_search_input.textChanged.connect(self._search_customer)
        search_row.addWidget(self.customer_search_input, 4)

        search_btn = QPushButton("Search")
        search_btn.setCursor(Qt.PointingHandCursor)
        search_btn.setStyleSheet(self._secondary_button_style())
        search_btn.clicked.connect(self._search_customer)
        search_row.addWidget(search_btn, 1)

        self.btn_quick_add_cust = QPushButton("➕ New Customer")
        self.btn_quick_add_cust.setToolTip("Quickly register a new customer profile without leaving AMC screen")
        self.btn_quick_add_cust.setCursor(Qt.PointingHandCursor)
        self.btn_quick_add_cust.setStyleSheet(f"""
            QPushButton {{
                background-color: {ENTERPRISE_COLORS['primary_light']};
                color: {ENTERPRISE_COLORS['primary']};
                border: 1px solid {ENTERPRISE_COLORS['primary_border']};
                border-radius: 8px;
                padding: 7px 12px;
                font-size: 8.5pt;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['primary']};
                color: #ffffff;
            }}
        """)
        self.btn_quick_add_cust.clicked.connect(self._open_quick_add_customer)
        search_row.addWidget(self.btn_quick_add_cust, 2)

        cust_layout.addLayout(search_row)

        # Customer Dropdown
        self.customer_combo = QComboBox()
        self.customer_combo.addItem("-- Choose Customer (Select or Search) --", "")
        self.customer_combo.setStyleSheet(self._combo_style())
        self.customer_combo.currentTextChanged.connect(self._on_customer_select)
        cust_layout.addWidget(self.customer_combo)

        # Customer Details Badge
        self.customer_details_label = QLabel("No customer selected. Choose from dropdown above or click '➕ New Customer'.")
        self.customer_details_label.setWordWrap(True)
        self.customer_details_label.setStyleSheet(f"""
            color: {ENTERPRISE_COLORS['text_secondary']};
            font-size: 8.5pt;
            padding: 10px 14px;
            background-color: {ENTERPRISE_COLORS['table_stripe']};
            border: 1px solid {ENTERPRISE_COLORS['border_light']};
            border-radius: 8px;
            font-family: {FONT_FAMILY};
        """)
        cust_layout.addWidget(self.customer_details_label)

        grid.addWidget(cust_card, 0, 0)

        # ── Card 2: Contract Terms, Duration & Frequency ─────────────────────
        contract_card = self._create_card("📜  Contract Plan, Duration & Frequency", "Configure plan type, duration presets, visit frequency & technician")
        c_layout = QFormLayout(contract_card)
        c_layout.setContentsMargins(16, 14, 16, 14)
        c_layout.setSpacing(10)

        # 1. Contract Type Dropdown
        self.contract_type_combo = QComboBox()
        self.contract_type_combo.addItems([
            "Comprehensive AMC (Full Spares, Gas & Wet Wash)",
            "Non-Comprehensive AMC (Labor & Jet Wash Only)",
            "Preventive Maintenance Service Care (PMSC)",
            "Corporate / Custom Service Agreement"
        ])
        self.contract_type_combo.setStyleSheet(self._combo_style())
        self.contract_type_combo.currentIndexChanged.connect(self._on_contract_type_changed)
        c_layout.addRow("Contract Plan:", self.contract_type_combo)

        # 2. Duration Dropdown & Spinbox Row
        dur_row = QHBoxLayout()
        dur_row.setSpacing(8)

        self.duration_preset_combo = QComboBox()
        self.duration_preset_combo.addItems([
            "1 Year (Standard — 365 Days)",
            "2 Years (Extended — 730 Days)",
            "3 Years (Commercial Enterprise)",
            "6 Months (Seasonal Summer Pack)",
            "Custom Duration..."
        ])
        self.duration_preset_combo.setStyleSheet(self._combo_style())
        self.duration_preset_combo.currentIndexChanged.connect(self._on_duration_preset_changed)
        dur_row.addWidget(self.duration_preset_combo, 3)

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 5)
        self.duration_spin.setValue(1)
        self.duration_spin.setSuffix(" year(s)")
        self.duration_spin.setStyleSheet(self._spin_style())
        self.duration_spin.valueChanged.connect(self._update_end_date)
        dur_row.addWidget(self.duration_spin, 2)
        c_layout.addRow("Contract Duration:", dur_row)

        # 3. Visit Frequency Dropdown & Spinbox Row
        freq_row = QHBoxLayout()
        freq_row.setSpacing(8)

        self.visit_frequency_combo = QComboBox()
        self.visit_frequency_combo.addItems([
            "4 Visits / Year (Quarterly — Every 3 Months [Recommended])",
            "3 Visits / Year (Tri-Annual — Every 4 Months)",
            "2 Visits / Year (Semi-Annual — Every 6 Months)",
            "6 Visits / Year (Bi-Monthly — Every 2 Months)",
            "12 Visits / Year (Monthly — Commercial Regular)",
            "Custom Visits..."
        ])
        self.visit_frequency_combo.setStyleSheet(self._combo_style())
        self.visit_frequency_combo.currentIndexChanged.connect(self._on_visit_frequency_preset_changed)
        freq_row.addWidget(self.visit_frequency_combo, 3)

        self.services_per_year = QSpinBox()
        self.services_per_year.setRange(1, 12)
        self.services_per_year.setValue(4)
        self.services_per_year.setSuffix(" visits / year")
        self.services_per_year.setStyleSheet(self._spin_style())
        self.services_per_year.valueChanged.connect(self._on_services_spin_changed)
        freq_row.addWidget(self.services_per_year, 2)
        c_layout.addRow("Visit Frequency:", freq_row)

        # 4. Validity Dates
        dates_row = QHBoxLayout()
        dates_row.setSpacing(6)

        self.start_date_input = QDateEdit()
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(QDate.currentDate())
        self.start_date_input.setDisplayFormat("dd-MM-yyyy")
        self.start_date_input.setStyleSheet(self._date_style())
        self.start_date_input.dateChanged.connect(self._update_end_date)
        dates_row.addWidget(self.start_date_input, 1)

        arrow_lbl = QLabel("→")
        arrow_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow_lbl.setStyleSheet("font-weight: 800; color: #64748b;")
        dates_row.addWidget(arrow_lbl)

        self.end_date_input = QDateEdit()
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDate(QDate.currentDate().addYears(1).addDays(-1))
        self.end_date_input.setDisplayFormat("dd-MM-yyyy")
        self.end_date_input.setStyleSheet(self._date_style())
        self.end_date_input.dateChanged.connect(self._update_projected_visits_preview)
        dates_row.addWidget(self.end_date_input, 1)
        c_layout.addRow("Agreement Period:", dates_row)

        # 5. Primary Technician Dropdown
        self.technician_combo = QComboBox()
        self.technician_combo.addItem("👤  -- Auto / Assign by Service Manager --", None)
        self.technician_combo.setStyleSheet(self._combo_style())
        self.technician_combo.currentIndexChanged.connect(self._update_projected_visits_preview)
        c_layout.addRow("Allocated Tech:", self.technician_combo)

        grid.addWidget(contract_card, 0, 1)

        # ── Card 3: AC Units Equipment Registry ──────────────────────────────
        unit_card = self._create_card("❄️  AC Units Equipment Registry", "Register air conditioners covered under this contract")
        u_layout = QVBoxLayout(unit_card)
        u_layout.setContentsMargins(16, 14, 16, 14)
        u_layout.setSpacing(10)

        # Add Unit Controls Row
        u_input_row = QHBoxLayout()
        u_input_row.setSpacing(8)

        # AC Type Dropdown
        self.unit_type_combo = QComboBox()
        self.unit_type_combo.addItems(["Split AC", "Window AC", "Inverter Split AC", "Cassette AC", "Tower AC", "Ductable / VRF", "Portable AC"])
        self.unit_type_combo.setStyleSheet(self._combo_style())
        self.unit_type_combo.setToolTip("Select Air Conditioner Type")
        u_input_row.addWidget(self.unit_type_combo, 2)

        # Brand Dropdown
        self.unit_brand_combo = QComboBox()
        self.unit_brand_combo.setEditable(True)
        self.unit_brand_combo.addItems([
            "Daikin", "Voltas", "LG", "Blue Star", "Hitachi", "Carrier",
            "Panasonic", "Samsung", "Mitsubishi Heavy", "O-General", "Lloyd", "Godrej", "Haier", "IFB", "Whirlpool"
        ])
        self.unit_brand_combo.setStyleSheet(self._combo_style())
        self.unit_brand_combo.setToolTip("Select or type AC brand name")
        u_input_row.addWidget(self.unit_brand_combo, 2)

        # Tonnage Dropdown
        self.unit_ton_combo = QComboBox()
        self.unit_ton_combo.addItems(["0.8 Ton", "1.0 Ton", "1.5 Ton", "2.0 Ton", "2.5 Ton", "3.0 Ton", "4.0 Ton", "5.0 Ton"])
        self.unit_ton_combo.setCurrentIndex(2)  # Default 1.5 Ton
        self.unit_ton_combo.setStyleSheet(self._combo_style())
        self.unit_ton_combo.setToolTip("Select Tonnage / Capacity")
        u_input_row.addWidget(self.unit_ton_combo, 2)

        # Location / Room Dropdown
        self.unit_loc_combo = QComboBox()
        self.unit_loc_combo.setEditable(True)
        self.unit_loc_combo.addItems([
            "Master Bedroom", "Living Room", "Bedroom 2", "Kids Room", "Guest Room",
            "Office Cabin", "Server Room", "Conference Room", "Main Reception", "Dining Area"
        ])
        self.unit_loc_combo.setStyleSheet(self._combo_style())
        self.unit_loc_combo.setToolTip("Select or type room / indoor location")
        u_input_row.addWidget(self.unit_loc_combo, 2)

        # Serial / Model #
        self.unit_serial_input = QLineEdit()
        self.unit_serial_input.setPlaceholderText("Serial / Model #")
        self.unit_serial_input.setStyleSheet(self._input_style())
        u_input_row.addWidget(self.unit_serial_input, 2)

        # Add Unit Button
        add_unit_btn = QPushButton("➕ Add Unit")
        add_unit_btn.setCursor(Qt.PointingHandCursor)
        add_unit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ENTERPRISE_COLORS['success']};
                color: #ffffff;
                font-weight: 700;
                font-size: 8.5pt;
                padding: 7px 14px;
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['success_hover']};
            }}
        """)
        add_unit_btn.clicked.connect(self._add_unit)
        u_input_row.addWidget(add_unit_btn, 1)

        u_layout.addLayout(u_input_row)

        # Units Counter Bar
        u_meta_bar = QHBoxLayout()
        self.units_count_lbl = QLabel("❄️  0 AC Units Covered")
        self.units_count_lbl.setStyleSheet(f"font-size: 8.5pt; font-weight: 700; color: {ENTERPRISE_COLORS['primary']};")
        u_meta_bar.addWidget(self.units_count_lbl)
        u_meta_bar.addStretch()

        self.btn_auto_price_mini = QPushButton("⚡ Auto Suggest Price for Units")
        self.btn_auto_price_mini.setCursor(Qt.PointingHandCursor)
        self.btn_auto_price_mini.setStyleSheet(f"""
            QPushButton {{
                background-color: {ENTERPRISE_COLORS['primary_light']};
                color: {ENTERPRISE_COLORS['primary']};
                border: 1px solid {ENTERPRISE_COLORS['primary_border']};
                border-radius: 6px;
                padding: 3px 10px;
                font-size: 8pt;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['primary']};
                color: #ffffff;
            }}
        """)
        self.btn_auto_price_mini.clicked.connect(self._auto_calculate_price)
        u_meta_bar.addWidget(self.btn_auto_price_mini)
        u_layout.addLayout(u_meta_bar)

        # Units Table
        self.units_table = QTableWidget()
        self.units_table.setColumnCount(6)
        self.units_table.setHorizontalHeaderLabels(['#', 'AC Type', 'Brand', 'Capacity', 'Location / Room', 'Serial / Model #', 'Action'][:6])
        self.units_table.verticalHeader().setVisible(False)
        self.units_table.setShowGrid(True)
        self.units_table.setAlternatingRowColors(True)
        self.units_table.setFixedHeight(140)
        self._style_white_table(self.units_table)

        uhdr = self.units_table.horizontalHeader()
        uhdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        uhdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        uhdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        uhdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        uhdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        uhdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        u_layout.addWidget(self.units_table)

        grid.addWidget(unit_card, 1, 0)

        # ── Card 4: Commercials, Pricing & Payment ───────────────────────────
        fin_card = self._create_card("💰  Commercials, Pricing & Payment", "Set contract value, taxes, payment mode & advance deposit")
        f_layout = QFormLayout(fin_card)
        f_layout.setContentsMargins(16, 14, 16, 14)
        f_layout.setSpacing(9)

        # Base Amount with Smart Price Helper
        amt_row = QHBoxLayout()
        amt_row.setSpacing(8)

        self.contract_value_input = QDoubleSpinBox()
        self.contract_value_input.setRange(0, 9999999)
        self.contract_value_input.setPrefix(f"{self.currency_symbol} ")
        self.contract_value_input.setDecimals(2)
        self.contract_value_input.setStyleSheet(self._spin_style())
        self.contract_value_input.valueChanged.connect(self._calc_totals)
        amt_row.addWidget(self.contract_value_input, 3)

        self.btn_auto_price = QPushButton("⚡ Auto Calc")
        self.btn_auto_price.setToolTip("Auto-calculate recommended AMC price based on covered ACs and plan")
        self.btn_auto_price.setCursor(Qt.PointingHandCursor)
        self.btn_auto_price.setStyleSheet(self._secondary_button_style())
        self.btn_auto_price.clicked.connect(self._auto_calculate_price)
        amt_row.addWidget(self.btn_auto_price, 1)
        f_layout.addRow("Base Contract Value:", amt_row)

        # GST Rate Dropdown
        self.gst_combo = QComboBox()
        self.gst_combo.addItems(["18% (Standard GST)", "12% (Concessional)", "5% (Minimal)", "28% (Luxury)", "No GST / Nil Exempted"])
        self.gst_combo.setCurrentIndex(0)
        self.gst_combo.setStyleSheet(self._combo_style())
        self.gst_combo.currentTextChanged.connect(self._calc_totals)
        f_layout.addRow("Applicable GST:", self.gst_combo)

        # Total Contract Amount Label
        self.total_label = QLabel(f"{self.currency_symbol}0.00")
        self.total_label.setStyleSheet(f"font-size: 13pt; font-weight: 800; color: {ENTERPRISE_COLORS['primary']}; font-family: {FONT_FAMILY};")
        f_layout.addRow("Total Agreement Value:", self.total_label)

        # Advance Deposit & Payment Mode Row
        pay_row = QHBoxLayout()
        pay_row.setSpacing(8)

        self.advance_input = QDoubleSpinBox()
        self.advance_input.setRange(0, 9999999)
        self.advance_input.setPrefix(f"{self.currency_symbol} ")
        self.advance_input.setDecimals(2)
        self.advance_input.setStyleSheet(self._spin_style())
        self.advance_input.valueChanged.connect(self._calc_totals)
        pay_row.addWidget(self.advance_input, 2)

        self.payment_mode_combo = QComboBox()
        self.payment_mode_combo.addItems([
            "Cash",
            "UPI / QR Code (GPay, PhonePe, Paytm)",
            "Online / Net Banking (NEFT / IMPS)",
            "Bank Cheque",
            "Credit / Debit Card",
            "Pending / Pay Later"
        ])
        self.payment_mode_combo.setStyleSheet(self._combo_style())
        pay_row.addWidget(self.payment_mode_combo, 3)
        f_layout.addRow("Advance & Mode:", pay_row)

        # Balance Due Badge
        self.balance_label = QLabel(f"{self.currency_symbol}0.00")
        self.balance_label.setStyleSheet(f"font-size: 11pt; font-weight: 800; color: {ENTERPRISE_COLORS['warning']}; font-family: {FONT_FAMILY};")
        f_layout.addRow("Outstanding Balance:", self.balance_label)

        grid.addWidget(fin_card, 1, 1)

        # ── Card 5: Service Scope & Inclusions Checklist ─────────────────────
        service_card = self._create_card("🛠️  Service Scope & Inclusions Checklist", "Choose pre-configured plan templates or append service chips")
        s_layout = QVBoxLayout(service_card)
        s_layout.setContentsMargins(16, 14, 16, 14)
        s_layout.setSpacing(8)

        # Template Dropdown
        tpl_row = QHBoxLayout()
        tpl_row.setSpacing(8)
        tpl_lbl = QLabel("Scope Template:")
        tpl_lbl.setStyleSheet(f"font-size: 8.5pt; font-weight: 700; color: {ENTERPRISE_COLORS['text_secondary']};")
        tpl_row.addWidget(tpl_lbl)

        self.scope_template_combo = QComboBox()
        self.scope_template_combo.addItems([
            "-- Select Scope / Checklist Template --",
            "Comprehensive AMC (Full Spares + Gas + Jet Wash + Electricals)",
            "Non-Comprehensive AMC (Labor + Jet Wash + Filter Sanitization)",
            "Commercial High-Uptime Facility AMC (Continuous Preventive Care)",
            "Residential Standard Seasonal AMC (2 Jet Washes + Gas Check)"
        ])
        self.scope_template_combo.setStyleSheet(self._combo_style())
        self.scope_template_combo.currentTextChanged.connect(self._apply_scope_template)
        tpl_row.addWidget(self.scope_template_combo, 1)
        s_layout.addLayout(tpl_row)

        # Inclusions Chips
        chips_row = QHBoxLayout()
        chips_row.setSpacing(6)
        chips = [
            "Wet Jet Service", "Chemical Wash", "Gas Check", "Capacitor/Wiring", "Drain Flushing", "Emergency 4h SLA"
        ]
        for chip in chips:
            btn = QPushButton(f"+ {chip}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ENTERPRISE_COLORS['primary_light']};
                    color: {ENTERPRISE_COLORS['primary']};
                    border: 1px solid {ENTERPRISE_COLORS['primary_border']};
                    border-radius: 10px;
                    padding: 3px 8px;
                    font-size: 7.5pt;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    background-color: #dbeafe;
                }}
            """)
            btn.clicked.connect(lambda ch, c=chip: self._append_service_chip(c))
            chips_row.addWidget(btn)
        chips_row.addStretch()
        s_layout.addLayout(chips_row)

        self.services_text = QTextEdit()
        self.services_text.setPlaceholderText("Enter included services, parts coverage, and customer specific notes...")
        self.services_text.setFixedHeight(85)
        self.services_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['text']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                padding: 8px 10px;
                font-size: 9pt;
                font-family: {FONT_FAMILY};
                line-height: 1.4;
            }}
        """)
        self.services_text.setText(
            "1. Complete High-Pressure Jet Pump Indoor & Outdoor Wet Service\n"
            "2. Refrigerant Gas Pressure Check & Operating Ampere Verification\n"
            "3. Electrical Wiring, Capacitor & Motor Inspection\n"
            "4. Antibacterial Air Filter Cleaning & Drain Tray Flushing"
        )
        s_layout.addWidget(self.services_text)

        grid.addWidget(service_card, 2, 0)

        # ── Card 6: Planned Visit Schedule Live Preview ──────────────────────
        schedule_card = self._create_card("📅  Projected Visit Schedule Preview", "Live preview of periodic preventive visits that will be auto-scheduled")
        sch_layout = QVBoxLayout(schedule_card)
        sch_layout.setContentsMargins(16, 14, 16, 14)
        sch_layout.setSpacing(8)

        self.projected_visits_table = QTableWidget()
        self.projected_visits_table.setColumnCount(4)
        self.projected_visits_table.setHorizontalHeaderLabels(['Visit #', 'Projected Date', 'Assigned Technician', 'Planned Maintenance Scope'])
        self.projected_visits_table.verticalHeader().setVisible(False)
        self.projected_visits_table.setShowGrid(True)
        self.projected_visits_table.setAlternatingRowColors(True)
        self.projected_visits_table.setFixedHeight(120)
        self._style_white_table(self.projected_visits_table)

        pj_hdr = self.projected_visits_table.horizontalHeader()
        pj_hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        pj_hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        pj_hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        pj_hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        sch_layout.addWidget(self.projected_visits_table)

        grid.addWidget(schedule_card, 2, 1)

        layout.addLayout(grid)

        # ── Bottom Action Bar ────────────────────────────────────────────────
        action_bar = QHBoxLayout()
        action_bar.setContentsMargins(0, 8, 0, 0)
        action_bar.setSpacing(12)

        self.btn_reset_form = QPushButton("🔄  Reset Form")
        self.btn_reset_form.setCursor(Qt.PointingHandCursor)
        self.btn_reset_form.setStyleSheet(self._secondary_button_style())
        self.btn_reset_form.clicked.connect(self._reset_new_contract_form)
        action_bar.addWidget(self.btn_reset_form)

        action_bar.addStretch()

        # Action 1: Regular Save
        self.btn_save_amc = QPushButton("💾  Save AMC Contract")
        self.btn_save_amc.setCursor(Qt.PointingHandCursor)
        self.btn_save_amc.setStyleSheet(f"""
            QPushButton {{
                background-color: {ENTERPRISE_COLORS['primary']};
                color: #ffffff;
                font-size: 10pt;
                font-weight: 800;
                font-family: "Segoe UI Emoji", {FONT_FAMILY};
                padding: 10px 20px;
                min-height: 22px;
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['primary_hover']};
            }}
        """)
        self.btn_save_amc.clicked.connect(lambda: self._save_amc(open_preview=False))
        action_bar.addWidget(self.btn_save_amc)

        # Action 2: Save & Immediately Preview / Share PDF
        self.btn_save_and_preview = QPushButton("📄  Save & Open Form / PDF")
        self.btn_save_and_preview.setToolTip("Save contract and immediately launch the live preview, print & WhatsApp sharing certificate")
        self.btn_save_and_preview.setCursor(Qt.PointingHandCursor)
        self.btn_save_and_preview.setStyleSheet(f"""
            QPushButton {{
                background-color: {ENTERPRISE_COLORS['success']};
                color: #ffffff;
                font-size: 10pt;
                font-weight: 800;
                font-family: "Segoe UI Emoji", {FONT_FAMILY};
                padding: 10px 22px;
                min-height: 22px;
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['success_hover']};
            }}
        """)
        self.btn_save_and_preview.clicked.connect(lambda: self._save_amc(open_preview=True))
        action_bar.addWidget(self.btn_save_and_preview)

        layout.addLayout(action_bar)
        layout.addSpacing(32)

        scroll.setWidget(content)

        # Initial calculation and visit schedule preview
        self._update_projected_visits_preview()
        self._calc_totals()

        return scroll

    def _create_card(self, title, subtitle):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 12px;
            }}
        """)
        return card

    def _open_quick_add_customer(self):
        """Open Add Customer Dialog and auto-select new customer on success"""
        try:
            from views.customer_view import AddCustomerDialog
            dlg = AddCustomerDialog(self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self.show_success_message("Customer registered successfully! Updating customer directory...")
                self._search_customer()
        except Exception as e:
            self.show_error_message(f"Could not open Add Customer dialog: {str(e)}")

    def _on_contract_type_changed(self, idx):
        """Update checklist template and suggested rate when contract type changes"""
        raw = self.contract_type_combo.currentText()
        if "Comprehensive" in raw and "Non" not in raw:
            self.scope_template_combo.setCurrentIndex(1)
        elif "Non-Comprehensive" in raw:
            self.scope_template_combo.setCurrentIndex(2)

    def _on_duration_preset_changed(self, idx):
        """Map duration preset dropdown to spinbox and end date"""
        dur_map = {0: 1, 1: 2, 2: 3, 3: 1}  # 6-months still maps to 1 yr duration in spin
        if idx in dur_map:
            self.duration_spin.blockSignals(True)
            self.duration_spin.setValue(dur_map[idx])
            self.duration_spin.blockSignals(False)
            self._update_end_date()

    def _on_visit_frequency_preset_changed(self, idx):
        """Map visit frequency preset dropdown to spinbox"""
        freq_map = {0: 4, 1: 3, 2: 2, 3: 6, 4: 12}
        if idx in freq_map:
            self.services_per_year.blockSignals(True)
            self.services_per_year.setValue(freq_map[idx])
            self.services_per_year.blockSignals(False)
            self._update_projected_visits_preview()

    def _on_services_spin_changed(self, val):
        self._update_projected_visits_preview()

    def _auto_calculate_price(self, show_msg=False):
        """Auto-calculate suggested AMC base contract value"""
        units_cnt = len(self.amc_units)
        if units_cnt == 0:
            if show_msg:
                self.show_warning_message("Please add at least one AC unit to calculate suggested pricing.")
            return

        raw_ctype = self.contract_type_combo.currentText()
        is_comp = "Comprehensive" in raw_ctype and "Non" not in raw_ctype
        dur = self.duration_spin.value()

        rate_per_unit = 4500.0 if is_comp else 2200.0
        suggested_total = rate_per_unit * units_cnt * dur
        self.contract_value_input.setValue(suggested_total)
        plan_name = "Comprehensive" if is_comp else "Non-Comprehensive"
        if show_msg:
            self.show_success_message(
                f"Suggested Price Auto-Calculated:\n\n"
                f"• Plan: {plan_name} AMC\n"
                f"• Rate: ₹{rate_per_unit:,.0f} / unit / year\n"
                f"• Units Covered: {units_cnt} AC(s)\n"
                f"• Duration: {dur} Year(s)\n\n"
                f"Total Base Value: ₹{suggested_total:,.2f}"
            )

    def _apply_scope_template(self, template_name):
        """Apply pre-configured service checklist based on chosen template"""
        if not template_name or "--" in template_name:
            return
        if "Comprehensive" in template_name and "Non" not in template_name:
            self.services_text.setPlainText(
                "1. Comprehensive High-Pressure Jet Pump Indoor & Outdoor Wet Service\n"
                "2. Refrigerant Gas Pressure Check & Leakage Detection (Gas Top-Up Included)\n"
                "3. Electrical Components (Capacitor, Contactor, Terminal Blocks) Replacement Included\n"
                "4. Fan Motor, Blower Wheel Servicing & Lubrication\n"
                "5. Antibacterial Air Filter Chemical Cleaning & Drain Pipe Flushing\n"
                "6. Priority Emergency Breakdown Visits with Zero Labor Charge"
            )
        elif "Non-Comprehensive" in template_name:
            self.services_text.setPlainText(
                "1. Complete High-Pressure Jet Pump Indoor & Outdoor Wet Service\n"
                "2. Air Filter Cleaning, Sanitization & Drain Tray Flushing\n"
                "3. Electrical Wiring & Operating Ampere Verification\n"
                "4. Refrigerant Operating Pressure Inspection (Gas charging extra if required)\n"
                "5. Routine Preventive Performance Profiling (Spare parts charged extra at discount)"
            )
        elif "Commercial" in template_name:
            self.services_text.setPlainText(
                "1. Monthly / Bi-Monthly Heavy Usage Cleaning & Coil Degreasing\n"
                "2. Continuous Temperature Delta-T & CFM Airflow Verification\n"
                "3. Belt Tension, Bearing Lubrication & Blower Balancing\n"
                "4. Control Panel & Thermostat Sensor Calibration\n"
                "5. Dedicated 4-Hour Response SLA for Unscheduled Downtime"
            )
        elif "Residential" in template_name:
            self.services_text.setPlainText(
                "1. Pre-Summer Deep Chemical Coil Wash & Outdoor Unit Jet Cleaning\n"
                "2. Post-Summer Routine Service, Filter Cleaning & Drain De-clogging\n"
                "3. Gas Pressure Check & General Efficiency Audit"
            )

    def _append_service_chip(self, chip):
        cur = self.services_text.toPlainText().strip()
        lines = [l for l in cur.split("\n") if l.strip()]
        new_line = f"{len(lines) + 1}. {chip}"
        if cur:
            self.services_text.setPlainText(f"{cur}\n{new_line}")
        else:
            self.services_text.setPlainText(new_line)

    def _reset_new_contract_form(self):
        self.amc_units = []
        self.units_table.setRowCount(0)
        self.units_count_lbl.setText("❄️  0 AC Units Covered")
        self.contract_value_input.setValue(0)
        self.advance_input.setValue(0)
        self.contract_type_combo.setCurrentIndex(0)
        self.duration_preset_combo.setCurrentIndex(0)
        self.duration_spin.setValue(1)
        self.visit_frequency_combo.setCurrentIndex(0)
        self.services_per_year.setValue(4)
        self.customer_combo.setCurrentIndex(0)
        self.customer_search_input.clear()
        self.customer_details_label.setText("No customer selected. Choose from dropdown above or click '➕ New Customer'.")
        self.start_date_input.setDate(QDate.currentDate())
        self._update_end_date()
        self._calc_totals()

    def _update_projected_visits_preview(self):
        """Update live table of projected visit schedules"""
        if not hasattr(self, 'projected_visits_table'):
            return
        start_qdate = self.start_date_input.date()
        dur_years = self.duration_spin.value()
        svcs_per_year = self.services_per_year.value()
        total_visits = max(1, svcs_per_year * dur_years)

        self.projected_visits_table.setRowCount(0)
        start_pydate = datetime(start_qdate.year(), start_qdate.month(), start_qdate.day())
        end_pydate = start_pydate + timedelta(days=round(dur_years * 365.25)) - timedelta(days=1)
        total_days = (end_pydate - start_pydate).days
        interval_days = total_days // total_visits if total_visits > 0 else 90

        tech_text = "Assigned by Manager"
        if hasattr(self, 'technician_combo') and self.technician_combo.currentIndex() > 0:
            tech_text = self.technician_combo.currentText().replace("🔧", "").replace("👤", "").strip()

        for i in range(1, total_visits + 1):
            v_date = start_pydate + timedelta(days=interval_days * (i - 1))
            row = self.projected_visits_table.rowCount()
            self.projected_visits_table.insertRow(row)

            # Visit #
            item_num = QTableWidgetItem(f"Visit #{i}")
            item_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_num.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            item_num.setForeground(QColor(ENTERPRISE_COLORS['primary']))
            self.projected_visits_table.setItem(row, 0, item_num)

            # Projected Date
            item_date = QTableWidgetItem(v_date.strftime("%d-%m-%Y"))
            item_date.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.projected_visits_table.setItem(row, 1, item_date)

            # Technician
            item_tech = QTableWidgetItem(tech_text)
            self.projected_visits_table.setItem(row, 2, item_tech)

            # Service Scope
            if i == 1:
                scope_desc = "Initial Deep Jet Wash & System Operating Inspection"
            elif i == total_visits:
                scope_desc = "Annual Contract Closure Preventive Inspection & Profiling"
            elif i % 2 == 0:
                scope_desc = "Periodic Filter Cleaning, Operating Pressure Check & Descaling"
            else:
                scope_desc = "Intermediate Chemical Wash & Electrical Ampere Verification"

            item_scope = QTableWidgetItem(scope_desc)
            self.projected_visits_table.setItem(row, 3, item_scope)

    def _calc_totals(self):
        amt = self.contract_value_input.value()
        gst_str = self.gst_combo.currentText()
        gst_pct = 0 if "No GST" in gst_str else int(gst_str.split("%")[0].strip())
        gst_amt = amt * gst_pct / 100
        total = amt + gst_amt
        self.total_label.setText(f"{self.currency_symbol}{total:,.2f}")
        bal = max(0.0, total - self.advance_input.value())

        if bal <= 0 and total > 0:
            self.balance_label.setText(f"{self.currency_symbol}0.00  (✓ Fully Settled)")
            self.balance_label.setStyleSheet(f"font-size: 11pt; font-weight: 800; color: {ENTERPRISE_COLORS['success']}; font-family: {FONT_FAMILY};")
        else:
            self.balance_label.setText(f"{self.currency_symbol}{bal:,.2f}")
            self.balance_label.setStyleSheet(f"font-size: 11pt; font-weight: 800; color: {ENTERPRISE_COLORS['warning']}; font-family: {FONT_FAMILY};")

    def _update_end_date(self):
        start = self.start_date_input.date()
        dur = self.duration_spin.value()
        end = start.addYears(dur).addDays(-1)
        self.end_date_input.setDate(end)
        self._update_projected_visits_preview()

    def _search_customer(self):
        search_term = self.customer_search_input.text().strip()
        self.run_in_thread(
            lambda: self._search_customer_thread(search_term),
            self._update_customer_combo
        )

    def _search_customer_thread(self, search_term):
        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            query = "SELECT id, name, mobile, email, address, landmark FROM customers WHERE is_active = TRUE"
            params = []
            if search_term:
                query += " AND (name LIKE %s OR mobile LIKE %s OR address LIKE %s)"
                params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])
            query += " ORDER BY name LIMIT 100"
            return db.execute_query(query, params, fetch_all=True)

    def _update_customer_combo(self, customers):
        self.customer_list = customers or []
        self.customer_combo.blockSignals(True)
        self.customer_combo.clear()
        self.customer_combo.addItem("-- Choose Customer (Select or Search) --", "")
        for c in self.customer_list:
            c_name = c.get('name', 'Unknown')
            c_mob = c.get('mobile', '')
            c_addr = str(c.get('address') or '').strip()
            display_text = f"{c_name} — 📞 {c_mob}"
            if c_addr:
                short_addr = c_addr if len(c_addr) <= 25 else c_addr[:23] + "..."
                display_text += f" ({short_addr})"
            self.customer_combo.addItem(display_text, c['id'])
        self.customer_combo.blockSignals(False)

    def _on_customer_select(self):
        cid = self.customer_combo.currentData()
        if not cid:
            self.customer_details_label.setText("No customer selected. Choose from dropdown above or click '➕ New Customer'.")
            return
        c = next((c for c in self.customer_list if c['id'] == cid), None)
        if c:
            name = c.get('name', 'Customer')
            mob = c.get('mobile', 'N/A')
            email = c.get('email', '')
            addr = c.get('address', '')
            land = c.get('landmark', '')

            html = f"""
            <div style="line-height: 1.5;">
                <div style="font-size: 10pt; font-weight: 800; color: #1e3a8a;">👤 {name}</div>
                <div style="font-size: 8.5pt; color: #334155; margin-top: 2px;">
                    📞 <b>Mobile:</b> {mob} {f"&nbsp;|&nbsp; ✉️ <b>Email:</b> {email}" if email else ""}
                </div>
                <div style="font-size: 8.5pt; color: #475569; margin-top: 2px;">
                    📍 <b>Service Site:</b> {addr if addr else 'Address not specified'}
                    {f"&nbsp;(<b>Landmark:</b> {land})" if land else ""}
                </div>
            </div>
            """
            self.customer_details_label.setText(html)

    def _add_unit(self):
        utype = self.unit_type_combo.currentText()
        ubrand = self.unit_brand_combo.currentText().strip() or "Standard AC"
        uton = self.unit_ton_combo.currentText()
        uloc = self.unit_loc_combo.currentText().strip() or "Customer Site"
        userial = self.unit_serial_input.text().strip()

        row = self.units_table.rowCount()
        self.units_table.insertRow(row)

        # Col 0: Unit #
        it_idx = QTableWidgetItem(f"#{row + 1}")
        it_idx.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        it_idx.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        it_idx.setForeground(QColor(ENTERPRISE_COLORS['primary']))
        self.units_table.setItem(row, 0, it_idx)

        # Col 1: AC Type
        self.units_table.setItem(row, 1, QTableWidgetItem(utype))

        # Col 2: Brand
        it_brand = QTableWidgetItem(ubrand)
        it_brand.setFont(QFont("Segoe UI", 8.5, QFont.Weight.Bold))
        self.units_table.setItem(row, 2, it_brand)

        # Col 3: Capacity
        it_cap = QTableWidgetItem(uton)
        it_cap.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.units_table.setItem(row, 3, it_cap)

        # Col 4: Location / Room
        self.units_table.setItem(row, 4, QTableWidgetItem(uloc))

        # Col 5: Serial / Model #
        self.units_table.setItem(row, 5, QTableWidgetItem(userial or "--"))

        self.amc_units.append({
            'type': utype,
            'ac_type': utype,
            'brand': ubrand,
            'ton': uton.replace(' Ton', '').strip(),
            'indoor_location': uloc,
            'location': uloc,
            'serial': userial,
            'serial_number': userial,
            'model': userial
        })
        self.unit_serial_input.clear()
        self.units_count_lbl.setText(f"❄️  {len(self.amc_units)} AC Unit(s) Covered")

    def _remove_unit(self, row):
        if 0 <= row < self.units_table.rowCount():
            self.units_table.removeRow(row)
            if 0 <= row < len(self.amc_units):
                self.amc_units.pop(row)
            self.units_count_lbl.setText(f"❄️  {len(self.amc_units)} AC Unit(s) Covered")

    def _save_amc(self, open_preview=False):
        from database.db_connection import DatabaseConnection
        from controllers.amc_controller import AMCController

        cid = self.customer_combo.currentData()
        if not cid:
            self.show_warning_message("Please select a customer first.")
            return
        if not self.amc_units:
            self.show_warning_message("Please add at least one AC unit to the contract.")
            return
        if self.contract_value_input.value() <= 0:
            self.show_warning_message("Please enter a valid contract base amount.")
            return

        gst_str = self.gst_combo.currentText()
        gst_pct = 0 if "No GST" in gst_str else int(gst_str.split("%")[0].strip())
        amt = self.contract_value_input.value()
        pay_mode = self.payment_mode_combo.currentText() if hasattr(self, 'payment_mode_combo') else 'Cash'
        tech_id = self.technician_combo.currentData() if hasattr(self, 'technician_combo') else None

        # Clean contract type for database standard
        raw_ctype = self.contract_type_combo.currentText()
        if "Comprehensive" in raw_ctype and "Non" not in raw_ctype:
            contract_type = "Comprehensive"
        elif "Non-Comprehensive" in raw_ctype:
            contract_type = "Non-Comprehensive"
        else:
            contract_type = raw_ctype.split("(")[0].strip()

        contract_data = {
            'customer_id': cid,
            'contract_type': contract_type,
            'start_date': self.start_date_input.date().toString("dd-MM-yyyy"),
            'contract_duration': self.duration_spin.value(),
            'no_of_units': len(self.amc_units),
            'services_per_year': self.services_per_year.value(),
            'contract_amount': amt,
            'gst_percent': gst_pct,
            'advance_paid': self.advance_input.value(),
            'payment_mode': pay_mode,
            'technician_id': tech_id,
            'notes': self.services_text.toPlainText().strip(),
            'units': self.amc_units
        }

        ctrl = AMCController(DatabaseConnection())
        result_id, error = ctrl.create_amc_contract(contract_data)
        if result_id:
            amc_id_str = f"AMC{result_id:04d}" if isinstance(result_id, int) else str(result_id)
            total_visits_cnt = self.services_per_year.value() * self.duration_spin.value()
            self.show_success_message(
                f"AMC Contract created successfully!\n\n"
                f"• Contract ID: {amc_id_str}\n"
                f"• AC Units: {len(self.amc_units)}\n"
                f"• Preventive Visits: {total_visits_cnt} Scheduled\n"
                f"• Status: Active"
            )
            self._reset_new_contract_form()
            self.load_amc_data()
            self._load_visits()
            self.tabs.setCurrentIndex(0)

            if open_preview:
                self._preview_amc_pdf(amc_id_str)
        else:
            self.show_error_message(f"Failed to create AMC contract: {error}")

    # ═══════════════════════════════════════════════════════════════════════════
    # DATA RETRIEVAL & TABLE POPULATION
    # ═══════════════════════════════════════════════════════════════════════════
    def load_amc_data(self):
        search = self.amc_search_input.text().strip()
        status = self.amc_status_filter.currentText()
        ctype = self.amc_type_filter.currentText()
        self.run_in_thread(
            lambda: self._load_amc_data_thread(search, status, ctype),
            self._update_amc_table
        )

    def _load_amc_data_thread(self, search, status, ctype):
        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            from controllers.amc_controller import AMCController
            ctrl = AMCController(db)
            if search:
                data = ctrl.search_amc_contracts(search)
            else:
                data = ctrl.get_all_amc_contracts()

            data = data or []
            if status == "Active":
                data = [a for a in data if a.get('amc_status') == 'Active']
            elif status == "Expiring Soon":
                data = [a for a in data if a.get('amc_status') == 'Expiring Soon']
            elif status == "Expired":
                data = [a for a in data if a.get('amc_status') == 'Expired']
            elif status == "Completed":
                data = [a for a in data if a.get('amc_status') == 'Completed']

            if ctype != "All Types":
                data = [a for a in data if a.get('contract_type') == ctype]

            stats = ctrl.get_amc_stats()
            # Count scheduled visits
            visits_row = db.execute_query(
                "SELECT COUNT(*) as count FROM amc_visits WHERE visit_status = 'Scheduled' AND is_active = TRUE",
                fetch_one=True
            )
            scheduled_count = visits_row['count'] if visits_row else 0

            return {'contracts': data, 'stats': stats, 'scheduled_visits': scheduled_count}

    def _update_amc_table(self, result):
        if isinstance(result, dict):
            amc_list = result.get('contracts', [])
            stats = result.get('stats', {})
            scheduled_count = result.get('scheduled_visits', 0)
        else:
            amc_list = result or []
            stats = {}
            scheduled_count = 0

        self.amc_list = amc_list

        # Update KPI Summary Cards
        self.amc_summary_labels['amc_total'].setText(str(stats.get('total_active', 0) + stats.get('expiring_soon', 0) + len(amc_list)))
        self.amc_summary_labels['amc_active'].setText(str(stats.get('total_active', 0)))
        self.amc_summary_labels['amc_expiring'].setText(str(stats.get('expiring_soon', 0)))
        self.amc_summary_labels['amc_revenue'].setText(f"{self.currency_symbol}{float(stats.get('total_revenue') or 0):,.0f}")
        self.amc_summary_labels['amc_scheduled_visits'].setText(str(scheduled_count))

        self.tabs.setTabText(0, f"📋  All Contracts ({len(amc_list)})")

        self.amc_table.setUpdatesEnabled(False)
        try:
            self.amc_table.setRowCount(0)
            for amc in amc_list:
                row = self.amc_table.rowCount()
                self.amc_table.insertRow(row)

                # 0. AMC ID
                id_item = QTableWidgetItem(f"📄 {amc['amc_id']}")
                id_item.setData(Qt.ItemDataRole.UserRole, amc['id'])
                id_item.setForeground(QColor(ENTERPRISE_COLORS['primary']))
                font = id_item.font()
                font.setBold(True)
                id_item.setFont(font)
                id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                id_item.setToolTip(f"<b>AMC Contract ID:</b> {amc['amc_id']}<br>Double-click to inspect 360° details.")
                self.amc_table.setItem(row, 0, id_item)

                # 1. Customer Details (Name on Line 1, Phone on Line 2, Address in Tooltip)
                c_name = amc.get('customer_name', 'Unknown')
                c_mob = amc.get('customer_mobile', '')
                c_addr = amc.get('customer_address', '')
                phone_str = f"📞 {c_mob}" if c_mob else "📞 No Phone"
                cust_item = QTableWidgetItem(f"{c_name}\n{phone_str}")
                cust_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                cust_item.setToolTip(f"<b>Customer:</b> {c_name}<br><b>Phone:</b> {c_mob or 'N/A'}<br><b>Address:</b> {c_addr or 'No address provided'}")
                self.amc_table.setItem(row, 1, cust_item)

                # 2. Contract Type
                ctype = amc.get('contract_type', 'Comprehensive')
                type_item = QTableWidgetItem(ctype)
                type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                type_item.setToolTip(f"<b>Coverage Level:</b> {ctype}")
                self.amc_table.setItem(row, 2, type_item)

                # 3. Period / Dates
                start_d = Formatters.format_date(amc.get('start_date'))
                end_d = Formatters.format_date(amc.get('end_date'))
                dur = amc.get('contract_duration', 1)
                period_item = QTableWidgetItem(f"{start_d}\n→ {end_d}")
                period_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                period_item.setToolTip(f"<b>Contract Validity:</b><br>Start: {start_d}<br>End: {end_d}<br>Duration: {dur} Year(s)")
                self.amc_table.setItem(row, 3, period_item)

                # 4. Units
                units_cnt = amc.get('no_of_units', 1)
                units_item = QTableWidgetItem(f"❄️ {units_cnt} Unit(s)")
                units_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                units_item.setToolTip(f"<b>Air Conditioner Units:</b> {units_cnt} covered unit(s)")
                self.amc_table.setItem(row, 4, units_item)

                # 5. Services (Remaining / Total)
                rem = amc.get('services_remaining', 0)
                tot_s = amc.get('services_per_year', 0)
                serv_item = QTableWidgetItem(f"🛠️ {rem} / {tot_s} Rem.")
                serv_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                serv_item.setToolTip(f"<b>Preventive Visits:</b><br>Remaining: {rem}<br>Total Per Year: {tot_s}")
                self.amc_table.setItem(row, 5, serv_item)

                # 6. Contract Scope / Notes
                notes_raw = amc.get('notes') or amc.get('terms_conditions') or "Standard AC Preventive Maintenance coverage"
                notes_clean = " • ".join([l.strip() for l in str(notes_raw).splitlines() if l.strip()])
                notes_item = QTableWidgetItem(notes_clean[:70] + ("..." if len(notes_clean) > 70 else ""))
                notes_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                notes_item.setToolTip(f"<b>Contract Scope & Inclusions:</b><br>{str(notes_raw).replace(chr(10), '<br>')}")
                self.amc_table.setItem(row, 6, notes_item)

                # 7. Total Amount
                tot_val = float(amc.get('total_amount', 0) or 0)
                amt_item = QTableWidgetItem(f"{self.currency_symbol}{tot_val:,.2f}")
                amt_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                font_amt = amt_item.font()
                font_amt.setBold(True)
                amt_item.setFont(font_amt)
                amt_item.setForeground(QColor(ENTERPRISE_COLORS['text']))
                amt_item.setToolTip(f"<b>Gross Agreement Value:</b> {self.currency_symbol}{tot_val:,.2f}")
                self.amc_table.setItem(row, 7, amt_item)

                # 8. Paid / Balance
                paid_val = float(amc.get('advance_paid', 0) or 0)
                bal_val = float(amc.get('balance_amount', 0) or 0)
                bal_text = f"Paid: {self.currency_symbol}{paid_val:,.0f}\nBal: {self.currency_symbol}{bal_val:,.0f}"
                bal_item = QTableWidgetItem(bal_text)
                bal_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                font_b = bal_item.font()
                font_b.setBold(True)
                bal_item.setFont(font_b)
                if bal_val > 0:
                    bal_item.setForeground(QColor(ENTERPRISE_COLORS['warning']))
                else:
                    bal_item.setForeground(QColor(ENTERPRISE_COLORS['success']))
                bal_item.setToolTip(f"<b>Payment Status:</b><br>Paid: {self.currency_symbol}{paid_val:,.2f}<br>Balance Due: {self.currency_symbol}{bal_val:,.2f}")
                self.amc_table.setItem(row, 8, bal_item)

                # 9. Status Badge (Centered Wrapper)
                status_badge = AMCStatusBadge(amc.get('amc_status', 'Active'))
                self.amc_table.setCellWidget(row, 9, _make_centered_cell_widget(status_badge))

                # 10. Quick Actions (3 Crisp Buttons: View, Pay, WhatsApp)
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(4, 2, 4, 2)
                actions_layout.setSpacing(4)
                actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

                btn_style_common = f"""
                    QPushButton {{
                        font-size: 8pt;
                        font-weight: 700;
                        font-family: "Segoe UI Emoji", "Segoe UI", {FONT_FAMILY};
                        padding: 3px 6px;
                        border-radius: 6px;
                    }}
                """

                view_btn = QPushButton("👁️ View")
                view_btn.setToolTip("View 360° Contract Details Inspector")
                view_btn.setCursor(Qt.PointingHandCursor)
                view_btn.setStyleSheet(f"""
                    {btn_style_common}
                    QPushButton {{
                        background-color: {ENTERPRISE_COLORS['primary_light']};
                        color: {ENTERPRISE_COLORS['primary']};
                        border: 1px solid {ENTERPRISE_COLORS['primary_border']};
                    }}
                    QPushButton:hover {{
                        background-color: {ENTERPRISE_COLORS['primary']};
                        color: #ffffff;
                    }}
                """)
                view_btn.clicked.connect(lambda ch, aid=amc['id']: self._show_amc_details(aid))
                actions_layout.addWidget(view_btn)

                pdf_btn = QPushButton("📄 Form")
                pdf_btn.setToolTip("Preview, Print, Download or WhatsApp Share official AMC Contract Agreement Form")
                pdf_btn.setCursor(Qt.PointingHandCursor)
                pdf_btn.setStyleSheet(f"""
                    {btn_style_common}
                    QPushButton {{
                        background-color: {ENTERPRISE_COLORS['purple_light']};
                        color: {ENTERPRISE_COLORS['purple']};
                        border: 1px solid {ENTERPRISE_COLORS['purple_border']};
                    }}
                    QPushButton:hover {{
                        background-color: {ENTERPRISE_COLORS['purple']};
                        color: #ffffff;
                    }}
                """)
                pdf_btn.clicked.connect(lambda ch, aid=amc['id']: self._preview_amc_pdf(aid))
                actions_layout.addWidget(pdf_btn)

                wa_btn = QPushButton("💬 WA")
                wa_btn.setToolTip("Share AMC Agreement Summary on WhatsApp")
                wa_btn.setCursor(Qt.PointingHandCursor)
                wa_btn.setStyleSheet(f"""
                    {btn_style_common}
                    QPushButton {{
                        background-color: #ecfdf5;
                        color: #059669;
                        border: 1px solid #a7f3d0;
                    }}
                    QPushButton:hover {{
                        background-color: #059669;
                        color: #ffffff;
                    }}
                """)
                wa_btn.clicked.connect(lambda ch, a=amc: self._send_whatsapp_amc(a))
                actions_layout.addWidget(wa_btn)

                self.amc_table.setCellWidget(row, 10, actions_widget)
        finally:
            self.amc_table.setUpdatesEnabled(True)

    def _load_visits(self):
        status = self.visit_status_combo.currentText()
        self.run_in_thread(
            lambda: self._load_visits_thread(status),
            self._update_visits_table
        )

    def _load_visits_thread(self, status):
        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            q = """
                SELECT v.*, ac.amc_id as amc_number, c.name as customer_name, c.mobile as customer_mobile, c.address as customer_address,
                       t.name as technician_name, t.mobile as technician_phone
                FROM amc_visits v
                JOIN amc_contracts ac ON v.amc_id = ac.id
                JOIN customers c ON ac.customer_id = c.id
                LEFT JOIN technicians t ON v.technician_id = t.id
                WHERE v.is_active = TRUE
            """
            params = []
            if status != "All":
                q += " AND v.visit_status = %s"
                params.append(status)
            q += " ORDER BY v.visit_date ASC"
            return db.execute_query(q, tuple(params) if params else None, fetch_all=True)

    def _update_visits_table(self, visits):
        self.visits_list = visits or []
        self.tabs.setTabText(1, f"📅  Visit Schedules ({len(self.visits_list)})")

        self.visits_table.setUpdatesEnabled(False)
        try:
            self.visits_table.setRowCount(0)
            for v in self.visits_list:
                row = self.visits_table.rowCount()
                self.visits_table.insertRow(row)

                # 0. Visit #
                v_num = v.get('visit_number', 1)
                id_item = QTableWidgetItem(f"Visit #{v_num}")
                id_item.setData(Qt.ItemDataRole.UserRole, v['id'])
                id_item.setForeground(QColor(ENTERPRISE_COLORS['primary']))
                font = id_item.font()
                font.setBold(True)
                id_item.setFont(font)
                id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                id_item.setToolTip(f"<b>Visit #{v_num}</b><br>Double-click to view or complete this maintenance visit.")
                self.visits_table.setItem(row, 0, id_item)

                # 1. AMC Contract Number
                amc_num = v.get('amc_number', '')
                contract_item = QTableWidgetItem(f"📄 {amc_num}")
                contract_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                contract_item.setForeground(QColor(ENTERPRISE_COLORS['text']))
                font_c = contract_item.font()
                font_c.setBold(True)
                contract_item.setFont(font_c)
                contract_item.setToolTip(f"<b>AMC Contract:</b> {amc_num}")
                self.visits_table.setItem(row, 1, contract_item)

                # 2. Customer Details (Name on line 1, Phone on line 2, Address in Tooltip)
                c_name = v.get('customer_name', 'Unknown')
                c_mob = v.get('customer_mobile', '')
                c_addr = v.get('customer_address', '')
                phone_str = f"📞 {c_mob}" if c_mob else "📞 No Phone"
                cust_item = QTableWidgetItem(f"{c_name}\n{phone_str}")
                cust_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                cust_item.setToolTip(f"<b>Customer:</b> {c_name}<br><b>Phone:</b> {c_mob or 'N/A'}<br><b>Address:</b> {c_addr or 'No address recorded'}")
                self.visits_table.setItem(row, 2, cust_item)

                # 3. Scheduled Date (with Overdue Detection)
                v_raw_date = v.get('visit_date')
                v_date = Formatters.format_date(v_raw_date)
                is_overdue = False
                if v.get('visit_status') == 'Scheduled' and v_raw_date:
                    try:
                        v_dt = datetime.strptime(str(v_raw_date)[:10], '%Y-%m-%d').date() if isinstance(v_raw_date, str) else v_raw_date
                        if v_dt < datetime.now().date():
                            is_overdue = True
                    except Exception:
                        pass

                date_text = f"🗓️ {v_date}\n⚠️ OVERDUE" if is_overdue else f"🗓️ {v_date}"
                d_item = QTableWidgetItem(date_text)
                d_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if is_overdue:
                    d_item.setForeground(QColor(ENTERPRISE_COLORS['danger']))
                    font_d = d_item.font()
                    font_d.setBold(True)
                    d_item.setFont(font_d)
                d_item.setToolTip(f"<b>Scheduled Date:</b> {v_date}" + ("<br><span style='color:red;'><b>⚠️ This visit is overdue!</b> Reschedule or complete immediately.</span>" if is_overdue else ""))
                self.visits_table.setItem(row, 3, d_item)

                # 4. Assigned Technician
                t_name = v.get('technician_name', '')
                t_phone = v.get('technician_phone', '')
                if t_name:
                    t_text = f"👤 {t_name}" + (f"\n📞 {t_phone}" if t_phone else "")
                    t_item = QTableWidgetItem(t_text)
                    t_item.setForeground(QColor(ENTERPRISE_COLORS['text']))
                    t_item.setToolTip(f"<b>Technician:</b> {t_name}<br><b>Phone:</b> {t_phone or 'N/A'}")
                else:
                    t_item = QTableWidgetItem("⚠️ Unassigned\n(Click to Assign)")
                    t_item.setForeground(QColor(ENTERPRISE_COLORS['warning']))
                    font_t = t_item.font()
                    font_t.setBold(True)
                    t_item.setFont(font_t)
                    t_item.setToolTip("No technician assigned. Use 'Assign Technician' below or right-click to allocate.")
                t_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.visits_table.setItem(row, 4, t_item)

                # 5. Status Badge (Centered Wrapper)
                badge = VisitStatusBadge(v.get('visit_status', 'Scheduled'))
                self.visits_table.setCellWidget(row, 5, _make_centered_cell_widget(badge))

                # 6. Work / Description / Notes (Full text visible)
                work = v.get('work_done', '')
                parts = v.get('parts_replaced', '')
                notes = v.get('notes', '')
                extra = float(v.get('extra_charge', 0) or 0)

                desc_parts = []
                if work:
                    desc_parts.append(f"Work: {work}")
                if parts:
                    desc_parts.append(f"Parts: {parts}")
                if extra > 0:
                    desc_parts.append(f"Extra: {self.currency_symbol}{extra:,.2f}")
                if notes:
                    desc_parts.append(f"Notes: {notes}")

                desc_str = " • ".join(desc_parts) if desc_parts else "Scheduled AC Preventive Maintenance Service"
                work_item = QTableWidgetItem(desc_str)
                work_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                work_item.setToolTip(
                    f"<b>Work Performed:</b> {work or '--'}<br>"
                    f"<b>Parts Replaced:</b> {parts or '--'}<br>"
                    f"<b>Extra Charge:</b> {self.currency_symbol}{extra:,.2f}<br>"
                    f"<b>Notes:</b> {notes or '--'}"
                )
                self.visits_table.setItem(row, 6, work_item)

                # 7. Quick Actions (Centered with crisp labeled buttons)
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(4, 2, 4, 2)
                actions_layout.setSpacing(5)
                actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

                v_btn_common = f"""
                    QPushButton {{
                        font-size: 8pt;
                        font-weight: 700;
                        font-family: "Segoe UI Emoji", "Segoe UI", {FONT_FAMILY};
                        padding: 3px 7px;
                        border-radius: 6px;
                    }}
                """

                if v.get('visit_status') == 'Scheduled':
                    done_btn = QPushButton("✓ Done")
                    done_btn.setToolTip("Mark this visit as completed and log work details")
                    done_btn.setCursor(Qt.PointingHandCursor)
                    done_btn.setStyleSheet(f"""
                        {v_btn_common}
                        QPushButton {{
                            background-color: {ENTERPRISE_COLORS['success_light']};
                            color: {ENTERPRISE_COLORS['success']};
                            border: 1px solid {ENTERPRISE_COLORS['success_border']};
                        }}
                        QPushButton:hover {{
                            background-color: {ENTERPRISE_COLORS['success']};
                            color: #ffffff;
                        }}
                    """)
                    done_btn.clicked.connect(lambda ch, vid=v['id']: self._complete_visit(vid))
                    actions_layout.addWidget(done_btn)

                    resched_btn = QPushButton("📅 Date")
                    resched_btn.setToolTip("Reschedule scheduled visit date")
                    resched_btn.setCursor(Qt.PointingHandCursor)
                    resched_btn.setStyleSheet(f"""
                        {v_btn_common}
                        QPushButton {{
                            background-color: {ENTERPRISE_COLORS['primary_light']};
                            color: {ENTERPRISE_COLORS['primary']};
                            border: 1px solid {ENTERPRISE_COLORS['primary_border']};
                        }}
                        QPushButton:hover {{
                            background-color: {ENTERPRISE_COLORS['primary']};
                            color: #ffffff;
                        }}
                    """)
                    resched_btn.clicked.connect(lambda ch, vid=v['id']: self._reschedule_visit(vid))
                    actions_layout.addWidget(resched_btn)

                    wa_rem_btn = QPushButton("💬 WA")
                    wa_rem_btn.setToolTip("Send WhatsApp Visit Reminder to Customer")
                    wa_rem_btn.setCursor(Qt.PointingHandCursor)
                    wa_rem_btn.setStyleSheet(f"""
                        {v_btn_common}
                        QPushButton {{
                            background-color: #ecfdf5;
                            color: #059669;
                            border: 1px solid #a7f3d0;
                        }}
                        QPushButton:hover {{
                            background-color: #059669;
                            color: #ffffff;
                        }}
                    """)
                    wa_rem_btn.clicked.connect(lambda ch, vis=v: self._send_whatsapp_visit_reminder(vis))
                    actions_layout.addWidget(wa_rem_btn)

                else:
                    view_btn = QPushButton("👁️ Details")
                    view_btn.setToolTip("View visit work summary and details")
                    view_btn.setCursor(Qt.PointingHandCursor)
                    view_btn.setStyleSheet(f"""
                        {v_btn_common}
                        QPushButton {{
                            background-color: {ENTERPRISE_COLORS['primary_light']};
                            color: {ENTERPRISE_COLORS['primary']};
                            border: 1px solid {ENTERPRISE_COLORS['primary_border']};
                        }}
                        QPushButton:hover {{
                            background-color: {ENTERPRISE_COLORS['primary']};
                            color: #ffffff;
                        }}
                    """)
                    view_btn.clicked.connect(lambda ch, vis=v: self._view_completed_visit_details(vis))
                    actions_layout.addWidget(view_btn)

                    wa_btn = QPushButton("💬 Summary")
                    wa_btn.setToolTip("Send WhatsApp service completion notice")
                    wa_btn.setCursor(Qt.PointingHandCursor)
                    wa_btn.setStyleSheet(f"""
                        {v_btn_common}
                        QPushButton {{
                            background-color: #ecfdf5;
                            color: #059669;
                            border: 1px solid #a7f3d0;
                        }}
                        QPushButton:hover {{
                            background-color: #059669;
                            color: #ffffff;
                        }}
                    """)
                    wa_btn.clicked.connect(lambda ch, vis=v: self._send_whatsapp_visit_completion(vis))
                    actions_layout.addWidget(wa_btn)

                self.visits_table.setCellWidget(row, 7, actions_widget)
        finally:
            self.visits_table.setUpdatesEnabled(True)

    # ═══════════════════════════════════════════════════════════════════════════
    # 360° CONTRACT INSPECTOR DIALOG
    # ═══════════════════════════════════════════════════════════════════════════
    def _on_amc_double_click(self, row, col):
        id_item = self.amc_table.item(row, 0)
        if id_item and id_item.data(Qt.ItemDataRole.UserRole):
            self._show_amc_details(id_item.data(Qt.ItemDataRole.UserRole))

    def _on_view_details_clicked(self):
        sel = self.amc_table.selectedItems()
        if not sel:
            self.show_warning_message("Please select an AMC contract from the table first.")
            return
        row = sel[0].row()
        id_item = self.amc_table.item(row, 0)
        if id_item and id_item.data(Qt.ItemDataRole.UserRole):
            self._show_amc_details(id_item.data(Qt.ItemDataRole.UserRole))

    def _on_add_payment_clicked(self):
        sel = self.amc_table.selectedItems()
        if not sel:
            self.show_warning_message("Please select an AMC contract from the table first.")
            return
        row = sel[0].row()
        id_item = self.amc_table.item(row, 0)
        if id_item and id_item.data(Qt.ItemDataRole.UserRole):
            self._add_amc_payment(id_item.data(Qt.ItemDataRole.UserRole))

    def _on_schedule_visit_clicked(self):
        sel = self.amc_table.selectedItems()
        if not sel:
            self.show_warning_message("Please select an AMC contract from the table first.")
            return
        row = sel[0].row()
        id_item = self.amc_table.item(row, 0)
        if id_item and id_item.data(Qt.ItemDataRole.UserRole):
            self._schedule_visit_for_amc(id_item.data(Qt.ItemDataRole.UserRole))

    def _on_generate_pdf_clicked(self):
        sel = self.amc_table.selectedItems()
        if not sel:
            self.show_warning_message("Please select an AMC contract from the table first.")
            return
        row = sel[0].row()
        id_item = self.amc_table.item(row, 0)
        if id_item and id_item.data(Qt.ItemDataRole.UserRole):
            self._preview_amc_pdf(id_item.data(Qt.ItemDataRole.UserRole))

    def _preview_amc_pdf(self, amc_id):
        """Open the official AMC Agreement & Certificate Preview and Share Dialog"""
        try:
            from views.amc_preview_dialog import AMCContractPreviewDialog
            dlg = AMCContractPreviewDialog(amc_id, parent=self)
            dlg.exec()
        except Exception as e:
            self.show_error_message(f"Error opening AMC Contract Agreement: {str(e)}")

    def _on_whatsapp_share_clicked(self):
        sel = self.amc_table.selectedItems()
        if not sel:
            self.show_warning_message("Please select an AMC contract from the table first.")
            return
        row = sel[0].row()
        id_item = self.amc_table.item(row, 0)
        aid = id_item.data(Qt.ItemDataRole.UserRole)
        amc = next((a for a in self.amc_list if a['id'] == aid), None)
        if amc:
            self._send_whatsapp_amc(amc)

    def _on_renew_amc_clicked(self):
        sel = self.amc_table.selectedItems()
        if not sel:
            self.show_warning_message("Please select an AMC contract from the table first.")
            return
        row = sel[0].row()
        id_item = self.amc_table.item(row, 0)
        if id_item and id_item.data(Qt.ItemDataRole.UserRole):
            self._renew_amc(id_item.data(Qt.ItemDataRole.UserRole))

    def _on_delete_amc_clicked(self):
        sel = self.amc_table.selectedItems()
        if not sel:
            self.show_warning_message("Please select an AMC contract from the table first.")
            return
        row = sel[0].row()
        id_item = self.amc_table.item(row, 0)
        if id_item and id_item.data(Qt.ItemDataRole.UserRole):
            self._delete_amc(id_item.data(Qt.ItemDataRole.UserRole))

    def _on_visit_double_click(self, row, col):
        id_item = self.visits_table.item(row, 0)
        if not id_item or not id_item.data(Qt.ItemDataRole.UserRole):
            return
        vid = id_item.data(Qt.ItemDataRole.UserRole)
        v = next((x for x in self.visits_list if x['id'] == vid), None)
        if not v:
            return
        if v.get('visit_status') == 'Scheduled':
            self._complete_visit(vid)
        else:
            self._view_completed_visit_details(v)

    def _on_visit_complete_clicked(self):
        sel = self.visits_table.selectedItems()
        if not sel:
            self.show_warning_message("Please select a visit from the table first.")
            return
        row = sel[0].row()
        id_item = self.visits_table.item(row, 0)
        if id_item and id_item.data(Qt.ItemDataRole.UserRole):
            self._complete_visit(id_item.data(Qt.ItemDataRole.UserRole))

    def _on_visit_resched_clicked(self):
        sel = self.visits_table.selectedItems()
        if not sel:
            self.show_warning_message("Please select a visit from the table first.")
            return
        row = sel[0].row()
        id_item = self.visits_table.item(row, 0)
        if id_item and id_item.data(Qt.ItemDataRole.UserRole):
            self._reschedule_visit(id_item.data(Qt.ItemDataRole.UserRole))

    def _on_visit_assign_clicked(self):
        sel = self.visits_table.selectedItems()
        if not sel:
            self.show_warning_message("Please select a visit from the table first.")
            return
        row = sel[0].row()
        id_item = self.visits_table.item(row, 0)
        if id_item and id_item.data(Qt.ItemDataRole.UserRole):
            self._assign_technician_to_visit(id_item.data(Qt.ItemDataRole.UserRole))

    def _on_visit_wa_clicked(self):
        sel = self.visits_table.selectedItems()
        if not sel:
            self.show_warning_message("Please select a visit from the table first.")
            return
        row = sel[0].row()
        id_item = self.visits_table.item(row, 0)
        vid = id_item.data(Qt.ItemDataRole.UserRole)
        v = next((x for x in self.visits_list if x['id'] == vid), None)
        if v:
            self._send_whatsapp_visit_reminder(v)

    def _on_visit_cancel_clicked(self):
        sel = self.visits_table.selectedItems()
        if not sel:
            self.show_warning_message("Please select a visit from the table first.")
            return
        row = sel[0].row()
        id_item = self.visits_table.item(row, 0)
        if id_item and id_item.data(Qt.ItemDataRole.UserRole):
            self._cancel_visit(id_item.data(Qt.ItemDataRole.UserRole))

    def _assign_technician_to_visit(self, visit_id):
        from database.db_connection import DatabaseContext

        with DatabaseContext() as db:
            visit = db.execute_query(
                """
                SELECT v.*, ac.amc_id as amc_number, c.name as customer_name
                FROM amc_visits v
                JOIN amc_contracts ac ON v.amc_id = ac.id
                JOIN customers c ON ac.customer_id = c.id
                WHERE v.id = %s
                """,
                (visit_id,), fetch_one=True
            )
            techs = db.execute_query("SELECT id, name, mobile FROM technicians WHERE is_active = TRUE ORDER BY name", fetch_all=True) or []

        if not visit:
            self.show_error_message("Visit record not found.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Assign Technician - Visit #{visit.get('visit_number', '')} ({visit.get('amc_number', '')})")
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet(f"QDialog {{ background-color: {ENTERPRISE_COLORS['bg']}; font-family: {FONT_FAMILY}; }}")
        dl = QVBoxLayout(dialog)
        dl.setContentsMargins(20, 20, 20, 20)
        dl.setSpacing(14)

        v_date = Formatters.format_date(visit.get('visit_date'))
        info = QLabel(f"Customer: <b>{visit.get('customer_name')}</b><br>Scheduled Date: <b>🗓️ {v_date}</b>")
        info.setStyleSheet(f"font-size: 9.5pt; color: {ENTERPRISE_COLORS['text']};")
        dl.addWidget(info)

        form = QFormLayout()
        tech_combo = QComboBox()
        tech_combo.addItem("-- Unassigned --", None)
        cur_tech_idx = 0
        for i, t in enumerate(techs):
            label = f"{t['name']}  ({t.get('mobile', '')})" if t.get('mobile') else t['name']
            tech_combo.addItem(label, t['id'])
            if t['id'] == visit.get('technician_id'):
                cur_tech_idx = i + 1
        tech_combo.setCurrentIndex(cur_tech_idx)
        tech_combo.setStyleSheet(self._combo_style())
        form.addRow("Assign To:", tech_combo)
        dl.addLayout(form)

        btns = QHBoxLayout()
        def do_assign():
            tid = tech_combo.currentData()
            with DatabaseContext() as db:
                db.execute_query("UPDATE amc_visits SET technician_id = %s WHERE id = %s", (tid, visit_id))
            self.show_success_message("Technician assigned successfully to this maintenance visit!")
            dialog.accept()
            self._load_visits()

        save_btn = QPushButton("Save Assignment")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ENTERPRISE_COLORS['primary']};
                color: #ffffff;
                font-weight: 700;
                padding: 8px 18px;
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['primary_hover']};
            }}
        """)
        save_btn.clicked.connect(do_assign)
        btns.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(self._secondary_button_style())
        cancel_btn.clicked.connect(dialog.reject)
        btns.addWidget(cancel_btn)
        dl.addLayout(btns)

        dialog.exec()

    def _view_completed_visit_details(self, visit):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Visit Summary - #{visit.get('visit_number', '')} ({visit.get('amc_number', '')})")
        dialog.setMinimumWidth(460)
        dialog.setStyleSheet(f"QDialog {{ background-color: {ENTERPRISE_COLORS['bg']}; font-family: {FONT_FAMILY}; }}")
        dl = QVBoxLayout(dialog)
        dl.setContentsMargins(20, 20, 20, 20)
        dl.setSpacing(14)

        title = QLabel(f"<b>Visit #{visit.get('visit_number')}</b> - Contract {visit.get('amc_number')}")
        title.setStyleSheet(f"font-size: 13pt; font-weight: 800; color: {ENTERPRISE_COLORS['primary']}; font-family: {FONT_FAMILY};")
        dl.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.addRow("Customer:", QLabel(f"<b>{visit.get('customer_name', '--')}</b> (📞 {visit.get('customer_mobile', '--')})"))
        form.addRow("Address:", QLabel(visit.get('customer_address', '--') or '--'))
        form.addRow("Visit Date:", QLabel(Formatters.format_date(visit.get('visit_date'))))
        form.addRow("Technician:", QLabel(f"👤 {visit.get('technician_name', 'Unassigned')}"))
        form.addRow("Status:", QLabel(f"● {visit.get('visit_status', 'Completed')}"))
        form.addRow("Work Done:", QLabel(visit.get('work_done', '--') or '--'))
        form.addRow("Parts Replaced:", QLabel(visit.get('parts_replaced', '--') or '--'))
        extra = float(visit.get('extra_charge', 0) or 0)
        form.addRow("Extra Charges:", QLabel(f"{self.currency_symbol}{extra:,.2f}"))
        if visit.get('notes'):
            form.addRow("Notes:", QLabel(visit.get('notes')))
        dl.addLayout(form)

        btns = QHBoxLayout()
        wa_btn = QPushButton("💬  Send Summary to Customer")
        wa_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ENTERPRISE_COLORS['success']};
                color: #ffffff;
                font-weight: 700;
                padding: 8px 16px;
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['success_hover']};
            }}
        """)
        wa_btn.clicked.connect(lambda: (dialog.accept(), self._send_whatsapp_visit_completion(visit)))
        btns.addWidget(wa_btn)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(self._secondary_button_style())
        close_btn.clicked.connect(dialog.accept)
        btns.addWidget(close_btn)
        dl.addLayout(btns)

        dialog.exec()

    def _send_whatsapp_visit_completion(self, visit):
        phone = visit.get('customer_mobile', '')
        if not phone:
            self.show_warning_message("Customer phone number is missing.")
            return

        c_name = visit.get('customer_name', 'Customer')
        amc_num = visit.get('amc_number', '')
        v_num = visit.get('visit_number', '')
        v_date = Formatters.format_date(visit.get('visit_date'))
        work = visit.get('work_done') or "AC Preventive Maintenance Service"
        tech = visit.get('technician_name') or "Certified Technician"

        msg = (
            f"Hello *{c_name}*,\n\n"
            f"Your AC maintenance *Visit #{v_num}* under AMC Contract *{amc_num}* has been successfully *COMPLETED* on {v_date}.\n\n"
            f"🔧 *Technician:* {tech}\n"
            f"🛠️ *Work Performed:* {work}\n"
        )
        if visit.get('parts_replaced'):
            msg += f"⚙️ *Parts Replaced:* {visit.get('parts_replaced')}\n"
        extra = float(visit.get('extra_charge', 0) or 0)
        if extra > 0:
            msg += f"💵 *Extra Charges:* {self.currency_symbol}{extra:,.2f}\n"

        msg += (
            f"\nThank you for trusting *{get_setting('shop_name', 'Ansh Aircon')}*! If you need any assistance, feel free to contact us."
        )
        self._open_whatsapp_web(phone, msg)

    def _show_amc_details(self, amc_id):
        from database.db_connection import DatabaseContext
        from controllers.amc_controller import AMCController

        with DatabaseContext() as db:
            ctrl = AMCController(db)
            amc = ctrl.get_amc_contract(amc_id)
            if not amc:
                self.show_error_message("AMC Contract not found.")
                return
            units = ctrl.get_amc_units(amc_id) or []
            visits = ctrl.get_amc_visits(amc_id) or []

        dialog = QDialog(self)
        dialog.setWindowTitle(f"AMC Contract Inspector - {amc['amc_id']}")
        dialog.setMinimumSize(780, 640)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {ENTERPRISE_COLORS['bg']};
                font-family: {FONT_FAMILY};
            }}
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header card
        header_card = QFrame()
        header_card.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        hl = QHBoxLayout(header_card)
        hl.setSpacing(14)

        h_icon = QLabel("📄")
        h_icon.setFixedSize(46, 46)
        h_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_icon.setStyleSheet(f"""
            background-color: {ENTERPRISE_COLORS['primary_light']};
            border-radius: 12px;
            font-size: 20pt;
        """)
        hl.addWidget(h_icon)

        htext = QVBoxLayout()
        htitle = QLabel(f"{amc['amc_id']}  •  {amc.get('contract_type', 'Comprehensive')}")
        htitle.setStyleSheet(f"font-size: 14pt; font-weight: 800; color: {ENTERPRISE_COLORS['text']}; font-family: {FONT_FAMILY};")
        hcust = QLabel(f"Customer: <b>{amc.get('customer_name', '')}</b> | Phone: <b>{amc.get('customer_mobile', '')}</b> | Address: {amc.get('customer_address', '--')}")
        hcust.setStyleSheet(f"font-size: 9pt; color: {ENTERPRISE_COLORS['text_secondary']};")
        htext.addWidget(htitle)
        htext.addWidget(hcust)
        hl.addLayout(htext)

        hl.addStretch()
        hl.addWidget(AMCStatusBadge(amc.get('amc_status', 'Active')))
        layout.addWidget(header_card)

        # 4 Mini KPI cards
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(10)

        completed_visits = sum(1 for v in visits if v.get('visit_status') == 'Completed')
        total_visits = amc.get('services_per_year', len(visits))

        metrics = [
            ("PERIOD", f"{Formatters.format_date(amc.get('start_date'))} → {Formatters.format_date(amc.get('end_date'))}", ENTERPRISE_COLORS['text']),
            ("VISITS COMPLETED", f"{completed_visits} / {total_visits}", ENTERPRISE_COLORS['primary']),
            ("TOTAL VALUE", f"{self.currency_symbol}{float(amc.get('total_amount', 0) or 0):,.2f}", ENTERPRISE_COLORS['text']),
            ("BALANCE DUE", f"{self.currency_symbol}{float(amc.get('balance_amount', 0) or 0):,.2f}", ENTERPRISE_COLORS['warning'] if float(amc.get('balance_amount', 0) or 0) > 0 else ENTERPRISE_COLORS['success']),
        ]
        for lbl, val, col in metrics:
            f = QFrame()
            f.setStyleSheet(f"QFrame {{ background-color: #ffffff; border: 1px solid {ENTERPRISE_COLORS['border']}; border-radius: 8px; padding: 8px 12px; }}")
            fl = QVBoxLayout(f)
            fl.setContentsMargins(0, 0, 0, 0)
            fl.setSpacing(2)
            l = QLabel(lbl)
            l.setStyleSheet(f"font-size: 7.5pt; font-weight: 700; color: {ENTERPRISE_COLORS['text_muted']};")
            v = QLabel(val)
            v.setStyleSheet(f"font-size: 11pt; font-weight: 800; color: {col};")
            fl.addWidget(l)
            fl.addWidget(v)
            kpi_row.addWidget(f)
        layout.addLayout(kpi_row)

        # Tab widget inside dialog
        detail_tabs = QTabWidget()
        detail_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                background-color: #ffffff;
            }}
            QTabBar::tab {{
                background-color: #f1f5f9;
                color: {ENTERPRISE_COLORS['text_secondary']};
                padding: 8px 16px;
                font-weight: 700;
                font-size: 9pt;
            }}
            QTabBar::tab:selected {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['primary']};
            }}
        """)

        # Tab A: AC Units Table
        units_widget = QWidget()
        uw_l = QVBoxLayout(units_widget)
        uw_l.setContentsMargins(12, 12, 12, 12)
        u_table = QTableWidget()
        u_table.setColumnCount(5)
        u_table.setHorizontalHeaderLabels(['Unit #', 'AC Type', 'Brand', 'Tonnage', 'Serial Number'])
        u_table.verticalHeader().setVisible(False)
        self._style_white_table(u_table)
        uh = u_table.horizontalHeader()
        uh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        uh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        uh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        uh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        uh.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        for i, u in enumerate(units):
            row = u_table.rowCount()
            u_table.insertRow(row)
            u_table.setItem(row, 0, QTableWidgetItem(str(i + 1)))
            u_table.setItem(row, 1, QTableWidgetItem(u.get('ac_type', 'Split')))
            u_table.setItem(row, 2, QTableWidgetItem(u.get('brand', '')))
            u_table.setItem(row, 3, QTableWidgetItem(f"{u.get('ton', '')} Ton"))
            u_table.setItem(row, 4, QTableWidgetItem(u.get('serial_number', '') or "--"))
        uw_l.addWidget(u_table)
        detail_tabs.addTab(units_widget, f"❄️  AC Units ({len(units)})")

        # Tab B: Preventive Visits Timeline
        visits_widget = QWidget()
        vw_l = QVBoxLayout(visits_widget)
        vw_l.setContentsMargins(12, 12, 12, 12)
        v_table = QTableWidget()
        v_table.setColumnCount(6)
        v_table.setHorizontalHeaderLabels(['Visit #', 'Scheduled Date', 'Technician', 'Status', 'Work Summary', 'Parts Replaced'])
        v_table.verticalHeader().setVisible(False)
        self._style_white_table(v_table)
        vh = v_table.horizontalHeader()
        vh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        vh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        vh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        vh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        vh.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        vh.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        for v in visits:
            row = v_table.rowCount()
            v_table.insertRow(row)
            v_table.setItem(row, 0, QTableWidgetItem(f"Visit #{v['visit_number']}"))
            v_table.setItem(row, 1, QTableWidgetItem(Formatters.format_date(v.get('visit_date'))))
            v_table.setItem(row, 2, QTableWidgetItem(v.get('technician_name', '') or "Unassigned"))
            v_table.setCellWidget(row, 3, VisitStatusBadge(v.get('visit_status', 'Scheduled')))
            v_table.setItem(row, 4, QTableWidgetItem(v.get('work_done', '') or "--"))
            v_table.setItem(row, 5, QTableWidgetItem(v.get('parts_replaced', '') or "--"))
        vw_l.addWidget(v_table)
        detail_tabs.addTab(visits_widget, f"📅  Visits Timeline ({len(visits)})")

        # Tab C: Notes & Terms
        notes_widget = QWidget()
        nw_l = QVBoxLayout(notes_widget)
        nw_l.setContentsMargins(12, 12, 12, 12)
        notes_box = QTextEdit()
        notes_box.setReadOnly(True)
        notes_box.setPlainText(amc.get('notes', '') or "No special contract notes provided.")
        notes_box.setStyleSheet(f"background:#ffffff; color:{ENTERPRISE_COLORS['text']}; border:1px solid {ENTERPRISE_COLORS['border']}; border-radius:6px; padding:10px;")
        nw_l.addWidget(notes_box)
        detail_tabs.addTab(notes_widget, "📝  Notes & Inclusions")

        layout.addWidget(detail_tabs, 1)

        # Dialog bottom actions
        bl = QHBoxLayout()
        bl.setSpacing(10)

        if float(amc.get('balance_amount', 0) or 0) > 0:
            pay_btn = QPushButton("💳  Record Payment")
            pay_btn.setStyleSheet(self._secondary_button_style())
            pay_btn.clicked.connect(lambda: (dialog.accept(), self._add_amc_payment(amc_id)))
            bl.addWidget(pay_btn)

        sched_btn = QPushButton("📅  Schedule Visit")
        sched_btn.setStyleSheet(self._secondary_button_style())
        sched_btn.clicked.connect(lambda: (dialog.accept(), self._schedule_visit_for_amc(amc_id)))
        bl.addWidget(sched_btn)

        pdf_btn = QPushButton("📄  Contract PDF / Form")
        pdf_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ENTERPRISE_COLORS['primary_light']};
                color: {ENTERPRISE_COLORS['primary']};
                font-size: 9pt;
                font-weight: 700;
                padding: 8px 14px;
                border-radius: 8px;
                border: 1px solid {ENTERPRISE_COLORS['primary_border']};
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['primary']};
                color: #ffffff;
            }}
        """)
        pdf_btn.clicked.connect(lambda: self._preview_amc_pdf(amc_id))
        bl.addWidget(pdf_btn)

        wa_btn = QPushButton("💬  WhatsApp Contract")
        wa_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                color: #059669;
                font-size: 9pt;
                font-weight: 700;
                padding: 8px 14px;
                border-radius: 8px;
                border: 1px solid #a7f3d0;
            }}
            QPushButton:hover {{
                background-color: #ecfdf5;
            }}
        """)
        wa_btn.clicked.connect(lambda: self._send_whatsapp_amc(amc))
        bl.addWidget(wa_btn)

        if amc.get('amc_status') in ('Expired', 'Completed', 'Expiring Soon'):
            renew_btn = QPushButton("🔄  Renew AMC")
            renew_btn.setStyleSheet(self._secondary_button_style())
            renew_btn.clicked.connect(lambda: (dialog.accept(), self._renew_amc(amc_id)))
            bl.addWidget(renew_btn)

        bl.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(self._secondary_button_style())
        close_btn.clicked.connect(dialog.accept)
        bl.addWidget(close_btn)

        layout.addLayout(bl)
        dialog.exec()

    # ═══════════════════════════════════════════════════════════════════════════
    # CONTEXT MENUS & OPERATIONAL ACTIONS
    # ═══════════════════════════════════════════════════════════════════════════
    def _show_amc_context_menu(self, pos):
        item = self.amc_table.itemAt(pos)
        if not item:
            return
        row = item.row()
        id_item = self.amc_table.item(row, 0)
        if not id_item:
            return
        amc_db_id = id_item.data(Qt.ItemDataRole.UserRole)
        amc = next((a for a in self.amc_list if a['id'] == amc_db_id), None)

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['text']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                padding: 4px 0px;
                font-family: {FONT_FAMILY};
                font-size: 9.5pt;
            }}
            QMenu::item {{
                padding: 8px 20px;
            }}
            QMenu::item:selected {{
                background-color: {ENTERPRISE_COLORS['primary_light']};
                color: {ENTERPRISE_COLORS['primary']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {ENTERPRISE_COLORS['border']};
                margin: 4px 0px;
            }}
        """)

        menu.addAction("👁️  View 360° Details", lambda: self._show_amc_details(amc_db_id))
        menu.addAction("📄  Contract PDF / Form (Preview & Share)", lambda: self._preview_amc_pdf(amc_db_id))
        menu.addSeparator()
        menu.addAction("💳  Add Payment", lambda: self._add_amc_payment(amc_db_id))
        menu.addAction("📅  Schedule Maintenance Visit", lambda: self._schedule_visit_for_amc(amc_db_id))
        if amc:
            menu.addAction("💬  Share on WhatsApp", lambda: self._send_whatsapp_amc(amc))
        menu.addAction("🔄  Renew Contract", lambda: self._renew_amc(amc_db_id))
        menu.addSeparator()
        menu.addAction("🗑️  Delete Contract", lambda: self._delete_amc(amc_db_id))

        menu.exec(self.amc_table.viewport().mapToGlobal(pos))

    def _show_visit_context_menu(self, pos):
        item = self.visits_table.itemAt(pos)
        if not item:
            return
        row = item.row()
        id_item = self.visits_table.item(row, 0)
        if not id_item:
            return
        v_id = id_item.data(Qt.ItemDataRole.UserRole)
        if not v_id:
            return

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['text']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                padding: 4px 0px;
                font-family: {FONT_FAMILY};
                font-size: 9.5pt;
            }}
            QMenu::item {{
                padding: 8px 20px;
            }}
            QMenu::item:selected {{
                background-color: {ENTERPRISE_COLORS['primary_light']};
                color: {ENTERPRISE_COLORS['primary']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {ENTERPRISE_COLORS['border']};
                margin: 4px 0px;
            }}
        """)
        menu.addAction("✓  Mark Completed", lambda: self._complete_visit(v_id))
        menu.addAction("📅  Reschedule Visit", lambda: self._reschedule_visit(v_id))
        menu.addAction("✕  Cancel Visit", lambda: self._cancel_visit(v_id))
        menu.exec(self.visits_table.viewport().mapToGlobal(pos))

    def _add_amc_payment(self, amc_id):
        from database.db_connection import DatabaseConnection
        from controllers.amc_controller import AMCController

        ctrl = AMCController(DatabaseConnection())
        contract = ctrl.get_amc_contract(amc_id)
        if not contract:
            self.show_error_message("Contract not found.")
            return

        balance = float(contract.get('balance_amount', 0) or 0)
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Record AMC Payment - {contract['amc_id']}")
        dialog.setMinimumWidth(380)
        dialog.setStyleSheet(f"QDialog {{ background-color: {ENTERPRISE_COLORS['bg']}; font-family: {FONT_FAMILY}; }}")
        dl = QVBoxLayout(dialog)
        dl.setContentsMargins(20, 20, 20, 20)
        dl.setSpacing(14)

        info = QLabel(f"Customer: <b>{contract.get('customer_name', '')}</b><br>Outstanding Balance: <b>{self.currency_symbol}{balance:,.2f}</b>")
        info.setStyleSheet(f"font-size: 9.5pt; color: {ENTERPRISE_COLORS['text']};")
        dl.addWidget(info)

        form = QFormLayout()
        amt_spin = QDoubleSpinBox()
        amt_spin.setRange(1, 9999999)
        amt_spin.setValue(balance if balance > 0 else 1000)
        amt_spin.setPrefix(f"{self.currency_symbol} ")
        amt_spin.setStyleSheet(self._spin_style())
        form.addRow("Payment Amount:", amt_spin)

        mode_combo = QComboBox()
        mode_combo.addItems(["Cash", "UPI", "Cheque", "NEFT / RTGS", "Card"])
        mode_combo.setStyleSheet(self._combo_style())
        form.addRow("Payment Mode:", mode_combo)
        dl.addLayout(form)

        btns = QHBoxLayout()
        save_btn = QPushButton("Save Payment")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ENTERPRISE_COLORS['success']};
                color: #ffffff;
                font-weight: 700;
                padding: 8px 18px;
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['success_hover']};
            }}
        """)
        def do_pay():
            amt = amt_spin.value()
            if amt <= 0:
                self.show_warning_message("Enter a valid payment amount.")
                return
            success, msg = ctrl.update_amc_payment(amc_id, amt, mode_combo.currentText())
            if success:
                self.show_success_message(f"Payment of {self.currency_symbol}{amt:,.2f} recorded successfully!")
                dialog.accept()
                self.load_amc_data()
            else:
                self.show_error_message(f"Failed to record payment: {msg}")

        save_btn.clicked.connect(do_pay)
        btns.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(self._secondary_button_style())
        cancel_btn.clicked.connect(dialog.reject)
        btns.addWidget(cancel_btn)
        dl.addLayout(btns)

        dialog.exec()

    def _schedule_visit_for_amc(self, amc_id):
        from database.db_connection import DatabaseConnection, DatabaseContext
        from controllers.amc_controller import AMCController

        dialog = QDialog(self)
        dialog.setWindowTitle("Schedule AMC Preventive Visit")
        dialog.setMinimumWidth(420)
        dialog.setStyleSheet(f"QDialog {{ background-color: {ENTERPRISE_COLORS['bg']}; font-family: {FONT_FAMILY}; }}")
        dl = QVBoxLayout(dialog)
        dl.setContentsMargins(20, 20, 20, 20)
        dl.setSpacing(14)

        with DatabaseContext() as db:
            contract = AMCController(db).get_amc_contract(amc_id)
            techs = db.execute_query("SELECT id, name FROM technicians WHERE is_active=TRUE ORDER BY name", fetch_all=True) or []

        form = QFormLayout()
        amc_lbl = QLabel(f"<b>{contract['amc_id']}</b>  ({contract.get('customer_name', '')})")
        amc_lbl.setStyleSheet(f"font-size: 10pt; color: {ENTERPRISE_COLORS['primary']};")
        form.addRow("AMC Contract:", amc_lbl)

        visit_date = QDateEdit()
        visit_date.setDate(QDate.currentDate().addDays(3))
        visit_date.setCalendarPopup(True)
        visit_date.setDisplayFormat("dd-MM-yyyy")
        visit_date.setStyleSheet(self._date_style())
        form.addRow("Visit Date:", visit_date)

        tech_combo = QComboBox()
        tech_combo.addItem("-- Assign Technician --", None)
        for t in techs:
            tech_combo.addItem(t['name'], t['id'])
        tech_combo.setStyleSheet(self._combo_style())
        form.addRow("Technician:", tech_combo)

        notes_input = QLineEdit()
        notes_input.setPlaceholderText("Routine preventive maintenance")
        notes_input.setStyleSheet(self._input_style())
        form.addRow("Notes:", notes_input)
        dl.addLayout(form)

        btns = QHBoxLayout()
        def do_schedule():
            ctrl = AMCController(DatabaseConnection())
            visits = ctrl.get_amc_visits(amc_id) or []
            vnum = len(visits) + 1
            vd = visit_date.date().toString("yyyy-MM-dd")
            vdata = {
                'amc_id': amc_id,
                'visit_number': vnum,
                'visit_date': vd,
                'technician_id': tech_combo.currentData(),
                'visit_status': 'Scheduled',
                'notes': notes_input.text().strip()
            }
            vid, err = ctrl.add_amc_visit(vdata)
            if vid:
                self.show_success_message(f"Visit #{vnum} successfully scheduled for {visit_date.date().toString('dd-MM-yyyy')}!")
                dialog.accept()
                self._load_visits()
                self.load_amc_data()
            else:
                self.show_error_message(f"Failed to schedule visit: {err}")

        ok = QPushButton("Schedule Visit")
        ok.setStyleSheet(f"""
            QPushButton {{
                background-color: {ENTERPRISE_COLORS['primary']};
                color: #ffffff;
                font-weight: 700;
                padding: 8px 18px;
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['primary_hover']};
            }}
        """)
        ok.clicked.connect(do_schedule)
        btns.addWidget(ok)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(self._secondary_button_style())
        cancel_btn.clicked.connect(dialog.reject)
        btns.addWidget(cancel_btn)
        dl.addLayout(btns)

        dialog.exec()

    def _complete_visit(self, visit_id):
        from database.db_connection import DatabaseConnection
        from controllers.amc_controller import AMCController

        dialog = QDialog(self)
        dialog.setWindowTitle("Complete Preventive Maintenance Visit")
        dialog.setMinimumWidth(440)
        dialog.setStyleSheet(f"QDialog {{ background-color: {ENTERPRISE_COLORS['bg']}; font-family: {FONT_FAMILY}; }}")
        dl = QVBoxLayout(dialog)
        dl.setContentsMargins(20, 20, 20, 20)
        dl.setSpacing(14)

        form = QFormLayout()
        work_done = QTextEdit()
        work_done.setFixedHeight(70)
        work_done.setPlaceholderText("Detailed work executed (e.g. Jet pump cleaning, coil wash, ampere check)...")
        work_done.setStyleSheet(self._input_style())
        form.addRow("Work Done:", work_done)

        parts = QTextEdit()
        parts.setFixedHeight(50)
        parts.setPlaceholderText("Parts replaced (if any, e.g. Capacitor 45uF)...")
        parts.setStyleSheet(self._input_style())
        form.addRow("Parts Replaced:", parts)

        extra = QDoubleSpinBox()
        extra.setRange(0, 99999)
        extra.setPrefix(f"{self.currency_symbol} ")
        extra.setStyleSheet(self._spin_style())
        form.addRow("Extra Charges (if any):", extra)
        dl.addLayout(form)

        btns = QHBoxLayout()
        def do_complete():
            ctrl = AMCController(DatabaseConnection())
            vdata = {
                'work_done': work_done.toPlainText().strip() or "General AC Preventive Maintenance",
                'parts_replaced': parts.toPlainText().strip(),
                'extra_charge': extra.value(),
                'next_due_date': None,
                'notes': ''
            }
            ok, err = ctrl.complete_visit(visit_id, vdata)
            if ok:
                self.show_success_message("Maintenance visit marked as Completed! Remaining visit counter updated.")
                dialog.accept()
                self._load_visits()
                self.load_amc_data()
            else:
                self.show_error_message(f"Failed to complete visit: {err}")

        ok_btn = QPushButton("✓ Confirm Completed")
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ENTERPRISE_COLORS['success']};
                color: #ffffff;
                font-weight: 700;
                padding: 8px 18px;
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['success_hover']};
            }}
        """)
        ok_btn.clicked.connect(do_complete)
        btns.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(self._secondary_button_style())
        cancel_btn.clicked.connect(dialog.reject)
        btns.addWidget(cancel_btn)
        dl.addLayout(btns)

        dialog.exec()

    def _reschedule_visit(self, visit_id):
        from database.db_connection import DatabaseConnection
        from controllers.amc_controller import AMCController

        dialog = QDialog(self)
        dialog.setWindowTitle("Reschedule Maintenance Visit")
        dialog.setStyleSheet(f"QDialog {{ background-color: {ENTERPRISE_COLORS['bg']}; font-family: {FONT_FAMILY}; }}")
        dl = QVBoxLayout(dialog)
        dl.setContentsMargins(20, 20, 20, 20)
        dl.setSpacing(14)

        nd = QDateEdit()
        nd.setDate(QDate.currentDate().addDays(7))
        nd.setCalendarPopup(True)
        nd.setDisplayFormat("dd-MM-yyyy")
        nd.setStyleSheet(self._date_style())

        dl.addWidget(QLabel("Select New Scheduled Date:"))
        dl.addWidget(nd)

        btns = QHBoxLayout()
        def do_reschedule():
            ctrl = AMCController(DatabaseConnection())
            vdata = {
                'visit_status': 'Scheduled',
                'work_done': '',
                'parts_replaced': '',
                'extra_charge': 0,
                'next_due_date': nd.date().toString("yyyy-MM-dd"),
                'notes': f"Rescheduled to {nd.date().toString('dd-MM-yyyy')}"
            }
            # Update date in database
            ctrl.db.execute_query(
                "UPDATE amc_visits SET visit_date=%s, visit_status='Scheduled' WHERE id=%s",
                (nd.date().toString("yyyy-MM-dd"), visit_id)
            )
            self.show_success_message(f"Visit rescheduled to {nd.date().toString('dd-MM-yyyy')}!")
            dialog.accept()
            self._load_visits()

        ok_btn = QPushButton("Confirm Reschedule")
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ENTERPRISE_COLORS['primary']};
                color: #ffffff;
                font-weight: 700;
                padding: 8px 18px;
                border-radius: 8px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['primary_hover']};
            }}
        """)
        ok_btn.clicked.connect(do_reschedule)
        btns.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(self._secondary_button_style())
        cancel_btn.clicked.connect(dialog.reject)
        btns.addWidget(cancel_btn)
        dl.addLayout(btns)

        dialog.exec()

    def _cancel_visit(self, visit_id):
        if QMessageBox.question(
            self, "Confirm Cancellation",
            "Are you sure you want to cancel this scheduled visit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            from database.db_connection import DatabaseConnection
            from controllers.amc_controller import AMCController
            ctrl = AMCController(DatabaseConnection())
            vdata = {
                'visit_status': 'Cancelled',
                'work_done': 'Visit Cancelled',
                'parts_replaced': '',
                'extra_charge': 0,
                'next_due_date': None,
                'notes': 'Cancelled by manager'
            }
            ctrl.update_visit_status(visit_id, vdata)
            self.show_success_message("Visit marked as Cancelled.")
            self._load_visits()

    def _renew_amc(self, amc_id):
        from database.db_connection import DatabaseConnection
        from controllers.amc_controller import AMCController

        dur, ok = QInputDialog.getInt(self, "Renew AMC Contract", "Enter renewal extension (in years):", 1, 1, 5)
        if ok and dur > 0:
            ctrl = AMCController(DatabaseConnection())
            contract = ctrl.get_amc_contract(amc_id)
            if contract:
                old_end = contract['end_date']
                if isinstance(old_end, str):
                    old_end_dt = datetime.strptime(old_end[:10], '%Y-%m-%d').date()
                else:
                    old_end_dt = old_end
                new_start = (old_end_dt + timedelta(days=1)).strftime('%Y-%m-%d')
                new_end = ctrl._calculate_end_date(new_start, dur)
                ctrl.db.execute_query(
                    "UPDATE amc_contracts SET end_date=%s, amc_status='Active', services_remaining=services_per_year WHERE id=%s",
                    (new_end, amc_id)
                )
                ctrl._schedule_amc_visits(amc_id, new_start, new_end, contract.get('services_per_year', 3))
                self.show_success_message(f"AMC contract successfully renewed until {Formatters.format_date(new_end)}!")
                self.load_amc_data()
                self._load_visits()

    def _delete_amc(self, amc_id):
        if QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this AMC contract?\nAll scheduled visits will also be cancelled.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            from database.db_connection import DatabaseConnection
            from controllers.amc_controller import AMCController
            ctrl = AMCController(DatabaseConnection())
            ok, err = ctrl.delete_amc_contract(amc_id)
            if ok:
                self.show_success_message("AMC Contract deleted successfully.")
                self.load_amc_data()
                self._load_visits()
            else:
                self.show_error_message(f"Failed to delete contract: {err}")

    def _open_whatsapp_web(self, phone, message):
        clean_phone = ''.join(c for c in str(phone) if c.isdigit())
        if not clean_phone:
            self.show_warning_message("Phone number is missing or invalid.")
            return
        if len(clean_phone) == 10:
            clean_phone = f"91{clean_phone}"

        encoded_msg = urllib.parse.quote(message)
        wa_url = f"https://wa.me/{clean_phone}?text={encoded_msg}"
        QDesktopServices.openUrl(QUrl(wa_url))

    def _send_whatsapp_amc(self, amc):
        phone = amc.get('customer_mobile', '')
        if not phone:
            self.show_warning_message("Customer phone number is missing.")
            return

        c_name = amc.get('customer_name', 'Valued Customer')
        amc_id = amc.get('amc_id', '')
        c_type = amc.get('contract_type', 'Comprehensive')
        start_d = Formatters.format_date(amc.get('start_date'))
        end_d = Formatters.format_date(amc.get('end_date'))
        val = float(amc.get('total_amount', 0) or 0)
        bal = float(amc.get('balance_amount', 0) or 0)
        units_c = amc.get('no_of_units', 1)
        visits_yr = amc.get('services_per_year', 3)

        msg = (
            f"Hello *{c_name}*,\n\n"
            f"Thank you for choosing us for your AC maintenance! Here are your *Annual Maintenance Contract (AMC)* details:\n\n"
            f"📄 *Contract ID:* {amc_id}\n"
            f"🛡️ *Coverage:* {c_type}\n"
            f"❄️ *AC Units Covered:* {units_c} Unit(s)\n"
            f"📅 *Contract Validity:* {start_d} to {end_d}\n"
            f"🛠️ *Services Included:* {visits_yr} Preventive Visits/Year\n"
            f"💵 *Total Contract Value:* {self.currency_symbol}{val:,.2f}\n"
        )
        if bal > 0:
            msg += f"⏳ *Outstanding Balance:* {self.currency_symbol}{bal:,.2f}\n\n"
        else:
            msg += f"✅ *Payment Status:* Paid in Full\n\n"

        msg += (
            "Our certified technician will service your AC units as per schedule. "
            "For priority assistance or service requests, please feel free to reach out to us.\n\n"
            "Best Regards,\n"
            f"*{get_setting('shop_name', 'Ansh Aircon')}*"
        )

        self._open_whatsapp_web(phone, msg)

    def _send_whatsapp_visit_reminder(self, visit):
        phone = visit.get('customer_mobile', '')
        if not phone:
            self.show_warning_message("Customer phone number is missing.")
            return

        c_name = visit.get('customer_name', 'Customer')
        amc_num = visit.get('amc_number', '')
        v_date = Formatters.format_date(visit.get('visit_date'))
        tech = visit.get('technician_name') or "Our Service Technician"

        msg = (
            f"Dear *{c_name}*,\n\n"
            f"This is a gentle reminder regarding your upcoming *AC Preventive Maintenance Visit* under contract *{amc_num}*:\n\n"
            f"🗓️ *Scheduled Date:* {v_date}\n"
            f"🔧 *Technician Assigned:* {tech}\n\n"
            f"Please ensure premises are accessible during business hours. If you wish to reschedule, please let us know in advance.\n\n"
            f"Best Regards,\n*{get_setting('shop_name', 'Ansh Aircon')}*"
        )
        self._open_whatsapp_web(phone, msg)

    def _export_amc_to_excel(self):
        from utils.excel_helper import ExcelExporter
        from database.db_connection import DatabaseContext

        with DatabaseContext() as db:
            from controllers.amc_controller import AMCController
            contracts = AMCController(db).get_all_amc_contracts() or []

        if not contracts:
            self.show_warning_message("No AMC contracts to export.")
            return

        headers = ['AMC ID', 'Customer Name', 'Contact Phone', 'Contract Type', 'Start Date', 'End Date', 'Units', 'Contract Value', 'Paid Amount', 'Balance Due', 'Status']
        number_cols = {7, 8, 9, 10}
        rows = []
        total_amt = total_paid = total_bal = 0

        for c in contracts:
            amt = float(c.get('total_amount', 0) or 0)
            paid = float(c.get('advance_paid', 0) or 0)
            bal = float(c.get('balance_amount', 0) or 0)
            sd = Formatters.format_date(c.get('start_date'))
            ed = Formatters.format_date(c.get('end_date'))
            rows.append([
                c.get('amc_id', ''),
                c.get('customer_name', ''),
                c.get('customer_mobile', ''),
                c.get('contract_type', ''),
                sd, ed,
                c.get('no_of_units', 1),
                amt, paid, bal,
                c.get('amc_status', '')
            ])
            total_amt += amt
            total_paid += paid
            total_bal += bal

        active_count = sum(1 for r in rows if str(r[10]).lower() == 'active')
        expiring_count = sum(1 for r in rows if 'expiring' in str(r[10]).lower())
        expired_count = sum(1 for r in rows if str(r[10]).lower() == 'expired')

        charts_data = [
            {
                'type': 'pie',
                'title': 'Contract Status Distribution',
                'categories': ['Active', 'Expiring Soon', 'Expired'],
                'values': [('Count', [active_count, expiring_count, expired_count])]
            }
        ]

        wb = ExcelExporter.build_excel(
            sheet_title='AMC_Contracts',
            title_text='AMC Contract Portfolio & Receivables Report',
            subtitle_text=f'Total: {len(rows)} agreements | Generated: {datetime.now().strftime("%d-%m-%Y %H:%M")}',
            headers=headers,
            rows=rows,
            total_row=['', 'TOTALS', '', '', '', '', '', total_amt, total_paid, total_bal, ''],
            number_cols=number_cols,
            kpis=[
                ('Total Contracts', len(rows)),
                ('Total Value', total_amt),
                ('Total Collected', total_paid),
                ('Outstanding Dues', total_bal),
                ('Realization Rate', f'{(total_paid / total_amt * 100) if total_amt > 0 else 0:.1f}%'),
            ],
            charts_data=charts_data,
            freeze_col=True
        )

        filepath, _ = QFileDialog.getSaveFileName(
            self, 'Save AMC Portfolio Report',
            f"AMC_Contracts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            'Excel Files (*.xlsx)'
        )
        if filepath:
            try:
                wb.save(filepath)
                self.show_success_message(f"AMC report successfully exported:\n{filepath}")
            except Exception as e:
                self.show_error_message(f"Export failed: {str(e)}")

    def load_technicians(self):
        self.run_in_thread(self._load_technicians_thread, self._update_technician_data)

    def _load_technicians_thread(self):
        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            return db.execute_query("SELECT id, name FROM technicians WHERE is_active = TRUE ORDER BY name", fetch_all=True)

    def _update_technician_data(self, technicians):
        self.technicians_list = technicians or []
        if hasattr(self, 'technician_combo'):
            self.technician_combo.blockSignals(True)
            self.technician_combo.clear()
            self.technician_combo.addItem("👤  -- Auto / Assign by Service Manager --", None)
            for t in self.technicians_list:
                self.technician_combo.addItem(f"🔧  {t['name']}", t['id'])
            self.technician_combo.blockSignals(False)
            self._update_projected_visits_preview()

    def refresh_data(self):
        """Global refresh trigger"""
        self.load_amc_data()
        self._load_visits()
        self.load_technicians()
        self._search_customer()

    # ═══════════════════════════════════════════════════════════════════════════
    # STYLING HELPERS
    # ═══════════════════════════════════════════════════════════════════════════
    def _secondary_button_style(self):
        return f"""
            QPushButton {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['text_secondary']};
                font-size: 9pt;
                font-weight: 700;
                font-family: {FONT_FAMILY};
                padding: 8px 14px;
                border-radius: 8px;
                border: 1px solid {ENTERPRISE_COLORS['border']};
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['card_hover']};
                border-color: {ENTERPRISE_COLORS['primary_border']};
                color: {ENTERPRISE_COLORS['primary']};
            }}
        """

    def _action_icon_button_style(self):
        return f"""
            QPushButton {{
                background-color: #ffffff;
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 6px;
                font-size: 11pt;
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['primary_light']};
                border-color: {ENTERPRISE_COLORS['primary_border']};
            }}
        """

    def _input_style(self):
        return f"""
            QLineEdit, QTextEdit {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['text']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 9.5pt;
                font-family: {FONT_FAMILY};
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border: 2px solid {ENTERPRISE_COLORS['primary']};
            }}
        """

    def _combo_style(self):
        return f"""
            QComboBox {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['text']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                padding: 7px 12px;
                font-size: 9.5pt;
                font-family: {FONT_FAMILY};
                min-height: 20px;
            }}
            QComboBox:focus {{
                border: 2px solid {ENTERPRISE_COLORS['primary']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['text']};
                selection-background-color: {ENTERPRISE_COLORS['primary_light']};
                selection-color: {ENTERPRISE_COLORS['primary']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 6px;
                padding: 4px;
            }}
        """

    def _spin_style(self):
        return f"""
            QSpinBox, QDoubleSpinBox {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['text']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                padding: 7px 12px;
                font-size: 9.5pt;
                font-family: {FONT_FAMILY};
                min-height: 20px;
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 2px solid {ENTERPRISE_COLORS['primary']};
            }}
        """

    def _date_style(self):
        return f"""
            QDateEdit {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['text']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                padding: 7px 12px;
                font-size: 9.5pt;
                font-family: {FONT_FAMILY};
            }}
            QDateEdit:focus {{
                border: 2px solid {ENTERPRISE_COLORS['primary']};
            }}
        """

    def _style_white_table(self, table):
        table.setShowGrid(True)
        table.setGridStyle(Qt.PenStyle.SolidLine)
        table.setWordWrap(True)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(54)
        table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['text']};
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                gridline-color: #cbd5e1;
                selection-background-color: {ENTERPRISE_COLORS['primary_light']};
                selection-color: {ENTERPRISE_COLORS['primary']};
                outline: none;
                alternate-background-color: #f8fafc;
                font-size: 9.5pt;
                font-family: "Segoe UI Emoji", "Segoe UI", {FONT_FAMILY};
            }}
            QTableWidget::item {{
                padding: 4px 6px;
                border-right: 1px solid #e2e8f0;
                border-bottom: 1px solid #e2e8f0;
                color: {ENTERPRISE_COLORS['text']};
                background-color: transparent;
            }}
            QTableWidget::item:selected {{
                background-color: {ENTERPRISE_COLORS['primary_light']};
                color: {ENTERPRISE_COLORS['primary']};
                font-weight: 700;
            }}
            QTableWidget::item:hover {{
                background-color: #f1f5f9;
            }}
            QHeaderView::section {{
                background-color: #f1f5f9;
                color: #1e293b;
                padding: 8px 4px;
                border: none;
                border-bottom: 2px solid #64748b;
                border-right: 1px solid #cbd5e1;
                font-weight: 800;
                font-size: 8.5pt;
                text-transform: uppercase;
                letter-spacing: 0.4px;
                font-family: "Segoe UI Emoji", "Segoe UI", {FONT_FAMILY};
            }}
            QHeaderView::section:first {{
                border-top-left-radius: 8px;
            }}
            QHeaderView::section:last {{
                border-top-right-radius: 8px;
                border-right: none;
            }}
        """)
