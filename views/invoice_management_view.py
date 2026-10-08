"""
Invoice Management View - Enterprise Level List, Edit, Preview, Download & Share
Professional invoice management with KPI stats, instant PDF inspection, and WhatsApp sharing.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea,
    QSizePolicy, QComboBox, QDateEdit, QMenu, QMessageBox, QFileDialog,
    QDialog, QDialogButtonBox, QFormLayout, QTextEdit, QCheckBox,
    QProgressDialog, QDoubleSpinBox, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QDate, QUrl, QTimer
from PySide6.QtGui import QFont, QBrush, QColor, QDesktopServices, QCursor
from datetime import datetime, timedelta
import os
import platform
import subprocess

from utils.unified_theme import UnifiedTheme
from utils.app_settings import get_setting
from utils.formatters import Formatters
from views.base_window import BaseView

FONT_FAMILY = "'Inter', 'Segoe UI', sans-serif"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHEVRON_ICON_PATH = os.path.join(BASE_DIR, "assets", "icons", "chevron_down.png").replace("\\", "/")

# Enterprise Design Tokens (White Theme matching Customer & Technician views)
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


def _apply_card_shadow(widget):
    """Clean lightweight border styling avoids heavy software rasterization passes"""
    pass


class InvoiceStatusBadge(QLabel):
    """Modern enterprise badge for payment status"""

    def __init__(self, status, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(24)

        status_norm = (status or "").capitalize()
        cfg = {
            'Paid': (ENTERPRISE_COLORS['success'], ENTERPRISE_COLORS['success_light'], ENTERPRISE_COLORS['success_border']),
            'Partial': (ENTERPRISE_COLORS['warning'], ENTERPRISE_COLORS['warning_light'], ENTERPRISE_COLORS['warning_border']),
            'Pending': (ENTERPRISE_COLORS['danger'], ENTERPRISE_COLORS['danger_light'], ENTERPRISE_COLORS['danger_border'])
        }
        fg, bg, brd = cfg.get(status_norm, (ENTERPRISE_COLORS['text_muted'], ENTERPRISE_COLORS['border_light'], ENTERPRISE_COLORS['border']))
        self.setText(f"● {status_norm}")
        self.setStyleSheet(f"""
            background-color: {bg};
            color: {fg};
            border: 1px solid {brd};
            border-radius: 12px;
            padding: 2px 10px;
            font-size: 8.5pt;
            font-weight: 700;
            font-family: {FONT_FAMILY};
        """)


class InvoiceManagementView(BaseView):
    """Enterprise invoice management view with list, edit, preview, and download features"""

    def __init__(self):
        super().__init__()
        self.theme_manager = UnifiedTheme()
        self.invoice_list = []
        self.selected_invoice_id = None
        self._all_selected = False

        self._setup_ui()
        
        try:
            from utils.event_bus import EventBus
            EventBus().privacy_mode_toggled.connect(self._on_privacy_toggled)
        except Exception:
            pass

        self.load_invoices()

    def update_theme_colors(self):
        """Update theme colors for enterprise white styling"""
        self._style_white_table(self.invoice_table)
        self.load_invoices()

    def _setup_ui(self):
        """Setup enterprise invoice management UI with White Theme"""
        self.currency_symbol = get_setting("currency_symbol", "₹")
        self.setStyleSheet(f"""
            InvoiceManagementView, QWidget {{
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

        # 2. Executive KPI Stat Cards
        self._create_summary_bar(main_layout)

        # 3. Modern Search and Filter Toolbar
        self._create_filters(main_layout)

        # 4. Invoice Data Table
        self._create_invoice_table(main_layout)

        # 5. Consolidated Enterprise Action Toolbar
        self._create_action_buttons(main_layout)

    def _create_header(self, layout):
        """Executive top header with primary actions"""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        # Title & Subtitle
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title = QLabel("INVOICE MANAGEMENT")
        title.setObjectName("headingLabel")
        title.setStyleSheet(f"""
            font-size: 18pt;
            font-weight: 800;
            color: {ENTERPRISE_COLORS['text']};
            font-family: {FONT_FAMILY};
            letter-spacing: -0.5px;
        """)
        text_layout.addWidget(title)

        subtitle = QLabel("Track billings, monitor outstanding balances, inspect PDFs & share instantly")
        subtitle.setObjectName("subheadingLabel")
        subtitle.setStyleSheet(f"""
            font-size: 9.5pt;
            color: {ENTERPRISE_COLORS['text_muted']};
            font-family: {FONT_FAMILY};
        """)
        text_layout.addWidget(subtitle)
        header_layout.addLayout(text_layout)

        header_layout.addStretch()

        # Top Action Suite
        self.refresh_btn = QPushButton("🔄  Refresh")
        self.refresh_btn.setToolTip("Reload invoice records")
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['text_secondary']};
                font-size: 9.5pt;
                font-weight: 600;
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
        """)
        self.refresh_btn.clicked.connect(self.load_invoices)
        header_layout.addWidget(self.refresh_btn)

        self.export_excel_btn = QPushButton("📊  Export Excel")
        self.export_excel_btn.setToolTip("Export invoices to styled Excel sheet with KPIs & charts")
        self.export_excel_btn.setCursor(Qt.PointingHandCursor)
        self.export_excel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['text_secondary']};
                font-size: 9.5pt;
                font-weight: 600;
                font-family: {FONT_FAMILY};
                padding: 8px 14px;
                border-radius: 8px;
                border: 1px solid {ENTERPRISE_COLORS['border']};
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['card_hover']};
                border-color: {ENTERPRISE_COLORS['success_border']};
                color: {ENTERPRISE_COLORS['success']};
            }}
        """)
        self.export_excel_btn.clicked.connect(self.export_invoices_to_excel)
        header_layout.addWidget(self.export_excel_btn)

        self.new_inv_btn = QPushButton("➕  New Invoice")
        self.new_inv_btn.setObjectName("newInvoiceHeaderBtn")
        self.new_inv_btn.setToolTip("Create a new bill / invoice")
        self.new_inv_btn.setCursor(Qt.PointingHandCursor)
        self.new_inv_btn.setStyleSheet(f"""
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
        self.new_inv_btn.clicked.connect(self._create_new_invoice)
        header_layout.addWidget(self.new_inv_btn)

        layout.addWidget(header_widget)

    def _create_summary_bar(self, layout):
        """Executive KPI Stat Cards with individual pure white card grid, accent borders, and soft shadows"""
        self.summary_container = QWidget()
        self.summary_container.setStyleSheet("background: transparent;")
        cards_layout = QHBoxLayout(self.summary_container)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(14)

        self._invoice_raw_summary = {}
        self._invoice_peeked = {}

        is_priv = False
        try:
            from utils.privacy_manager import get_privacy_manager
            is_priv = get_privacy_manager().is_privacy_enabled()
        except Exception:
            pass

        init_val = f"{self.currency_symbol} ••••••" if is_priv else f"{self.currency_symbol}0"
        metrics = [
            ('total_invoices', 'TOTAL INVOICES', '0', '#2563EB', '📄', '#EFF6FF', 'Total records'),
            ('total_amount', 'TOTAL BILLED', init_val, '#0F172A', '💵', '#F8FAFC', 'Gross receivables'),
            ('total_collected', 'COLLECTED REVENUE', init_val, '#059669', '💰', '#ECFDF5', 'Realized payments'),
            ('total_pending', 'PENDING RECEIVABLES', init_val, '#D97706', '⏳', '#FFFBEB', 'Outstanding dues'),
        ]
        self.summary_labels = {}
        for key, label, default, val_color, icon, badge_bg, subtext in metrics:
            card = QFrame()
            card.setObjectName(f"kpiCard_{key}")
            card.setStyleSheet(f"""
                QFrame#kpiCard_{key} {{
                    background-color: #ffffff;
                    border: 1px solid #E2E8F0;
                    border-top: 3.5px solid {val_color};
                    border-radius: 10px;
                    padding: 10px 14px;
                }}
            """)
            _apply_card_shadow(card)

            card_lay = QVBoxLayout(card)
            card_lay.setContentsMargins(4, 4, 4, 4)
            card_lay.setSpacing(4)

            # Top row: icon badge + label + stretch
            top_row = QHBoxLayout()
            top_row.setSpacing(8)

            icon_box = QLabel(icon)
            icon_box.setStyleSheet(f"""
                background-color: {badge_bg};
                border-radius: 6px;
                padding: 4px;
                font-size: 11pt;
            """)
            icon_box.setFixedSize(28, 28)
            icon_box.setAlignment(Qt.AlignCenter)
            top_row.addWidget(icon_box)

            lbl = QLabel(label)
            lbl.setStyleSheet(f"""
                font-size: 8.5pt;
                color: #64748B;
                font-weight: 700;
                font-family: {FONT_FAMILY};
                letter-spacing: 0.5px;
            """)
            top_row.addWidget(lbl)
            top_row.addStretch()
            card_lay.addLayout(top_row)

            # Big Value label
            val = QLabel(default)
            val.setStyleSheet(f"""
                font-size: 17pt;
                font-weight: 800;
                color: {val_color};
                font-family: {FONT_FAMILY};
                padding-top: 2px;
            """)
            card_lay.addWidget(val)

            # Subtext
            sub_lbl = QLabel(subtext)
            sub_lbl.setStyleSheet(f"""
                font-size: 8pt;
                color: #94A3B8;
                font-family: {FONT_FAMILY};
            """)
            card_lay.addWidget(sub_lbl)

            # Click to peek for financial cards
            if key != 'total_invoices':
                card.setCursor(Qt.PointingHandCursor)
                def _make_peek_handler(k, v_lbl):
                    def _card_clicked(event):
                        try:
                            from utils.privacy_manager import get_privacy_manager
                            if get_privacy_manager().is_privacy_enabled():
                                self._invoice_peeked[k] = not self._invoice_peeked.get(k, False)
                                if self._invoice_peeked[k]:
                                    raw = self._invoice_raw_summary.get(k, f"{self.currency_symbol}0")
                                    v_lbl.setText(raw)
                                else:
                                    v_lbl.setText(f"{self.currency_symbol} ••••••")
                        except Exception:
                            pass
                    return _card_clicked
                card.mousePressEvent = _make_peek_handler(key, val)

            cards_layout.addWidget(card)
            self.summary_labels[key] = val
            setattr(self, f'summary_{key}', val)

        layout.addWidget(self.summary_container)

    def _update_summary_bar(self):
        """Update KPI metrics with live data (respects Privacy Shield)"""
        total = len(self.invoice_list)
        amt = sum(float(inv.get('total_amount') or 0) for inv in self.invoice_list)
        col = sum(float(inv.get('advance_payment') or 0) for inv in self.invoice_list)
        pen = sum(float(inv.get('balance_amount') or 0) for inv in self.invoice_list)
        self.summary_total_invoices.setText(str(total))
        
        self._invoice_raw_summary['total_amount'] = f'{self.currency_symbol}{amt:,.0f}'
        self._invoice_raw_summary['total_collected'] = f'{self.currency_symbol}{col:,.0f}'
        self._invoice_raw_summary['total_pending'] = f'{self.currency_symbol}{pen:,.0f}'

        try:
            from utils.privacy_manager import get_privacy_manager
            is_priv = get_privacy_manager().is_privacy_enabled()
        except Exception:
            is_priv = False

        if is_priv:
            self.summary_total_amount.setText(
                self._invoice_raw_summary['total_amount'] if self._invoice_peeked.get('total_amount', False)
                else f'{self.currency_symbol} ••••••'
            )
            self.summary_total_collected.setText(
                self._invoice_raw_summary['total_collected'] if self._invoice_peeked.get('total_collected', False)
                else f'{self.currency_symbol} ••••••'
            )
            self.summary_total_pending.setText(
                self._invoice_raw_summary['total_pending'] if self._invoice_peeked.get('total_pending', False)
                else f'{self.currency_symbol} ••••••'
            )
        else:
            self.summary_total_amount.setText(self._invoice_raw_summary['total_amount'])
            self.summary_total_collected.setText(self._invoice_raw_summary['total_collected'])
            self.summary_total_pending.setText(self._invoice_raw_summary['total_pending'])

    def _on_privacy_toggled(self, enabled: bool):
        """Handle real-time Privacy Shield toggle (updates summary cards only)"""
        try:
            self._invoice_peeked.clear()
            self._update_summary_bar()
        except Exception as e:
            print(f"[INVOICE_VIEW] Error handling privacy toggle: {e}")

    def _create_filters(self, layout):
        """Create executive search and filter controls"""
        filter_frame = QFrame()
        filter_frame.setObjectName("filterCard")
        filter_frame.setStyleSheet(f"""
            QFrame#filterCard {{
                background-color: {ENTERPRISE_COLORS['card']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 10px;
            }}
        """)
        _apply_card_shadow(filter_frame)

        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 12, 16, 12)
        filter_layout.setSpacing(12)

        # Search bar
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 11pt;")
        filter_layout.addWidget(search_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Invoice #, Customer Name, or Mobile...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMinimumWidth(320)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['text']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 9.5pt;
                font-family: {FONT_FAMILY};
            }}
            QLineEdit:focus {{
                border: 1.5px solid {ENTERPRISE_COLORS['primary']};
                background-color: #ffffff;
            }}
        """)
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(200)
        self._search_timer.timeout.connect(self.load_invoices)
        self.search_input.textChanged.connect(lambda: self._search_timer.start())
        filter_layout.addWidget(self.search_input)

        # Date Preset Dropdown
        self.date_preset_combo = QComboBox()
        self.date_preset_combo.addItems([
            "All Time", "Last 30 Days", "This Month", "Today", "This Week", "Last 90 Days", "Custom Range"
        ])
        self.date_preset_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['text_secondary']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                padding: 7px 12px;
                font-size: 9pt;
                font-weight: 600;
                font-family: {FONT_FAMILY};
                min-width: 120px;
            }}
            QComboBox:hover {{
                border-color: {ENTERPRISE_COLORS['primary_border']};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 26px;
                border: none;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }}
            QComboBox::down-arrow {{
                image: url("{CHEVRON_ICON_PATH}");
                width: 12px;
                height: 12px;
                margin-right: 8px;
            }}
            QComboBox::down-arrow:on {{
                top: 1px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['text']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                selection-background-color: {ENTERPRISE_COLORS['primary_light']};
                selection-color: {ENTERPRISE_COLORS['primary']};
                padding: 4px;
            }}
        """)
        self.date_preset_combo.currentTextChanged.connect(self._on_date_preset_changed)
        filter_layout.addWidget(self.date_preset_combo)

        # From Date
        from_lbl = QLabel("From:")
        from_lbl.setStyleSheet(f"font-size: 9pt; font-weight: 600; color: {ENTERPRISE_COLORS['text_secondary']};")
        filter_layout.addWidget(from_lbl)

        self.from_date = QDateEdit()
        self.from_date.setDate(QDate(2020, 1, 1))
        self.from_date.setCalendarPopup(True)
        self.from_date.setDisplayFormat("dd-MM-yyyy")
        self.from_date.setMinimumWidth(115)
        self.from_date.setStyleSheet(f"""
            QDateEdit {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['text']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                padding: 7px 10px;
                font-size: 9pt;
                font-family: {FONT_FAMILY};
            }}
            QDateEdit::drop-down {{
                border: none;
                width: 20px;
            }}
        """)
        self.from_date.dateChanged.connect(self.load_invoices)
        filter_layout.addWidget(self.from_date)

        # To Date
        to_lbl = QLabel("To:")
        to_lbl.setStyleSheet(f"font-size: 9pt; font-weight: 600; color: {ENTERPRISE_COLORS['text_secondary']};")
        filter_layout.addWidget(to_lbl)

        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        self.to_date.setDisplayFormat("dd-MM-yyyy")
        self.to_date.setMinimumWidth(115)
        self.to_date.setStyleSheet(f"""
            QDateEdit {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['text']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                padding: 7px 10px;
                font-size: 9pt;
                font-family: {FONT_FAMILY};
            }}
            QDateEdit::drop-down {{
                border: none;
                width: 20px;
            }}
        """)
        self.to_date.dateChanged.connect(self.load_invoices)
        filter_layout.addWidget(self.to_date)

        # Status Filter
        self.status_combo = QComboBox()
        self.status_combo.addItems(["All Status", "Paid", "Partial", "Pending"])
        self.status_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['text_secondary']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                padding: 7px 12px;
                font-size: 9pt;
                font-weight: 600;
                font-family: {FONT_FAMILY};
                min-width: 100px;
            }}
            QComboBox:hover {{
                border-color: {ENTERPRISE_COLORS['primary_border']};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 26px;
                border: none;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
            }}
            QComboBox::down-arrow {{
                image: url("{CHEVRON_ICON_PATH}");
                width: 12px;
                height: 12px;
                margin-right: 8px;
            }}
            QComboBox::down-arrow:on {{
                top: 1px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['text']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                selection-background-color: {ENTERPRISE_COLORS['primary_light']};
                selection-color: {ENTERPRISE_COLORS['primary']};
                padding: 4px;
            }}
        """)
        self.status_combo.currentTextChanged.connect(self.load_invoices)
        filter_layout.addWidget(self.status_combo)

        # Reset button
        reset_btn = QPushButton("Reset")
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {ENTERPRISE_COLORS['text_muted']};
                border: none;
                font-size: 9pt;
                font-weight: 600;
                padding: 6px 10px;
            }}
            QPushButton:hover {{
                color: {ENTERPRISE_COLORS['primary']};
            }}
        """)
        reset_btn.clicked.connect(self._reset_filters)
        filter_layout.addWidget(reset_btn)

        filter_layout.addStretch()
        layout.addWidget(filter_frame)

    def _on_date_preset_changed(self, preset):
        """Handle quick date preset selection"""
        today = QDate.currentDate()
        self.from_date.blockSignals(True)
        self.to_date.blockSignals(True)

        if preset == "Today":
            self.from_date.setDate(today)
            self.to_date.setDate(today)
        elif preset == "This Week":
            self.from_date.setDate(today.addDays(-(today.dayOfWeek() - 1)))
            self.to_date.setDate(today)
        elif preset == "This Month":
            self.from_date.setDate(QDate(today.year(), today.month(), 1))
            self.to_date.setDate(today)
        elif preset == "Last 30 Days":
            self.from_date.setDate(today.addDays(-30))
            self.to_date.setDate(today)
        elif preset == "Last 90 Days":
            self.from_date.setDate(today.addDays(-90))
            self.to_date.setDate(today)
        elif preset == "All Time":
            self.from_date.setDate(QDate(2020, 1, 1))
            self.to_date.setDate(today)

        self.from_date.blockSignals(False)
        self.to_date.blockSignals(False)
        self.load_invoices()

    def _reset_filters(self):
        """Reset search and date filters to default"""
        self.search_input.clear()
        self.date_preset_combo.setCurrentText("All Time")
        self.status_combo.setCurrentText("All Status")

    def _create_invoice_table(self, layout):
        """Create modern enterprise table with white theme and quick actions"""
        table_container = QFrame()
        table_container.setObjectName("tableCard")
        table_container.setStyleSheet(f"""
            QFrame#tableCard {{
                background-color: {ENTERPRISE_COLORS['card']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 10px;
            }}
        """)
        _apply_card_shadow(table_container)
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(1, 1, 1, 1)

        self.invoice_table = QTableWidget()
        self.invoice_table.setColumnCount(10)
        self.invoice_table.setHorizontalHeaderLabels([
            'ID', 'Invoice No', 'Customer', 'Mobile', 'Amount', 'Advance', 'Balance', 'Status', 'Date', 'Actions'
        ])

        self.invoice_table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.invoice_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.invoice_table.setShowGrid(True)
        self.invoice_table.setAlternatingRowColors(True)
        self.invoice_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.invoice_table.verticalHeader().setVisible(False)
        self.invoice_table.verticalHeader().setDefaultSectionSize(46)
        self.invoice_table.setFocusPolicy(Qt.NoFocus)

        header = self.invoice_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.Fixed)
        self.invoice_table.setColumnWidth(7, 105)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.Fixed)
        self.invoice_table.setColumnWidth(9, 180)

        self._style_white_table(self.invoice_table)

        self.invoice_table.cellDoubleClicked.connect(self.edit_selected_invoice)
        self.invoice_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.invoice_table.customContextMenuRequested.connect(self.show_context_menu)
        self.invoice_table.itemSelectionChanged.connect(self._update_selection_counter)

        table_layout.addWidget(self.invoice_table)
        layout.addWidget(table_container)

        # Status footer label
        self.status_label = QLabel("Loading invoices...")
        self.status_label.setStyleSheet(f"color: {ENTERPRISE_COLORS['text_muted']}; font-size: 9pt; font-family: {FONT_FAMILY}; padding-left: 4px;")
        layout.addWidget(self.status_label)

    def _style_white_table(self, table):
        """Apply pure white enterprise table styling with subtle borders and clean badges"""
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['text']};
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                gridline-color: #E2E8F0;
                alternate-background-color: {ENTERPRISE_COLORS['table_stripe']};
                font-family: {FONT_FAMILY};
                font-size: 9.5pt;
            }}
            QTableWidget::item {{
                padding: 6px 10px;
                border: none;
                color: {ENTERPRISE_COLORS['text']};
            }}
            QTableWidget::item:hover {{
                background-color: #F1F5F9;
            }}
            QTableWidget::item:selected {{
                background-color: #EFF6FF;
                color: #1E3A8A;
            }}
            QHeaderView::section {{
                background-color: #F8FAFC;
                border: none;
                border-right: 1px solid #E2E8F0;
                border-bottom: 2px solid #CBD5E1;
                padding: 10px 8px;
                font-weight: 700;
                font-size: 8.5pt;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                color: #475569;
                font-family: {FONT_FAMILY};
            }}
            QHeaderView::section:last {{
                border-right: none;
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

    def _update_selection_counter(self):
        """Update count of highlighted / selected invoices"""
        selected_rows = len(self.invoice_table.selectionModel().selectedRows())
        if selected_rows > 0:
            self.selected_count_label.setText(f"{selected_rows} invoice{'s' if selected_rows > 1 else ''} selected")
            is_all = (selected_rows == self.invoice_table.rowCount())
            self.select_toggle_btn.setText("☑  Deselect All" if is_all else "☐  Select All")
            self._all_selected = is_all
        else:
            self.selected_count_label.setText("0 invoices selected")
            self.select_toggle_btn.setText("☐  Select All")
            self._all_selected = False

    def _create_action_buttons(self, layout):
        """Consolidated Enterprise Action Suite - clean, de-cluttered, executive layout"""
        action_container = QFrame()
        action_container.setStyleSheet(f"""
            QFrame {{
                background-color: {ENTERPRISE_COLORS['card']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 10px;
            }}
        """)
        _apply_card_shadow(action_container)

        btn_layout = QHBoxLayout(action_container)
        btn_layout.setContentsMargins(16, 12, 16, 12)
        btn_layout.setSpacing(10)

        # Left: Bulk selection controls
        self.select_toggle_btn = QPushButton("☐  Select All")
        self.select_toggle_btn.setToolTip("Click to select all, click again to deselect all")
        self.select_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.select_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['text_secondary']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 9.5pt;
                font-weight: 600;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{
                border-color: {ENTERPRISE_COLORS['primary_border']};
                color: {ENTERPRISE_COLORS['primary']};
            }}
        """)
        self.select_toggle_btn.clicked.connect(self._toggle_select_all)
        btn_layout.addWidget(self.select_toggle_btn)

        self.selected_count_label = QLabel("0 invoices selected")
        self.selected_count_label.setStyleSheet(f"""
            color: {ENTERPRISE_COLORS['text_muted']};
            font-size: 9pt;
            font-family: {FONT_FAMILY};
            padding-left: 6px;
        """)
        btn_layout.addWidget(self.selected_count_label)

        btn_layout.addStretch()

        # Right: Consolidated Executive Suite
        # 1. 👁️ View PDF Button
        self.view_pdf_btn = QPushButton("👁️  View PDF")
        self.view_pdf_btn.setToolTip("Directly open and inspect the generated PDF invoice in default system viewer")
        self.view_pdf_btn.setCursor(Qt.PointingHandCursor)
        self.view_pdf_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ENTERPRISE_COLORS['primary_light']};
                color: {ENTERPRISE_COLORS['primary']};
                border: 1px solid {ENTERPRISE_COLORS['primary_border']};
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 9.5pt;
                font-weight: 700;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['primary']};
                color: #ffffff;
            }}
        """)
        self.view_pdf_btn.clicked.connect(lambda: self.view_selected_invoice_pdf())
        btn_layout.addWidget(self.view_pdf_btn)

        # 2. 📥 Download PDF
        self.download_pdf_btn = QPushButton("📥  Download PDF")
        self.download_pdf_btn.setToolTip("Save invoice PDF to a chosen folder on your disk")
        self.download_pdf_btn.setCursor(Qt.PointingHandCursor)
        self.download_pdf_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['text_secondary']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 9.5pt;
                font-weight: 600;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{
                border-color: {ENTERPRISE_COLORS['info_border']};
                color: {ENTERPRISE_COLORS['info']};
            }}
        """)
        self.download_pdf_btn.clicked.connect(self.download_selected_invoice)
        btn_layout.addWidget(self.download_pdf_btn)

        # 3. 📱 WhatsApp
        self.wa_btn = QPushButton("📱  WhatsApp")
        self.wa_btn.setToolTip("Share selected invoice PDF directly to customer WhatsApp")
        self.wa_btn.setCursor(Qt.PointingHandCursor)
        self.wa_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #25D366;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 9.5pt;
                font-weight: 700;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: #128C7E;
            }}
        """)
        self.wa_btn.clicked.connect(self.share_invoice_whatsapp)
        btn_layout.addWidget(self.wa_btn)

        # 4. 🖨️ Print
        self.print_btn = QPushButton("🖨️  Print")
        self.print_btn.setToolTip("Print selected invoice(s)")
        self.print_btn.setCursor(Qt.PointingHandCursor)
        self.print_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['text_secondary']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 9.5pt;
                font-weight: 600;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{
                border-color: {ENTERPRISE_COLORS['primary_border']};
                color: {ENTERPRISE_COLORS['primary']};
            }}
        """)
        self.print_btn.clicked.connect(self.print_invoices)
        btn_layout.addWidget(self.print_btn)

        # 5. 💰 Receive Payment
        self.payment_btn = QPushButton("💰  Receive Payment")
        self.payment_btn.setToolTip("Record incoming payment against selected invoice")
        self.payment_btn.setCursor(Qt.PointingHandCursor)
        self.payment_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ENTERPRISE_COLORS['success']};
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 9.5pt;
                font-weight: 700;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['success_hover']};
            }}
        """)
        self.payment_btn.clicked.connect(self._receive_payment)
        btn_layout.addWidget(self.payment_btn)

        # 6. 🗑️ Delete
        self.delete_btn = QPushButton("🗑️  Delete")
        self.delete_btn.setToolTip("Soft delete selected invoice")
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['danger']};
                border: 1px solid {ENTERPRISE_COLORS['danger_border']};
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 9.5pt;
                font-weight: 600;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['danger']};
                color: #ffffff;
            }}
        """)
        self.delete_btn.clicked.connect(self.delete_selected_invoice)
        btn_layout.addWidget(self.delete_btn)

        layout.addWidget(action_container)

    def _create_new_invoice(self):
        """Switch to New Invoice view from Invoice Management"""
        parent = self.parent()
        while parent:
            if hasattr(parent, '_show_invoice'):
                parent._show_invoice()
                return
            parent = parent.parent()

    def load_invoices(self):
        """Load invoices from database with enterprise white formatting"""
        try:
            from database.db_connection import DatabaseContext

            with DatabaseContext() as db:
                query = """
                    SELECT 
                        i.id, i.invoice_number, 
                        c.name as customer_name, c.mobile,
                        i.total_amount, i.advance_payment, i.balance_amount,
                        i.payment_status, DATE(i.created_at) as invoice_date
                    FROM invoices i
                    JOIN customers c ON i.customer_id = c.id
                    WHERE i.is_active = TRUE
                """
                params = []

                # Search filter
                search_term = self.search_input.text().strip()
                if search_term:
                    query += " AND (i.invoice_number LIKE %s OR c.name LIKE %s OR c.mobile LIKE %s)"
                    params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])

                # Date filter
                preset = self.date_preset_combo.currentText()
                if preset != "All Time":
                    from_date_widget = self.from_date.date().toString("yyyy-MM-dd")
                    to_date_widget = self.to_date.date().toString("yyyy-MM-dd")
                    query += " AND DATE(i.created_at) BETWEEN %s AND %s"
                    params.extend([from_date_widget, to_date_widget])

                # Status filter
                status = self.status_combo.currentText()
                if status != "All Status":
                    query += " AND i.payment_status = %s"
                    params.append(status)

                query += " ORDER BY i.created_at DESC"

                results = db.execute_query(query, params, fetch_all=True)
                self.invoice_list = results if results else []

                self.invoice_table.setUpdatesEnabled(False)
                try:
                    self.invoice_table.setRowCount(len(self.invoice_list))
                    for row, invoice in enumerate(self.invoice_list):
                        def _fmt_val(val):
                            return f"{self.currency_symbol}{val:,.0f}"

                        items_data = [
                            (str(invoice['id']), Qt.AlignCenter),
                            (str(invoice['invoice_number']), Qt.AlignLeft),
                            (str(invoice['customer_name']), Qt.AlignLeft),
                            (str(invoice['mobile']), Qt.AlignCenter),
                            (_fmt_val(float(invoice.get('total_amount') or 0)), Qt.AlignRight),
                            (_fmt_val(float(invoice.get('advance_payment') or 0)), Qt.AlignRight),
                            (_fmt_val(float(invoice.get('balance_amount') or 0)), Qt.AlignRight),
                        ]

                        for col_idx, (text, align) in enumerate(items_data):
                            table_item = QTableWidgetItem(text)
                            table_item.setTextAlignment(align | Qt.AlignVCenter)
                            if col_idx == 0:  # ID
                                table_item.setForeground(QBrush(QColor("#64748B")))
                            elif col_idx == 1:  # Invoice No
                                font = table_item.font()
                                font.setBold(True)
                                table_item.setFont(font)
                                table_item.setForeground(QBrush(QColor(ENTERPRISE_COLORS['primary'])))
                            elif col_idx == 2:  # Customer
                                font = table_item.font()
                                font.setBold(True)
                                table_item.setFont(font)
                                table_item.setForeground(QBrush(QColor("#0F172A")))
                            elif col_idx == 3:  # Mobile
                                table_item.setForeground(QBrush(QColor("#475569")))
                            elif col_idx == 4:  # Amount
                                font = table_item.font()
                                font.setBold(True)
                                table_item.setFont(font)
                                table_item.setForeground(QBrush(QColor("#0F172A")))
                            elif col_idx == 5:  # Advance
                                amt_adv = float(invoice.get('advance_payment') or 0)
                                if amt_adv > 0:
                                    table_item.setForeground(QBrush(QColor(ENTERPRISE_COLORS['success'])))
                            elif col_idx == 6:  # Balance
                                amt_bal = float(invoice.get('balance_amount') or 0)
                                if amt_bal > 0:
                                    font = table_item.font()
                                    font.setBold(True)
                                    table_item.setFont(font)
                                    table_item.setForeground(QBrush(QColor(ENTERPRISE_COLORS['danger'])))
                                else:
                                    table_item.setForeground(QBrush(QColor(ENTERPRISE_COLORS['success'])))
                            self.invoice_table.setItem(row, col_idx, table_item)

                        # 7. Status Badge
                        status_text = invoice.get('payment_status', 'Pending')
                        status_container = QWidget()
                        status_container_layout = QHBoxLayout(status_container)
                        status_container_layout.setContentsMargins(4, 2, 4, 2)
                        status_container_layout.setAlignment(Qt.AlignCenter)
                        status_badge = InvoiceStatusBadge(status_text)
                        status_container_layout.addWidget(status_badge)
                        self.invoice_table.setCellWidget(row, 7, status_container)
                        status_item = QTableWidgetItem(status_text)
                        status_item.setTextAlignment(Qt.AlignCenter)
                        self.invoice_table.setItem(row, 7, status_item)

                        # 8. Date
                        date_text = Formatters.format_date(invoice.get('invoice_date'))
                        date_item = QTableWidgetItem(date_text)
                        date_item.setTextAlignment(Qt.AlignCenter)
                        self.invoice_table.setItem(row, 8, date_item)

                        # 9. Actions Column (👁️ PDF + 💬 WA) - Centered with plenty of room
                        action_widget = QWidget()
                        action_widget.setStyleSheet("background: transparent;")
                        action_layout = QHBoxLayout(action_widget)
                        action_layout.setContentsMargins(4, 2, 4, 2)
                        action_layout.setSpacing(8)
                        action_layout.setAlignment(Qt.AlignCenter)

                        # 👁️ View PDF row button
                        row_view_btn = QPushButton("👁️ PDF")
                        row_view_btn.setToolTip(f"View PDF ({invoice['invoice_number']})")
                        row_view_btn.setCursor(Qt.PointingHandCursor)
                        row_view_btn.setFixedHeight(28)
                        row_view_btn.setMinimumWidth(68)
                        row_view_btn.setStyleSheet(f"""
                            QPushButton {{
                                background-color: {ENTERPRISE_COLORS['primary_light']};
                                color: {ENTERPRISE_COLORS['primary']};
                                border: 1px solid {ENTERPRISE_COLORS['primary_border']};
                                border-radius: 6px;
                                padding: 4px 8px;
                                font-size: 8.5pt;
                                font-weight: 700;
                                font-family: {FONT_FAMILY};
                            }}
                            QPushButton:hover {{
                                background-color: {ENTERPRISE_COLORS['primary']};
                                color: #ffffff;
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
                        inv_id = invoice['id']
                        row_view_btn.clicked.connect(lambda checked=False, i_id=inv_id: self.view_selected_invoice_pdf(i_id))
                        action_layout.addWidget(row_view_btn)

                        # 💬 WhatsApp row button
                        row_wa_btn = QPushButton("💬 WA")
                        row_wa_btn.setToolTip(f"Share on WhatsApp ({invoice['customer_name']})")
                        row_wa_btn.setCursor(Qt.PointingHandCursor)
                        row_wa_btn.setFixedHeight(28)
                        row_wa_btn.setMinimumWidth(62)
                        row_wa_btn.setStyleSheet(f"""
                            QPushButton {{
                                background-color: #25D36615;
                                color: #128C7E;
                                border: 1px solid #25D36640;
                                border-radius: 6px;
                                padding: 4px 8px;
                                font-size: 8.5pt;
                                font-weight: 700;
                                font-family: {FONT_FAMILY};
                            }}
                            QPushButton:hover {{
                                background-color: #25D366;
                                color: #ffffff;
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
                        row_wa_btn.clicked.connect(lambda checked=False, inv=invoice: self.share_single_invoice_whatsapp(inv))
                        action_layout.addWidget(row_wa_btn)

                        self.invoice_table.setCellWidget(row, 9, action_widget)
                finally:
                    self.invoice_table.setUpdatesEnabled(True)

                self.status_label.setText(f"Showing {len(self.invoice_list)} invoices")
                self._update_summary_bar()
                self._update_selection_counter()

        except Exception as e:
            self.show_error_message(f"Error loading invoices: {str(e)}")
            print(f"Error: {str(e)}")

    def show_context_menu(self, pos):
        """Show context menu on right-click"""
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: #ffffff;
                color: {ENTERPRISE_COLORS['text']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                padding: 4px;
                font-family: {FONT_FAMILY};
                font-size: 9pt;
            }}
            QMenu::item {{
                padding: 6px 16px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {ENTERPRISE_COLORS['primary_light']};
                color: {ENTERPRISE_COLORS['primary']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {ENTERPRISE_COLORS['divider']};
                margin: 4px 8px;
            }}
        """)
        menu.addAction("👁️  View PDF", lambda: self.view_selected_invoice_pdf())
        menu.addAction("✏️  Edit Invoice", self.edit_selected_invoice)
        menu.addAction("📥  Download PDF", self.download_selected_invoice)
        menu.addAction("📱  Share on WhatsApp", self.share_invoice_whatsapp)
        menu.addAction("💰  Receive Payment", self._receive_payment)
        menu.addSeparator()
        menu.addAction("📊  Export to Excel", self.export_invoices_to_excel)
        menu.addAction("🖨️  Print Invoices", self.print_invoices)
        menu.addSeparator()
        menu.addAction("🗑️  Delete Invoice", self.delete_selected_invoice)
        menu.exec(self.invoice_table.viewport().mapToGlobal(pos))

    def _get_selected_invoice_ids(self):
        """Get list of invoice IDs for currently highlighted/selected rows"""
        selected_rows = self.invoice_table.selectionModel().selectedRows()
        ids = []
        for idx in selected_rows:
            item = self.invoice_table.item(idx.row(), 0)
            if item:
                try:
                    ids.append(int(item.text()))
                except ValueError:
                    pass
        if not ids and self.invoice_table.currentRow() >= 0:
            item = self.invoice_table.item(self.invoice_table.currentRow(), 0)
            if item:
                try:
                    ids.append(int(item.text()))
                except ValueError:
                    pass
        return ids

    def get_selected_invoice(self):
        """Get selected invoice data from table row selection or current active row"""
        invoice_id = None
        selected_rows = self.invoice_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            id_item = self.invoice_table.item(row, 0)
            if id_item:
                try:
                    invoice_id = int(id_item.text())
                except ValueError:
                    pass
        elif self.invoice_table.currentRow() >= 0:
            id_item = self.invoice_table.item(self.invoice_table.currentRow(), 0)
            if id_item:
                try:
                    invoice_id = int(id_item.text())
                except ValueError:
                    pass

        if invoice_id is None:
            self.show_warning_message("Please select an invoice first")
            return None

        # Find invoice in list
        for invoice in self.invoice_list:
            if invoice['id'] == invoice_id:
                return invoice

        return None

    def _build_pdf_for_invoice(self, invoice_id, force_regenerate=False):
        """Build and generate the PDF invoice for a given invoice ID and return its path"""
        from database.db_connection import DatabaseContext
        from utils.pdf_invoice_generator import PDFInvoiceGenerator
        from utils.formatters import Formatters
        from config import PDF_DIR

        with DatabaseContext() as db:
            query = """
                SELECT i.*, c.name as customer_name, c.mobile as customer_mobile,
                       c.email as customer_email, c.address as customer_address, c.landmark,
                       ab.brand_name as ac_brand, i.ac_type, i.star_rating, i.ton_capacity,
                       i.ac_inverter, i.technician_id, i.payment_mode,
                       i.subtotal, i.gst_percentage, i.gst_amount,
                       i.total_amount, i.advance_payment, i.balance_amount,
                       i.payment_status, i.notes, DATE(i.created_at) as invoice_date
                FROM invoices i
                JOIN customers c ON i.customer_id = c.id
                LEFT JOIN ac_brands ab ON i.ac_brand_id = ab.id
                WHERE i.id = %s
            """
            invoice_data = db.execute_query(query, (invoice_id,), fetch_one=True)
            if not invoice_data:
                raise Exception(f"Invoice #{invoice_id} not found")

            safe_name = "".join(c if c.isalnum() or c in ' -_' else '_' for c in invoice_data.get('customer_name', 'Customer'))
            expected_path = os.path.join(str(PDF_DIR), f"{safe_name}_{invoice_data['invoice_number']}.pdf")
            if not force_regenerate and os.path.exists(expected_path) and os.path.getsize(expected_path) > 1000:
                return expected_path

            items_query = """
                SELECT ii.*, s.service_name, p.part_name, p.unit
                FROM invoice_items ii
                LEFT JOIN services s ON ii.service_id = s.id
                LEFT JOIN parts p ON ii.part_id = p.id
                WHERE ii.invoice_id = %s
            """
            items = db.execute_query(items_query, (invoice_id,), fetch_all=True) or []

            technician_name = ''
            technician_mobile = ''
            if invoice_data.get('technician_id'):
                tech = db.execute_query(
                    "SELECT name, mobile FROM technicians WHERE id = %s",
                    (invoice_data['technician_id'],),
                    fetch_one=True
                )
                if tech:
                    technician_name = tech.get('name') or ''
                    technician_mobile = tech.get('mobile') or ''

        pdf_data = {
            'invoice_number': invoice_data['invoice_number'],
            'invoice_date': Formatters.format_date(invoice_data.get('invoice_date')) or 'N/A',
            'customer_name': invoice_data['customer_name'],
            'customer_mobile': invoice_data['customer_mobile'],
            'customer_address': invoice_data.get('customer_address') or 'N/A',
            'ac_brand': invoice_data.get('ac_brand', 'N/A'),
            'ac_type': invoice_data.get('ac_type', 'N/A'),
            'ton_capacity': invoice_data.get('ton_capacity', 'N/A'),
            'technician_name': technician_name,
            'technician_mobile': technician_mobile,
            'items': [{
                'description': it.get('service_name') or it.get('part_name') or 'Service',
                'quantity': it.get('quantity', 1),
                'rate': float(it.get('rate') or 0),
                'amount': float(it.get('amount') or 0),
                'unit': it.get('unit', 'pcs')
            } for it in items],
            'subtotal': float(invoice_data.get('subtotal') or invoice_data.get('total_amount') or 0),
            'gst_amount': float(invoice_data.get('gst_amount') or 0),
            'gst_percentage': float(invoice_data.get('gst_percentage') or 0),
            'total_amount': float(invoice_data.get('total_amount') or 0),
            'paid_amount': float(invoice_data.get('advance_payment') or 0),
            'balance_amount': float(invoice_data.get('balance_amount') or 0),
            'payment_mode': invoice_data.get('payment_mode', ''),
            'payment_status': invoice_data.get('payment_status', '')
        }

        generator = PDFInvoiceGenerator()
        return generator.generate_invoice(pdf_data)

    def view_selected_invoice_pdf(self, invoice_id=None):
        """1-click direct preview of the generated professional PDF in system viewer"""
        if invoice_id is None:
            inv = self.get_selected_invoice()
            if not inv:
                return
            invoice_id = inv['id']

        try:
            pdf_path = self._build_pdf_for_invoice(invoice_id)
            if not pdf_path or not os.path.exists(pdf_path):
                self.show_error_message("Could not generate or locate the PDF invoice.")
                return

            # Open PDF in OS default viewer
            abs_path = os.path.abspath(pdf_path)
            opened = QDesktopServices.openUrl(QUrl.fromLocalFile(abs_path))
            if not opened:
                # Windows fallback
                if platform.system() == 'Windows':
                    os.startfile(abs_path)
                elif platform.system() == 'Darwin':
                    subprocess.run(['open', abs_path])
                else:
                    subprocess.run(['xdg-open', abs_path])
        except Exception as e:
            self.show_error_message(f"Error opening PDF: {str(e)}")
            import traceback
            traceback.print_exc()

    def share_single_invoice_whatsapp(self, invoice):
        """Row action to directly share this invoice on WhatsApp"""
        try:
            pdf_path = self._build_pdf_for_invoice(invoice['id'])
            self._send_whatsapp_with_pdf(invoice, pdf_path)
        except Exception as e:
            self.show_error_message(f"Error opening WhatsApp: {str(e)}")
            import traceback
            traceback.print_exc()

    def edit_selected_invoice(self):
        """Edit selected invoice"""
        invoice = self.get_selected_invoice()
        if not invoice:
            return

        # Open invoice in edit mode
        try:
            from database.db_connection import DatabaseContext
            from views.edit_invoice_dialog import EditInvoiceDialog

            # Get full invoice data
            with DatabaseContext() as db:
                query = """
                    SELECT i.*, c.name, c.mobile, c.email, c.address, c.landmark,
                           ab.brand_name, i.ac_type, i.star_rating, i.ton_capacity,
                           i.ac_inverter, i.payment_mode, i.payment_status, i.notes,
                           i.advance_payment, i.gst_percentage,
                           t.name as technician_name
                    FROM invoices i
                    JOIN customers c ON i.customer_id = c.id
                    LEFT JOIN ac_brands ab ON i.ac_brand_id = ab.id
                    LEFT JOIN technicians t ON i.technician_id = t.id
                    WHERE i.id = %s
                """
                invoice_data = db.execute_query(query, (invoice['id'],), fetch_one=True)

                if invoice_data:
                    # Open edit dialog
                    dialog = EditInvoiceDialog(self, invoice_data)
                    
                    if dialog.exec():
                        # Save changes to database
                        self._save_edited_invoice(invoice_data['id'], dialog)
                    
        except Exception as e:
            self.show_error_message(f"Error opening invoice: {str(e)}")
            import traceback
            traceback.print_exc()

    def _receive_payment(self):
        invoice = self.get_selected_invoice()
        if not invoice:
            return
        if invoice['balance_amount'] <= 0:
            self.show_warning_message("This invoice has no pending balance")
            return
        dlg = ReceivePaymentDialog(self, invoice)
        if dlg.exec():
            from controllers.invoice_controller import InvoiceController
            from database.db_connection import DatabaseContext
            with DatabaseContext() as db:
                ctrl = InvoiceController(db)
                amount = dlg.amount_spin.value()
                mode = dlg.mode_combo.currentText()
                notes = dlg.notes_input.toPlainText().strip()
                success, msg = ctrl.update_invoice_payment(invoice['id'], amount, mode, notes)
                if success:
                    self.show_success_message(f"Payment received: {self.currency_symbol}{amount:,.2f}")
                    self.load_invoices()
                else:
                    self.show_error_message(msg)

    def _save_edited_invoice(self, invoice_id, dialog):
        """Save edited invoice to database"""
        try:
            from database.db_connection import DatabaseContext
            from decimal import Decimal

            with DatabaseContext() as db:
                # Start transaction
                db.begin_transaction()
                try:
                    # Get customer_id first (don't rely on mobile)
                    customer_query = """
                        SELECT id FROM customers WHERE mobile = %s LIMIT 1
                    """
                    customer_result = db.execute_query(customer_query, (dialog.customer_mobile_input.text().strip(),), fetch_one=True)
                    
                    if not customer_result:
                        raise Exception("Customer not found with this mobile number")
                    
                    customer_id = customer_result['id']

                    from utils.app_settings import get_setting
                    discount_before_gst = get_setting('discount_before_gst', False)

                    # Calculate totals from items
                    subtotal = sum(item['amount'] for item in dialog.invoice_items)
                    subtotal_decimal = Decimal(str(subtotal))

                    # Calculate discount (base is always subtotal; legacy mode recalculates below)
                    discount_type = ''
                    discount_value = Decimal('0.00')
                    discount_amount = Decimal('0.00')
                    if dialog.disc_checkbox.isChecked():
                        raw_type = dialog.disc_type_combo.currentText()
                        discount_type = 'percentage' if raw_type == '%' else 'fixed'
                        discount_value = Decimal(str(dialog.disc_value_spin.value()))
                        base_for_disc = subtotal_decimal
                        if discount_type == 'percentage':
                            discount_amount = base_for_disc * discount_value / Decimal('100')
                        else:
                            discount_amount = discount_value

                    # Calculate GST (on discounted subtotal if GST-compliant mode)
                    gst_amount = Decimal('0.00')
                    if dialog.gst_checkbox.isChecked():
                        gst_rate_text = dialog.gst_rate_combo.currentText()
                        gst_rate = Decimal(gst_rate_text.replace('%', ''))
                        if discount_before_gst:
                            gst_base = subtotal_decimal - discount_amount
                            if gst_base < 0:
                                gst_base = Decimal('0')
                            gst_amount = gst_base * gst_rate / Decimal('100')
                        else:
                            gst_amount = subtotal_decimal * gst_rate / Decimal('100')

                    # Recalculate discount for legacy mode (discount on subtotal+GST)
                    if dialog.disc_checkbox.isChecked() and not discount_before_gst:
                        total_before_disc = subtotal_decimal + gst_amount
                        if discount_type == 'percentage':
                            discount_amount = total_before_disc * discount_value / Decimal('100')

                    # Calculate total and balance
                    total = subtotal_decimal + gst_amount - discount_amount
                    advance = Decimal(str(dialog.advance_input.value()))
                    balance = total - advance

                    # Parse GST rate
                    gst_rate_str = dialog.gst_rate_combo.currentText().replace('%', '')
                    gst_rate = float(gst_rate_str) if dialog.gst_checkbox.isChecked() else 0.0

                    # Update invoice (including discount columns)
                    query = """
                        UPDATE invoices SET
                            customer_id = %s,
                            ac_brand_id = (SELECT id FROM ac_brands WHERE brand_name = %s LIMIT 1),
                            ac_type = %s,
                            star_rating = %s,
                            ton_capacity = %s,
                            ac_inverter = %s,
                            payment_mode = %s,
                            payment_status = %s,
                            notes = %s,
                            advance_payment = %s,
                            gst_percentage = %s,
                            gst_amount = %s,
                            discount_type = %s,
                            discount_value = %s,
                            discount_amount = %s,
                            subtotal = %s,
                            total_amount = %s,
                            balance_amount = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """

                    db.execute_query(query, (
                        customer_id,
                        dialog.ac_brand_combo.currentText(),
                        dialog.ac_type_combo.currentText(),
                        dialog.ac_star_combo.currentText(),
                        dialog.ac_ton_combo.currentText(),
                        dialog.ac_inverter_combo.currentText(),
                        dialog.payment_mode_combo.currentText(),
                        dialog.payment_status_combo.currentText(),
                        dialog.notes_input.toPlainText().strip(),
                        float(dialog.advance_input.value()),
                        gst_rate,
                        float(gst_amount),
                        discount_type,
                        float(discount_value),
                        float(discount_amount),
                        float(subtotal_decimal),
                        float(total),
                        float(balance),
                        invoice_id
                    ))

                    # Update customer details using customer_id (not mobile)
                    customer_update_query = """
                        UPDATE customers SET
                            name = %s,
                            mobile = %s,
                            email = %s,
                            address = %s,
                            landmark = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """
                    db.execute_query(customer_update_query, (
                        dialog.customer_name_input.text().strip(),
                        dialog.customer_mobile_input.text().strip(),
                        dialog.customer_email_input.text().strip(),
                        dialog.customer_address_input.toPlainText().strip(),
                        dialog.customer_landmark_input.text().strip(),
                        customer_id
                    ))

                    # Delete old invoice items
                    db.execute_query("DELETE FROM invoice_items WHERE invoice_id = %s", (invoice_id,))

                    # Insert new invoice items
                    for item in dialog.invoice_items:
                        insert_query = """
                            INSERT INTO invoice_items (invoice_id, service_id, part_id, quantity, rate, amount)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        db.execute_query(insert_query, (
                            invoice_id,
                            item.get('service_id'),
                            item.get('part_id'),
                            item['quantity'],
                            item['rate'],
                            item['amount']
                        ))

                    # Commit transaction
                    db.commit()

                    # Purge any stale PDF on disk for this invoice
                    try:
                        import glob
                        from config import PDF_DIR
                        inv_num = dialog.invoice_data.get('invoice_number', '')
                        if inv_num:
                            for p in glob.glob(os.path.join(str(PDF_DIR), f"*{inv_num}*.pdf")):
                                try:
                                    os.remove(p)
                                except Exception:
                                    pass
                    except Exception:
                        pass

                    self.show_success_message("Invoice updated successfully!")
                    self.load_invoices()  # Refresh list

                except Exception as e:
                    # Rollback on error
                    db.rollback()
                    raise e
                finally:
                    if getattr(db, '_transaction_active', False):
                        db.rollback()

        except Exception as e:
            self.show_error_message(f"Error saving changes: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def show_invoice_details(self, invoice):
        """Show complete invoice details in a dialog - Professional Layout"""
        try:
            from database.db_connection import DatabaseContext

            with DatabaseContext() as db:
                # Get complete invoice data
                query = """
                    SELECT i.*, c.name as customer_name, c.mobile, c.email, c.address, c.landmark,
                           ab.brand_name as ac_brand, i.ac_type, i.star_rating, i.ton_capacity as ac_capacity,
                           i.ac_inverter, t.name as technician_name, t.mobile as technician_mobile
                    FROM invoices i
                    JOIN customers c ON i.customer_id = c.id
                    LEFT JOIN ac_brands ab ON i.ac_brand_id = ab.id
                    LEFT JOIN technicians t ON i.technician_id = t.id
                    WHERE i.id = %s
                """
                invoice_data = db.execute_query(query, (invoice['id'],), fetch_one=True)

                # Get invoice items
            items_query = """
                SELECT ii.*,
                       COALESCE(s.service_name, p.part_name, ii.description, 'N/A') as item_name
                FROM invoice_items ii
                LEFT JOIN services s ON ii.service_id = s.id
                LEFT JOIN parts p ON ii.part_id = p.id
                WHERE ii.invoice_id = %s
            """
            items = db.execute_query(items_query, (invoice['id'],), fetch_all=True)

            dialog = QDialog(self)
            dialog.setWindowTitle(f"Invoice Details - {invoice['invoice_number']}")
            dialog.setMinimumSize(700, 600)

            layout = QVBoxLayout(dialog)
            layout.setSpacing(15)

            # Title
            title = QLabel(f"Invoice: {invoice['invoice_number']}")
            title.setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {self.theme_manager.get_colors()['fg']};")
            layout.addWidget(title)

            # Scroll area for content
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("border: none; background: transparent;")

            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)
            content_layout.setSpacing(12)

            # Customer Details
            customer_group = QLabel("<b>CUSTOMER DETAILS</b>")
            customer_group.setStyleSheet("font-size: 11pt; font-weight: bold; background: #f0f0f0; padding: 5px;")
            content_layout.addWidget(customer_group)

            customer_details = f"""
            <table style="width: 100%; font-size: 9pt;">
                <tr><td style="width: 100px;"><b>Name:</b></td><td>{invoice_data.get('customer_name', 'N/A')}</td></tr>
                <tr><td><b>Mobile:</b></td><td>{invoice_data.get('mobile', 'N/A')}</td></tr>
                <tr><td><b>Email:</b></td><td>{invoice_data.get('email', 'N/A') or 'N/A'}</td></tr>
                <tr><td><b>Address:</b></td><td>{invoice_data.get('address', 'N/A') or 'N/A'}</td></tr>
            </table>
            """
            content_layout.addWidget(QLabel(customer_details))

            # Service & AC Details
            service_group = QLabel("<b>SERVICE & AC DETAILS</b>")
            service_group.setStyleSheet("font-size: 11pt; font-weight: bold; background: #f0f0f0; padding: 5px;")
            content_layout.addWidget(service_group)

            service_details = f"""
            <table style="width: 100%; font-size: 9pt;">
                <tr><td style="width: 120px;"><b>Technician:</b></td><td>{invoice_data.get('technician_name', 'N/A')} ({invoice_data.get('technician_mobile', 'N/A')})</td></tr>
                <tr><td><b>AC Brand:</b></td><td>{invoice_data.get('ac_brand', 'N/A') or 'N/A'}</td></tr>
                <tr><td><b>AC Type:</b></td><td>{invoice_data.get('ac_type', 'N/A')}</td></tr>
                <tr><td><b>Capacity:</b></td><td>{invoice_data.get('ac_capacity', 'N/A')}</td></tr>
                <tr><td><b>Inverter:</b></td><td>{invoice_data.get('ac_inverter', 'N/A')}</td></tr>
            </table>
            """
            content_layout.addWidget(QLabel(service_details))

            # Items
            items_group = QLabel("<b>ITEMS</b>")
            items_group.setStyleSheet("font-size: 11pt; font-weight: bold; background: #f0f0f0; padding: 5px;")
            content_layout.addWidget(items_group)

            if items:
                items_text = """
                <table style="width: 100%; font-size: 9pt; border-collapse: collapse;">
                    <tr style="background: #e0e0e0;">
                        <td style="padding: 5px; border: 1px solid #ccc;"><b>Type</b></td>
                        <td style="padding: 5px; border: 1px solid #ccc;"><b>Name</b></td>
                        <td style="padding: 5px; border: 1px solid #ccc;"><b>Qty</b></td>
                        <td style="padding: 5px; border: 1px solid #ccc;"><b>Rate</b></td>
                        <td style="padding: 5px; border: 1px solid #ccc;"><b>Amount</b></td>
                    </tr>
                """
                for item in items:
                    item_type = item.get('item_type', 'N/A')
                    item_name = item.get('service_name') or item.get('part_name') or 'N/A'
                    qty = item.get('quantity', 0)
                    rate = float(item.get('rate', 0))
                    amount = float(item.get('amount', 0))
                    items_text += f"""
                    <tr>
                        <td style="padding: 5px; border: 1px solid #ccc;">{item_type}</td>
                        <td style="padding: 5px; border: 1px solid #ccc;">{item_name}</td>
                        <td style="padding: 5px; border: 1px solid #ccc;">{qty}</td>
                        <td style="padding: 5px; border: 1px solid #ccc;">{self.currency_symbol}{rate:,.2f}</td>
                        <td style="padding: 5px; border: 1px solid #ccc;">{self.currency_symbol}{amount:,.2f}</td>
                    </tr>
                    """
                items_text += "</table>"
                content_layout.addWidget(QLabel(items_text))
            else:
                content_layout.addWidget(QLabel("No items"))

            # Payment Summary
            payment_group = QLabel("<b>PAYMENT SUMMARY</b>")
            payment_group.setStyleSheet("font-size: 11pt; font-weight: bold; background: #f0f0f0; padding: 5px;")
            content_layout.addWidget(payment_group)

            total = float(invoice_data.get('total_amount', 0))
            advance = float(invoice_data.get('advance_payment', 0))
            balance = float(invoice_data.get('balance_amount', 0))

            payment_details = f"""
            <table style="width: 100%; font-size: 9pt;">
                <tr><td style="width: 120px;"><b>Total Amount:</b></td><td style="text-align: right;"><b>{self.currency_symbol}{total:,.2f}</b></td></tr>
                <tr><td><b>Advance Paid:</b></td><td style="text-align: right;">{self.currency_symbol}{advance:,.2f}</td></tr>
                <tr><td><b>Balance Due:</b></td><td style="text-align: right; color: #d97706;"><b>{self.currency_symbol}{balance:,.2f}</b></td></tr>
                <tr><td><b>Payment Status:</b></td><td>{invoice_data.get('payment_status', 'N/A')}</td></tr>
                <tr><td><b>Payment Mode:</b></td><td>{invoice_data.get('payment_mode', 'N/A')}</td></tr>
            </table>
            """
            content_layout.addWidget(QLabel(payment_details))

            # Notes
            notes = invoice_data.get('notes', '')
            if notes:
                notes_group = QLabel("<b>NOTES</b>")
                notes_group.setStyleSheet("font-size: 11pt; font-weight: bold; background: #f0f0f0; padding: 5px;")
                content_layout.addWidget(notes_group)
                content_layout.addWidget(QLabel(notes))

            scroll.setWidget(content_widget)
            layout.addWidget(scroll)

            # Buttons
            btn_box = QDialogButtonBox()
            btn_box.setStandardButtons(QDialogButtonBox.Ok)
            btn_box.setStyleSheet("padding: 10px;")
            btn_box.accepted.connect(dialog.accept)
            layout.addWidget(btn_box)

            dialog.exec()

        except Exception as e:
            self.show_error_message(f"Error showing invoice details: {str(e)}")
            import traceback
            traceback.print_exc()

    def download_selected_invoice(self):
        """Download selected invoice as PDF"""
        invoice = self.get_selected_invoice()
        if not invoice:
            return

        # Create filename with customer name and invoice number
        customer_name = invoice.get('customer_name', 'Customer')
        invoice_number = invoice['invoice_number']
        # Sanitize filename - replace invalid characters with underscore
        safe_customer_name = "".join(c if c.isalnum() or c in ' -_' else '_' for c in customer_name)
        safe_filename = f"{safe_customer_name}_{invoice_number}.pdf"

        # Ask for save location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Invoice",
            safe_filename,
            "PDF Files (*.pdf);;Text Files (*.txt)"
        )

        if file_path:
            try:
                if file_path.endswith('.txt'):
                    # Save as text
                    self.save_invoice_as_text(invoice, file_path)
                else:
                    # Save as PDF (simplified version)
                    self.save_invoice_as_pdf(invoice, file_path)

                self.show_success_message(f"Invoice saved to: {file_path}")

            except Exception as e:
                self.show_error_message(f"Error saving invoice: {str(e)}")
    
    def save_invoice_as_text(self, invoice, file_path):
        """Save invoice as text file"""
        from database.db_connection import DatabaseContext
        
        with DatabaseContext() as db:
            # Get invoice items
            items_query = """
                SELECT ii.*, s.service_name, p.part_name
                FROM invoice_items ii
                LEFT JOIN services s ON ii.service_id = s.id
                LEFT JOIN parts p ON ii.part_id = p.id
                WHERE ii.invoice_id = %s
            """
            items = db.execute_query(items_query, (invoice['id'],), fetch_all=True)
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write(f"INVOICE - {invoice['invoice_number']}\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Customer: {invoice['customer_name']}\n")
                f.write(f"Mobile: {invoice['mobile']}\n")
                f.write(f"Date: {Formatters.format_date(invoice.get('invoice_date'))}\n\n")
                f.write("-" * 60 + "\n")
                f.write("ITEMS:\n")
                f.write("-" * 60 + "\n")
                
                if items:
                    for item in items:
                        item_name = item.get('item_name', 'N/A')
                        f.write(f"  {item_name}\n")
                        f.write(f"    Qty: {item.get('quantity', 0)} x {self.currency_symbol}{item.get('rate', 0):,.2f} = {self.currency_symbol}{item.get('amount', 0):,.2f}\n")
                
                f.write("\n" + "-" * 60 + "\n")
                f.write(f"Total Amount:  {self.currency_symbol}{invoice['total_amount']:,.2f}\n")
                f.write(f"Advance Paid:  {self.currency_symbol}{invoice['advance_payment']:,.2f}\n")
                f.write(f"BALANCE DUE:   {self.currency_symbol}{invoice['balance_amount']:,.2f}\n")
                f.write(f"Payment Status: {invoice['payment_status']}\n")
                f.write("\n" + "=" * 60 + "\n")
                cname = get_setting('company_name', '')
                wa = get_setting('whatsapp_number', '')
                if not cname or not wa:
                    try:
                        s_row = db.execute_query("SELECT shop_name, phone, owner_phone FROM shop_details ORDER BY id DESC LIMIT 1", fetch_one=True)
                        if s_row:
                            if not cname:
                                cname = s_row.get('shop_name') or 'Ansh Air Cool'
                            if not wa:
                                wa = s_row.get('phone') or s_row.get('owner_phone') or ''
                    except Exception:
                        pass
                if not cname:
                    cname = 'Ansh Air Cool'
                f.write(get_setting('thank_you_note', 'Thank you for your business!') + "\n")
                f.write(f"{cname}\n")
                if wa:
                    f.write(f"\U0001f4de {wa}\n")
    
    def save_invoice_as_pdf(self, invoice, file_path):
        """Save invoice as professional PDF using PDFGenerator"""
        from utils.pdf_generator import PDFGenerator
        from database.db_connection import DatabaseContext
        import os

        with DatabaseContext() as db:
            # Get complete invoice data with ALL required fields
            query = """
                SELECT i.*, c.name as customer_name, c.mobile as customer_mobile,
                       c.email as customer_email, c.address as customer_address, c.landmark,
                       ab.brand_name as ac_brand, i.ac_type, i.star_rating, i.ton_capacity as ac_capacity,
                       i.ac_inverter, i.technician_id, i.payment_mode,
                       i.subtotal, i.gst_percentage as cgst_rate, i.gst_amount,
                       i.total_amount, i.advance_payment, i.balance_amount,
                       i.payment_status, i.notes, i.created_at, i.updated_at
                FROM invoices i
                JOIN customers c ON i.customer_id = c.id
                LEFT JOIN ac_brands ab ON i.ac_brand_id = ab.id
                WHERE i.id = %s
            """
            invoice_data = db.execute_query(query, (invoice['id'],), fetch_one=True)
            
            if not invoice_data:
                raise Exception("Invoice data not found")

            # Get invoice items
            items_query = """
                SELECT ii.*, s.service_name, p.part_name
                FROM invoice_items ii
                LEFT JOIN services s ON ii.service_id = s.id
                LEFT JOIN parts p ON ii.part_id = p.id
                WHERE ii.invoice_id = %s
            """
            items = db.execute_query(items_query, (invoice['id'],), fetch_all=True)

            # Get shop data
            shop_query = """
                SELECT shop_name, address, phone, email, tagline, services, '' as footer_message
                FROM shop_details LIMIT 1
            """
            shop_data = db.execute_query(shop_query, fetch_one=True)
            
            if not shop_data:
                shop_data = {
                    'shop_name': 'Your Shop Name',
                    'address': 'Shop Address Not Provided',
                    'phone': 'N/A',
                    'email': 'N/A',
                    'tagline': 'Your Tagline Here',
                    'services': 'Your Services Here',
                    'footer_message': get_setting('thank_you_note', 'Thank you for your business!')
                }
            
            # Map 'phone' to 'mobile' for PDF generator compatibility
            if shop_data:
                shop_data['mobile'] = shop_data.get('phone') or 'N/A'

            # Get technician name and mobile
            technician_name = 'N/A'
            technician_mobile = 'N/A'
            if invoice_data.get('technician_id'):
                tech_query = "SELECT name, mobile FROM technicians WHERE id = %s"
                tech_result = db.execute_query(tech_query, (invoice_data['technician_id'],), fetch_one=True)
                if tech_result:
                    technician_name = tech_result['name'] or 'N/A'
                    technician_mobile = tech_result['mobile'] or 'N/A'

            # Prepare invoice data for PDF generator - FIXED MAPPING
            pdf_invoice_data = {
                # Invoice Basics
                'invoice_no': invoice_data['invoice_number'],
                'invoice_date': Formatters.format_date(invoice_data.get('created_at')) or datetime.now().strftime('%d-%m-%Y'),
                'due_date': Formatters.format_date(invoice_data.get('updated_at')) or 'N/A',
                'invoice_type': 'Regular',  # Default, can be extended for AMC/Installation

                # Payment Details - CRITICAL: Map correctly from database
                'payment_mode': invoice_data.get('payment_mode', 'N/A'),
                'payment_status': invoice_data.get('payment_status', 'Pending'),

                # Customer Details
                'customer_name': invoice_data.get('customer_name', 'N/A'),
                'customer_address': invoice_data.get('customer_address') or 'N/A',
                'customer_mobile': invoice_data.get('customer_mobile', 'N/A'),
                'customer_email': invoice_data.get('customer_email') or 'N/A',
                'landmark': invoice_data.get('landmark') or '',

                # AC Details - Map from database fields
                'ac_brand': invoice_data.get('ac_brand') or 'N/A',
                'ac_type': invoice_data.get('ac_type') or 'N/A',
                'ac_ton': invoice_data.get('ac_capacity') or 'N/A',
                'ac_star': invoice_data.get('star_rating') or 'N/A',
                'ac_inverter': invoice_data.get('ac_inverter') or 'N/A',
                'ac_gas': 'N/A',  # Not stored in database currently
                'ac_serial': 'N/A',  # Not stored in database currently

                # Service Details
                'technician_name': technician_name,
                'technician_mobile': technician_mobile,
                'service_date': Formatters.format_date(invoice_data.get('created_at')) or 'N/A',
                'service_type': get_setting('service_types', 'AC Service,Installation,Repair,Gas Refilling,AMC Visit,AC Rent Delivery,AC Rent Pickup,Other').split(',')[0],

                # Items with GST (HSN removed as requested)
                'items': [
                    {
                        'service_name': item.get('service_name'),
                        'part_name': item.get('part_name'),
                        'description': item.get('service_name') or item.get('part_name') or 'N/A',
                        'quantity': item.get('quantity', 1),
                        'rate': float(item.get('rate', 0)),
                        'gst_percent': float(invoice_data.get('gst_percentage', 18)),
                        'amount': float(item.get('amount', 0))
                    }
                    for item in items
                ] if items else [],

                # Payment Summary - CRITICAL: Map correctly
                'subtotal': float(invoice_data.get('subtotal', 0)),
                'discount': float(invoice_data.get('discount_amount', 0)),
                'cgst_rate': float(invoice_data.get('gst_percentage', 9)) / 2,
                'cgst_amount': float(invoice_data.get('gst_amount', 0)) / 2,
                'sgst_rate': float(invoice_data.get('gst_percentage', 9)) / 2,
                'sgst_amount': float(invoice_data.get('gst_amount', 0)) / 2,
                'igst_amount': 0,  # Not applicable currently
                'total': float(invoice_data.get('total_amount', 0)),
                'amount_paid': float(invoice_data.get('advance_payment', 0)),  # Map advance_payment -> amount_paid
                'balance_due': float(invoice_data.get('balance_amount', 0)),

                # Notes
                'notes': invoice_data.get('notes') or get_setting('thank_you_note', 'Thank you for your business!')
            }

            # Generate professional PDF
            pdf_generator = PDFGenerator()
            
            # Ensure exports directory exists
            os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
            
            pdf_generator.generate_invoice(pdf_invoice_data, shop_data, file_path)

    def _email_selected_invoice(self):
        """Email the selected invoice as PDF"""
        invoice = self.get_selected_invoice()
        if not invoice:
            return
        from views.email_invoice_dialog import EmailInvoiceDialog
        dialog = EmailInvoiceDialog(invoice['id'], self)
        dialog.exec()

    def share_invoice_whatsapp(self):
        """🆕 Streamlined WhatsApp sharing - generates PDF and opens WhatsApp with clear instructions"""
        invoice = self.get_selected_invoice()
        if not invoice:
            return

        try:
            from database.db_connection import DatabaseContext
            from utils.whatsapp_helper import WhatsAppHelper
            from utils.pdf_invoice_generator import PDFInvoiceGenerator
            from PySide6.QtWidgets import QMessageBox
            import os

            # Show progress
            progress = QProgressDialog("Generating PDF and preparing WhatsApp...", None, 0, 0, self)
            progress.setWindowTitle("WhatsApp Share")
            progress.show()

            with DatabaseContext() as db:
                # 1. Get complete invoice data
                query = """
                    SELECT i.*, c.name as customer_name, c.mobile as customer_mobile,
                           c.address as customer_address, ab.brand_name as ac_brand,
                           i.total_amount, i.advance_payment, i.balance_amount,
                           i.payment_mode, i.payment_status, DATE(i.created_at) as invoice_date
                    FROM invoices i
                    JOIN customers c ON i.customer_id = c.id
                    LEFT JOIN ac_brands ab ON i.ac_brand_id = ab.id
                    WHERE i.id = %s
                """
                invoice_data = db.execute_query(query, (invoice['id'],), fetch_one=True)

                if not invoice_data:
                    progress.close()
                    self.show_error_message("Invoice data not found")
                    return

                # 2. Get invoice items
                items_query = """
                    SELECT ii.*, s.service_name, p.part_name, p.unit
                    FROM invoice_items ii
                    LEFT JOIN services s ON ii.service_id = s.id
                    LEFT JOIN parts p ON ii.part_id = p.id
                    WHERE ii.invoice_id = %s
                """
                items = db.execute_query(items_query, (invoice['id'],), fetch_all=True)

                # 3. Format data for PDF generator
                pdf_data = {
                    'invoice_number': invoice_data['invoice_number'],
                    'invoice_date': Formatters.format_date(invoice_data.get('invoice_date')) or 'N/A',
                    'customer_name': invoice_data['customer_name'],
                    'customer_mobile': invoice_data['customer_mobile'],
                    'customer_address': invoice_data['customer_address'] or 'N/A',
                    'ac_brand': invoice_data.get('ac_brand', 'N/A'),
                    'ac_type': invoice_data.get('ac_type', 'N/A'),
                    'ton_capacity': invoice_data.get('ton_capacity', 'N/A'),
                    'items': [{
                        'description': item.get('service_name') or item.get('part_name') or 'Service',
                        'quantity': item.get('quantity', 1),
                        'rate': float(item.get('rate') or 0),
                        'amount': float(item.get('amount') or 0),
                        'unit': item.get('unit', 'pcs')
                    } for item in items],
                    'subtotal': float(invoice_data.get('subtotal') or invoice_data.get('total_amount') or 0),
                    'gst_amount': float(invoice_data.get('gst_amount') or 0),
                    'gst_percentage': float(invoice_data.get('gst_percentage') or 0),
                    'total_amount': float(invoice_data.get('total_amount') or 0),
                    'paid_amount': float(invoice_data.get('advance_payment') or 0),
                    'balance_amount': float(invoice_data.get('balance_amount') or 0),
                    'payment_mode': invoice_data.get('payment_mode', ''),
                    'payment_status': invoice_data.get('payment_status', '')
                }

                # 4. Generate PDF
                generator = PDFInvoiceGenerator()
                pdf_path = generator.generate_invoice(pdf_data)
                progress.close()

                # Open direct WhatsApp share (PDF copied to clipboard + customer chat opened)
                self._send_whatsapp_with_pdf(invoice_data, pdf_path)

        except Exception as e:
            if 'progress' in locals(): progress.close()
            self.show_error_message(f"Error preparing WhatsApp: {str(e)}")
            import traceback; traceback.print_exc()

    def _send_whatsapp_with_pdf(self, invoice_data, pdf_path):
        """Direct WhatsApp sharing: PDF on clipboard + chat opens directly + auto-paste"""
        try:
            from utils.whatsapp_messages import format_message
            from views.whatsapp_share_dialog import WhatsAppShareDialog

            # 1. Format the message (caption)
            message = format_message(
                'invoice_share',
                customer_name=invoice_data['customer_name'],
                invoice_number=invoice_data['invoice_number'],
                total_amount=f"{invoice_data['total_amount']:,.2f}",
                paid_amount=f"{invoice_data['advance_payment']:,.2f}",
                balance_amount=f"{invoice_data['balance_amount']:,.2f}",
                invoice_date=Formatters.format_date(invoice_data.get('invoice_date')) or 'N/A'
            )

            # 2. Show direct-share dialog (copies PDF to clipboard + opens chat + auto Ctrl+V)
            dialog = WhatsAppShareDialog(
                self,
                customer_name=invoice_data['customer_name'],
                mobile=invoice_data.get('customer_mobile', ''),
                message=message or "",
                pdf_path=pdf_path,
                invoice_number=invoice_data['invoice_number'],
            )
            dialog.exec()

        except Exception as e:
            self.show_error_message(f"WhatsApp Error: {str(e)}")
            import traceback; traceback.print_exc()

    def export_invoices_to_excel(self):
        checked_rows = self._get_selected_invoice_ids()
        invoices_to_export = []
        if checked_rows:
            invoices_to_export = checked_rows
        else:
            for invoice in self.invoice_list:
                invoices_to_export.append(invoice['id'])

        if not invoices_to_export:
            self.show_warning_message("Koi invoice nahi hai export karne ke liye.")
            return

        from database.db_connection import DatabaseContext

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Invoices Report",
            f"Invoices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel Files (*.xlsx)"
        )
        if not filepath:
            return

        with DatabaseContext() as db:
            placeholders = ','.join(['%s'] * len(invoices_to_export))
            query = f"""
                SELECT i.invoice_number, c.name as customer_name, c.mobile,
                       i.total_amount, i.advance_payment, i.balance_amount,
                       i.payment_status, i.payment_mode, DATE(i.created_at) as invoice_date
                FROM invoices i
                JOIN customers c ON i.customer_id = c.id
                WHERE i.id IN ({placeholders}) AND i.is_active = TRUE
                ORDER BY i.created_at DESC
            """
            data = db.execute_query(query, tuple(invoices_to_export), fetch_all=True) or []

        if not data:
            self.show_warning_message("Data nahi mila.")
            return

        from utils.excel_helper import ExcelExporter
        headers = ["Invoice No", "Customer", "Mobile", "Amount", "Advance", "Balance", "Status", "Payment Mode", "Date"]
        number_cols = {4, 5, 6}
        rows = []
        total_amount = total_advance = total_balance = 0
        for inv in data:
            amt = float(inv.get('total_amount', 0) or 0)
            adv = float(inv.get('advance_payment', 0) or 0)
            bal = float(inv.get('balance_amount', 0) or 0)
            rows.append([
                inv['invoice_number'], inv.get('customer_name', ''),
                inv.get('mobile', ''), amt, adv, bal,
                inv['payment_status'], inv.get('payment_mode', ''),
                Formatters.format_date(inv.get('invoice_date'))
            ])
            total_amount += amt; total_advance += adv; total_balance += bal

        paid_count = sum(1 for inv in data if inv['payment_status'] == 'Paid')
        pending_count = sum(1 for inv in data if inv['payment_status'] == 'Pending')
        partial_count = len(data) - paid_count - pending_count
        charts_data = [{
            'type': 'pie', 'title': 'Invoice Status Distribution',
            'categories': ['Paid', 'Pending', 'Partial'],
            'values': [('Count', [paid_count, pending_count, partial_count])]
        }, {
            'type': 'bar', 'title': 'Invoice Amounts Summary',
            'categories': ['Total', 'Collected', 'Pending'],
            'values': [('Amount', [total_amount, total_advance, total_balance])],
            'y_axis': f'Amount ({self.currency_symbol})'
        }]
        wb = ExcelExporter.build_excel(
            sheet_title='Invoices',
            title_text='Invoice Report',
            subtitle_text=f'Total: {len(data)} invoices | Generated: {datetime.now().strftime("%d-%m-%Y %H:%M")}',
            headers=headers, rows=rows,
            total_row=['TOTAL', '', '', total_amount, total_advance, total_balance, '', '', ''],
            number_cols=number_cols,
            cond_rules=[(7, 'paid'), (7, 'pending'), (7, 'partial')],
            kpis=[
                ('Total Invoices', len(data)),
                ('Total Amount', total_amount),
                ('Total Collected', total_advance),
                ('Total Pending', total_balance),
                ('Paid Invoices', paid_count),
                ('Collection Rate', f'{total_amount and total_advance / total_amount * 100:.1f}%'),
            ],
            charts_data=charts_data,
            freeze_col=True
        )
        try:
            wb.save(filepath)
            self.show_success_message(f"✅ {len(data)} invoice(s) export ho gaye!\n{filepath}")
        except Exception as e:
            self.show_error_message(f"Export failed: {str(e)}")

    def print_invoices(self):
        checked_rows = self._get_selected_invoice_ids()
        invoices_to_print = []
        if checked_rows:
            for inv in self.invoice_list:
                if inv['id'] in checked_rows:
                    invoices_to_print.append(inv)
        else:
            selected = self.get_selected_invoice()
            if selected:
                invoices_to_print = [selected]

        if not invoices_to_print:
            self.show_warning_message("Select invoice(s) to print first")
            return

        import tempfile, os
        from database.db_connection import DatabaseContext

        tmp_dir = tempfile.mkdtemp()
        pdf_paths = []

        try:
            from utils.pdf_invoice_generator import PDFInvoiceGenerator
            with DatabaseContext() as db:
                for inv in invoices_to_print:
                    inv_data = db.execute_query(
                        """SELECT i.*, c.name as customer_name, c.mobile as customer_mobile,
                                  c.email as customer_email, c.address as customer_address,
                                  c.pincode, ab.brand_name, t.name as technician_name,
                                  t.mobile as technician_mobile
                           FROM invoices i
                           JOIN customers c ON i.customer_id = c.id
                           LEFT JOIN ac_brands ab ON i.ac_brand_id = ab.id
                           LEFT JOIN technicians t ON i.technician_id = t.id
                           WHERE i.id = %s""",
                        (inv['id'],), fetch_one=True)
                    if not inv_data:
                        continue
                    items = db.execute_query(
                        """SELECT ii.*, s.service_name, p.part_name, p.unit
                           FROM invoice_items ii
                           LEFT JOIN services s ON ii.service_id = s.id
                           LEFT JOIN parts p ON ii.part_id = p.id
                           WHERE ii.invoice_id = %s""",
                        (inv['id'],), fetch_all=True) or []
                    mapped_items = []
                    for it in (items or []):
                        desc = it.get('service_name') or it.get('part_name') or it.get('description', 'Item')
                        mapped_items.append({
                            'description': desc,
                            'quantity': it.get('quantity', 1),
                            'rate': float(it.get('rate', 0)),
                            'amount': float(it.get('amount', 0)),
                            'unit': it.get('unit', 'pcs')
                        })
                    inv_data['items'] = mapped_items
                    pdf_path = os.path.join(tmp_dir, f"{inv['invoice_number']}.pdf")
                    gen = PDFInvoiceGenerator()
                    gen.generate_invoice(inv_data, pdf_path)
                    pdf_paths.append(pdf_path)
        except Exception as e:
            self.show_error_message(f"Error generating PDF: {str(e)}")
            import traceback; traceback.print_exc()
            return

        if not pdf_paths:
            self.show_warning_message("No PDF files generated")
            return

        import platform, subprocess
        if len(pdf_paths) == 1:
            if platform.system() == 'Windows':
                subprocess.Popen(['start', '', pdf_paths[0]], shell=True)
            elif platform.system() == 'Darwin':
                subprocess.run(['open', pdf_paths[0]])
            else:
                subprocess.run(['xdg-open', pdf_paths[0]])
        else:
            merged = os.path.join(tmp_dir, "print_all.pdf")
            try:
                from PyPDF2 import PdfMerger
                merger = PdfMerger()
                for p in pdf_paths:
                    merger.append(p)
                merger.write(merged)
                merger.close()
                if platform.system() == 'Windows':
                    subprocess.Popen(['start', '', merged], shell=True)
                elif platform.system() == 'Darwin':
                    subprocess.run(['open', merged])
                else:
                    subprocess.run(['xdg-open', merged])
            except ImportError:
                if platform.system() == 'Windows':
                    subprocess.Popen(['start', '', pdf_paths[0]], shell=True)
                else:
                    subprocess.run(['xdg-open', pdf_paths[0]])
        self.show_success_message(f"✅ {len(pdf_paths)} invoice(s) ready for print preview")

    def _toggle_select_all(self):
        if self._all_selected:
            self.deselect_all_invoices()
        else:
            self.select_all_invoices()
        self._all_selected = not self._all_selected
        self.select_toggle_btn.setText("☑  Deselect All" if self._all_selected else "☐  Select All")

    def select_all_invoices(self):
        self.invoice_table.selectAll()

    def deselect_all_invoices(self):
        self.invoice_table.clearSelection()

    def convert_selected_to_pdf(self):
        """Convert selected invoices to PDF and save to selected folder"""
        checked_rows = self._get_selected_invoice_ids()

        if not checked_rows:
            self.show_warning_message("Koi invoice select nahi kiya gaya.\nInvoice row par click karke phir se koshish karein.")
            return

        from utils.pdf_generator import PDFGenerator
        from database.db_connection import DatabaseContext

        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Save PDFs")
        if not folder:
            return

        progress = QProgressDialog("Converting invoices to PDF...", "Cancel", 0, len(checked_rows), self)
        progress.setWindowTitle("Bulk PDF Conversion")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()

        success_count = 0
        fail_count = 0
        error_details = []

        for i, invoice_id in enumerate(checked_rows):
            if progress.wasCanceled():
                break

            progress.setLabelText(f"Converting invoice {i + 1} of {len(checked_rows)}...")
            progress.setValue(i)

            try:
                with DatabaseContext() as db:
                    query = """
                        SELECT i.*, c.name as customer_name, c.mobile as customer_mobile,
                               c.email as customer_email, c.address as customer_address, c.landmark,
                               ab.brand_name as ac_brand, i.ac_type, i.star_rating, i.ton_capacity as ac_capacity,
                               i.ac_inverter, i.technician_id, i.payment_mode,
                               i.subtotal, i.gst_percentage as cgst_rate, i.gst_amount,
                               i.total_amount, i.advance_payment, i.balance_amount,
                               i.payment_status, i.notes, i.created_at, i.updated_at
                        FROM invoices i
                        JOIN customers c ON i.customer_id = c.id
                        LEFT JOIN ac_brands ab ON i.ac_brand_id = ab.id
                        WHERE i.id = %s
                    """
                    invoice_data = db.execute_query(query, (invoice_id,), fetch_one=True)
                    if not invoice_data:
                        fail_count += 1
                        continue

                    items_query = """
                        SELECT ii.*,
                               COALESCE(s.service_name, p.part_name, ii.description, 'N/A') as item_name,
                               COALESCE(p.unit, 'pcs') as unit
                        FROM invoice_items ii
                        LEFT JOIN services s ON ii.service_id = s.id
                        LEFT JOIN parts p ON ii.part_id = p.id
                        WHERE ii.invoice_id = %s
                    """
                    items = db.execute_query(items_query, (invoice_id,), fetch_all=True)

                    shop_query = """
                        SELECT shop_name, address, phone, email, tagline, services, '' as footer_message
                        FROM shop_details LIMIT 1
                    """
                    shop_data = db.execute_query(shop_query, fetch_one=True)
                    if not shop_data:
                        shop_data = {
                            'shop_name': 'Your Shop Name',
                            'address': 'Shop Address Not Provided',
                            'phone': 'N/A',
                            'email': 'N/A',
                            'tagline': 'Your Tagline Here',
                            'services': 'Your Services Here',
                            'footer_message': get_setting('thank_you_note', 'Thank you for your business!')
                        }
                    if shop_data:
                        shop_data = dict(shop_data)
                        shop_data['mobile'] = shop_data.get('phone') or 'N/A'

                    technician_name = 'N/A'
                    technician_mobile = 'N/A'
                    if invoice_data.get('technician_id'):
                        tech_query = "SELECT name, mobile FROM technicians WHERE id = %s"
                        tech_result = db.execute_query(tech_query, (invoice_data['technician_id'],), fetch_one=True)
                        if tech_result:
                            technician_name = tech_result['name'] or 'N/A'
                            technician_mobile = tech_result['mobile'] or 'N/A'

                    safe_name = "".join(c if c.isalnum() or c in ' -_' else '_' for c in invoice_data.get('customer_name', 'Customer') or 'Customer')
                    file_path = os.path.join(folder, f"{safe_name}_{invoice_data['invoice_number']}.pdf")

                    def _f(val, default=0):
                        if val is None: return float(default)
                        try: return float(val)
                        except: return float(default)

                    def _parse_date(val, fmt='%d-%m-%Y'):
                        if not val:
                            return datetime.now().strftime(fmt)
                        if isinstance(val, datetime):
                            return val.strftime(fmt)
                        try:
                            return datetime.strptime(str(val), '%Y-%m-%d %H:%M:%S').strftime(fmt)
                        except ValueError:
                            pass
                        try:
                            return datetime.strptime(str(val), '%Y-%m-%d').strftime(fmt)
                        except ValueError:
                            pass
                        return str(val)

                    pdf_invoice_data = {
                        'invoice_no': invoice_data['invoice_number'],
                        'invoice_date': _parse_date(invoice_data.get('created_at')),
                        'due_date': _parse_date(invoice_data.get('updated_at'), '%d-%m-%Y') or 'N/A',
                        'invoice_type': 'Regular',
                        'payment_mode': invoice_data.get('payment_mode', 'N/A'),
                        'payment_status': invoice_data.get('payment_status', 'Pending'),
                        'customer_name': invoice_data.get('customer_name', 'N/A'),
                        'customer_address': invoice_data.get('customer_address') or 'N/A',
                        'customer_mobile': invoice_data.get('customer_mobile', 'N/A'),
                        'customer_email': invoice_data.get('customer_email') or 'N/A',
                        'landmark': invoice_data.get('landmark') or '',
                        'ac_brand': invoice_data.get('ac_brand') or 'N/A',
                        'ac_type': invoice_data.get('ac_type') or 'N/A',
                        'ac_ton': invoice_data.get('ac_capacity') or 'N/A',
                        'ac_star': invoice_data.get('star_rating') or 'N/A',
                        'ac_inverter': invoice_data.get('ac_inverter') or 'N/A',
                        'ac_gas': 'N/A',
                        'ac_serial': 'N/A',
                        'technician_name': technician_name,
                        'technician_mobile': technician_mobile,
                        'service_date': _parse_date(invoice_data.get('created_at')),
                        'service_type': get_setting('service_types', 'AC Service,Installation,Repair,Gas Refilling,AMC Visit,AC Rent Delivery,AC Rent Pickup,Other').split(',')[0],
                        'items': [
                            {
                                'description': item.get('item_name', 'N/A'),
                                'quantity': int(_f(item.get('quantity'), 1)),
                                'rate': _f(item.get('rate', 0)),
                                'amount': _f(item.get('amount', 0)),
                                'unit': item.get('unit') or 'pcs'
                            }
                            for item in (items or [])
                        ],
                        'subtotal': _f(invoice_data.get('subtotal'), 0),
                        'discount': _f(invoice_data.get('discount_amount'), 0),
                        'cgst_rate': _f(invoice_data.get('gst_percentage'), 9) / 2,
                        'cgst_amount': _f(invoice_data.get('gst_amount'), 0) / 2,
                        'sgst_rate': _f(invoice_data.get('gst_percentage'), 9) / 2,
                        'sgst_amount': _f(invoice_data.get('gst_amount'), 0) / 2,
                        'igst_amount': 0,
                        'total': _f(invoice_data.get('total_amount'), 0),
                        'amount_paid': _f(invoice_data.get('advance_payment'), 0),
                        'balance_due': _f(invoice_data.get('balance_amount'), 0),
                        'notes': invoice_data.get('notes') or get_setting('thank_you_note', 'Thank you for your business!')
                    }

                    pdf_generator = PDFGenerator()
                    os.makedirs(folder, exist_ok=True)
                    pdf_generator.generate_invoice(pdf_invoice_data, shop_data, file_path)
                    success_count += 1

            except Exception as e:
                fail_count += 1
                import traceback
                traceback.print_exc()
                error_details.append(f"#{invoice_id}: {str(e)[:150]}")

        progress.setValue(len(checked_rows))

        msg = f"✅ {success_count} invoice(s) successfully converted to PDF!"
        if fail_count:
            msg += f"\n❌ {fail_count} invoice(s) failed."
            if error_details:
                msg += "\n\nErrors:\n" + "\n".join(error_details[:3])
                if len(error_details) > 3:
                    msg += f"\n...and {len(error_details) - 3} more"
        msg += f"\n\nLocation: {folder}"
        self.show_error_message(msg) if fail_count and not success_count else self.show_success_message(msg)

    def delete_selected_invoice(self):
        """Delete selected invoice(s)"""
        selected_ids = self._get_selected_invoice_ids()
        if not selected_ids:
            self.show_warning_message("Please select an invoice to delete")
            return

        if len(selected_ids) == 1:
            inv = self.get_selected_invoice()
            inv_num = inv['invoice_number'] if inv else f"ID {selected_ids[0]}"
            msg = f"Are you sure you want to delete invoice {inv_num}?"
        else:
            msg = f"Are you sure you want to delete {len(selected_ids)} selected invoices?"

        reply = QMessageBox.question(
            self,
            'Delete Invoice',
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                from database.db_connection import DatabaseContext

                with DatabaseContext() as db:
                    for inv_id in selected_ids:
                        query = "UPDATE invoices SET is_active = FALSE WHERE id = %s"
                        db.execute_query(query, (inv_id,))

                    self.show_success_message(f"Invoice{'s' if len(selected_ids) > 1 else ''} deleted successfully")
                    self.load_invoices()

            except Exception as e:
                self.show_error_message(f"Error deleting invoice: {str(e)}")

    def refresh_data(self):
        """Refresh invoice list"""
        self.load_invoices()

    def reload_ui_settings(self):
        """Reload UI settings from DB in real-time"""
        self.currency_symbol = get_setting("currency_symbol", "\u20b9")
        self.load_invoices()


class ReceivePaymentDialog(QDialog):
    """Dialog for receiving payment against an invoice with Enterprise styling"""

    def __init__(self, parent, invoice):
        super().__init__(parent)
        self.invoice = invoice
        self.currency_symbol = get_setting("currency_symbol", "₹")
        self.setWindowTitle(f"Receive Payment - {invoice['invoice_number']}")
        self.setMinimumWidth(440)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{ background: #ffffff; font-family: {FONT_FAMILY}; }}
            QLabel {{ color: {ENTERPRISE_COLORS['text']}; font-size: 9.5pt; }}
            QDoubleSpinBox, QComboBox, QTextEdit {{
                background: #ffffff;
                color: {ENTERPRISE_COLORS['text']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 9.5pt;
            }}
            QDoubleSpinBox:focus, QComboBox:focus, QTextEdit:focus {{
                border: 1.5px solid {ENTERPRISE_COLORS['primary']};
            }}
            QPushButton {{
                padding: 9px 20px;
                font-size: 9.5pt;
                font-weight: 700;
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Receive Payment")
        title.setStyleSheet(f"font-size: 14pt; font-weight: 800; color: {ENTERPRISE_COLORS['text']};")
        layout.addWidget(title)

        customer_name = self.invoice.get('customer_name', self.invoice.get('name', 'Unknown'))
        balance_due = float(self.invoice.get('balance_amount', 0) or 0)

        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {ENTERPRISE_COLORS['bg']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(4)
        info_layout.setContentsMargins(10, 8, 10, 8)

        inv_lbl = QLabel(f"<b>Invoice:</b> {self.invoice['invoice_number']} &nbsp;|&nbsp; <b>Customer:</b> {customer_name}")
        inv_lbl.setStyleSheet(f"color: {ENTERPRISE_COLORS['text']}; font-size: 9.5pt;")
        bal_lbl = QLabel(f"<b>Pending Balance:</b> <span style='color: {ENTERPRISE_COLORS['danger']}; font-size: 11pt;'>{self.currency_symbol}{balance_due:,.2f}</span>")
        bal_lbl.setStyleSheet("font-size: 9.5pt;")
        info_layout.addWidget(inv_lbl)
        info_layout.addWidget(bal_lbl)
        layout.addWidget(info_frame)

        form = QFormLayout()
        form.setSpacing(12)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(1, max(1.0, balance_due))
        self.amount_spin.setValue(balance_due)
        self.amount_spin.setPrefix(self.currency_symbol + " ")
        self.amount_spin.setDecimals(2)
        form.addRow("Amount Received:", self.amount_spin)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Cash", "UPI", "Card", "Bank Transfer", "Cheque"])
        form.addRow("Payment Mode:", self.mode_combo)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Optional payment reference or notes...")
        self.notes_input.setMaximumHeight(65)
        form.addRow("Notes:", self.notes_input)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: #ffffff;
                color: {ENTERPRISE_COLORS['text_secondary']};
                border: 1px solid {ENTERPRISE_COLORS['border']};
            }}
            QPushButton:hover {{
                background: {ENTERPRISE_COLORS['card_hover']};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        self.confirm_btn = QPushButton(f"Receive {self.currency_symbol}{self.amount_spin.value():,.2f}")
        self.confirm_btn.setCursor(Qt.PointingHandCursor)
        self.confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ENTERPRISE_COLORS['success']};
                color: #ffffff;
                border: none;
            }}
            QPushButton:hover {{
                background: {ENTERPRISE_COLORS['success_hover']};
            }}
        """)
        self.confirm_btn.clicked.connect(self.accept)
        self.amount_spin.valueChanged.connect(
            lambda v: self.confirm_btn.setText(f"Receive {self.currency_symbol}{v:,.2f}")
        )
        btn_row.addWidget(self.confirm_btn)
        layout.addLayout(btn_row)
