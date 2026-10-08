"""
Daily Log View - Enterprise Daily Work, Advance & Cost Log Management
Full-page integrated navigation with Back buttons, Customer multi-visit tracking by mobile/name,
Technician 360° Dossier, and Month-End Settlement without visible raw DB IDs.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDialog, QFormLayout, QComboBox, QTextEdit,
    QDoubleSpinBox, QFileDialog, QMenu, QScrollArea, QProgressBar,
    QAbstractItemView, QApplication, QSizePolicy, QDateEdit, QCompleter,
    QStackedWidget, QGroupBox
)
from PySide6.QtCore import Qt, QDate, Signal, QTimer, QSize
from PySide6.QtGui import QColor, QFont, QCursor, QIcon
from utils.unified_theme import UnifiedTheme
from utils.app_settings import get_setting
from utils.formatters import Formatters
from views.base_window import BaseView, MetricCard
from controllers.daily_log_controller import DailyLogController
from database.db_connection import DatabaseConnection, DatabaseContext
from datetime import datetime, timedelta
import os
import webbrowser
import urllib.parse


class DailyLogView(BaseView):
    """Full-page Daily Logs with seamless switching to Month Settlement, Tech Dossier & Customer Ledger"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_manager = UnifiedTheme()
        self.currency_symbol = get_setting('currency_symbol', '₹')
        self.metric_cards = {}
        self.logs_data = []

        from utils.privacy_manager import get_privacy_manager
        self.privacy_mgr = get_privacy_manager()

        self._init_ui()
        
        # Connect to Global Event Bus for real-time Privacy Mode toggles
        try:
            from utils.event_bus import EventBus
            EventBus().privacy_mode_toggled.connect(self._on_privacy_mode_toggled)
        except Exception:
            pass

        QTimer.singleShot(50, self.load_data)

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Main Stacked Widget for Full Page views
        self.stack = QStackedWidget(self)
        root_layout.addWidget(self.stack)

        colors = self.theme_manager.get_colors()

        # Page 0: Main Daily Register
        self.page_register = QWidget()
        self.page_register.setAutoFillBackground(True)
        self.page_register.setStyleSheet(f"background-color: {colors['bg']};")
        self._build_register_page(self.page_register)
        self.stack.addWidget(self.page_register)

        # Page 1: Full-Page Month-End Settlement
        self.page_settlement = QWidget()
        self.page_settlement.setAutoFillBackground(True)
        self.page_settlement.setStyleSheet(f"background-color: {colors['bg']};")
        self._build_settlement_page(self.page_settlement)
        self.stack.addWidget(self.page_settlement)

        # Page 2: Full-Page Technician 360° Dossier & Sites
        self.page_tech_dossier = QWidget()
        self.page_tech_dossier.setAutoFillBackground(True)
        self.page_tech_dossier.setStyleSheet(f"background-color: {colors['bg']};")
        self._build_tech_dossier_page(self.page_tech_dossier)
        self.stack.addWidget(self.page_tech_dossier)

        # Page 3: Full-Page Customer History & Multi-Visit Ledger
        self.page_cust_history = QWidget()
        self.page_cust_history.setAutoFillBackground(True)
        self.page_cust_history.setStyleSheet(f"background-color: {colors['bg']};")
        self._build_cust_history_page(self.page_cust_history)
        self.stack.addWidget(self.page_cust_history)

        self.stack.setCurrentIndex(0)

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE 0: MAIN DAILY REGISTER
    # ═════════════════════════════════════════════════════════════════════════
    def _build_register_page(self, container: QWidget):
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)

        colors = self.theme_manager.get_colors()

        # ── 1. Top Header Bar ──
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = QLabel("📋 Daily Work & Cost Logs")
        title_lbl.setStyleSheet(f"font-size: 18pt; font-weight: 800; color: {colors['fg']}; letter-spacing: -0.5px;")
        subtitle_lbl = QLabel("Daily multi-site visits, advance payments, petrol & material expenses, and settlements")
        subtitle_lbl.setStyleSheet(f"font-size: 9pt; color: {colors['muted']}; font-weight: 500;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(subtitle_lbl)
        header_row.addLayout(title_box)

        header_row.addStretch()

        # Tech Dossier Button (Full Page)
        self.btn_tech_dossier = QPushButton("👨‍🔧 Tech Dossier & Sites")
        self.btn_tech_dossier.setCursor(Qt.PointingHandCursor)
        self.btn_tech_dossier.setFixedHeight(38)
        self.btn_tech_dossier.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['hover']};
                color: #0284c7;
                border: 1px solid {colors['border']};
                border-radius: 8px;
                padding: 0 14px;
                font-size: 9pt;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #0284c715;
                border-color: #0284c7;
            }}
        """)
        self.btn_tech_dossier.clicked.connect(self._go_to_tech_dossier)
        header_row.addWidget(self.btn_tech_dossier)

        # Customer History Button (Full Page)
        self.btn_cust_dossier = QPushButton("👤 Customer History")
        self.btn_cust_dossier.setCursor(Qt.PointingHandCursor)
        self.btn_cust_dossier.setFixedHeight(38)
        self.btn_cust_dossier.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['hover']};
                color: #7c3aed;
                border: 1px solid {colors['border']};
                border-radius: 8px;
                padding: 0 14px;
                font-size: 9pt;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: #7c3aed15;
                border-color: #7c3aed;
            }}
        """)
        self.btn_cust_dossier.clicked.connect(self._go_to_customer_history)
        header_row.addWidget(self.btn_cust_dossier)

        # Month-End Settlement Button (Full Page)
        self.btn_reconcile = QPushButton("📊 Month-End Settlement")
        self.btn_reconcile.setCursor(Qt.PointingHandCursor)
        self.btn_reconcile.setFixedHeight(38)
        self.btn_reconcile.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['hover']};
                color: {colors['primary']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                padding: 0 14px;
                font-size: 9pt;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {colors['primary']}15;
                border-color: {colors['primary']};
            }}
        """)
        self.btn_reconcile.clicked.connect(self._go_to_month_settlement)
        header_row.addWidget(self.btn_reconcile)

        # Privacy Shield Button (Eye Toggle)
        self.btn_privacy = QPushButton()
        self.btn_privacy.setCursor(Qt.PointingHandCursor)
        self.btn_privacy.setFixedHeight(38)
        self.btn_privacy.clicked.connect(self._toggle_privacy_mode)
        self._update_privacy_button_ui()
        header_row.addWidget(self.btn_privacy)

        # Excel Export Button
        self.btn_export = QPushButton("📥 Export Excel")
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setFixedHeight(38)
        self.btn_export.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['hover']};
                color: {colors['fg']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                padding: 0 14px;
                font-size: 9pt;
                font-weight: 600;
            }}
            QPushButton:hover {{
                border-color: {colors['primary']};
                color: {colors['primary']};
            }}
        """)
        self.btn_export.clicked.connect(self._export_to_excel)
        header_row.addWidget(self.btn_export)

        # Add New Entry Button
        self.btn_add_log = QPushButton("+ New Daily Log")
        self.btn_add_log.setCursor(Qt.PointingHandCursor)
        self.btn_add_log.setFixedHeight(38)
        self.btn_add_log.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {colors['primary']}, stop:1 #1d4ed8);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 18px;
                font-size: 9.5pt;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #2563eb);
            }}
        """)
        self.btn_add_log.clicked.connect(self._open_add_dialog)
        header_row.addWidget(self.btn_add_log)

        layout.addLayout(header_row)

        # ── 2. KPI Metric Cards ──
        kpi_frame = QFrame()
        kpi_frame.setStyleSheet("background: transparent;")
        kpi_layout = QHBoxLayout(kpi_frame)
        kpi_layout.setContentsMargins(0, 0, 0, 0)
        kpi_layout.setSpacing(12)

        kpis = [
            ('total_billed', 'Total Billed', '📑', '#2563eb'),
            ('total_advance', 'Advance Collected', '💵', '#0284c7'),
            ('total_payment', 'Total Received', '💰', '#059669'),
            ('total_expense', 'Total Expenses', '💸', '#dc2626'),
            ('net_profit', 'Net Profit', '📈', '#16a34a'),
            ('total_pending', 'Pending Dues', '⏳', '#d97706'),
        ]

        for key, label, icon, color in kpis:
            card = MetricCard(label, f"{self.currency_symbol}0", icon, color)
            self.metric_cards[key] = card
            kpi_layout.addWidget(card)

        layout.addWidget(kpi_frame)

        # ── 3. Filters & Search Strip ──
        filter_card = QFrame()
        filter_card.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['card_bg']};
                border: 1px solid {colors['border']};
                border-radius: 10px;
            }}
        """)
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(14, 10, 14, 10)
        filter_layout.setSpacing(10)

        self.combo_period = QComboBox()
        self.combo_period.setFixedWidth(135)
        self.combo_period.addItems(["Today", "Yesterday", "This Week", "This Month", "Last Month", "Custom Range"])
        self.combo_period.setCurrentText("This Month")
        self.combo_period.currentTextChanged.connect(self._on_period_changed)
        filter_layout.addWidget(self.combo_period)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("dd-MM-yyyy")
        self.date_from.setFixedWidth(125)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.dateChanged.connect(self.load_data)
        filter_layout.addWidget(self.date_from)

        lbl_to = QLabel("to")
        lbl_to.setStyleSheet(f"color: {colors['muted']}; font-weight: 500;")
        filter_layout.addWidget(lbl_to)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("dd-MM-yyyy")
        self.date_to.setFixedWidth(125)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.dateChanged.connect(self.load_data)
        filter_layout.addWidget(self.date_to)

        self.combo_tech_filter = QComboBox()
        self.combo_tech_filter.setFixedWidth(160)
        self.combo_tech_filter.addItem("All Technicians", None)
        self._populate_tech_filter()
        self.combo_tech_filter.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(self.combo_tech_filter)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Search by Mobile No (e.g. 9812345678), Customer Name, Site Address, Tech...")
        self.txt_search.setClearButtonEnabled(True)
        self.txt_search.textChanged.connect(self._on_search_delayed)
        filter_layout.addWidget(self.txt_search)

        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.setFixedHeight(34)
        self.btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['hover']};
                color: {colors['fg']};
                border: 1px solid {colors['border']};
                border-radius: 6px;
                padding: 0 12px;
                font-weight: 600;
                font-size: 8.5pt;
            }}
            QPushButton:hover {{
                border-color: {colors['primary']};
                color: {colors['primary']};
            }}
        """)
        self.btn_refresh.clicked.connect(self.load_data)
        filter_layout.addWidget(self.btn_refresh)

        layout.addWidget(filter_card)

        # ── 4. Main Data Table with Crisp Visible Borders and Clear Columns ──
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(True)
        self.table.setGridStyle(Qt.PenStyle.SolidLine)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.doubleClicked.connect(self._on_row_double_clicked)

        headers = [
            "#", "Date", "Customer", "Mobile", "Site Address",
            "Technician", "Work & Parts", "Total Bill",
            "Advance Recd", "Adv Receiver", "Final Recd", "Total Collected",
            "Balance Due", "Parts Cost", "Petrol", "Total Cost",
            "Net Profit", "Status", "Actions"
        ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        header_tooltips = [
            "Serial Number",
            "Service / Visit Date (DD-MM-YYYY)",
            "Customer / Client Name",
            "Customer Mobile Contact Number",
            "Job Site / Location Address",
            "Assigned Service Technician",
            "Work Performed & Spare Parts Installed",
            "Total Billed Amount for the Job (₹)",
            "Advance Payment Received Upfront (₹)",
            "Person / Account Receiving Advance",
            "Final Payment Received upon Completion (₹)",
            "Total Amount Collected (Advance + Final) (₹)",
            "Pending Balance Due from Customer (₹)",
            "Material & Spare Parts Cost (₹)",
            "Technician Travel & Petrol Allowance (₹)",
            "Total Expenses on this Job (Parts + Petrol) (₹)",
            "Net Profit (Total Collected - Total Cost) (₹)",
            "Payment Status (Paid / Partial / Pending)",
            "Quick Actions (Edit, Customer History, WhatsApp, Delete)"
        ]
        for col_idx, tip in enumerate(header_tooltips):
            item = self.table.horizontalHeaderItem(col_idx)
            if item:
                item.setToolTip(tip)

        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setHighlightSections(False)
        col_widths = [
            45,   # 0: #
            95,   # 1: Date
            135,  # 2: Customer
            110,  # 3: Mobile
            155,  # 4: Site Address
            120,  # 5: Technician
            165,  # 6: Work & Parts
            95,   # 7: Total Bill
            95,   # 8: Advance Recd
            100,  # 9: Adv Receiver
            90,   # 10: Final Recd
            105,  # 11: Total Collected
            100,  # 12: Balance Due
            85,   # 13: Parts Cost
            75,   # 14: Petrol
            95,   # 15: Total Cost
            100,  # 16: Net Profit
            90,   # 17: Status
            125,  # 18: Actions
        ]
        for idx, w in enumerate(col_widths):
            self.table.setColumnWidth(idx, w)

        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {colors['card_bg']};
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                gridline-color: #E2E8F0;
                selection-background-color: #EFF6FF;
                selection-color: {colors['fg']};
            }}
            QHeaderView::section {{
                background-color: #F8FAFC;
                color: #334155;
                font-weight: 700;
                font-size: 8.5pt;
                padding: 9px 8px;
                border-top: none;
                border-left: none;
                border-right: 1px solid #CBD5E1;
                border-bottom: 2px solid #94A3B8;
            }}
            QTableWidget::item {{
                padding: 7px 8px;
                border-bottom: 1px solid #E2E8F0;
                border-right: 1px solid #E2E8F0;
                font-size: 8.5pt;
            }}
            QTableWidget::item:selected {{
                background-color: #EFF6FF;
                color: #0F172A;
            }}
        """)

        layout.addWidget(self.table, stretch=1)

        # ── 5. Bottom Status Bar ──
        status_row = QHBoxLayout()
        self.lbl_row_count = QLabel("Showing 0 records")
        self.lbl_row_count.setStyleSheet(f"color: {colors['muted']}; font-size: 8.5pt; font-weight: 500;")
        status_row.addWidget(self.lbl_row_count)

        status_row.addStretch()

        help_lbl = QLabel("💡 Double click to edit • Right-click row for Technician Dossier, Customer Multi-Visit History & WhatsApp")
        help_lbl.setStyleSheet(f"color: {colors['muted']}; font-size: 8.5pt; font-style: italic;")
        status_row.addWidget(help_lbl)

        layout.addLayout(status_row)

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self.load_data)

    def _populate_tech_filter(self):
        try:
            with DatabaseContext() as db:
                ctrl = DailyLogController(db)
                techs = ctrl.get_all_technicians_list()
                for t in techs:
                    self.combo_tech_filter.addItem(t['name'], t['id'])
        except Exception:
            pass

    def _on_period_changed(self, text):
        today = QDate.currentDate()
        self.date_from.blockSignals(True)
        self.date_to.blockSignals(True)

        if text == "Today":
            self.date_from.setDate(today)
            self.date_to.setDate(today)
        elif text == "Yesterday":
            self.date_from.setDate(today.addDays(-1))
            self.date_to.setDate(today.addDays(-1))
        elif text == "This Week":
            day_of_week = today.dayOfWeek()
            self.date_from.setDate(today.addDays(-(day_of_week - 1)))
            self.date_to.setDate(today)
        elif text == "This Month":
            self.date_from.setDate(QDate(today.year(), today.month(), 1))
            self.date_to.setDate(today)
        elif text == "Last Month":
            first_this_month = QDate(today.year(), today.month(), 1)
            last_day_prev = first_this_month.addDays(-1)
            first_day_prev = QDate(last_day_prev.year(), last_day_prev.month(), 1)
            self.date_from.setDate(first_day_prev)
            self.date_to.setDate(last_day_prev)

        self.date_from.blockSignals(False)
        self.date_to.blockSignals(False)
        self.load_data()

    def _on_search_delayed(self):
        self._search_timer.start()

    def load_data(self):
        """Fetch logs from DB and populate table + KPI cards"""
        start_date = self.date_from.date().toString("yyyy-MM-dd")
        end_date = self.date_to.date().toString("yyyy-MM-dd")
        tech_id = self.combo_tech_filter.currentData()
        search_txt = self.txt_search.text().strip()

        try:
            with DatabaseContext() as db:
                ctrl = DailyLogController(db)
                self.logs_data = ctrl.get_logs(
                    start_date=start_date,
                    end_date=end_date,
                    technician_id=tech_id,
                    search_term=search_txt
                )
                summary = ctrl.get_summary(
                    start_date=start_date,
                    end_date=end_date,
                    technician_id=tech_id
                )

            # Update KPI Cards
            sym = self.currency_symbol
            def _fmt_kpi(val: float) -> str:
                if val.is_integer():
                    return f"{sym}{int(val):,}"
                return f"{sym}{val:,.2f}"

            if 'total_billed' in self.metric_cards:
                self.metric_cards['total_billed'].set_value(_fmt_kpi(summary['total_billed']))
            if 'total_advance' in self.metric_cards:
                self.metric_cards['total_advance'].set_value(_fmt_kpi(summary['total_advance']))
            if 'total_payment' in self.metric_cards:
                self.metric_cards['total_payment'].set_value(_fmt_kpi(summary['total_payment']))
            if 'total_expense' in self.metric_cards:
                self.metric_cards['total_expense'].set_value(_fmt_kpi(summary['total_expense']))
            if 'net_profit' in self.metric_cards:
                self.metric_cards['net_profit'].set_value(_fmt_kpi(summary['net_profit']))
            if 'total_pending' in self.metric_cards:
                self.metric_cards['total_pending'].set_value(_fmt_kpi(summary['total_pending']))

            # Populate Table
            self._render_table(self.logs_data)
            self.lbl_row_count.setText(f"Showing {len(self.logs_data)} daily logs")

        except Exception as e:
            QMessageBox.critical(self, "Error Loading Logs", f"Failed to load daily logs: {e}")

    def _render_table(self, logs: list):
        self.table.setRowCount(0)
        self.table.setRowCount(len(logs))
        colors = self.theme_manager.get_colors()
        sym = self.currency_symbol

        for row_idx, log in enumerate(logs):
            log_id = log['id']
            date_raw = log.get('log_date', '')
            date_str = Formatters.format_date(date_raw) if date_raw else ''
            cust_name = str(log.get('customer_name', '') or '')
            cust_mob = str(log.get('customer_mobile', '') or '')
            cust_addr = str(log.get('customer_address', '') or '')
            tech_name = str(log.get('technician_name', '') or '')
            work_desc = str(log.get('work_description', '') or '')

            billed = float(log.get('total_billed', 0) or log.get('total_payment', 0) or 0)
            advance = float(log.get('advance_payment', 0) or 0)
            adv_to = str(log.get('advance_receiver', 'Tech (Cash)') or '')
            final = float(log.get('final_payment', 0) or 0)
            recd = float(log.get('total_payment', 0) or 0)
            pending = float(log.get('pending_amount', 0) or max(0.0, billed - recd))

            mat_cost = float(log.get('material_cost', 0) or 0)
            petrol = float(log.get('petrol_expense', 0) or 0)
            total_exp = float(log.get('total_expense', 0) or (mat_cost + petrol))
            profit = float(log.get('net_profit', 0) or (recd - total_exp))
            status = str(log.get('payment_status', 'Paid') or 'Paid')

            # Column 0: Clean Serial Number (stores DB log_id in data role for background lookups)
            item_sno = QTableWidgetItem(str(row_idx + 1))
            item_sno.setData(Qt.UserRole, log_id)
            item_sno.setTextAlignment(Qt.AlignCenter)
            item_sno.setForeground(QColor("#64748b"))
            self.table.setItem(row_idx, 0, item_sno)

            # Column 1: Date in DD-MM-YYYY format
            item_date = QTableWidgetItem(date_str)
            item_date.setTextAlignment(Qt.AlignCenter)
            item_date.setFont(QFont("Segoe UI", 8, QFont.Bold))
            item_date.setForeground(QColor("#334155"))
            self.table.setItem(row_idx, 1, item_date)

            # Column 2: Customer Name
            cust_item = QTableWidgetItem(cust_name)
            cust_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            cust_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.table.setItem(row_idx, 2, cust_item)

            # Column 3: Mobile Number (Formatted e.g. 98765 43210)
            mob_formatted = Formatters.format_mobile(cust_mob) if cust_mob else ''
            mob_item = QTableWidgetItem(mob_formatted)
            mob_item.setTextAlignment(Qt.AlignCenter)
            mob_item.setForeground(QColor("#0284c7"))
            self.table.setItem(row_idx, 3, mob_item)

            # Column 4: Site Address
            addr_item = QTableWidgetItem(cust_addr)
            addr_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            addr_item.setToolTip(cust_addr)
            self.table.setItem(row_idx, 4, addr_item)

            # Column 5: Technician Name
            tech_item = QTableWidgetItem(tech_name)
            tech_item.setFont(QFont("Segoe UI", 9, QFont.DemiBold))
            tech_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.table.setItem(row_idx, 5, tech_item)

            # Column 6: Work & Parts
            work_item = QTableWidgetItem(work_desc)
            work_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            work_item.setToolTip(work_desc)
            self.table.setItem(row_idx, 6, work_item)

            # Helper for cell formatting (table rows always show actual figures)
            def _fmt_cell(val: float) -> str:
                if val.is_integer():
                    return f"{sym}{int(val):,}"
                return f"{sym}{val:,.2f}"

            # Column 7: Total Bill
            item_billed = QTableWidgetItem(_fmt_cell(billed))
            item_billed.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_billed.setFont(QFont("Segoe UI", 8, QFont.DemiBold))
            self.table.setItem(row_idx, 7, item_billed)

            # Column 8: Advance Paid
            item_adv = QTableWidgetItem(_fmt_cell(advance))
            item_adv.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_idx, 8, item_adv)

            # Column 9: Adv Receiver
            item_adv_to = QTableWidgetItem(adv_to)
            item_adv_to.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 9, item_adv_to)

            # Column 10: Final Paid
            item_final = QTableWidgetItem(_fmt_cell(final))
            item_final.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_idx, 10, item_final)

            # Column 11: Total Collected
            item_recd = QTableWidgetItem(_fmt_cell(recd))
            item_recd.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_recd.setForeground(QColor("#059669"))
            item_recd.setFont(QFont("Segoe UI", 8, QFont.Bold))
            self.table.setItem(row_idx, 11, item_recd)

            # Column 12: Balance Due (Highlighted if pending > 0)
            item_pend = QTableWidgetItem(_fmt_cell(pending))
            item_pend.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if pending > 0:
                item_pend.setForeground(QColor("#d97706"))
                item_pend.setFont(QFont("Segoe UI", 8, QFont.Bold))
            else:
                item_pend.setForeground(QColor("#94a3b8"))
            self.table.setItem(row_idx, 12, item_pend)

            # Column 13: Parts Cost
            item_mat = QTableWidgetItem(_fmt_cell(mat_cost))
            item_mat.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_idx, 13, item_mat)

            # Column 14: Petrol
            item_pet = QTableWidgetItem(_fmt_cell(petrol))
            item_pet.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_idx, 14, item_pet)

            # Column 15: Total Expenses
            item_exp = QTableWidgetItem(_fmt_cell(total_exp))
            item_exp.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_exp.setForeground(QColor("#dc2626"))
            self.table.setItem(row_idx, 15, item_exp)

            # Column 16: Net Profit (Green if positive, Red if loss)
            item_prof = QTableWidgetItem(_fmt_cell(profit))
            item_prof.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_prof.setFont(QFont("Segoe UI", 8, QFont.Bold))
            if profit >= 0:
                item_prof.setForeground(QColor("#16a34a"))
            else:
                item_prof.setForeground(QColor("#dc2626"))
            self.table.setItem(row_idx, 16, item_prof)

            # Status Badge
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(4, 2, 4, 2)
            status_lbl = QLabel(status)
            status_lbl.setAlignment(Qt.AlignCenter)

            if "Paid" in status and "Partial" not in status:
                badge_bg, badge_fg = "#dcfce7", "#15803d"
            elif "Partial" in status or "Advance" in status:
                badge_bg, badge_fg = "#fef3c7", "#b45309"
            elif "Pending" in status:
                badge_bg, badge_fg = "#fee2e2", "#b91c1c"
            else:
                badge_bg, badge_fg = "#e0e7ff", "#4338ca"

            status_lbl.setStyleSheet(f"""
                background-color: {badge_bg};
                color: {badge_fg};
                border-radius: 4px;
                padding: 2px 8px;
                font-weight: 700;
                font-size: 7.5pt;
            """)
            status_layout.addWidget(status_lbl)
            self.table.setCellWidget(row_idx, 17, status_widget)

            # Action Buttons Widget
            actions_widget = QWidget()
            act_layout = QHBoxLayout(actions_widget)
            act_layout.setContentsMargins(2, 2, 2, 2)
            act_layout.setSpacing(4)

            btn_edit = QPushButton("✏️")
            btn_edit.setToolTip("Edit Log")
            btn_edit.setFixedSize(26, 26)
            btn_edit.setCursor(Qt.PointingHandCursor)
            btn_edit.setStyleSheet(f"QPushButton {{ background: {colors['hover']}; border-radius: 4px; border: 1px solid {colors['border']}; }} QPushButton:hover {{ border-color: {colors['primary']}; }}")
            btn_edit.clicked.connect(lambda _, lid=log_id: self._edit_log_by_id(lid))
            act_layout.addWidget(btn_edit)

            btn_cust = QPushButton("👤")
            btn_cust.setToolTip("View Customer Full Multi-Visit History")
            btn_cust.setFixedSize(26, 26)
            btn_cust.setCursor(Qt.PointingHandCursor)
            btn_cust.setStyleSheet(f"QPushButton {{ background: #7c3aed15; color: #7c3aed; border-radius: 4px; border: 1px solid #7c3aed40; }} QPushButton:hover {{ background: #7c3aed30; }}")
            btn_cust.clicked.connect(lambda _, mob=cust_mob, cname=cust_name: self._go_to_customer_history(mob or cname))
            act_layout.addWidget(btn_cust)

            btn_wa = QPushButton("💬")
            btn_wa.setToolTip("Send WhatsApp Receipt")
            btn_wa.setFixedSize(26, 26)
            btn_wa.setCursor(Qt.PointingHandCursor)
            btn_wa.setStyleSheet(f"QPushButton {{ background: #25d36615; color: #25d366; border-radius: 4px; border: 1px solid #25d36640; }} QPushButton:hover {{ background: #25d36630; }}")
            btn_wa.clicked.connect(lambda _, row_log=log: self._send_whatsapp_receipt(row_log))
            act_layout.addWidget(btn_wa)

            btn_del = QPushButton("🗑️")
            btn_del.setToolTip("Delete Log")
            btn_del.setFixedSize(26, 26)
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setStyleSheet(f"QPushButton {{ background: #fee2e2; color: #dc2626; border-radius: 4px; border: 1px solid #fca5a5; }} QPushButton:hover {{ background: #fecaca; }}")
            btn_del.clicked.connect(lambda _, lid=log_id: self._delete_log_by_id(lid))
            act_layout.addWidget(btn_del)

            self.table.setCellWidget(row_idx, 18, actions_widget)

    def _open_add_dialog(self):
        dlg = LogDialog(parent=self)
        if dlg.exec():
            self.load_data()

    def _edit_log_by_id(self, log_id: int):
        try:
            with DatabaseContext() as db:
                ctrl = DailyLogController(db)
                log = ctrl.get_log(log_id)
            if not log:
                QMessageBox.warning(self, "Not Found", "Log entry could not be found.")
                return
            dlg = LogDialog(log_data=log, parent=self)
            if dlg.exec():
                self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open edit dialog: {e}")

    def _delete_log_by_id(self, log_id: int):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this daily work log entry?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                with DatabaseContext() as db:
                    ctrl = DailyLogController(db)
                    ctrl.delete_log(log_id)
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Delete Error", f"Failed to delete log: {e}")

    def _toggle_privacy_mode(self):
        """Toggle privacy mode globally from Daily Logs view."""
        self.privacy_mgr.toggle_privacy()

    def _on_privacy_mode_toggled(self, enabled: bool):
        """Handle privacy mode change across the UI (cards only)."""
        self._update_privacy_button_ui()
        if hasattr(self, 'settle_techs_data') and self.settle_techs_data:
            if hasattr(self, '_render_settle_techs'):
                self._render_settle_techs()

    def _update_privacy_button_ui(self):
        """Update the daily logs local privacy button styling."""
        if not hasattr(self, 'btn_privacy') or self.btn_privacy is None:
            return
        colors = self.theme_manager.get_colors()
        is_active = self.privacy_mgr.is_privacy_enabled()

        if is_active:
            self.btn_privacy.setText("🔒 Privacy ON")
            self.btn_privacy.setToolTip("Financial data masked with '••••••'. Click to show actual numbers.")
            self.btn_privacy.setStyleSheet("""
                QPushButton {
                    background-color: #dc262618;
                    color: #dc2626;
                    border: 1.5px solid #dc2626;
                    border-radius: 8px;
                    padding: 0 14px;
                    font-size: 9pt;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background-color: #dc262628;
                }
            """)
        else:
            self.btn_privacy.setText("👁️ Privacy Shield")
            self.btn_privacy.setToolTip("Mask monetary amounts & profit in cards & table")
            self.btn_privacy.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['hover']};
                    color: {colors['fg']};
                    border: 1px solid {colors['border']};
                    border-radius: 8px;
                    padding: 0 14px;
                    font-size: 9pt;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    border-color: {colors['primary']};
                    color: {colors['primary']};
                }}
            """)

    def _on_row_double_clicked(self, index):
        row = index.row()
        item = self.table.item(row, 0)
        if item:
            log_id = item.data(Qt.UserRole)
            if log_id:
                self._edit_log_by_id(int(log_id))

    def _show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item:
            return
        row = item.row()
        sno_item = self.table.item(row, 0)
        if not sno_item:
            return
        log_id = sno_item.data(Qt.UserRole)

        selected_log = next((l for l in self.logs_data if l['id'] == log_id), None)
        if not selected_log:
            return

        menu = QMenu(self)
        action_edit = menu.addAction("✏️ Edit Entry")
        action_cust_history = menu.addAction(f"👤 View Customer Multi-Visit History ({selected_log.get('customer_name', 'Customer')})")
        action_tech_dossier = menu.addAction(f"👨‍🔧 View Technician Dossier ({selected_log.get('technician_name', 'Tech')})")
        menu.addSeparator()
        action_wa = menu.addAction("💬 Send WhatsApp Receipt")
        action_invoice = menu.addAction("🧾 Generate Formal Tax Invoice")
        menu.addSeparator()
        action_del = menu.addAction("🗑️ Delete Entry")

        chosen = menu.exec(self.table.viewport().mapToGlobal(pos))
        if chosen == action_edit:
            self._edit_log_by_id(log_id)
        elif chosen == action_cust_history:
            self._go_to_customer_history(selected_log.get('customer_mobile') or selected_log.get('customer_name'))
        elif chosen == action_tech_dossier:
            self._go_to_tech_dossier(selected_log.get('technician_name'))
        elif chosen == action_wa:
            self._send_whatsapp_receipt(selected_log)
        elif chosen == action_invoice:
            self._convert_to_invoice(selected_log)
        elif chosen == action_del:
            self._delete_log_by_id(log_id)

    def _send_whatsapp_receipt(self, log: dict):
        mob = str(log.get('customer_mobile', '') or '').strip()
        mob_clean = "".join([c for c in mob if c.isdigit()])
        if not mob_clean:
            QMessageBox.warning(self, "No Mobile Number", "No customer mobile number is recorded for this entry.")
            return

        if len(mob_clean) == 10:
            mob_clean = "91" + mob_clean

        name = log.get('customer_name', 'Customer')
        date_val = log.get('log_date', '')
        work = log.get('work_description', 'AC Service / Repair')
        tech = log.get('technician_name', '')
        billed = float(log.get('total_billed', 0) or log.get('total_payment', 0) or 0)
        advance = float(log.get('advance_payment', 0) or 0)
        recd = float(log.get('total_payment', 0) or 0)
        pending = float(log.get('pending_amount', 0) or max(0.0, billed - recd))

        msg = (
            f"Hello {name},\n\n"
            f"Thank you for choosing our service!\n"
            f"📅 Date: {date_val}\n"
            f"🛠️ Work: {work}\n"
            f"👨‍🔧 Technician: {tech}\n\n"
            f"💰 Total Billed: ₹{billed:,.2f}\n"
            f"💵 Advance Paid: ₹{advance:,.2f}\n"
            f"✅ Total Received: ₹{recd:,.2f}\n"
            f"⏳ Balance Due: ₹{pending:,.2f}\n\n"
            f"For any queries, please contact us. Have a great day!"
        )
        encoded_msg = urllib.parse.quote(msg)
        wa_url = f"https://wa.me/{mob_clean}?text={encoded_msg}"
        webbrowser.open(wa_url)

    def _convert_to_invoice(self, log: dict):
        main_win = self.window()
        if hasattr(main_win, '_show_invoice'):
            customer_data = {
                'name': log.get('customer_name', ''),
                'mobile': log.get('customer_mobile', ''),
                'address': log.get('customer_address', ''),
                'customer_id': log.get('customer_id'),
                'work_description': log.get('work_description', ''),
                'amount': log.get('total_billed', 0) or log.get('total_payment', 0)
            }
            main_win._show_invoice(customer_data=customer_data)
        else:
            QMessageBox.information(self, "Create Invoice", "Please navigate to Invoice section to generate an invoice for this customer.")

    def _export_to_excel(self):
        if not self.logs_data:
            QMessageBox.warning(self, "Export", "No daily logs data available to export for the current filters.")
            return

        default_name = f"Daily_Work_Logs_{self.date_from.date().toString('yyyyMMdd')}_{self.date_to.date().toString('yyyyMMdd')}.xlsx"
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Excel Register",
            default_name,
            "Excel Files (*.xlsx)"
        )
        if not filepath:
            return

        try:
            with DatabaseContext() as db:
                ctrl = DailyLogController(db)
                ctrl.export_to_excel(self.logs_data, filepath)
            QMessageBox.information(self, "Export Successful", f"Logs exported successfully to:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export Excel file: {e}")

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE 1: FULL-PAGE MONTH-END SETTLEMENT & RECONCILIATION
    # ═════════════════════════════════════════════════════════════════════════
    def _build_settlement_page(self, container: QWidget):
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)
        colors = self.theme_manager.get_colors()

        # Top Bar with Back Button
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        self.btn_back_from_settle = QPushButton("⬅️ Back to Daily Logs")
        self.btn_back_from_settle.setCursor(Qt.PointingHandCursor)
        self.btn_back_from_settle.setFixedHeight(38)
        self.btn_back_from_settle.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['hover']};
                color: {colors['primary']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                padding: 0 16px;
                font-weight: 700;
                font-size: 9pt;
            }}
            QPushButton:hover {{
                background-color: {colors['primary']}15;
                border-color: {colors['primary']};
            }}
        """)
        self.btn_back_from_settle.clicked.connect(self._go_to_register)
        top_bar.addWidget(self.btn_back_from_settle)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = QLabel("📊 Month-End Settlement & Cash Handover Report")
        title_lbl.setStyleSheet(f"font-size: 15pt; font-weight: 800; color: {colors['fg']};")
        sub_lbl = QLabel("Itemized breakdown of Advance to Tech, Final Cash, Material & Petrol expenses, and Net Cash Handover")
        sub_lbl.setStyleSheet(f"font-size: 8.5pt; color: {colors['muted']};")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        top_bar.addLayout(title_box)

        top_bar.addStretch()

        lbl_m = QLabel("Month:")
        lbl_m.setStyleSheet("font-weight: 700;")
        top_bar.addWidget(lbl_m)

        self.settle_combo_month = QComboBox()
        self.settle_combo_month.setFixedWidth(140)
        for m in range(1, 13):
            self.settle_combo_month.addItem(datetime(2000, m, 1).strftime("%B"), m)
        self.settle_combo_month.setCurrentIndex(datetime.now().month - 1)
        self.settle_combo_month.currentIndexChanged.connect(self._load_settlement_data)
        top_bar.addWidget(self.settle_combo_month)

        lbl_y = QLabel("Year:")
        lbl_y.setStyleSheet("font-weight: 700;")
        top_bar.addWidget(lbl_y)

        self.settle_combo_year = QComboBox()
        self.settle_combo_year.setFixedWidth(100)
        curr_y = datetime.now().year
        for y in range(curr_y - 3, curr_y + 3):
            self.settle_combo_year.addItem(str(y), y)
        self.settle_combo_year.setCurrentText(str(curr_y))
        self.settle_combo_year.currentIndexChanged.connect(self._load_settlement_data)
        top_bar.addWidget(self.settle_combo_year)

        layout.addLayout(top_bar)

        # Company Summary Cards Frame (Solid cards, no ghosting/overlapping)
        self.settle_summary_frame = QFrame()
        self.settle_summary_frame.setStyleSheet(f"background-color: {colors['hover']}; border: 1px solid {colors['border']}; border-radius: 10px; padding: 4px;")
        self.settle_summary_layout = QHBoxLayout(self.settle_summary_frame)
        self.settle_summary_layout.setSpacing(10)
        self.settle_summary_layout.setContentsMargins(6, 6, 6, 6)

        settle_kpi_defs = [
            ('total_billed', 'TOTAL BILLED', 'Total Agreed Value', '#2563eb'),
            ('total_advance', 'ADVANCE COLLECTED', 'Upfront deposits', '#0284c7'),
            ('total_payment', 'TOTAL RECEIVED', 'All cleared collections', '#059669'),
            ('total_material', 'PARTS COST', 'Spare parts & supplies', '#ea580c'),
            ('total_petrol', 'PETROL COST', 'Conveyance & fuel', '#d97706'),
            ('total_expense', 'TOTAL EXPENSES', 'Material + Petrol', '#dc2626'),
            ('net_profit', 'NET MONTH PROFIT', 'Revenue minus Kharcha', '#16a34a'),
            ('total_pending', 'PENDING DUES', 'Uncollected balance', '#7c3aed'),
        ]

        self.settle_metric_labels = {}
        for key, title, sub, col in settle_kpi_defs:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors['card_bg']};
                    border: 1px solid {colors['border']};
                    border-radius: 8px;
                    padding: 8px 10px;
                }}
            """)
            c_box = QVBoxLayout(card)
            c_box.setContentsMargins(0, 0, 0, 0)
            c_box.setSpacing(2)

            l1 = QLabel(title)
            l1.setStyleSheet("font-size: 7.5pt; color: #64748b; font-weight: 700;")

            l2 = QLabel(f"{self.currency_symbol}0")
            l2.setStyleSheet(f"font-size: 11pt; font-weight: 800; color: {col};")

            l3 = QLabel(sub)
            l3.setStyleSheet("font-size: 7pt; color: #94a3b8;")

            c_box.addWidget(l1)
            c_box.addWidget(l2)
            c_box.addWidget(l3)

            self.settle_summary_layout.addWidget(card)
            self.settle_metric_labels[key] = l2

        layout.addWidget(self.settle_summary_frame)

        # Simple Calculation Guide Banner
        guide_box = QFrame()
        guide_box.setStyleSheet("""
            QFrame {
                background-color: #f0fdf4;
                border: 1px solid #bbf7d0;
                border-radius: 8px;
                padding: 10px 14px;
            }
        """)
        guide_layout = QHBoxLayout(guide_box)
        guide_layout.setContentsMargins(8, 4, 8, 4)

        guide_icon = QLabel("💡")
        guide_icon.setStyleSheet("font-size: 16pt;")
        guide_layout.addWidget(guide_icon)

        guide_text = QLabel(
            "<b>How Net Settlement is Calculated:</b> "
            "<span style='color:#0284c7;'>[Advance to Tech]</span> + "
            "<span style='color:#059669;'>[Final Cash to Tech]</span> = "
            "<b>[Total Cash in Tech's Hand]</b> — "
            "<span style='color:#ea580c;'>[Material/Parts Kharch]</span> — "
            "<span style='color:#d97706;'>[Petrol Kharch]</span> = "
            "<b style='color:#15803d;'>[Net Cash to Hand Over to Owner]</b> "
            "<span style='color:#64748b; font-size:8pt;'>(Direct UPI/Bank to Owner is not in Tech's cash)</span>"
        )
        guide_text.setStyleSheet("font-size: 9pt; color: #1e293b;")
        guide_text.setWordWrap(True)
        guide_layout.addWidget(guide_text, stretch=1)
        layout.addWidget(guide_box)

        # Table
        self.table_settle_techs = QTableWidget()
        self.table_settle_techs.setAlternatingRowColors(True)
        self.table_settle_techs.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_settle_techs.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_settle_techs.setShowGrid(True)
        self.table_settle_techs.setGridStyle(Qt.PenStyle.SolidLine)
        self.table_settle_techs.verticalHeader().setVisible(False)
        self.table_settle_techs.verticalHeader().setDefaultSectionSize(42)
        self.table_settle_techs.doubleClicked.connect(self._on_settle_tech_double_clicked)

        headers = [
            "Technician Name", "Jobs", "Total Billed",
            "Advance to Tech", "Final to Tech", "Total Tech Cash",
            "Direct to Owner", "Parts Cost", "Petrol Cost",
            "Total Expenses", "Net Cash to Owner", "Action"
        ]
        self.table_settle_techs.setColumnCount(len(headers))
        self.table_settle_techs.setHorizontalHeaderLabels(headers)

        th = self.table_settle_techs.horizontalHeader()
        th.setStretchLastSection(False)
        th.setHighlightSections(False)
        col_widths = [
            145,  # 0: Technician Name
            65,   # 1: Jobs
            95,   # 2: Total Billed
            105,  # 3: Advance to Tech
            105,  # 4: Final to Tech
            110,  # 5: Total Tech Cash
            105,  # 6: Direct to Owner
            95,   # 7: Parts Cost
            90,   # 8: Petrol Cost
            105,  # 9: Total Expenses
            125,  # 10: Net Cash to Owner
            115,  # 11: Action
        ]
        for idx, w in enumerate(col_widths):
            self.table_settle_techs.setColumnWidth(idx, w)

        self.table_settle_techs.setStyleSheet(f"""
            QTableWidget {{
                background-color: {colors['card_bg']};
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                gridline-color: #E2E8F0;
                selection-background-color: #EFF6FF;
                selection-color: {colors['fg']};
            }}
            QHeaderView::section {{
                background-color: #F8FAFC;
                color: #334155;
                font-weight: 700;
                font-size: 8.5pt;
                padding: 8px 6px;
                border-top: none;
                border-left: none;
                border-right: 1px solid #CBD5E1;
                border-bottom: 2px solid #94A3B8;
            }}
            QTableWidget::item {{
                padding: 6px 6px;
                border-bottom: 1px solid #E2E8F0;
                border-right: 1px solid #E2E8F0;
                font-size: 8.5pt;
            }}
            QTableWidget::item:selected {{
                background-color: #EFF6FF;
                color: #0F172A;
            }}
        """)
        layout.addWidget(self.table_settle_techs, stretch=1)

        self.lbl_settle_footer = QLabel("")
        self.lbl_settle_footer.setStyleSheet("font-weight: 700; font-size: 9.5pt; color: #1e293b;")
        layout.addWidget(self.lbl_settle_footer)

    def _load_settlement_data(self):
        sym = self.currency_symbol
        year = int(self.settle_combo_year.currentText())
        month = self.settle_combo_month.currentData()

        try:
            with DatabaseContext() as db:
                ctrl = DailyLogController(db)
                recon = ctrl.get_month_reconciliation(year, month)

            overall = recon['overall']

            is_priv = self.privacy_mgr.is_privacy_enabled()
            def _fmt_amt(val: float) -> str:
                if is_priv:
                    return f"{sym} ••••••"
                if val.is_integer():
                    return f"{sym}{int(val):,}"
                return f"{sym}{val:,.2f}"

            for key, label_widget in self.settle_metric_labels.items():
                val = float(overall.get(key, 0) or 0)
                label_widget.setText(_fmt_amt(val))

            self.settle_techs_data = recon['technicians']
            self.table_settle_techs.setRowCount(0)
            self.table_settle_techs.setRowCount(len(self.settle_techs_data))

            total_handover_all = 0.0

            for row_idx, t in enumerate(self.settle_techs_data):
                name_item = QTableWidgetItem(t['tech_name'])
                name_item.setFont(QFont("Segoe UI", 9.5, QFont.Bold))
                self.table_settle_techs.setItem(row_idx, 0, name_item)

                item_jobs = QTableWidgetItem(str(t['total_jobs']))
                item_jobs.setTextAlignment(Qt.AlignCenter)
                self.table_settle_techs.setItem(row_idx, 1, item_jobs)

                item_billed = QTableWidgetItem(_fmt_amt(t['total_billed']))
                item_billed.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table_settle_techs.setItem(row_idx, 2, item_billed)

                adv_tech = t.get('tech_advance_collected', t.get('total_advance', 0))
                item_adv = QTableWidgetItem(_fmt_amt(adv_tech))
                item_adv.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item_adv.setForeground(QColor("#0284c7"))
                self.table_settle_techs.setItem(row_idx, 3, item_adv)

                fin_tech = t.get('tech_final_collected', t['cash_collected'] - adv_tech)
                item_fin = QTableWidgetItem(_fmt_amt(fin_tech))
                item_fin.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item_fin.setForeground(QColor("#059669"))
                self.table_settle_techs.setItem(row_idx, 4, item_fin)

                item_cash = QTableWidgetItem(_fmt_amt(t['cash_collected']))
                item_cash.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item_cash.setFont(QFont("Segoe UI", 9, QFont.Bold))
                item_cash.setForeground(QColor("#0f172a"))
                self.table_settle_techs.setItem(row_idx, 5, item_cash)

                item_direct = QTableWidgetItem(_fmt_amt(t['direct_seth']))
                item_direct.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item_direct.setForeground(QColor("#6366f1"))
                self.table_settle_techs.setItem(row_idx, 6, item_direct)

                item_mat = QTableWidgetItem(_fmt_amt(t['total_material']))
                item_mat.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item_mat.setForeground(QColor("#ea580c"))
                self.table_settle_techs.setItem(row_idx, 7, item_mat)

                item_pet = QTableWidgetItem(_fmt_amt(t['total_petrol']))
                item_pet.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item_pet.setForeground(QColor("#d97706"))
                self.table_settle_techs.setItem(row_idx, 8, item_pet)

                item_exp = QTableWidgetItem(_fmt_amt(t['total_expense']))
                item_exp.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item_exp.setFont(QFont("Segoe UI", 9, QFont.Bold))
                item_exp.setForeground(QColor("#dc2626"))
                self.table_settle_techs.setItem(row_idx, 9, item_exp)

                due = t['net_due_to_seth']
                total_handover_all += due
                item_due = QTableWidgetItem(_fmt_amt(due))
                item_due.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item_due.setFont(QFont("Segoe UI", 10, QFont.Bold))

                if due >= 0:
                    item_due.setForeground(QColor("#15803d"))
                else:
                    item_due.setForeground(QColor("#dc2626"))
                self.table_settle_techs.setItem(row_idx, 10, item_due)

                # Centered, perfectly aligned Action button inside cell container
                cell_widget = QWidget()
                cell_layout = QHBoxLayout(cell_widget)
                cell_layout.setContentsMargins(4, 2, 4, 2)
                cell_layout.setAlignment(Qt.AlignCenter)

                btn_view = QPushButton("📍 View Sites")
                btn_view.setCursor(Qt.PointingHandCursor)
                btn_view.setFixedHeight(28)
                btn_view.setFixedWidth(95)
                btn_view.setStyleSheet("""
                    QPushButton {
                        background-color: #eff6ff;
                        color: #2563eb;
                        border: 1px solid #bfdbfe;
                        border-radius: 6px;
                        padding: 0;
                        font-size: 8pt;
                        font-weight: 700;
                    }
                    QPushButton:hover {
                        background-color: #2563eb;
                        color: #ffffff;
                        border-color: #2563eb;
                    }
                """)
                tech_name_val = t['tech_name']
                btn_view.clicked.connect(lambda _, tn=tech_name_val: self._go_to_tech_dossier(tn))
                cell_layout.addWidget(btn_view)
                self.table_settle_techs.setCellWidget(row_idx, 11, cell_widget)

            month_name = datetime(2000, month, 1).strftime("%B")
            self.lbl_settle_footer.setText(f"Total Net Cash Handover to Owner across all technicians for {month_name} {year}: {sym}{total_handover_all:,.2f}")

        except Exception as e:
            QMessageBox.critical(self, "Reconciliation Error", f"Failed to load month-end data: {e}")

    def _on_settle_tech_double_clicked(self, index):
        row = index.row()
        if hasattr(self, 'settle_techs_data') and row < len(self.settle_techs_data):
            self._go_to_tech_dossier(self.settle_techs_data[row]['tech_name'])

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE 2: FULL-PAGE TECHNICIAN 360° DOSSIER & SITES
    # ═════════════════════════════════════════════════════════════════════════
    def _build_tech_dossier_page(self, container: QWidget):
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)
        colors = self.theme_manager.get_colors()

        # Top Bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        self.btn_back_from_tech = QPushButton("⬅️ Back to Daily Logs")
        self.btn_back_from_tech.setCursor(Qt.PointingHandCursor)
        self.btn_back_from_tech.setFixedHeight(38)
        self.btn_back_from_tech.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['hover']};
                color: {colors['primary']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                padding: 0 16px;
                font-weight: 700;
                font-size: 9pt;
            }}
            QPushButton:hover {{
                background-color: {colors['primary']}15;
                border-color: {colors['primary']};
            }}
        """)
        self.btn_back_from_tech.clicked.connect(self._go_to_register)
        top_bar.addWidget(self.btn_back_from_tech)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = QLabel("👨‍🔧 Technician 360° Performance, Advance & Site Dossier")
        title_lbl.setStyleSheet(f"font-size: 15pt; font-weight: 800; color: {colors['fg']};")
        sub_lbl = QLabel("Full audit of jobs completed, advances collected, spare parts purchased, petrol expenses, and site ledger")
        sub_lbl.setStyleSheet(f"font-size: 8.5pt; color: {colors['muted']};")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        top_bar.addLayout(title_box)

        top_bar.addStretch()

        lbl_select = QLabel("Technician:")
        lbl_select.setStyleSheet("font-weight: 700;")
        top_bar.addWidget(lbl_select)

        self.dossier_combo_tech = QComboBox()
        self.dossier_combo_tech.setMinimumWidth(200)
        self._populate_dossier_technicians()
        self.dossier_combo_tech.currentIndexChanged.connect(self._load_tech_dossier_data)
        top_bar.addWidget(self.dossier_combo_tech)

        self.dossier_date_from = QDateEdit()
        self.dossier_date_from.setCalendarPopup(True)
        self.dossier_date_from.setDisplayFormat("dd-MM-yyyy")
        self.dossier_date_from.setFixedWidth(125)
        self.dossier_date_from.setDate(QDate.currentDate().addDays(-90))
        self.dossier_date_from.dateChanged.connect(self._load_tech_dossier_data)
        top_bar.addWidget(self.dossier_date_from)

        top_bar.addWidget(QLabel("to"))

        self.dossier_date_to = QDateEdit()
        self.dossier_date_to.setCalendarPopup(True)
        self.dossier_date_to.setDisplayFormat("dd-MM-yyyy")
        self.dossier_date_to.setFixedWidth(125)
        self.dossier_date_to.setDate(QDate.currentDate())
        self.dossier_date_to.dateChanged.connect(self._load_tech_dossier_data)
        top_bar.addWidget(self.dossier_date_to)

        btn_ref = QPushButton("🔄 Refresh")
        btn_ref.clicked.connect(self._load_tech_dossier_data)
        top_bar.addWidget(btn_ref)

        layout.addLayout(top_bar)

        # Metric Cards Frame (Solid cards, no ghosting)
        self.dossier_metrics_frame = QFrame()
        self.dossier_metrics_frame.setStyleSheet(f"background-color: {colors['hover']}; border: 1px solid {colors['border']}; border-radius: 10px; padding: 4px;")
        self.dossier_metrics_layout = QHBoxLayout(self.dossier_metrics_frame)
        self.dossier_metrics_layout.setSpacing(10)
        self.dossier_metrics_layout.setContentsMargins(6, 6, 6, 6)

        dossier_kpi_defs = [
            ('jobs', 'TOTAL JOBS DONE', '0 visits', '#2563eb'),
            ('advance', 'ADVANCE COLLECTED', 'Upfront cash/UPI', '#0284c7'),
            ('cash', 'TOTAL CASH HANDLED', 'Advance + Final cash', '#059669'),
            ('material', 'PARTS PURCHASED', 'Spare parts expense', '#ea580c'),
            ('petrol', 'PETROL EXPENSE', 'Conveyance', '#d97706'),
            ('net', 'NET CASH TO OWNER', 'Cash minus Total Kharch', '#16a34a'),
        ]

        self.dossier_metric_labels = {}
        for key, title, sub, col in dossier_kpi_defs:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors['card_bg']};
                    border: 1px solid {colors['border']};
                    border-radius: 8px;
                    padding: 8px 10px;
                }}
            """)
            c_box = QVBoxLayout(card)
            c_box.setContentsMargins(0, 0, 0, 0)
            c_box.setSpacing(2)

            l1 = QLabel(title)
            l1.setStyleSheet("font-size: 7.5pt; color: #64748b; font-weight: 700;")

            l2 = QLabel(f"{self.currency_symbol}0")
            l2.setStyleSheet(f"font-size: 11pt; font-weight: 800; color: {col};")

            l3 = QLabel(sub)
            l3.setStyleSheet("font-size: 7pt; color: #94a3b8;")

            c_box.addWidget(l1)
            c_box.addWidget(l2)
            c_box.addWidget(l3)

            self.dossier_metrics_layout.addWidget(card)
            self.dossier_metric_labels[key] = (l2, l3)

        layout.addWidget(self.dossier_metrics_frame)

        # Site Visits Table
        self.table_dossier_jobs = QTableWidget()
        self.table_dossier_jobs.setAlternatingRowColors(True)
        self.table_dossier_jobs.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_dossier_jobs.setShowGrid(True)
        self.table_dossier_jobs.setGridStyle(Qt.PenStyle.SolidLine)
        self.table_dossier_jobs.verticalHeader().setVisible(False)
        self.table_dossier_jobs.verticalHeader().setDefaultSectionSize(40)

        headers = [
            "Date", "Customer Name", "Mobile Number", "Site / Job Address",
            "Work / Parts Details", "Billed (₹)", "Advance (₹)",
            "Adv To", "Final (₹)", "Material Cost (₹)", "Petrol (₹)",
            "Total Cost (₹)", "Net Cash to Owner (₹)", "Status"
        ]
        self.table_dossier_jobs.setColumnCount(len(headers))
        self.table_dossier_jobs.setHorizontalHeaderLabels(headers)

        self.table_dossier_jobs.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        th = self.table_dossier_jobs.horizontalHeader()
        th.setStretchLastSection(False)
        th.setHighlightSections(False)
        th.setMinimumSectionSize(80)

        dossier_col_widths = [
            95,   # 0: Date
            140,  # 1: Customer Name
            115,  # 2: Mobile Number
            240,  # 3: Site / Job Address
            250,  # 4: Work / Parts Details
            100,  # 5: Billed (₹)
            95,   # 6: Advance (₹)
            110,  # 7: Adv To
            95,   # 8: Final (₹)
            100,  # 9: Material Cost (₹)
            85,   # 10: Petrol (₹)
            105,  # 11: Total Cost (₹)
            120,  # 12: Net Cash to Owner (₹)
            100,  # 13: Status
        ]
        for idx, w in enumerate(dossier_col_widths):
            self.table_dossier_jobs.setColumnWidth(idx, w)
        th.setSectionResizeMode(QHeaderView.Interactive)

        self.table_dossier_jobs.setStyleSheet(f"""
            QTableWidget {{
                background-color: {colors['card_bg']};
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                gridline-color: #E2E8F0;
                selection-background-color: #EFF6FF;
                selection-color: {colors['fg']};
            }}
            QHeaderView::section {{
                background-color: #F8FAFC;
                color: #334155;
                font-weight: 700;
                font-size: 8.5pt;
                padding: 8px 6px;
                border-top: none;
                border-left: none;
                border-right: 1px solid #CBD5E1;
                border-bottom: 2px solid #94A3B8;
            }}
            QTableWidget::item {{
                padding: 6px 8px;
                border-bottom: 1px solid #E2E8F0;
                border-right: 1px solid #E2E8F0;
                font-size: 8.5pt;
            }}
            QTableWidget::item:selected {{
                background-color: #EFF6FF;
                color: #0F172A;
            }}
        """)
        layout.addWidget(self.table_dossier_jobs, stretch=1)

    def _populate_dossier_technicians(self):
        try:
            with DatabaseContext() as db:
                ctrl = DailyLogController(db)
                techs = ctrl.get_all_technicians_list()
                self.dossier_combo_tech.clear()
                for t in techs:
                    self.dossier_combo_tech.addItem(t['name'], t['id'])
        except Exception:
            pass

    def _load_tech_dossier_data(self):
        tech_id = self.dossier_combo_tech.currentData()
        tech_name = self.dossier_combo_tech.currentText().strip()
        start_date = self.dossier_date_from.date().toString("yyyy-MM-dd")
        end_date = self.dossier_date_to.date().toString("yyyy-MM-dd")

        try:
            with DatabaseContext() as db:
                ctrl = DailyLogController(db)
                dossier = ctrl.get_technician_dossier(
                    technician_name=tech_name,
                    technician_id=tech_id,
                    start_date=start_date,
                    end_date=end_date
                )

            sym = self.currency_symbol

            d_jobs = f"{dossier['total_jobs']} visits"
            d_sites = f"📍 {dossier['unique_sites']} unique sites"
            self.dossier_metric_labels['jobs'][0].setText(d_jobs)
            self.dossier_metric_labels['jobs'][1].setText(d_sites)

            self.dossier_metric_labels['advance'][0].setText(f"{sym}{dossier['total_advance']:,.2f}")
            self.dossier_metric_labels['cash'][0].setText(f"{sym}{dossier['cash_collected']:,.2f}")
            self.dossier_metric_labels['material'][0].setText(f"{sym}{dossier['total_material']:,.2f}")
            self.dossier_metric_labels['petrol'][0].setText(f"{sym}{dossier['total_petrol']:,.2f}")

            net_amt = dossier['net_handover_to_seth']
            self.dossier_metric_labels['net'][0].setText(f"{sym}{net_amt:,.2f}")
            self.dossier_metric_labels['net'][0].setStyleSheet(f"font-size: 11pt; font-weight: 800; color: {'#16a34a' if net_amt >= 0 else '#dc2626'};")

            jobs = dossier['jobs']
            self.table_dossier_jobs.setRowCount(0)
            self.table_dossier_jobs.setRowCount(len(jobs))

            for row_idx, j in enumerate(jobs):
                b = float(j.get('total_billed', 0) or j.get('total_payment', 0) or 0)
                adv = float(j.get('advance_payment', 0) or 0)
                fin = float(j.get('final_payment', 0) or 0)
                mat = float(j.get('material_cost', 0) or 0)
                pet = float(j.get('petrol_expense', 0) or 0)
                exp = float(j.get('total_expense', 0) or (mat + pet))

                adv_to = str(j.get('advance_receiver', 'Tech (Cash)') or '')
                fin_to = str(j.get('final_receiver', 'Tech (Cash)') or '')
                job_cash = 0.0
                if "Tech" in adv_to or "Cash" in adv_to:
                    job_cash += adv
                if "Tech" in fin_to or "Cash" in fin_to:
                    job_cash += fin
                job_net_handover = job_cash - exp

                date_raw = j.get('log_date')
                date_str = Formatters.format_date(date_raw) if date_raw else ''
                date_item = QTableWidgetItem(date_str)
                date_item.setTextAlignment(Qt.AlignCenter)
                date_item.setFont(QFont("Segoe UI", 8, QFont.Bold))
                self.table_dossier_jobs.setItem(row_idx, 0, date_item)

                cust_name = str(j.get('customer_name', '') or '')
                c_item = QTableWidgetItem(cust_name)
                c_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                c_item.setFont(QFont("Segoe UI", 8.5, QFont.Bold))
                c_item.setToolTip(f"Customer:\n{cust_name}")
                self.table_dossier_jobs.setItem(row_idx, 1, c_item)

                mob_raw = str(j.get('customer_mobile', '') or '')
                mob_item = QTableWidgetItem(Formatters.format_mobile(mob_raw) if mob_raw else '')
                mob_item.setTextAlignment(Qt.AlignCenter)
                self.table_dossier_jobs.setItem(row_idx, 2, mob_item)

                addr = str(j.get('customer_address', '') or '')
                addr_item = QTableWidgetItem(addr)
                addr_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                addr_item.setToolTip(f"Site / Job Address:\n{addr}")
                self.table_dossier_jobs.setItem(row_idx, 3, addr_item)

                work = str(j.get('work_description', '') or '')
                work_item = QTableWidgetItem(work)
                work_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                work_item.setToolTip(f"Work Performed & Parts:\n{work}")
                self.table_dossier_jobs.setItem(row_idx, 4, work_item)

                item_b = QTableWidgetItem(f"{sym}{b:,.2f}")
                item_b.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table_dossier_jobs.setItem(row_idx, 5, item_b)

                item_adv = QTableWidgetItem(f"{sym}{adv:,.2f}")
                item_adv.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table_dossier_jobs.setItem(row_idx, 6, item_adv)

                adv_item = QTableWidgetItem(adv_to)
                adv_item.setTextAlignment(Qt.AlignCenter)
                self.table_dossier_jobs.setItem(row_idx, 7, adv_item)

                item_fin = QTableWidgetItem(f"{sym}{fin:,.2f}")
                item_fin.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table_dossier_jobs.setItem(row_idx, 8, item_fin)

                item_mat = QTableWidgetItem(f"{sym}{mat:,.2f}")
                item_mat.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table_dossier_jobs.setItem(row_idx, 9, item_mat)

                item_pet = QTableWidgetItem(f"{sym}{pet:,.2f}")
                item_pet.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table_dossier_jobs.setItem(row_idx, 10, item_pet)

                item_exp = QTableWidgetItem(f"{sym}{exp:,.2f}")
                item_exp.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item_exp.setForeground(QColor("#dc2626"))
                self.table_dossier_jobs.setItem(row_idx, 11, item_exp)

                item_due = QTableWidgetItem(f"{sym}{job_net_handover:,.2f}")
                item_due.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item_due.setFont(QFont("Segoe UI", 9, QFont.Bold))
                if job_net_handover >= 0:
                    item_due.setForeground(QColor("#16a34a"))
                else:
                    item_due.setForeground(QColor("#dc2626"))
                self.table_dossier_jobs.setItem(row_idx, 12, item_due)

                status_raw = str(j.get('payment_status', 'Paid') or 'Paid').strip().capitalize()
                status_item = QTableWidgetItem(status_raw)
                status_item.setTextAlignment(Qt.AlignCenter)
                status_item.setFont(QFont("Segoe UI", 8.5, QFont.Bold))
                if status_raw == 'Paid':
                    status_item.setForeground(QColor("#059669"))
                elif status_raw == 'Pending':
                    status_item.setForeground(QColor("#dc2626"))
                else:
                    status_item.setForeground(QColor("#d97706"))
                self.table_dossier_jobs.setItem(row_idx, 13, status_item)

        except Exception as e:
            QMessageBox.critical(self, "Dossier Error", f"Failed to load technician dossier: {e}")

    # ═════════════════════════════════════════════════════════════════════════
    # PAGE 3: FULL-PAGE CUSTOMER MULTI-VISIT HISTORY & LEDGER
    # ═════════════════════════════════════════════════════════════════════════
    def _build_cust_history_page(self, container: QWidget):
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)
        colors = self.theme_manager.get_colors()

        # Top Bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        self.btn_back_from_cust = QPushButton("⬅️ Back to Daily Logs")
        self.btn_back_from_cust.setCursor(Qt.PointingHandCursor)
        self.btn_back_from_cust.setFixedHeight(38)
        self.btn_back_from_cust.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['hover']};
                color: {colors['primary']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                padding: 0 16px;
                font-weight: 700;
                font-size: 9pt;
            }}
            QPushButton:hover {{
                background-color: {colors['primary']}15;
                border-color: {colors['primary']};
            }}
        """)
        self.btn_back_from_cust.clicked.connect(self._go_to_register)
        top_bar.addWidget(self.btn_back_from_cust)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = QLabel("👤 Customer Service History & Multi-Visit Ledger")
        title_lbl.setStyleSheet(f"font-size: 15pt; font-weight: 800; color: {colors['fg']};")
        sub_lbl = QLabel("Track all visits done for a specific customer, assigned technicians, advances, and pending dues")
        sub_lbl.setStyleSheet(f"font-size: 8.5pt; color: {colors['muted']};")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        top_bar.addLayout(title_box)

        layout.addLayout(top_bar)

        # Search Bar for Phone Number or Name
        search_card = QFrame()
        search_card.setStyleSheet(f"background-color: {colors['hover']}; border-radius: 8px; padding: 10px;")
        search_layout = QHBoxLayout(search_card)
        search_layout.setSpacing(12)

        lbl_s = QLabel("🔍 Search by Mobile No / Customer / Address:")
        lbl_s.setStyleSheet(f"font-weight: 700; color: {colors['fg']};")
        search_layout.addWidget(lbl_s)

        self.cust_search_txt = QLineEdit()
        self.cust_search_txt.setPlaceholderText("Enter 10-digit mobile number, customer name, or site address...")
        self.cust_search_txt.setClearButtonEnabled(True)
        self.cust_search_txt.textChanged.connect(self._load_cust_history_data)
        search_layout.addWidget(self.cust_search_txt)

        btn_find = QPushButton("Search")
        btn_find.clicked.connect(self._load_cust_history_data)
        search_layout.addWidget(btn_find)

        layout.addWidget(search_card)

        # Metric Cards (Solid cards, no ghosting)
        self.cust_metrics_frame = QFrame()
        self.cust_metrics_frame.setStyleSheet(f"background-color: {colors['hover']}; border: 1px solid {colors['border']}; border-radius: 10px; padding: 4px;")
        self.cust_metrics_layout = QHBoxLayout(self.cust_metrics_frame)
        self.cust_metrics_layout.setSpacing(10)
        self.cust_metrics_layout.setContentsMargins(6, 6, 6, 6)

        cust_kpi_defs = [
            ('visits', 'TOTAL SERVICE VISITS', '0 visits', '#2563eb'),
            ('billed', 'TOTAL BILLED', 'Total charges', '#0284c7'),
            ('advance', 'TOTAL ADVANCE PAID', 'Advance deposits', '#059669'),
            ('cleared', 'TOTAL CLEARED', 'Cleared receipts', '#16a34a'),
            ('pending', 'PENDING BALANCE', 'Outstanding balance', '#dc2626'),
        ]

        self.cust_metric_labels = {}
        for key, title, sub, col in cust_kpi_defs:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors['card_bg']};
                    border: 1px solid {colors['border']};
                    border-radius: 8px;
                    padding: 8px 10px;
                }}
            """)
            c_box = QVBoxLayout(card)
            c_box.setContentsMargins(0, 0, 0, 0)
            c_box.setSpacing(2)

            l1 = QLabel(title)
            l1.setStyleSheet("font-size: 7.5pt; color: #64748b; font-weight: 700;")

            l2 = QLabel(f"{self.currency_symbol}0")
            l2.setStyleSheet(f"font-size: 11pt; font-weight: 800; color: {col};")

            l3 = QLabel(sub)
            l3.setStyleSheet("font-size: 7pt; color: #94a3b8;")

            c_box.addWidget(l1)
            c_box.addWidget(l2)
            c_box.addWidget(l3)

            self.cust_metrics_layout.addWidget(card)
            self.cust_metric_labels[key] = (l2, l3)

        layout.addWidget(self.cust_metrics_frame)

        # Visits Table
        self.table_cust_visits = QTableWidget()
        self.table_cust_visits.setAlternatingRowColors(True)
        self.table_cust_visits.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_cust_visits.setShowGrid(True)
        self.table_cust_visits.setGridStyle(Qt.PenStyle.SolidLine)
        self.table_cust_visits.verticalHeader().setVisible(False)
        self.table_cust_visits.verticalHeader().setDefaultSectionSize(40)
        self.table_cust_visits.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        headers = [
            "Visit Date", "Customer Name", "Mobile Number", "Site / Job Address",
            "Assigned Technician", "Work & Parts Installed", "Total Billed (₹)",
            "Advance (₹)", "Final (₹)", "Total Paid (₹)", "Pending Due (₹)", "Status"
        ]
        self.table_cust_visits.setColumnCount(len(headers))
        self.table_cust_visits.setHorizontalHeaderLabels(headers)

        th = self.table_cust_visits.horizontalHeader()
        th.setStretchLastSection(False)
        th.setHighlightSections(False)
        th.setMinimumSectionSize(80)

        col_widths = [
            105,  # 0: Visit Date
            145,  # 1: Customer Name
            115,  # 2: Mobile Number
            250,  # 3: Site / Job Address
            140,  # 4: Assigned Technician
            260,  # 5: Work & Parts Installed
            105,  # 6: Total Billed (₹)
            95,   # 7: Advance (₹)
            95,   # 8: Final (₹)
            105,  # 9: Total Paid (₹)
            105,  # 10: Pending Due (₹)
            105,  # 11: Status
        ]
        for idx, w in enumerate(col_widths):
            self.table_cust_visits.setColumnWidth(idx, w)
        th.setSectionResizeMode(QHeaderView.Interactive)

        self.table_cust_visits.setStyleSheet(f"""
            QTableWidget {{
                background-color: {colors['card_bg']};
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                gridline-color: #E2E8F0;
                selection-background-color: #EFF6FF;
                selection-color: {colors['fg']};
            }}
            QHeaderView::section {{
                background-color: #F8FAFC;
                color: #334155;
                font-weight: 700;
                font-size: 8.5pt;
                padding: 8px 6px;
                border-top: none;
                border-left: none;
                border-right: 1px solid #CBD5E1;
                border-bottom: 2px solid #94A3B8;
            }}
            QTableWidget::item {{
                padding: 6px 8px;
                border-bottom: 1px solid #E2E8F0;
                border-right: 1px solid #E2E8F0;
                font-size: 8.5pt;
            }}
            QTableWidget::item:selected {{
                background-color: #EFF6FF;
                color: #0F172A;
            }}
        """)
        layout.addWidget(self.table_cust_visits, stretch=1)

    def _load_cust_history_data(self):
        query = self.cust_search_txt.text().strip()
        try:
            with DatabaseContext() as db:
                ctrl = DailyLogController(db)
                dossier = ctrl.get_customer_dossier(customer_query=query)

            sym = self.currency_symbol

            visits_cnt = dossier['total_visits']
            visits_str = f"Visited {visits_cnt} Times" if visits_cnt > 0 else "0 Visits"
            tech_desc = f"👨‍🔧 {dossier['distinct_techs']} distinct technicians assigned"
            self.cust_metric_labels['visits'][0].setText(visits_str)
            self.cust_metric_labels['visits'][1].setText(tech_desc)

            self.cust_metric_labels['billed'][0].setText(f"{sym}{dossier['total_billed']:,.2f}")
            self.cust_metric_labels['advance'][0].setText(f"{sym}{dossier['total_advance']:,.2f}")
            self.cust_metric_labels['cleared'][0].setText(f"{sym}{dossier['total_paid']:,.2f}")

            pend = dossier['pending_balance']
            self.cust_metric_labels['pending'][0].setText(f"{sym}{pend:,.2f}")
            self.cust_metric_labels['pending'][0].setStyleSheet(f"font-size: 11pt; font-weight: 800; color: {'#dc2626' if pend > 0 else '#64748b'};")

            visits = dossier['visits']
            self.table_cust_visits.setRowCount(0)
            self.table_cust_visits.setRowCount(len(visits))

            for row_idx, v in enumerate(visits):
                b = float(v.get('total_billed', 0) or v.get('total_payment', 0) or 0)
                adv = float(v.get('advance_payment', 0) or 0)
                fin = float(v.get('final_payment', 0) or 0)
                paid = float(v.get('total_payment', 0) or 0)
                pend = float(v.get('pending_amount', 0) or max(0.0, b - paid))

                date_raw = v.get('log_date')
                date_str = Formatters.format_date(date_raw) if date_raw else ''
                date_item = QTableWidgetItem(date_str)
                date_item.setTextAlignment(Qt.AlignCenter)
                date_item.setFont(QFont("Segoe UI", 8, QFont.Bold))
                self.table_cust_visits.setItem(row_idx, 0, date_item)

                cust_name = str(v.get('customer_name', '') or '')
                c_item = QTableWidgetItem(cust_name)
                c_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                c_item.setFont(QFont("Segoe UI", 8.5, QFont.Bold))
                c_item.setToolTip(f"Customer:\n{cust_name}")
                self.table_cust_visits.setItem(row_idx, 1, c_item)

                mob_raw = str(v.get('customer_mobile', '') or '')
                mob_item = QTableWidgetItem(Formatters.format_mobile(mob_raw) if mob_raw else '')
                mob_item.setTextAlignment(Qt.AlignCenter)
                self.table_cust_visits.setItem(row_idx, 2, mob_item)

                addr = str(v.get('customer_address', '') or '')
                addr_item = QTableWidgetItem(addr)
                addr_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                addr_item.setToolTip(f"Job / Site Address:\n{addr}")
                self.table_cust_visits.setItem(row_idx, 3, addr_item)

                tech_name = str(v.get('technician_name', '') or '')
                tech_item = QTableWidgetItem(tech_name)
                tech_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                tech_item.setFont(QFont("Segoe UI", 8.5, QFont.Bold))
                tech_item.setToolTip(f"Technician:\n{tech_name}")
                self.table_cust_visits.setItem(row_idx, 4, tech_item)

                work = str(v.get('work_description', '') or '')
                work_item = QTableWidgetItem(work)
                work_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                work_item.setToolTip(f"Work & Parts Installed:\n{work}")
                self.table_cust_visits.setItem(row_idx, 5, work_item)

                item_b = QTableWidgetItem(f"{sym}{b:,.2f}")
                item_b.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table_cust_visits.setItem(row_idx, 6, item_b)

                item_adv = QTableWidgetItem(f"{sym}{adv:,.2f}")
                item_adv.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table_cust_visits.setItem(row_idx, 7, item_adv)

                item_fin = QTableWidgetItem(f"{sym}{fin:,.2f}")
                item_fin.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table_cust_visits.setItem(row_idx, 8, item_fin)

                item_paid = QTableWidgetItem(f"{sym}{paid:,.2f}")
                item_paid.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item_paid.setForeground(QColor("#059669"))
                item_paid.setFont(QFont("Segoe UI", 8.5, QFont.Bold))
                self.table_cust_visits.setItem(row_idx, 9, item_paid)

                item_pend = QTableWidgetItem(f"{sym}{pend:,.2f}")
                item_pend.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if pend > 0:
                    item_pend.setForeground(QColor("#dc2626"))
                    item_pend.setFont(QFont("Segoe UI", 8.5, QFont.Bold))
                self.table_cust_visits.setItem(row_idx, 10, item_pend)

                status_raw = str(v.get('payment_status', 'Paid') or 'Paid').strip().capitalize()
                status_item = QTableWidgetItem(status_raw)
                status_item.setTextAlignment(Qt.AlignCenter)
                status_item.setFont(QFont("Segoe UI", 8.5, QFont.Bold))
                if status_raw == 'Paid':
                    status_item.setForeground(QColor("#059669"))
                elif status_raw == 'Pending':
                    status_item.setForeground(QColor("#dc2626"))
                else:
                    status_item.setForeground(QColor("#d97706"))
                self.table_cust_visits.setItem(row_idx, 11, status_item)

        except Exception as e:
            QMessageBox.critical(self, "Customer Ledger Error", f"Failed to load customer records: {e}")

    # ═════════════════════════════════════════════════════════════════════════
    # NAVIGATION METHODS (SEAMLESS FULL-PAGE SWITCHING WITH BACK BUTTONS)
    # ═════════════════════════════════════════════════════════════════════════
    def _go_to_register(self):
        self.stack.setCurrentIndex(0)
        self.load_data()

    def _go_to_month_settlement(self):
        self._load_settlement_data()
        self.stack.setCurrentIndex(1)

    def _go_to_tech_dossier(self, default_tech_name=None):
        self._populate_dossier_technicians()
        if default_tech_name:
            idx = self.dossier_combo_tech.findText(default_tech_name)
            if idx >= 0:
                self.dossier_combo_tech.setCurrentIndex(idx)
        self._load_tech_dossier_data()
        self.stack.setCurrentIndex(2)

    def _go_to_customer_history(self, search_query=None):
        if search_query:
            self.cust_search_txt.setText(str(search_query))
        self._load_cust_history_data()
        self.stack.setCurrentIndex(3)


# ─────────────────────────────────────────────────────────────────────────────
# LOG ADD / EDIT DIALOG (ADVANCE PAYMENT SUPPORT + AUTO-CALCULATION)
# ─────────────────────────────────────────────────────────────────────────────
class LogDialog(QDialog):
    """Dialog to Add or Edit Daily Work, Advance, and Expense Entries"""

    def __init__(self, log_data=None, parent=None):
        super().__init__(parent)
        self.log_data = log_data
        self.theme_manager = UnifiedTheme()
        self.currency_symbol = get_setting('currency_symbol', '₹')
        self.customer_list = []

        self.setWindowTitle("Edit Daily Work Log" if log_data else "New Daily Work & Cost Entry")
        self.setMinimumWidth(680)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.theme_manager.get_colors()['card_bg']};
                color: {self.theme_manager.get_colors()['fg']};
            }}
            QLineEdit, QComboBox, QTextEdit, QDoubleSpinBox, QDateEdit {{
                background-color: {self.theme_manager.get_colors()['bg']};
                color: {self.theme_manager.get_colors()['fg']};
                border: 1px solid {self.theme_manager.get_colors()['border']};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 9pt;
            }}
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDoubleSpinBox:focus, QDateEdit:focus {{
                border-color: {self.theme_manager.get_colors()['primary']};
            }}
            QLabel {{
                font-weight: 600;
                font-size: 9pt;
            }}
        """)

        self._init_ui()
        self._load_customers_for_autocomplete()
        if log_data:
            self._populate_fields(log_data)
        else:
            self._recalculate()

    def _init_ui(self):
        colors = self.theme_manager.get_colors()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title_lbl = QLabel("📋 Work, Advance & Expense Entry Details")
        title_lbl.setStyleSheet(f"font-size: 13pt; font-weight: 800; color: {colors['primary']};")
        layout.addWidget(title_lbl)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(14)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Section 1: Date & Customer Details
        sec1 = QFrame()
        sec1.setStyleSheet(f"background-color: {colors['hover']}; border-radius: 8px; padding: 10px;")
        sec1_layout = QFormLayout(sec1)
        sec1_layout.setSpacing(8)

        date_row = QHBoxLayout()
        self.edit_date = QDateEdit()
        self.edit_date.setCalendarPopup(True)
        self.edit_date.setDisplayFormat("dd-MM-yyyy")
        self.edit_date.setDate(QDate.currentDate())
        date_row.addWidget(self.edit_date)

        btn_today = QPushButton("Today")
        btn_today.setFixedWidth(60)
        btn_today.setCursor(Qt.PointingHandCursor)
        btn_today.clicked.connect(lambda: self.edit_date.setDate(QDate.currentDate()))
        date_row.addWidget(btn_today)
        sec1_layout.addRow("Service / Visit Date *:", date_row)

        self.txt_customer_name = QLineEdit()
        self.txt_customer_name.setPlaceholderText("Customer or Business Name")
        sec1_layout.addRow("Customer Name *:", self.txt_customer_name)

        self.txt_customer_mobile = QLineEdit()
        self.txt_customer_mobile.setPlaceholderText("10-digit mobile number")
        sec1_layout.addRow("Customer Mobile:", self.txt_customer_mobile)

        self.txt_customer_address = QLineEdit()
        self.txt_customer_address.setPlaceholderText("Site Address / Flat / Society / Area")
        sec1_layout.addRow("Site / Work Address:", self.txt_customer_address)

        content_layout.addWidget(sec1)

        # Section 2: Technician & Work Description
        sec2 = QFrame()
        sec2.setStyleSheet(f"background-color: {colors['hover']}; border-radius: 8px; padding: 10px;")
        sec2_layout = QFormLayout(sec2)
        sec2_layout.setSpacing(8)

        self.combo_tech = QComboBox()
        self.combo_tech.setEditable(True)
        self.combo_tech.addItem("-- Select or Type Technician --", None)
        self._populate_technicians()
        sec2_layout.addRow("Assigned Technician:", self.combo_tech)

        self.txt_work = QTextEdit()
        self.txt_work.setPlaceholderText("e.g. Copper Piping 10ft, Gas Charging R32, PCB Repair, Capacitor 45uF replacement")
        self.txt_work.setFixedHeight(60)
        sec2_layout.addRow("Work & Parts Detail:", self.txt_work)

        content_layout.addWidget(sec2)

        # Section 3: Advance & Payment Tracking
        sec3 = QFrame()
        sec3.setStyleSheet(f"background-color: {colors['hover']}; border-radius: 8px; padding: 10px;")
        sec3_layout = QFormLayout(sec3)
        sec3_layout.setSpacing(8)

        self.spin_billed = QDoubleSpinBox()
        self.spin_billed.setRange(0, 9999999)
        self.spin_billed.setPrefix(f"{self.currency_symbol} ")
        self.spin_billed.setDecimals(2)
        self.spin_billed.valueChanged.connect(self._recalculate)
        sec3_layout.addRow("Total Agreed Charge / Bill (₹):", self.spin_billed)

        adv_row = QHBoxLayout()
        self.spin_advance = QDoubleSpinBox()
        self.spin_advance.setRange(0, 9999999)
        self.spin_advance.setPrefix(f"{self.currency_symbol} ")
        self.spin_advance.setDecimals(2)
        self.spin_advance.valueChanged.connect(self._recalculate)
        adv_row.addWidget(self.spin_advance)

        self.combo_adv_receiver = QComboBox()
        self.combo_adv_receiver.addItems(["Tech (Cash)", "Tech (UPI)", "Direct Seth (UPI/Bank)"])
        adv_row.addWidget(self.combo_adv_receiver)
        sec3_layout.addRow("Advance Collected (₹):", adv_row)

        final_row = QHBoxLayout()
        self.spin_final = QDoubleSpinBox()
        self.spin_final.setRange(0, 9999999)
        self.spin_final.setPrefix(f"{self.currency_symbol} ")
        self.spin_final.setDecimals(2)
        self.spin_final.valueChanged.connect(self._recalculate)
        final_row.addWidget(self.spin_final)

        self.combo_final_receiver = QComboBox()
        self.combo_final_receiver.addItems(["Tech (Cash)", "Tech (UPI)", "Direct Seth (UPI/Bank)", "Pending"])
        final_row.addWidget(self.combo_final_receiver)
        sec3_layout.addRow("Final Payment Collected (₹):", final_row)

        pay_mode_row = QHBoxLayout()
        self.combo_pay_mode = QComboBox()
        self.combo_pay_mode.addItems(["Cash", "UPI / GPay / PhonePe", "Bank Transfer (NEFT/IMPS)", "Cheque", "Card"])
        pay_mode_row.addWidget(self.combo_pay_mode)

        self.combo_status = QComboBox()
        self.combo_status.addItems(["Auto-Detect", "Paid", "Partial (Advance Paid)", "Pending"])
        pay_mode_row.addWidget(self.combo_status)
        sec3_layout.addRow("Payment Mode & Status:", pay_mode_row)

        content_layout.addWidget(sec3)

        # Section 4: Expenses & Live Calculation
        sec4 = QFrame()
        sec4.setStyleSheet(f"background-color: {colors['hover']}; border-radius: 8px; padding: 10px;")
        sec4_layout = QFormLayout(sec4)
        sec4_layout.setSpacing(8)

        self.spin_material = QDoubleSpinBox()
        self.spin_material.setRange(0, 9999999)
        self.spin_material.setPrefix(f"{self.currency_symbol} ")
        self.spin_material.setDecimals(2)
        self.spin_material.valueChanged.connect(self._recalculate)
        sec4_layout.addRow("Material Purchase Expense (₹):", self.spin_material)

        self.spin_petrol = QDoubleSpinBox()
        self.spin_petrol.setRange(0, 9999999)
        self.spin_petrol.setPrefix(f"{self.currency_symbol} ")
        self.spin_petrol.setDecimals(2)
        self.spin_petrol.valueChanged.connect(self._recalculate)
        sec4_layout.addRow("Petrol / Travel Expense (₹):", self.spin_petrol)

        calc_box = QFrame()
        calc_box.setStyleSheet(f"""
            background-color: {colors['card_bg']};
            border: 1px solid {colors['border']};
            border-radius: 8px;
            padding: 8px;
        """)
        calc_layout = QHBoxLayout(calc_box)

        self.lbl_calc_received = QLabel("Total Recd: ₹0.00")
        self.lbl_calc_received.setStyleSheet("color: #059669; font-weight: 700;")
        calc_layout.addWidget(self.lbl_calc_received)

        self.lbl_calc_pending = QLabel("Pending: ₹0.00")
        self.lbl_calc_pending.setStyleSheet("color: #d97706; font-weight: 700;")
        calc_layout.addWidget(self.lbl_calc_pending)

        self.lbl_calc_expense = QLabel("Total Kharch: ₹0.00")
        self.lbl_calc_expense.setStyleSheet("color: #dc2626; font-weight: 700;")
        calc_layout.addWidget(self.lbl_calc_expense)

        self.lbl_calc_profit = QLabel("Net Profit: ₹0.00")
        self.lbl_calc_profit.setStyleSheet("color: #16a34a; font-weight: 800; font-size: 10pt;")
        calc_layout.addWidget(self.lbl_calc_profit)

        sec4_layout.addRow(calc_box)

        self.txt_notes = QLineEdit()
        self.txt_notes.setPlaceholderText("Additional notes, follow-up remarks, or itemized details")
        sec4_layout.addRow("Notes / Remarks:", self.txt_notes)

        content_layout.addWidget(sec4)

        scroll.setWidget(content_widget)
        layout.addWidget(scroll, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedWidth(100)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        self.btn_save = QPushButton("Save Entry")
        self.btn_save.setFixedWidth(140)
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['primary']};
                color: white;
                font-weight: 700;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: #1d4ed8;
            }}
        """)
        self.btn_save.clicked.connect(self._save_log)
        btn_row.addWidget(self.btn_save)

        layout.addLayout(btn_row)

    def _populate_technicians(self):
        try:
            with DatabaseContext() as db:
                ctrl = DailyLogController(db)
                techs = ctrl.get_all_technicians_list()
                for t in techs:
                    self.combo_tech.addItem(t['name'], t['id'])
        except Exception:
            pass

    def _load_customers_for_autocomplete(self):
        try:
            with DatabaseContext() as db:
                self.customer_list = db.execute_query("SELECT id, name, mobile, address FROM customers WHERE is_active = 1 ORDER BY name ASC", fetch_all=True) or []
                names = [c['name'] for c in self.customer_list if c.get('name')]
                completer = QCompleter(names, self)
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                completer.setFilterMode(Qt.MatchContains)
                completer.activated.connect(self._on_customer_selected)
                self.txt_customer_name.setCompleter(completer)
        except Exception:
            pass

    def _on_customer_selected(self, name_text):
        for c in self.customer_list:
            if c.get('name', '').lower() == name_text.lower():
                if c.get('mobile') and not self.txt_customer_mobile.text():
                    self.txt_customer_mobile.setText(c['mobile'])
                if c.get('address') and not self.txt_customer_address.text():
                    self.txt_customer_address.setText(c['address'])
                break

    def _recalculate(self):
        billed = self.spin_billed.value()
        adv = self.spin_advance.value()
        final = self.spin_final.value()
        recd = adv + final
        pending = max(0.0, billed - recd)

        mat = self.spin_material.value()
        pet = self.spin_petrol.value()
        exp = mat + pet
        profit = recd - exp

        sym = self.currency_symbol
        self.lbl_calc_received.setText(f"Total Recd: {sym}{recd:,.2f}")
        self.lbl_calc_pending.setText(f"Pending: {sym}{pending:,.2f}")
        self.lbl_calc_expense.setText(f"Total Kharch: {sym}{exp:,.2f}")
        self.lbl_calc_profit.setText(f"Net Profit: {sym}{profit:,.2f}")

    def _populate_fields(self, data: dict):
        date_str = data.get('log_date')
        if date_str:
            self.edit_date.setDate(QDate.fromString(str(date_str)[:10], "yyyy-MM-dd"))

        self.txt_customer_name.setText(str(data.get('customer_name', '') or ''))
        self.txt_customer_mobile.setText(str(data.get('customer_mobile', '') or ''))
        self.txt_customer_address.setText(str(data.get('customer_address', '') or ''))

        tech_name = data.get('technician_name', '')
        idx = self.combo_tech.findText(tech_name)
        if idx >= 0:
            self.combo_tech.setCurrentIndex(idx)
        else:
            self.combo_tech.setEditText(tech_name)

        self.txt_work.setText(str(data.get('work_description', '') or ''))

        b = float(data.get('total_billed', 0) or data.get('total_payment', 0) or 0)
        self.spin_billed.setValue(b)
        self.spin_advance.setValue(float(data.get('advance_payment', 0) or 0))
        self.spin_final.setValue(float(data.get('final_payment', 0) or 0))

        adv_rec = str(data.get('advance_receiver', 'Tech (Cash)') or 'Tech (Cash)')
        idx_ar = self.combo_adv_receiver.findText(adv_rec)
        if idx_ar >= 0:
            self.combo_adv_receiver.setCurrentIndex(idx_ar)

        fin_rec = str(data.get('final_receiver', 'Tech (Cash)') or 'Tech (Cash)')
        idx_fr = self.combo_final_receiver.findText(fin_rec)
        if idx_fr >= 0:
            self.combo_final_receiver.setCurrentIndex(idx_fr)

        self.spin_material.setValue(float(data.get('material_cost', 0) or 0))
        self.spin_petrol.setValue(float(data.get('petrol_expense', 0) or 0))

        mode = str(data.get('payment_mode', 'Cash') or 'Cash')
        idx_m = self.combo_pay_mode.findText(mode)
        if idx_m >= 0:
            self.combo_pay_mode.setCurrentIndex(idx_m)

        stat = str(data.get('payment_status', 'Paid') or 'Paid')
        idx_s = self.combo_status.findText(stat)
        if idx_s >= 0:
            self.combo_status.setCurrentIndex(idx_s)

        self.txt_notes.setText(str(data.get('notes', '') or ''))
        self._recalculate()

    def _save_log(self):
        cust_name = self.txt_customer_name.text().strip()
        if not cust_name:
            QMessageBox.warning(self, "Validation Error", "Please enter customer name.")
            self.txt_customer_name.setFocus()
            return

        tech_id = self.combo_tech.currentData()
        tech_name = self.combo_tech.currentText().strip()
        if tech_name == "-- Select or Type Technician --":
            tech_name = ""

        status_chosen = self.combo_status.currentText()
        if status_chosen == "Auto-Detect":
            status_chosen = None

        payload = {
            'log_date': self.edit_date.date().toString("yyyy-MM-dd"),
            'customer_name': cust_name,
            'customer_mobile': self.txt_customer_mobile.text().strip(),
            'customer_address': self.txt_customer_address.text().strip(),
            'technician_id': tech_id,
            'technician_name': tech_name,
            'work_description': self.txt_work.toPlainText().strip(),
            'total_billed': self.spin_billed.value(),
            'advance_payment': self.spin_advance.value(),
            'advance_receiver': self.combo_adv_receiver.currentText(),
            'final_payment': self.spin_final.value(),
            'final_receiver': self.combo_final_receiver.currentText(),
            'material_cost': self.spin_material.value(),
            'petrol_expense': self.spin_petrol.value(),
            'payment_status': status_chosen,
            'payment_mode': self.combo_pay_mode.currentText(),
            'notes': self.txt_notes.text().strip()
        }

        try:
            with DatabaseContext() as db:
                ctrl = DailyLogController(db)
                if self.log_data and self.log_data.get('id'):
                    ctrl.update_log(self.log_data['id'], payload)
                else:
                    ctrl.add_log(payload)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save daily log: {e}")
