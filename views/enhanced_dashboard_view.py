"""
Enhanced Dashboard View - PySide6 Professional Analytics Dashboard
Modern SaaS-style dashboard with clickable metrics, detailed views, search/filter
Features:
- Clickable metric cards with detailed data views
- Search and filter functionality
- Modern hover effects and animations
- Back navigation to dashboard
"""
from utils.app_settings import get_setting
from utils.formatters import Formatters
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea,
    QSizePolicy, QSpacerItem, QGraphicsDropShadowEffect, QMenu, QMessageBox,
    QDialog, QLineEdit, QGridLayout, QSplitter, QTabWidget, QTextEdit,
    QDateEdit, QDoubleSpinBox, QSpinBox, QProgressBar
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor, QCursor, QPainter, QBrush, QPen, QIcon
from datetime import datetime, timedelta
from decimal import Decimal

from utils.unified_theme import UnifiedTheme
from views.base_window import BaseView, MetricCard
from utils.chart_widgets import BarChartWidget, PieChartWidget, HorizontalBarChartWidget
import os

CHEVRON_ICON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "icons", "chevron_down.png"
).replace("\\", "/")







class DetailViewDialog(QDialog):
    """Detailed view dialog for each metric with search/filter"""
    
    def __init__(self, parent, metric_type, data, period='this_week'):
        super().__init__(parent)
        self.metric_type = metric_type
        self.data = data
        self.period = period  # Store current dashboard period
        self.theme_manager = UnifiedTheme()
        self.colors = self.theme_manager.get_colors()
        
        self.setWindowTitle(f"{metric_type} - Detailed View ({period.replace('_', ' ').title()})")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)
        
        self._setup_ui()
        self.load_data()
        
    def _setup_ui(self):
        """Setup dialog UI"""

        self.currency_symbol = get_setting("currency_symbol", "₹")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header with back button and title
        self._create_header(layout)
        
        # Search and filter controls
        self._create_controls(layout)
        
        # Data table
        self._create_table(layout)
        
        # Status bar with count
        self._create_status_bar(layout)
        
    def _create_header(self, layout):
        """Create header with back navigation"""
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Back button
        back_btn = QPushButton("← Back to Dashboard")
        back_btn.setObjectName("primaryButton")
        back_btn.setFixedWidth(180)
        back_btn.clicked.connect(self.close)
        header_layout.addWidget(back_btn)
        
        # Title
        title_label = QLabel(f"📊 {self.metric_type} Details")
        title_label.setStyleSheet(f"""
            font-size: 18pt;
            font-weight: bold;
            color: {self.colors['fg']};
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        layout.addWidget(header_frame)
        
    def _create_controls(self, layout):
        """Create search and filter controls"""
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(0, 0, 0, 0)

        # Search
        search_label = QLabel("🔍 Search:")
        search_label.setStyleSheet(f"font-weight: bold; color: {self.colors['fg']};")
        control_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to search...")
        self.search_input.setMinimumWidth(300)
        self.search_input.textChanged.connect(self.filter_data)
        # Prevent Enter key from closing dialog
        self.search_input.setClearButtonEnabled(True)
        control_layout.addWidget(self.search_input)

        control_layout.addStretch()
        
        # Export button
        export_btn = QPushButton("📤 Export")
        export_btn.setObjectName("successButton")
        export_btn.clicked.connect(self.export_data)
        control_layout.addWidget(export_btn)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setObjectName("primaryButton")
        refresh_btn.clicked.connect(self.load_data)
        control_layout.addWidget(refresh_btn)
        
        layout.addWidget(control_frame)
        
    def _create_table(self, layout):
        """Create data table"""
        c = self.colors
        self.table = QTableWidget()
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {c['card_bg']};
                color: {c['fg']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                gridline-color: {c['border']};
            }}
            QTableWidget::item {{
                padding: 10px;
            }}
            QTableWidget::item:selected {{
                background-color: {c['primary']};
            }}
            QHeaderView::section {{
                background-color: {c['hover']};
                color: {c['fg']};
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 11pt;
            }}
        """)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        # Enable double-click to view details
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        self.table.cellDoubleClicked.connect(self._show_row_details)

        layout.addWidget(self.table)
        
    def _create_status_bar(self, layout):
        """Create status bar with count"""
        c = self.colors
        self.status_label = QLabel("Loading...")
        self.status_label.setStyleSheet(f"""
            font-size: 11pt;
            color: {c['muted']};
            padding: 10px;
            background-color: {c['card_bg']};
            border-radius: 6px;
        """)
        layout.addWidget(self.status_label)
        
    def load_data(self):
        """Load data based on metric type"""
        try:
            if self.metric_type == "Total Customers":
                self._load_customers()
            elif self.metric_type == "Total Services":
                self._load_services()
            elif self.metric_type == "Total Revenue":
                self._load_revenue()
            elif self.metric_type == "Active AMC":
                self._load_amc()
            elif self.metric_type == "Online Requests":
                self._load_online_requests()
            elif self.metric_type == "Total Invoices":
                self._load_services()
            elif self.metric_type == "Pending Payments":
                self._load_pending_payments()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}")
            
    def _load_customers(self):
        """Load customer data"""
        from database.db_connection import DatabaseContext
        
        with DatabaseContext() as db:
            query = """
                SELECT id, name, mobile, address, email, created_at
                FROM customers
                WHERE is_active = TRUE
                ORDER BY created_at DESC
            """
            customers = db.execute_query(query, fetch_all=True)
        
        # Setup table
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['ID', 'Name', 'Mobile', 'Address', 'Email', 'Created Date'])
        self.table.setRowCount(len(customers))
        
        for row, customer in enumerate(customers):
            self.table.setItem(row, 0, QTableWidgetItem(str(customer['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(customer['name'] or 'N/A'))
            self.table.setItem(row, 2, QTableWidgetItem(customer['mobile'] or 'N/A'))
            self.table.setItem(row, 3, QTableWidgetItem(customer['address'] or 'N/A'))
            self.table.setItem(row, 4, QTableWidgetItem(customer['email'] or 'N/A'))
            created_date = Formatters.format_date(customer.get('created_at')) or 'N/A'
            self.table.setItem(row, 5, QTableWidgetItem(created_date))
            
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        self.all_data = customers
        self.status_label.setText(f"Total Customers: {len(customers)}")
        
    def _get_date_range(self):
        """Calculate date range based on period"""
        today = datetime.now().date()
        
        if self.period == 'today':
            return today, today
        elif self.period == 'this_week':
            start = today - timedelta(days=today.weekday())  # Monday
            return start, today
        elif self.period == 'this_month':
            start = today.replace(day=1)
            return start, today
        else:  # this_year
            start = today.replace(month=1, day=1)
            return start, today
        
    def _load_services(self):
        """Load service/invoice data filtered by period"""
        from database.db_connection import DatabaseContext
        
        start_date, end_date = self._get_date_range()
        
        with DatabaseContext() as db:
            query = """
                SELECT i.id, i.invoice_number, c.name as customer_name,
                       s.service_name, i.total_amount, i.created_at
                FROM invoices i
                JOIN customers c ON i.customer_id = c.id
                JOIN invoice_items ii ON i.id = ii.invoice_id
                JOIN services s ON ii.service_id = s.id
                WHERE i.is_active = TRUE AND DATE(i.created_at) BETWEEN %s AND %s
                ORDER BY i.created_at DESC
                LIMIT 100
            """
            services = db.execute_query(query, (start_date, end_date), fetch_all=True)

        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['ID', 'Invoice No', 'Customer', 'Service', 'Amount', 'Date'])
        self.table.setRowCount(len(services))

        for row, service in enumerate(services):
            self.table.setItem(row, 0, QTableWidgetItem(str(service['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(service['invoice_number'] or 'N/A'))
            self.table.setItem(row, 2, QTableWidgetItem(service['customer_name'] or 'N/A'))
            self.table.setItem(row, 3, QTableWidgetItem(service['service_name'] or 'N/A'))
            self.table.setItem(row, 4, QTableWidgetItem(f"{self.currency_symbol}{service['total_amount']:,.2f}"))
            date_str = Formatters.format_datetime(service.get('created_at'), '%d-%m-%Y %H:%M') or 'N/A'
            self.table.setItem(row, 5, QTableWidgetItem(date_str))

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.all_data = services
        self.status_label.setText(f"Total Services: {len(services)} ({self.period.replace('_', ' ').title()})")
        
    def _load_revenue(self):
        """Load revenue/invoice data filtered by period"""
        from database.db_connection import DatabaseContext
        
        start_date, end_date = self._get_date_range()
        
        with DatabaseContext() as db:
            query = """
                SELECT i.invoice_number, c.name as customer_name,
                       i.total_amount, i.advance_payment, i.balance_amount,
                       i.created_at, i.payment_status
                FROM invoices i
                JOIN customers c ON i.customer_id = c.id
                WHERE i.is_active = TRUE AND DATE(i.created_at) BETWEEN %s AND %s
                ORDER BY i.created_at DESC
                LIMIT 100
            """
            revenues = db.execute_query(query, (start_date, end_date), fetch_all=True)

        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(['Invoice No', 'Customer', 'Total Amount', 'Paid', 'Balance', 'Status', 'Date'])
        self.table.setRowCount(len(revenues))

        for row, rev in enumerate(revenues):
            self.table.setItem(row, 0, QTableWidgetItem(rev['invoice_number'] or 'N/A'))
            self.table.setItem(row, 1, QTableWidgetItem(rev['customer_name'] or 'N/A'))
            self.table.setItem(row, 2, QTableWidgetItem(f"{self.currency_symbol}{rev['total_amount']:,.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{self.currency_symbol}{rev['advance_payment']:,.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{self.currency_symbol}{rev['balance_amount']:,.2f}"))
            status = rev['payment_status'] or 'Pending'
            self.table.setItem(row, 5, QTableWidgetItem(status))
            date_str = Formatters.format_date(rev.get('created_at')) or 'N/A'
            self.table.setItem(row, 6, QTableWidgetItem(date_str))

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self.all_data = revenues
        total_revenue = sum(r['total_amount'] for r in revenues)
        self.status_label.setText(f"Total Revenue: {self.currency_symbol}{total_revenue:,.2f} | Records: {len(revenues)} ({self.period.replace('_', ' ').title()})")

    def _load_amc(self):
        """Load AMC contract data"""
        from database.db_connection import DatabaseContext
        
        with DatabaseContext() as db:
            query = """
                SELECT ac.amc_id, c.name as customer_name, ac.contract_type,
                       ac.amc_status, ac.total_amount as amc_amount, ac.start_date, ac.end_date,
                       ac.services_per_year as total_visits, ac.services_per_year as visits_completed
                FROM amc_contracts ac
                JOIN customers c ON ac.customer_id = c.id
                WHERE ac.is_active = TRUE
                ORDER BY ac.created_at DESC
            """
            amc_data = db.execute_query(query, fetch_all=True)

        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(['AMC ID', 'Customer', 'Type', 'Status', 'Amount', 'Start Date', 'End Date', 'Visits', 'Progress'])
        self.table.setRowCount(len(amc_data) if amc_data else 0)

        for row, amc in enumerate(amc_data or []):
            self.table.setItem(row, 0, QTableWidgetItem(amc['amc_id'] or 'N/A'))
            self.table.setItem(row, 1, QTableWidgetItem(amc['customer_name'] or 'N/A'))
            self.table.setItem(row, 2, QTableWidgetItem(amc['contract_type'] or 'N/A'))
            status = amc['amc_status'] or 'Active'
            self.table.setItem(row, 3, QTableWidgetItem(status))
            self.table.setItem(row, 4, QTableWidgetItem(f"{self.currency_symbol}{amc['amc_amount']:,.2f}"))
            start_date = Formatters.format_date(amc.get('start_date')) or 'N/A'
            end_date = Formatters.format_date(amc.get('end_date')) or 'N/A'
            self.table.setItem(row, 5, QTableWidgetItem(start_date))
            self.table.setItem(row, 6, QTableWidgetItem(end_date))
            visits = f"{amc['visits_completed'] or 0}/{amc['total_visits'] or 0}"
            self.table.setItem(row, 7, QTableWidgetItem(visits))
            progress = f"{int((amc['visits_completed'] or 0) / max(amc['total_visits'] or 1, 1) * 100)}%"
            self.table.setItem(row, 8, QTableWidgetItem(progress))

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self.all_data = amc_data
        active_count = len([a for a in amc_data if a['amc_status'] == 'Active'])
        self.status_label.setText(f"Active AMC Contracts: {active_count} | Total: {len(amc_data)}")

    def _load_online_requests(self):
        """Load online requests from website filtered by period"""
        from database.db_connection import DatabaseContext
        
        start_date, end_date = self._get_date_range()

        requests = []
        try:
            with DatabaseContext() as db:
                query = """
                    SELECT 'Contact' as type, id, name, phone as mobile,
                           service_type, created_at, status
                    FROM contact_messages
                    WHERE DATE(created_at) BETWEEN %s AND %s
                    ORDER BY created_at DESC
                    LIMIT 100
                """
                requests = db.execute_query(query, (start_date, end_date), fetch_all=True) or []
        except Exception as e:
            try:
                from utils.logger import get_loggers
                get_loggers()['error'].error(f"Failed to load online requests: {e}")
            except Exception:
                pass
            requests = []

        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(['Type', 'ID', 'Name', 'Mobile', 'Service Type', 'Status', 'Date'])
        self.table.setRowCount(len(requests))

        for row, req in enumerate(requests):
            self.table.setItem(row, 0, QTableWidgetItem(req['type']))
            self.table.setItem(row, 1, QTableWidgetItem(str(req['id'])))
            self.table.setItem(row, 2, QTableWidgetItem(req['name'] or 'N/A'))
            self.table.setItem(row, 3, QTableWidgetItem(req['mobile'] or 'N/A'))
            self.table.setItem(row, 4, QTableWidgetItem(req['service_type'] or 'N/A'))
            self.table.setItem(row, 5, QTableWidgetItem(req['status'] or 'Pending'))
            date_str = Formatters.format_datetime(req.get('created_at'), '%d-%m-%Y %H:%M') or 'N/A'
            self.table.setItem(row, 6, QTableWidgetItem(date_str))
            
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        self.all_data = requests
        unread = len([r for r in requests if r['status'] == 'unread' or r['status'] == 'pending'])
        self.status_label.setText(f"Total Requests: {len(requests)} | Unread/Pending: {unread}")
        
    def _load_todays_services(self):
        """Load services filtered by period"""
        from database.db_connection import DatabaseContext
        
        start_date, end_date = self._get_date_range()
        
        with DatabaseContext() as db:
            query = """
                SELECT i.id, i.invoice_number, c.name as customer_name,
                       s.service_name, i.total_amount, i.created_at,
                       t.name as technician_name
                FROM invoices i
                JOIN customers c ON i.customer_id = c.id
                JOIN invoice_items ii ON i.id = ii.invoice_id
                JOIN services s ON ii.service_id = s.id
                LEFT JOIN technicians t ON i.technician_id = t.id
                WHERE i.is_active = TRUE AND DATE(i.created_at) BETWEEN %s AND %s
                ORDER BY i.created_at DESC
            """
            services = db.execute_query(query, (start_date, end_date), fetch_all=True)

        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(['ID', 'Invoice No', 'Customer', 'Service', 'Technician', 'Amount', 'Time'])
        self.table.setRowCount(len(services))

        for row, service in enumerate(services):
            self.table.setItem(row, 0, QTableWidgetItem(str(service['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(service['invoice_number'] or 'N/A'))
            self.table.setItem(row, 2, QTableWidgetItem(service['customer_name'] or 'N/A'))
            self.table.setItem(row, 3, QTableWidgetItem(service['service_name'] or 'N/A'))
            self.table.setItem(row, 4, QTableWidgetItem(service['technician_name'] or 'Unassigned'))
            self.table.setItem(row, 5, QTableWidgetItem(f"{self.currency_symbol}{service['total_amount']:,.2f}"))
            time_str = Formatters.format_datetime(service.get('created_at'), '%H:%M') or 'N/A'
            self.table.setItem(row, 6, QTableWidgetItem(time_str))

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.all_data = services
        total_amount = sum(s['total_amount'] for s in services)
        period_label = self.period.replace('_', ' ').title()
        self.status_label.setText(f"Services ({period_label}): {len(services)} | Revenue: {self.currency_symbol}{total_amount:,.2f}")

    def _load_pending_payments(self):
        """Load pending payment alerts data"""
        from database.db_connection import DatabaseContext

        with DatabaseContext() as db:
            from controllers.dashboard_controller import DashboardController
            controller = DashboardController(db)
            alerts = controller.get_payment_pending_alerts(limit=100) or []

        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['Customer', 'Invoice', 'Amount Due', 'Days Pending', 'Status', 'Date'])
        self.table.setRowCount(len(alerts))

        for row, a in enumerate(alerts):
            self.table.setItem(row, 0, QTableWidgetItem(a.get('customer_name') or 'N/A'))
            self.table.setItem(row, 1, QTableWidgetItem(a.get('invoice_number') or 'N/A'))
            self.table.setItem(row, 2, QTableWidgetItem(f"{self.currency_symbol}{float(a.get('balance_amount') or 0):,.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{int(float(a.get('days_pending') or 0))} days"))
            self.table.setItem(row, 4, QTableWidgetItem(a.get('payment_status') or 'Pending'))
            date_str = Formatters.format_date(a.get('invoice_date')) or 'N/A'
            self.table.setItem(row, 5, QTableWidgetItem(date_str))

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self.all_data = alerts
        total_due = sum(float(a.get('balance_amount') or 0) for a in alerts)
        self.status_label.setText(f"Pending Payments: {len(alerts)} | Total Due: {self.currency_symbol}{total_due:,.2f}")

    def filter_data(self, search_text):
        """Filter table data based on search text"""
        if not hasattr(self, 'all_data'):
            return

        search_text = search_text.lower()

        # Hide rows that don't match search
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def _show_row_details(self, row, column):
        """Show detailed view of selected row"""
        if self.metric_type == "Total Customers":
            self._show_customer_details(row)
        elif self.metric_type == "Total Services":
            self._show_service_details(row)
        elif self.metric_type == "Total Revenue":
            self._show_revenue_details(row)
        elif self.metric_type == "Active AMC":
            self._show_amc_details(row)
        elif self.metric_type == "Online Requests":
            self._show_request_details(row)
        elif self.metric_type == "Today's Services" or self.metric_type == "Total Invoices":
            self._show_service_details(row)
        elif self.metric_type == "Pending Payments":
            self._show_pending_payment_details(row)

    def _show_pending_payment_details(self, row):
        """Show pending payment detail popup"""
        if row < 0 or row >= len(self.all_data):
            return
        a = self.all_data[row]
        details_text = f"""
<b>⏳ PENDING PAYMENT</b>

<b>👤 Customer:</b> {a.get('customer_name', 'N/A') or 'N/A'}
<b>📝 Invoice:</b> {a.get('invoice_number', 'N/A') or 'N/A'}
<b>💰 Amount Due:</b> {self.currency_symbol}{float(a.get('balance_amount') or 0):,.2f}
<b>📅 Days Pending:</b> {int(float(a.get('days_pending') or 0))} days
<b>📊 Status:</b> {a.get('payment_status', 'Pending') or 'Pending'}
<b>📅 Invoice Date:</b> {Formatters.format_date(a.get('invoice_date')) or 'N/A'}
        """
        QMessageBox.information(self, "Pending Payment Details", details_text)

    def _show_customer_details(self, row):
        """Show customer details popup"""
        from database.db_connection import DatabaseContext
        
        # Get customer ID from table
        id_item = self.table.item(row, 0)
        if not id_item:
            return
            
        try:
            customer_id = int(id_item.text())
        except (ValueError, TypeError):
            QMessageBox.warning(self, "Error", "Could not get customer ID")
            return
        
        with DatabaseContext() as db:
            # Get customer details
            query = """
                SELECT id, name, mobile, email, address, landmark, created_at
                FROM customers
                WHERE id = %s AND is_active = TRUE
            """
            customer = db.execute_query(query, (customer_id,), fetch_one=True)
            
            if not customer:
                QMessageBox.warning(self, "Error", "Customer not found")
                return
            
            # Get customer's invoice count
            invoice_query = """
                SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
                FROM invoices
                WHERE customer_id = %s AND is_active = TRUE
            """
            invoice_stats = db.execute_query(invoice_query, (customer_id,), fetch_one=True)
            
            # Show details in message box
            details_text = f"""
<b>👤 CUSTOMER DETAILS</b>

<b>📋 ID:</b> {customer['id']}
<b>👤 Name:</b> {customer['name']}
<b>📱 Mobile:</b> {customer['mobile']}
<b>📧 Email:</b> {customer['email'] or 'N/A'}
<b>📍 Address:</b> {customer['address'] or 'N/A'}
<b>🏷️ Landmark:</b> {customer['landmark'] or 'N/A'}
<b>📅 Created:</b> {Formatters.format_date(customer.get('created_at')) or 'N/A'}

<b>📊 SERVICE HISTORY</b>
<b>📝 Total Invoices:</b> {invoice_stats['count'] or 0}
<b>💰 Total Revenue:</b> {self.currency_symbol}{invoice_stats['total']:,.0f}
            """
            
            QMessageBox.information(self, f"Customer Details - {customer['name']}", details_text)

    def _show_service_details(self, row):
        """Show service/invoice details popup"""
        # Get invoice ID from table
        id_item = self.table.item(row, 0)
        if not id_item:
            return
            
        try:
            invoice_id = int(id_item.text())
        except (ValueError, TypeError):
            QMessageBox.warning(self, "Error", "Could not get invoice ID")
            return
        
        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            query = """
                SELECT i.invoice_number, c.name, i.total_amount, i.created_at, s.service_name
                FROM invoices i
                JOIN customers c ON i.customer_id = c.id
                JOIN invoice_items ii ON i.id = ii.invoice_id
                JOIN services s ON ii.service_id = s.id
                WHERE i.id = %s
            """
            invoice = db.execute_query(query, (invoice_id,), fetch_one=True)
            
            if invoice:
                details_text = f"""
<b>🔧 SERVICE DETAILS</b>

<b>📝 Invoice:</b> {invoice['invoice_number']}
<b>👤 Customer:</b> {invoice['name']}
<b>🔧 Service:</b> {invoice['service_name']}
<b>💰 Amount:</b> {self.currency_symbol}{invoice['total_amount']:,.0f}
<b>📅 Date:</b> {Formatters.format_datetime(invoice.get('created_at'), '%d-%m-%Y %H:%M') or 'N/A'}
                """
                QMessageBox.information(self, "Service Details", details_text)

    def _show_revenue_details(self, row):
        """Show revenue/invoice details popup"""
        invoice_no_item = self.table.item(row, 0)
        if not invoice_no_item:
            return
        
        invoice_number = invoice_no_item.text()
        
        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            query = """
                SELECT i.invoice_number, c.name, i.total_amount, i.advance_payment, 
                       i.balance_amount, i.payment_status, i.created_at
                FROM invoices i
                JOIN customers c ON i.customer_id = c.id
                WHERE i.invoice_number = %s
            """
            invoice = db.execute_query(query, (invoice_number,), fetch_one=True)
            
            if invoice:
                details_text = f"""
<b>💰 INVOICE DETAILS</b>

<b>📝 Invoice No:</b> {invoice['invoice_number']}
<b>👤 Customer:</b> {invoice['name']}
<b>💵 Total Amount:</b> {self.currency_symbol}{invoice['total_amount']:,.0f}
<b>💰 Paid:</b> {self.currency_symbol}{invoice['advance_payment']:,.0f}
<b>⏳ Balance:</b> {self.currency_symbol}{invoice['balance_amount']:,.0f}
<b>📊 Status:</b> {invoice['payment_status']}
<b>📅 Date:</b> {Formatters.format_date(invoice.get('created_at')) or 'N/A'}
                """
                QMessageBox.information(self, "Invoice Details", details_text)

    def _show_amc_details(self, row):
        """Show AMC contract details popup"""
        amc_id_item = self.table.item(row, 0)
        if not amc_id_item:
            return
        
        amc_id = amc_id_item.text()

        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            query = """
                SELECT ac.amc_id, c.name, ac.contract_type, ac.amc_status,
                       ac.total_amount as amc_amount, ac.start_date, ac.end_date,
                       ac.services_per_year as total_visits, ac.services_per_year as visits_completed
                FROM amc_contracts ac
                JOIN customers c ON ac.customer_id = c.id
                WHERE ac.amc_id = %s
            """
            amc = db.execute_query(query, (amc_id,), fetch_one=True)

            if amc:
                progress = int((amc['visits_completed'] or 0) / max(amc['total_visits'] or 1, 1) * 100)
                details_text = f"""
<b>📋 AMC CONTRACT DETAILS</b>

<b>🔖 AMC ID:</b> {amc['amc_id']}
<b>👤 Customer:</b> {amc['name']}
<b>📊 Type:</b> {amc['contract_type']}
<b>✅ Status:</b> {amc['amc_status']}
<b>💰 Amount:</b> {self.currency_symbol}{amc['amc_amount']:,.0f}
<b>📅 Start Date:</b> {Formatters.format_date(amc.get('start_date')) or 'N/A'}
<b>📅 End Date:</b> {Formatters.format_date(amc.get('end_date')) or 'N/A'}
<b>🔧 Visits:</b> {amc['visits_completed'] or 0}/{amc['total_visits'] or 0} ({progress}%)
                """
                QMessageBox.information(self, "AMC Details", details_text)

    def _show_request_details(self, row):
        """Show online request details popup"""
        id_item = self.table.item(row, 1)
        req_type_item = self.table.item(row, 0)
        if not id_item or not req_type_item:
            return
        
        try:
            req_id = int(id_item.text())
            req_type = req_type_item.text()
        except (ValueError, TypeError):
            QMessageBox.warning(self, "Error", "Could not get request details")
            return

        from database.db_connection import DatabaseContext
        request = None
        with DatabaseContext() as db:
            if req_type == "Contact":
                query = """
                    SELECT name, phone, email, service_type, message, created_at, status
                    FROM contact_messages
                    WHERE id = %s
                """
                request = db.execute_query(query, (req_id,), fetch_one=True)

            if request:
                details_text = f"""
<b>🌐 {req_type.upper()} REQUEST DETAILS</b>

<b>👤 Name:</b> {request['name']}
<b>📱 Phone:</b> {request['phone']}
<b>📧 Email:</b> {request['email'] or 'N/A'}
<b>🔧 Service Type:</b> {request['service_type']}
<b>📝 Message:</b> {request['message'] or 'N/A'}
<b>📅 Date:</b> {Formatters.format_datetime(request.get('created_at'), '%d-%m-%Y %H:%M') or 'N/A'}
<b>📊 Status:</b> {request['status']}
                """
                QMessageBox.information(self, "Request Details", details_text)

    def keyPressEvent(self, event):
        """Override key press to prevent Enter from closing dialog"""
        from PySide6.QtCore import Qt
        # Ignore Enter/Return keys that might close the dialog
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # Just ignore - don't close the dialog
            return
        # Let other keys pass through
        super().keyPressEvent(event)

    def export_data(self):
        """Export data to Excel"""
        from datetime import datetime
        from PySide6.QtWidgets import QFileDialog
        from utils.excel_helper import ExcelExporter

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Data",
            f"Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel Files (*.xlsx)"
        )
        if not file_path:
            return

        try:
            headers = [self.table.horizontalHeaderItem(i).text()
                      for i in range(self.table.columnCount())]
            rows = []
            for row in range(self.table.rowCount()):
                if not self.table.isRowHidden(row):
                    row_data = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        row_data.append(item.text() if item else '')
                    rows.append(row_data)

            charts_data = None
            if len(rows) > 1:
                num_cols = []
                for c in range(len(headers)):
                    vals = []
                    for rw in rows[:50]:
                        try:
                            vals.append(float(rw[c].replace(',', '').replace(self.currency_symbol, '')))
                        except (ValueError, AttributeError):
                            vals.append(None)
                    if any(v is not None for v in vals):
                        num_cols.append((c, [v for v in vals if v is not None]))
                if num_cols:
                    cat_col = 0
                    cats = [rw[cat_col][:20] if len(rw) > cat_col else f'R{i}' for i, rw in enumerate(rows[:50])]
                    chart_series = []
                    for c_idx, c_vals in num_cols[:3]:
                        chart_series.append((headers[c_idx], c_vals[:len(cats)]))
                    charts_data = [{
                        'type': 'bar',
                        'title': 'Dashboard Data Overview',
                        'categories': cats,
                        'values': chart_series,
                        'y_axis': 'Value'
                    }]

            wb = ExcelExporter.build_excel(
                sheet_title='Report',
                title_text='Report Details',
                subtitle_text=f'Total rows: {len(rows)} | Generated: {datetime.now().strftime("%d-%m-%Y %H:%M")}',
                headers=headers, rows=rows,
                kpis=[
                    ('Total Rows', len(rows)),
                    ('Columns', len(headers)),
                ],
                charts_data=charts_data
            )

            wb.save(file_path)
            QMessageBox.information(self, "Success", f"Data exported to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")


class EnhancedDashboardView(BaseView):
    """Enhanced professional dashboard with clickable cards and detailed views"""

    def __init__(self, user_data, db, controller):
        super().__init__()
        self.user_data = user_data
        self.db = db
        self.controller = controller
        self.theme_manager = UnifiedTheme()
        self.colors = self.theme_manager.get_colors()
        self.period = 'this_year'  # Default: This Year (to show all data)
        self.metric_labels = {}
        self.metric_cards = {}
        self.loaded_data = {}
        self.last_online_count = 0
        self.last_pending_count = 0
        self.last_invoice_count = 0
        self.last_revenue_count = 0

        self._destroyed = False
        self._setup_ui()
        self.load_dashboard_data()
        QTimer.singleShot(500, self._safe_load_analytics)

        # Connect to Global Event Bus for real-time Privacy Shield updates
        try:
            from utils.event_bus import EventBus
            EventBus().privacy_mode_toggled.connect(self._on_privacy_toggled)
        except Exception:
            pass

        # Auto-refresh timer for real-time updates
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self._auto_refresh_check)
        self.auto_refresh_timer.start(120000)  # Refresh every 2 minutes

    def _on_privacy_toggled(self, enabled: bool):
        """Handle real-time Privacy Shield toggle across dashboard components"""
        try:
            self._alert_due_peeked = False
            data = getattr(self, '_all_alerts_data', [])
            self._update_payment_alerts(data)
        except Exception as e:
            print(f"[DASHBOARD] Error updating on privacy toggle: {e}")

    def _safe_load_analytics(self):
        """Load analytics with destruction guard"""
        if self._destroyed:
            return
        self.load_analytics_data()

    def cleanup(self):
        """Cleanup timers when view is closed"""
        try:
            self._destroyed = True
            if hasattr(self, 'auto_refresh_timer') and self.auto_refresh_timer:
                self.auto_refresh_timer.stop()
            if hasattr(self, 'auto_refresh_timer'):
                self.auto_refresh_timer = None
        except Exception as e:
            try:
                from utils.logger import get_loggers
                get_loggers()['error'].warning(f"Dashboard cleanup failed: {e}")
            except Exception:
                print(f"[WARN] Dashboard cleanup failed: {e}")

    def update_theme_colors(self):
        """Update theme colors for proper dark theme support"""
        colors = self.theme_manager.get_colors()

        # Apply QPalette colors
        self.theme_manager.apply_palette(self)

        # Apply stylesheet
        self.setStyleSheet(self.theme_manager.get_main_stylesheet())

        # Apply theme directly to all tables for proper alternating colors
        if hasattr(self, 'table'):
            self.theme_manager.apply_table_theme(self.table)

        if hasattr(self, 'alerts_table'):
            self.theme_manager.apply_table_theme(self.alerts_table)

        # Refresh data to ensure proper display
        self.load_dashboard_data()

    def _auto_refresh_check(self):
        """Auto-refresh check for new online requests AND periodic dashboard refresh"""
        if self._destroyed:
            return
        self.run_in_thread(
            self._auto_refresh_check_thread,
            self._auto_refresh_compare,
            lambda err: print(f"[ERROR] Auto-refresh check failed: {err}")
        )

    def _auto_refresh_check_thread(self):
        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            from controllers.dashboard_controller import DashboardController
            return DashboardController(db).get_dashboard_stats(self.period)

    def _auto_refresh_compare(self, stats):
        """Compare stats on main thread after background fetch"""
        if self._destroyed or not stats:
            return
        current_online = stats.get('online_requests', 0)
        current_invoices = stats.get('total_invoices', 0)
        current_revenue = stats.get('total_revenue', 0)
        
        if current_online > self.last_online_count and self.last_online_count > 0:
            new_count = current_online - self.last_online_count
            self.show_new_request_notification(new_count)
        
        if (current_invoices != self.last_invoice_count or 
            current_revenue != self.last_revenue_count):
            print(f"[AUTO-REFRESH] Data changed - refreshing dashboard")
            self.refresh_data()
            return
        
        self.last_online_count = current_online
        self.last_invoice_count = current_invoices
        self.last_revenue_count = current_revenue

    def show_new_request_notification(self, count):
        """Show notification for new requests"""
        try:
            # Play notification sound
            import winsound
            winsound.PlaySound("SystemNotification", winsound.SND_ALIAS | winsound.SND_ASYNC)
        except Exception as e:
            print(f"[INFO] Sound play failed: {e}")
        
        # Update greeting label to show notification
        for widget in self.findChildren(QLabel):
            if widget.text().startswith("Good") and "!" in widget.text():
                base_text = widget.text().split(' 🔔')[0].rstrip('!') + "!"
                widget.setText(f"{base_text} 🔔 {count} new request{'s' if count > 1 else ''}!")
                # Reset after 5 seconds
                QTimer.singleShot(5000, lambda w=widget, t=base_text: w.setText(t))
                break

    def _setup_ui(self):
        """Setup enhanced dashboard UI - scrollable enterprise layout"""
        self.currency_symbol = get_setting("currency_symbol", "₹")

        # Root layout
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Scroll area so all sections fit on smaller screens
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        root_layout.addWidget(scroll)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        scroll.setWidget(content)

        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # Header section
        self._create_header(main_layout)

        # Filter section
        self._create_filter(main_layout)

        # Metric cards with click handlers
        self._create_metric_cards(main_layout)

        # Pending Payments Section (Structured table + summary cards + filters)
        self._create_pending_payments_section(main_layout)

        main_layout.addStretch()


        # Main content removed - duplicate data already in analytics tabs

    def _create_header(self, layout):
        c = self.colors
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            greeting = "Good morning"
        elif 12 <= current_hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        user_name = self.user_data.get('full_name', 'Admin').split()[0]

        row = QHBoxLayout()
        row.setSpacing(12)
        g = QLabel(f"{greeting}, {user_name}! 👋")
        g.setStyleSheet(f"font-size: 22pt; font-weight: 800; color: {c['fg']}; letter-spacing: -0.5px;")
        row.addWidget(g)
        row.addStretch()
        d = QLabel(datetime.now().strftime('%A, %B %d, %Y'))
        d.setStyleSheet(f"font-size: 9pt; color: {c['muted']}; font-weight: 500;")
        row.addWidget(d)
        layout.addLayout(row)

    def _create_filter(self, layout):
        c = self.colors
        f = QFrame()
        f.setStyleSheet(f"QFrame {{ background-color: {c['card_bg']}; border: 1px solid {c['border']}; border-radius: 10px; }}")
        fl = QHBoxLayout(f)
        fl.setContentsMargins(16, 10, 16, 10)
        fl.setSpacing(12)

        lbl = QLabel("📅 Period")
        lbl.setStyleSheet(f"font-size: 9pt; font-weight: 700; color: {c['fg']}; background: transparent;")
        fl.addWidget(lbl)

        self.period_combo = QComboBox()
        self.period_combo.addItems(['Today', 'This Week', 'This Month', 'This Year'])
        self.period_combo.setCurrentIndex(3)  # This Year
        self.period_combo.setMinimumWidth(130)
        self.period_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {c['hover']}; color: {c['fg']};
                border: 1px solid {c['border']}; border-radius: 6px;
                padding: 6px 26px 6px 10px; font-size: 9pt;
            }}
            QComboBox:hover {{ border-color: {c['primary']}; }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border: none;
            }}
            QComboBox::down-arrow {{
                image: url("{CHEVRON_ICON_PATH}");
                width: 11px;
                height: 11px;
                margin-right: 6px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {c['card_bg']}; color: {c['fg']};
                border: 1px solid {c['border']};
                selection-background-color: {c['primary']};
                selection-color: white;
            }}
        """)
        self.period_combo.currentTextChanged.connect(self._on_period_change)
        fl.addWidget(self.period_combo)

        self.date_range_label = QLabel("")
        self.date_range_label.setStyleSheet(f"color: {c['muted']}; font-size: 9pt; font-weight: 500;")
        fl.addWidget(self.date_range_label)
        fl.addStretch()
        layout.addWidget(f)

    def _create_metric_cards(self, layout):
        """Create clickable metric cards - 2 rows of 4 for a rich enterprise KPI strip"""
        cards_frame = QFrame()
        cards_frame.setStyleSheet("""
            background-color: transparent;
        """)
        cards_layout = QVBoxLayout(cards_frame)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(14)

        # Metric definitions with colors and financial privacy flags — (key, label, icon, color, is_financial)
        # Note: 'Total Services' removed as it is identical to 'Total Invoices'
        # Default sequence: Row 1 (Customers -> Invoices -> Active AMC -> Today's Services)
        #                   Row 2 (Revenue -> Pending Payments -> Online Requests)
        metrics = [
            ('total_customers', 'Total Customers', '👥', '#2563EB', False),
            ('total_invoices', 'Total Invoices', '📄', '#10B981', False),
            ('active_amc', 'Active AMC', '🛡️', '#6366F1', False),
            ('today_services', "Today's Services", '📅', '#F59E0B', False),
            ('total_revenue', 'Total Revenue', '💰', '#8B5CF6', True),
            ('pending_payments', 'Pending Payments', '⏳', '#EF4444', False),
            ('online_requests', 'Online Requests', '🌐', '#EC4899', False),
        ]

        # Split into 2 rows of 4
        row1 = QHBoxLayout()
        row1.setSpacing(14)
        row2 = QHBoxLayout()
        row2.setSpacing(14)

        for i, (key, label, icon, color, is_fin) in enumerate(metrics):
            init_val = f"{self.currency_symbol}0" if is_fin else "0"
            card = MetricCard(label, init_val, icon, color, is_financial=is_fin)
            card.clicked.connect(self._on_card_clicked)
            self.metric_cards[key] = card
            if i < 4:
                row1.addWidget(card)
            else:
                row2.addWidget(card)

        cards_layout.addLayout(row1)
        cards_layout.addLayout(row2)

        layout.addWidget(cards_frame)

    def _create_pending_payments_section(self, layout):
        """Dedicated, enterprise-grade Pending Payments section with structured table, KPI summary, and real-time filters"""
        c = self.colors

        section = QFrame()
        section.setObjectName("pendingPaymentsSection")
        section.setStyleSheet("""
            QFrame#pendingPaymentsSection {
                background: transparent;
            }
        """)

        sec_layout = QVBoxLayout(section)
        sec_layout.setContentsMargins(0, 0, 0, 0)
        sec_layout.setSpacing(14)

        # ── 1. Section Header ──
        hdr = QFrame()
        hdr.setObjectName("pendingPaymentsHeader")
        hdr.setStyleSheet(f"""
            QFrame#pendingPaymentsHeader {{
                background-color: {c['card_bg']};
                border: 1px solid {c['border']};
                border-radius: 12px;
            }}
            QFrame#pendingPaymentsHeader QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(18, 14, 18, 14)
        hdr_lay.setSpacing(14)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        title_row = QHBoxLayout()
        title_row.setSpacing(10)

        icon_badge = QLabel("💰")
        icon_badge.setFixedSize(34, 34)
        icon_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_badge.setStyleSheet(f"""
            background-color: {c['primary']}15;
            border-radius: 8px;
            font-size: 13pt;
            border: none;
        """)
        title_row.addWidget(icon_badge)

        t = QLabel("Pending Payments & Collections")
        t.setStyleSheet(f"font-size: 14pt; font-weight: 800; color: {c['fg']}; letter-spacing: -0.3px; border: none;")
        title_row.addWidget(t)

        self.pending_badge_label = QLabel("0 Pending")
        self.pending_badge_label.setStyleSheet("""
            background-color: #FEF2F2;
            color: #DC2626;
            border: 1px solid #FECACA;
            border-radius: 10px;
            padding: 3px 10px;
            font-size: 8pt;
            font-weight: 700;
        """)
        title_row.addWidget(self.pending_badge_label)
        title_row.addStretch()
        title_col.addLayout(title_row)

        s = QLabel("Live overview of customer outstanding balances, unpaid invoices, and overdue collection accounts")
        s.setStyleSheet(f"font-size: 8.5pt; color: {c['muted']}; border: none;")
        title_col.addWidget(s)
        hdr_lay.addLayout(title_col)
        hdr_lay.addStretch()

        # WhatsApp Reminder for selected row
        self.header_remind_btn = QPushButton("💬 Send Reminder")
        self.header_remind_btn.setToolTip("Send WhatsApp reminder to selected customer")
        self.header_remind_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_remind_btn.setFixedHeight(36)
        self.header_remind_btn.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 9pt;
                font-weight: 700;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: #047857;
            }
            QPushButton:pressed {
                background-color: #065F46;
            }
        """)
        self.header_remind_btn.clicked.connect(self._send_whatsapp_reminder)
        hdr_lay.addWidget(self.header_remind_btn)

        # Refresh button
        self.pending_refresh_btn = QPushButton("🔄 Refresh")
        self.pending_refresh_btn.setToolTip("Refresh pending payments data")
        self.pending_refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pending_refresh_btn.setFixedHeight(36)
        self.pending_refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['card_bg']};
                color: {c['fg']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 0 14px;
                font-size: 9pt;
                font-weight: 600;
            }}
            QPushButton:hover {{
                border-color: {c['primary']};
                color: {c['primary']};
                background-color: {c['hover']};
            }}
        """)
        self.pending_refresh_btn.clicked.connect(self.load_analytics_data)
        hdr_lay.addWidget(self.pending_refresh_btn)

        # Export Excel button
        self.pending_export_btn = QPushButton("📥 Export Excel")
        self.pending_export_btn.setToolTip("Export pending payments ledger to Excel with executive dashboard and charts")
        self.pending_export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pending_export_btn.setFixedHeight(36)
        self.pending_export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c['card_bg']};
                color: {c['fg']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 0 14px;
                font-size: 9pt;
                font-weight: 600;
            }}
            QPushButton:hover {{
                border-color: #059669;
                color: #059669;
                background-color: {c['hover']};
            }}
        """)
        self.pending_export_btn.clicked.connect(self._export_pending_payments_to_excel)
        hdr_lay.addWidget(self.pending_export_btn)

        sec_layout.addWidget(hdr)

        # ── 2. Summary KPI Cards Strip ──
        cards_frame = QFrame()
        cards_frame.setStyleSheet("background: transparent;")
        cards_layout = QHBoxLayout(cards_frame)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(12)

        is_priv = False
        try:
            from utils.privacy_manager import get_privacy_manager
            is_priv = get_privacy_manager().is_privacy_enabled()
        except Exception:
            pass
        init_due = f"{self.currency_symbol} ••••••" if is_priv else f"{self.currency_symbol}0"

        card_defs = [
            ("👥", "Pending Invoices", "0", "#2563EB", "Unsettled accounts"),
            ("💰", "Total Outstanding", init_due, "#DC2626", "Gross receivables due"),
            ("🔥", "Overdue (>30 Days)", "0", "#EA580C", "Needs urgent follow-up"),
            ("⏱️", "Average Delay", "0 Days", "#D97706", "From billing date"),
        ]
        attrs = []
        for icon, lbl, val, color, sub in card_defs:
            card = self._create_crm_card(icon, lbl, val, color, sub)
            attrs.append(card)
            cards_layout.addWidget(card)

        (self.alert_pending_count_card, self.alert_total_due_card,
         self.alert_urgent_card, self.alert_avg_delay_card) = attrs

        self._alert_due_peeked = False
        self._alert_due_raw = f"{self.currency_symbol}0"

        def _on_alert_due_clicked(event):
            try:
                from utils.privacy_manager import get_privacy_manager
                if get_privacy_manager().is_privacy_enabled():
                    self._alert_due_peeked = not getattr(self, '_alert_due_peeked', False)
                    vlabel = self.alert_total_due_card.findChild(QLabel, "crmStatValue")
                    if vlabel:
                        if self._alert_due_peeked:
                            vlabel.setText(getattr(self, '_alert_due_raw', f"{self.currency_symbol}0"))
                        else:
                            vlabel.setText(f"{self.currency_symbol} ••••••")
            except Exception:
                pass

        self.alert_total_due_card.mousePressEvent = _on_alert_due_clicked
        self.alert_total_due_card.setCursor(Qt.CursorShape.PointingHandCursor)
        sec_layout.addWidget(cards_frame)

        # ── 3. Search & Filter Toolbar ──
        toolbar = QFrame()
        toolbar.setObjectName("pendingPaymentsToolbar")
        toolbar.setStyleSheet(f"""
            QFrame#pendingPaymentsToolbar {{
                background-color: {c['card_bg']};
                border: 1px solid {c['border']};
                border-radius: 10px;
            }}
            QFrame#pendingPaymentsToolbar QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(14, 10, 14, 10)
        tb.setSpacing(10)

        self.alert_search = QLineEdit()
        self.alert_search.setPlaceholderText("🔍  Search by Customer name, Mobile or Invoice #...")
        self.alert_search.textChanged.connect(self._filter_alerts_table)
        self.alert_search.setClearButtonEnabled(True)
        self.alert_search.setMinimumWidth(280)
        self.alert_search.setStyleSheet(f"""
            QLineEdit {{
                background-color: {c['bg']};
                color: {c['fg']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 7px 12px;
                font-size: 9pt;
            }}
            QLineEdit:focus {{
                border: 1.5px solid {c['primary']};
            }}
            QLineEdit::placeholder {{
                color: {c['muted']};
            }}
        """)
        tb.addWidget(self.alert_search)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"background: {c['border']}; max-width: 1px;")
        tb.addWidget(sep)

        filter_css = f"""
            QComboBox {{
                background-color: {c['bg']};
                color: {c['fg']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 6px 26px 6px 12px;
                font-size: 9pt;
                min-width: 115px;
            }}
            QComboBox:hover {{
                border-color: {c['primary']};
            }}
            QComboBox:focus {{
                border: 1.5px solid {c['primary']};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                border: none;
                width: 24px;
            }}
            QComboBox::down-arrow {{
                image: url("{CHEVRON_ICON_PATH}");
                width: 11px;
                height: 11px;
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {c['card_bg']};
                color: {c['fg']};
                border: 1px solid {c['border']};
                selection-background-color: {c['primary']};
                selection-color: white;
                border-radius: 6px;
                padding: 4px;
            }}
        """

        def mk_filter(items):
            cb = QComboBox()
            cb.addItems(items)
            cb.setStyleSheet(filter_css)
            cb.currentTextChanged.connect(self._apply_alert_filters)
            return cb

        self.alert_status_filter = mk_filter(['All Status', 'Pending', 'Partial'])
        self.alert_days_filter = mk_filter(['All Overdue', '0-15 Days', '16-30 Days', '30+ Days'])
        self.alert_amount_filter = mk_filter(['All Amounts', '< ₹1,000', '₹1,000 - ₹5,000', '> ₹5,000'])

        tb.addWidget(self.alert_status_filter)
        tb.addWidget(self.alert_days_filter)
        tb.addWidget(self.alert_amount_filter)
        tb.addStretch()

        self.alert_record_count_label = QLabel("0 records")
        self.alert_record_count_label.setStyleSheet(f"""
            QLabel {{
                background-color: {c['hover']};
                color: {c['muted']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 8pt;
                font-weight: 700;
            }}
        """)
        tb.addWidget(self.alert_record_count_label)

        sec_layout.addWidget(toolbar)

        # ── 4. Structured Table (Rows and Columns) ──
        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(9)
        self.alerts_table.setHorizontalHeaderLabels([
            '#', 'CUSTOMER DETAILS', 'INVOICE #', 'INVOICE DATE',
            'TOTAL BILLED', 'BALANCE DUE', 'AGING / OVERDUE', 'STATUS', 'ACTIONS'
        ])
        self.alerts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.alerts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.alerts_table.verticalHeader().setVisible(False)
        self.alerts_table.setAlternatingRowColors(True)
        self.alerts_table.setShowGrid(False)
        self.alerts_table.setSortingEnabled(False)
        self.alerts_table.setMinimumHeight(440)
        self.alerts_table.cellDoubleClicked.connect(self._on_table_cell_double_clicked)

        h = self.alerts_table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)

        self.alerts_table.setColumnWidth(0, 48)    # #
        self.alerts_table.setColumnWidth(2, 135)   # Invoice #
        self.alerts_table.setColumnWidth(3, 105)   # Date
        self.alerts_table.setColumnWidth(4, 115)   # Total Billed
        self.alerts_table.setColumnWidth(5, 125)   # Balance Due
        self.alerts_table.setColumnWidth(6, 140)   # Overdue
        self.alerts_table.setColumnWidth(7, 95)    # Status
        self.alerts_table.setColumnWidth(8, 170)   # Actions

        self.alerts_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {c['card_bg']};
                color: {c['fg']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                outline: none;
                gridline-color: transparent;
            }}
            QTableWidget::item {{
                padding: 6px 10px;
                border-bottom: 1px solid {c['border_light']};
                border-right: none;
                background-color: transparent;
            }}
            QTableWidget::item:selected {{
                background-color: {c['primary']}15;
                color: {c['fg']};
            }}
            QHeaderView::section {{
                background-color: {c['hover']};
                color: {c['muted']};
                padding: 11px 10px;
                border: none;
                border-bottom: 1.5px solid {c['border']};
                font-weight: 700;
                font-size: 8pt;
                text-transform: uppercase;
                letter-spacing: 0.6px;
            }}
            QHeaderView::section:hover {{
                color: {c['fg']};
            }}
        """)
        sec_layout.addWidget(self.alerts_table, stretch=1)

        # ── 5. Pagination ──
        pag = QFrame()
        pag.setStyleSheet("background: transparent;")
        pag_lay = QHBoxLayout(pag)
        pag_lay.setContentsMargins(4, 0, 4, 0)

        self.pag_info_label = QLabel("Showing 0 of 0")
        self.pag_info_label.setStyleSheet(f"color: {c['muted']}; font-size: 8.5pt; font-weight: 500;")
        pag_lay.addWidget(self.pag_info_label)
        pag_lay.addStretch()

        def pg_btn(text, w=95):
            b = QPushButton(text)
            b.setFixedWidth(w)
            b.setFixedHeight(32)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(f"""
                QPushButton {{
                    background: {c['card_bg']}; color: {c['fg']};
                    border: 1px solid {c['border']}; border-radius: 6px;
                    font-size: 8.5pt; font-weight: 600;
                }}
                QPushButton:hover:enabled {{ border-color: {c['primary']}; color: {c['primary']}; background: {c['hover']}; }}
                QPushButton:disabled {{ color: {c['muted']}; border-color: {c['border']}; background: transparent; }}
            """)
            return b

        self.pag_prev_btn = pg_btn("← Previous", 100)
        self.pag_prev_btn.clicked.connect(self._pag_prev)
        pag_lay.addWidget(self.pag_prev_btn)

        self.pag_page_label = QLabel("1")
        self.pag_page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pag_page_label.setFixedWidth(36)
        self.pag_page_label.setStyleSheet(f"""
            QLabel {{
                color: {c['primary']}; font-size: 9.5pt; font-weight: 700;
                background: {c['primary']}15;
                border: 1px solid {c['primary']}35;
                border-radius: 6px; padding: 4px 0;
            }}
        """)
        pag_lay.addWidget(self.pag_page_label)

        self.pag_next_btn = pg_btn("Next →", 100)
        self.pag_next_btn.clicked.connect(self._pag_next)
        pag_lay.addWidget(self.pag_next_btn)

        sec_layout.addWidget(pag)

        self._current_page = 0
        self._page_size = 12
        self._all_alerts_data = []

        layout.addWidget(section)

    def _create_crm_card(self, icon, title, value, color, subtitle=""):
        c = self.colors
        card = QFrame()
        card.setObjectName("crmStatCard")
        card.setMinimumWidth(180)
        card.setStyleSheet(f"""
            QFrame#crmStatCard {{
                background-color: {c['card_bg']};
                border: 1px solid {c['border']};
                border-radius: 12px;
                border-top: 3px solid {color};
            }}
            QFrame#crmStatCard:hover {{
                border-color: {color}80;
                background-color: {c['hover']};
            }}
            QFrame#crmStatCard QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        clayout = QVBoxLayout(card)
        clayout.setContentsMargins(16, 14, 16, 14)
        clayout.setSpacing(6)

        # Top row: Icon container + Title
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(32, 32)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(f"""
            background-color: {color}18;
            color: {color};
            border-radius: 8px;
            font-size: 13pt;
            border: none;
        """)
        top_row.addWidget(icon_lbl)

        tlabel = QLabel(title.upper())
        tlabel.setStyleSheet(f"""
            font-size: 8pt;
            color: {c['muted']};
            font-weight: 700;
            letter-spacing: 0.5px;
            border: none;
        """)
        top_row.addWidget(tlabel)
        top_row.addStretch()
        clayout.addLayout(top_row)

        # Value
        vlabel = QLabel(value)
        vlabel.setObjectName("crmStatValue")
        vlabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        vlabel.setStyleSheet(f"""
            font-size: 19pt;
            font-weight: 800;
            color: {color if color in ('#EF4444', '#DC2626') else c['fg']};
            letter-spacing: -0.5px;
            border: none;
            padding: 2px 0;
        """)
        clayout.addWidget(vlabel)

        # Subtitle footer
        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setStyleSheet(f"font-size: 7.5pt; color: {c['muted']}; font-weight: 500; border: none;")
            clayout.addWidget(sub_lbl)

        return card


    def _filter_alerts_table(self, text):
        self._apply_alert_filters()

    def _get_severity(self, days):
        if days > 60: return 'critical', 'Overdue'
        elif days > 30: return 'urgent', 'Overdue'
        elif days > 15: return 'normal', 'Pending'
        else: return 'recent', 'Recent'

    def _get_severity_colors(self, severity):
        if severity == 'recent': return QColor(22, 163, 74), QColor(220, 252, 231, 30)
        if severity == 'normal': return QColor(217, 119, 6), QColor(254, 243, 199, 30)
        if severity == 'urgent': return QColor(220, 38, 38), QColor(254, 226, 226, 30)
        if severity == 'critical': return QColor(185, 28, 28), QColor(254, 202, 202, 30)
        return QColor(self.colors['fg']), QColor(self.colors['card_bg'])

    def _apply_alert_filters(self):
        search = self.alert_search.text().lower().strip() if hasattr(self, 'alert_search') else ''
        status = self.alert_status_filter.currentText() if hasattr(self, 'alert_status_filter') else 'All Status'
        days = self.alert_days_filter.currentText() if hasattr(self, 'alert_days_filter') else 'All Overdue'
        amount = self.alert_amount_filter.currentText() if hasattr(self, 'alert_amount_filter') else 'All Amounts'

        visible_count = 0
        for row in range(self.alerts_table.rowCount()):
            show = True
            cust_item = self.alerts_table.item(row, 1)
            inv_item = self.alerts_table.item(row, 2)
            if not cust_item:
                continue

            if search:
                match = False
                for it in (cust_item, inv_item):
                    if it and search in it.text().lower():
                        match = True
                        break
                if not match:
                    show = False

            if show and status != 'All Status':
                status_item = self.alerts_table.item(row, 7)
                if status_item and status.lower() not in status_item.text().lower():
                    show = False

            if show and days != 'All Overdue':
                d = self._get_row_days(row)
                if '0-15' in days and not (0 <= d <= 15): show = False
                elif '16-30' in days and not (16 <= d <= 30): show = False
                elif '30+' in days and not (d > 30): show = False

            if show and amount != 'All Amounts':
                amt = self._get_row_amount(row)
                if '<' in amount and not (amt < 1000): show = False
                elif '1,000 - 5,000' in amount.replace('₹', '') and not (1000 <= amt <= 5000): show = False
                elif '>' in amount and not (amt > 5000): show = False

            self.alerts_table.setRowHidden(row, not show)
            if show:
                visible_count += 1

        if hasattr(self, 'alert_record_count_label'):
            self.alert_record_count_label.setText(f"{visible_count} visible")

    def _get_row_days(self, row):
        item = self.alerts_table.item(row, 6)
        if not item: return 0
        try:
            txt = item.text().replace('🔥', '').replace('⏳', '').replace('✓', '').strip()
            return int(float(txt.split()[0]))
        except: return 0

    def _get_row_amount(self, row):
        # Read from raw data rather than potentially masked cell text
        start = self._current_page * self._page_size
        idx = start + row
        if 0 <= idx < len(self._all_alerts_data):
            try:
                return float(self._all_alerts_data[idx].get('balance_amount') or 0)
            except:
                pass
        item = self.alerts_table.item(row, 5)
        if not item: return 0
        try:
            clean = item.text().replace(self.currency_symbol, '').replace(',', '').strip()
            return float(clean)
        except: return 0

    def _pag_prev(self):
        if self._current_page > 0:
            self._current_page -= 1
            self._render_pagination()

    def _pag_next(self):
        total_pages = (len(self._all_alerts_data) + self._page_size - 1) // self._page_size
        if self._current_page < total_pages - 1:
            self._current_page += 1
            self._render_pagination()

    def _render_pagination(self):
        total = len(self._all_alerts_data)
        total_pages = max((total + self._page_size - 1) // self._page_size, 1)
        start = self._current_page * self._page_size
        end = min(start + self._page_size, total)
        page = self._current_page + 1

        if total == 0:
            self.pag_info_label.setText("No pending payments found")
        else:
            self.pag_info_label.setText(f"Showing {start+1}–{end} of {total} records")
        self.pag_page_label.setText(str(page))
        self.pag_prev_btn.setEnabled(page > 1)
        self.pag_next_btn.setEnabled(page < total_pages)
        self._render_table_page()

    def _render_table_page(self):
        c = self.colors
        self.alerts_table.setSortingEnabled(False)

        start = self._current_page * self._page_size
        end = min(start + self._page_size, len(self._all_alerts_data))
        page_data = self._all_alerts_data[start:end]
        self.alerts_table.setRowCount(len(page_data))

        for i, alert in enumerate(page_data):
            name = str(alert.get('customer_name') or 'N/A')
            mobile = str(alert.get('customer_mobile') or '')
            invoice = str(alert.get('invoice_number') or 'N/A')
            inv_date = str(alert.get('invoice_date') or '-')
            total_amt = float(alert.get('total_amount') or 0)
            balance_amt = float(alert.get('balance_amount') or 0)
            days = int(float(alert.get('days_pending') or 0))
            status_text = str(alert.get('payment_status') or 'Pending')

            self.alerts_table.setRowHeight(i, 52)

            # Col 0: # (Index)
            idx_item = QTableWidgetItem(str(start + i + 1))
            idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            idx_item.setForeground(QColor(c['muted']))
            idx_item.setFont(QFont("Segoe UI", 8.5, QFont.Weight.Medium))
            self.alerts_table.setItem(i, 0, idx_item)

            # Col 1: Customer Details (Avatar + Name + Mobile)
            search_str = f"{name} {mobile}"
            name_item = QTableWidgetItem(search_str)
            name_item.setForeground(QColor(0, 0, 0, 0))  # transparent search placeholder
            self.alerts_table.setItem(i, 1, name_item)

            cell_widget = QWidget()
            cell_widget.setStyleSheet("background: transparent; border: none;")
            cell_lay = QHBoxLayout(cell_widget)
            cell_lay.setContentsMargins(8, 4, 8, 4)
            cell_lay.setSpacing(10)

            avatar_char = name[0].upper() if name and name != 'N/A' else '?'
            avatar_lbl = QLabel(avatar_char)
            avatar_lbl.setFixedSize(30, 30)
            avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            avatar_bg = "#EF4444" if days > 30 else ("#F59E0B" if days > 15 else "#2563EB")
            avatar_lbl.setStyleSheet(f"""
                background-color: {avatar_bg}; color: white;
                border-radius: 15px; font-size: 10pt; font-weight: 700;
                border: none;
            """)
            cell_lay.addWidget(avatar_lbl)

            cust_text_col = QVBoxLayout()
            cust_text_col.setSpacing(1)
            cust_text_col.setContentsMargins(0, 0, 0, 0)
            display_name = name if len(name) <= 28 else name[:26] + '...'
            name_lbl = QLabel(display_name)
            name_lbl.setStyleSheet(f"color: {c['fg']}; font-size: 9.5pt; font-weight: 600; border: none; background: transparent;")
            cust_text_col.addWidget(name_lbl)

            if mobile:
                mob_lbl = QLabel(f"📞 {mobile}")
                mob_lbl.setStyleSheet(f"color: {c['muted']}; font-size: 8pt; border: none; background: transparent;")
                cust_text_col.addWidget(mob_lbl)
            cell_lay.addLayout(cust_text_col)
            cell_lay.addStretch()
            self.alerts_table.setCellWidget(i, 1, cell_widget)

            # Col 2: Invoice #
            inv_item = QTableWidgetItem(invoice)
            inv_item.setForeground(QColor(c['primary']))
            inv_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            inv_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.alerts_table.setItem(i, 2, inv_item)

            # Col 3: Invoice Date
            date_item = QTableWidgetItem(inv_date)
            date_item.setForeground(QColor(c['muted']))
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            date_item.setFont(QFont("Segoe UI", 8.5))
            self.alerts_table.setItem(i, 3, date_item)

            # Col 4: Total Billed
            total_str = f"{self.currency_symbol}{total_amt:,.0f}"
            tot_item = QTableWidgetItem(total_str)
            tot_item.setForeground(QColor(c['fg']))
            tot_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            tot_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
            self.alerts_table.setItem(i, 4, tot_item)

            # Col 5: Balance Due (Highlighted in red)
            bal_str = f"{self.currency_symbol}{balance_amt:,.0f}"
            bal_item = QTableWidgetItem(bal_str)
            bal_item.setForeground(QColor("#DC2626"))
            bal_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            bal_item.setFont(QFont("Segoe UI", 9.5, QFont.Weight.Bold))
            self.alerts_table.setItem(i, 5, bal_item)

            # Col 6: Overdue Days (Badge Chip)
            od_container = QWidget()
            od_container.setStyleSheet("background: transparent; border: none;")
            oc_lay = QHBoxLayout(od_container)
            oc_lay.setContentsMargins(4, 4, 4, 4)
            oc_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

            if days > 30:
                od_bg, od_fg, od_border, od_text = "#FEF2F2", "#DC2626", "#FECACA", f"🔥 {days}d Overdue"
            elif days > 15:
                od_bg, od_fg, od_border, od_text = "#FFFBEB", "#D97706", "#FDE68A", f"⏳ {days}d Pending"
            else:
                od_bg, od_fg, od_border, od_text = "#F0FDF4", "#16A34A", "#BBF7D0", f"✓ {days}d Recent"

            od_chip = QLabel(od_text)
            od_chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
            od_chip.setStyleSheet(f"""
                background-color: {od_bg}; color: {od_fg};
                border: 1px solid {od_border}; border-radius: 6px;
                font-size: 8pt; font-weight: 700;
                padding: 3px 8px;
            """)
            oc_lay.addWidget(od_chip)
            self.alerts_table.setCellWidget(i, 6, od_container)

            # Item text for filtering on Col 6
            od_dummy = QTableWidgetItem(f"{days} days")
            od_dummy.setForeground(QColor(0, 0, 0, 0))
            self.alerts_table.setItem(i, 6, od_dummy)

            # Col 7: Status Badge Chip
            st_container = QWidget()
            st_container.setStyleSheet("background: transparent; border: none;")
            sc_lay = QHBoxLayout(st_container)
            sc_lay.setContentsMargins(4, 4, 4, 4)
            sc_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

            if status_text.lower() == 'partial':
                st_bg, st_fg, st_border = "#EFF6FF", "#2563EB", "#BFDBFE"
            else:
                st_bg, st_fg, st_border = "#FEF2F2", "#DC2626", "#FECACA"

            status_chip = QLabel(status_text)
            status_chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_chip.setStyleSheet(f"""
                background-color: {st_bg}; color: {st_fg};
                border: 1px solid {st_border}; border-radius: 6px;
                font-size: 8pt; font-weight: 700;
                padding: 3px 10px;
            """)
            sc_lay.addWidget(status_chip)
            self.alerts_table.setCellWidget(i, 7, st_container)

            st_dummy = QTableWidgetItem(status_text)
            st_dummy.setForeground(QColor(0, 0, 0, 0))
            self.alerts_table.setItem(i, 7, st_dummy)

            # Col 8: Action Buttons (View + WA)
            action_widget = QWidget()
            action_widget.setStyleSheet("background: transparent; border: none;")
            action_lay = QHBoxLayout(action_widget)
            action_lay.setContentsMargins(4, 4, 4, 4)
            action_lay.setSpacing(6)
            action_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

            view_btn = QPushButton("View")
            view_btn.setToolTip("View full invoice and customer details")
            view_btn.setFixedSize(58, 28)
            view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            view_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c['hover']};
                    color: {c['fg']};
                    border: 1px solid {c['border']};
                    border-radius: 6px;
                    font-size: 8.5pt;
                    font-weight: 600;
                    padding: 0;
                }}
                QPushButton:hover {{
                    background-color: {c['border']};
                    border-color: {c['primary']};
                    color: {c['primary']};
                }}
            """)
            view_btn.clicked.connect(lambda checked, a=alert: self._show_alert_detail_obj(a))
            action_lay.addWidget(view_btn)

            wa_btn = QPushButton("Remind")
            wa_btn.setToolTip("Send WhatsApp payment reminder")
            wa_btn.setFixedSize(68, 28)
            wa_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            wa_btn.setStyleSheet("""
                QPushButton {
                    background-color: #059669;
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    font-size: 8.5pt;
                    font-weight: 700;
                    padding: 0;
                }
                QPushButton:hover {
                    background-color: #047857;
                }
                QPushButton:pressed {
                    background-color: #065F46;
                }
            """)
            wa_meta = {
                'customer_name': name, 'mobile': mobile, 'invoice': invoice,
                'amount': f"{self.currency_symbol}{balance_amt:,.2f}", 'days': days
            }
            wa_btn.clicked.connect(lambda checked, m=wa_meta: self._quick_wa_reminder(m))
            action_lay.addWidget(wa_btn)

            self.alerts_table.setCellWidget(i, 8, action_widget)

        self._apply_alert_filters()

    def _on_table_cell_double_clicked(self, row, col):
        """Handle double-clicking on a row to open details"""
        start = self._current_page * self._page_size
        idx = start + row
        if 0 <= idx < len(self._all_alerts_data):
            self._show_alert_detail_obj(self._all_alerts_data[idx])

    def _show_alert_detail_obj(self, alert):
        """Show full invoice details modal for a pending payment alert"""
        name = alert.get('customer_name') or 'N/A'
        mobile = alert.get('customer_mobile') or 'N/A'
        invoice = alert.get('invoice_number') or 'N/A'
        inv_date = alert.get('invoice_date') or '-'
        tot = float(alert.get('total_amount') or 0)
        bal = float(alert.get('balance_amount') or 0)
        days = int(float(alert.get('days_pending') or 0))
        status = alert.get('payment_status') or 'Pending'

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Pending Payment Details — {invoice}")
        dialog.setMinimumWidth(440)
        dialog.setStyleSheet(f"background-color: {self.colors['card_bg']}; color: {self.colors['fg']};")

        dlg_lay = QVBoxLayout(dialog)
        dlg_lay.setContentsMargins(24, 20, 24, 20)
        dlg_lay.setSpacing(14)

        t_lbl = QLabel(f"📄 Invoice #{invoice}")
        t_lbl.setStyleSheet(f"font-size: 14pt; font-weight: 800; color: {self.colors['primary']};")
        dlg_lay.addWidget(t_lbl)

        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.colors['bg']};
                border: 1px solid {self.colors['border']};
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        ifl = QVBoxLayout(info_frame)
        ifl.setSpacing(8)

        def add_info_row(label, val, val_color=None):
            r = QHBoxLayout()
            l = QLabel(label)
            l.setStyleSheet(f"font-size: 9pt; color: {self.colors['muted']}; font-weight: 600;")
            v = QLabel(str(val))
            vc = val_color or self.colors['fg']
            v.setStyleSheet(f"font-size: 9.5pt; color: {vc}; font-weight: 700;")
            r.addWidget(l)
            r.addStretch()
            r.addWidget(v)
            ifl.addLayout(r)

        add_info_row("Customer:", name)
        add_info_row("Mobile:", mobile)
        add_info_row("Invoice Date:", inv_date)
        add_info_row("Total Amount:", f"{self.currency_symbol}{tot:,.2f}")
        add_info_row("Pending Balance:", f"{self.currency_symbol}{bal:,.2f}", "#DC2626")
        add_info_row("Days Pending:", f"{days} Days", "#F59E0B" if days <= 30 else "#DC2626")
        add_info_row("Status:", status, "#2563EB" if status == 'Partial' else "#D97706")

        dlg_lay.addWidget(info_frame)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        wa_btn = QPushButton("💬 Send WhatsApp Reminder")
        wa_btn.setFixedHeight(34)
        wa_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        wa_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #25D366, stop:1 #128C7E);
                color: white; border: none; border-radius: 6px; font-size: 9pt; font-weight: 600;
                padding: 0 14px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2ecc71, stop:1 #1da851); }
        """)
        wa_meta = {
            'customer_name': name, 'mobile': mobile, 'invoice': invoice,
            'amount': f"{self.currency_symbol}{bal:,.2f}", 'days': days
        }
        wa_btn.clicked.connect(lambda: [dialog.accept(), self._quick_wa_reminder(wa_meta)])
        btn_row.addWidget(wa_btn)

        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(34)
        close_btn.clicked.connect(dialog.accept)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['hover']}; color: {self.colors['fg']};
                border: 1px solid {self.colors['border']}; border-radius: 6px;
                padding: 0 16px; font-size: 9pt; font-weight: 600;
            }}
        """)
        btn_row.addWidget(close_btn)

        dlg_lay.addLayout(btn_row)
        dialog.exec_()

    def _show_alert_detail(self, customer_name, invoice):
        """Legacy fallback"""
        match = next((a for a in self._all_alerts_data if a.get('invoice_number') == invoice), None)
        if match:
            self._show_alert_detail_obj(match)
        else:
            QMessageBox.information(self, "Details", f"Customer: {customer_name}\nInvoice: {invoice}")

    def _quick_wa_reminder(self, meta):
        mobile = meta['mobile']
        if not mobile or mobile == 'N/A' or not mobile.strip():
            QMessageBox.warning(self, "No Mobile", f"No mobile number for {meta['customer_name']}")
            return
        reply = QMessageBox.question(
            self, "Send Reminder",
            f"Send payment reminder to {meta['customer_name']}?\n"
            f"Mobile: {mobile}\nInvoice: {meta['invoice']}\nAmount: {meta['amount']}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            self._do_send_wa(meta['customer_name'], mobile, meta['invoice'], meta['amount'])

    def load_dashboard_data(self):
        """Load dashboard data from database"""
        self.show_loading("Loading dashboard...")
        self.run_in_thread(
            self._load_data_thread,
            self._update_ui,
            self._on_dashboard_error
        )

    def _on_dashboard_error(self, err):
        self.hide_loading()
        self._default_error_handler(err)

    def _load_data_thread(self):
        """Load data in background thread"""
        from database.db_connection import DatabaseContext

        # Calculate date range
        today = datetime.now().date()

        if self.period == 'today':
            start_date = today
            end_date = today
            range_text = today.strftime('%d %b, %Y')
        elif self.period == 'this_week':
            start_date = today - timedelta(days=today.weekday())
            end_date = today
            range_text = f"{start_date.strftime('%d %b')} - {today.strftime('%d %b, %Y')}"
        elif self.period == 'this_month':
            start_date = today.replace(day=1)
            end_date = today
            range_text = today.strftime('%B %Y')
        else:  # this_year
            start_date = today.replace(month=1, day=1)
            end_date = today
            range_text = str(today.year)

        with DatabaseContext() as db:
            # Total customers
            result = db.execute_query(
                "SELECT COUNT(*) as count FROM customers WHERE is_active = TRUE",
                fetch_one=True
            )
            total_customers = result['count'] if result else 0

            # Total revenue for period
            query = """
                SELECT COALESCE(SUM(total_amount), 0) as revenue FROM invoices
                WHERE is_active = TRUE AND DATE(created_at) BETWEEN %s AND %s
            """
            result = db.execute_query(query, (start_date, end_date), fetch_one=True)
            total_revenue = result['revenue'] if result else 0

            # Today's services
            query = """
                SELECT COUNT(*) as count FROM invoices
                WHERE is_active = TRUE AND DATE(created_at) = CURDATE()
            """
            result = db.execute_query(query, fetch_one=True)
            today_services = result['count'] if result else 0

            # Total invoices for period
            total_invoices_query = """
                SELECT COUNT(*) as count
                FROM invoices
                WHERE is_active=TRUE AND DATE(created_at) BETWEEN %s AND %s
            """
            result = db.execute_query(total_invoices_query, (start_date, end_date), fetch_one=True)
            total_invoices = result['count'] if result else 0

            # Additional KPIs via the dashboard controller
            active_amc = 0
            pending_payments = 0
            online_requests = 0
            try:
                from controllers.dashboard_controller import DashboardController
                controller = DashboardController(db)
                stats = controller.get_dashboard_stats(self.period)
                active_amc = (stats.get('amc_stats') or {}).get('total_active', 0)
                pending_payments = len(stats.get('pending_payments') or [])
                online_requests = stats.get('online_requests', 0)
            except Exception:
                pass

            return {
                'total_customers': total_customers,
                'total_revenue': total_revenue,
                'today_services': today_services,
                'total_invoices': total_invoices,
                'active_amc': active_amc,
                'pending_payments': pending_payments,
                'online_requests': online_requests,
                'range_text': range_text
            }

    def _update_ui(self, data):
        """Update UI with loaded data"""
        try:
            if 'total_customers' in self.metric_cards:
                self.metric_cards['total_customers'].set_value(str(data['total_customers']))
            if 'total_revenue' in self.metric_cards:
                self.metric_cards['total_revenue'].set_value(f"{self.currency_symbol}{data['total_revenue']:,.0f}")
            if 'today_services' in self.metric_cards:
                self.metric_cards['today_services'].set_value(str(data['today_services']))
            if 'total_invoices' in self.metric_cards:
                self.metric_cards['total_invoices'].set_value(str(data['total_invoices']))
            if 'active_amc' in self.metric_cards:
                self.metric_cards['active_amc'].set_value(str(data.get('active_amc', 0)))
            if 'pending_payments' in self.metric_cards:
                self.metric_cards['pending_payments'].set_value(str(data.get('pending_payments', 0)))
            if 'online_requests' in self.metric_cards:
                self.metric_cards['online_requests'].set_value(str(data.get('online_requests', 0)))
            
            self.date_range_label.setText(f"({data['range_text']})")
        except Exception as e:
            print(f"Error updating dashboard UI: {e}")
        finally:
            self.hide_loading()

    def _on_card_clicked(self, metric_name):
        """Handle metric card click - show detailed view"""
        dialog = DetailViewDialog(self, metric_name, self.loaded_data, self.period)
        dialog.exec_()

    def _on_period_change(self, text):
        """Handle period filter change"""
        period_map = {
            'Today': 'today',
            'This Week': 'this_week',
            'This Month': 'this_month',
            'This Year': 'this_year'
        }
        self.period = period_map.get(text, 'today')
        self.load_dashboard_data()
        self.load_analytics_data()

    def load_analytics_data(self):
        """Load pending payments data in background thread"""
        self.show_loading("Loading pending payments...")
        self.run_in_thread(
            self._load_analytics_thread,
            self._update_analytics_ui,
            self._on_analytics_error
        )

    def _on_analytics_error(self, err):
        self.hide_loading()
        self._default_error_handler(err)

    def _load_analytics_thread(self):
        """Load pending payments data from database"""
        from database.db_connection import DatabaseContext
        
        with DatabaseContext() as db:
            from controllers.dashboard_controller import DashboardController
            controller = DashboardController(db)
            
            alerts = controller.get_payment_pending_alerts(limit=200) or []
            return {'payment_alerts': alerts}

    def _update_analytics_ui(self, data):
        """Update pending payments UI with loaded data"""
        try:
            self._update_payment_alerts(data.get('payment_alerts', []))
        except Exception as e:
            print(f"Error updating pending payments UI: {e}")
        finally:
            self.hide_loading()

    def _update_payment_alerts(self, alerts_data):
        """Update payment alerts summary cards and data (respects Privacy Shield)"""
        self._all_alerts_data = alerts_data if alerts_data else []
        self._current_page = 0
        self._render_pagination()

        # Summary cards calculation
        total_due = sum(float(a.get('balance_amount') or 0) for a in self._all_alerts_data) if self._all_alerts_data else 0
        customer_count = len(self._all_alerts_data) if self._all_alerts_data else 0
        avg_delay = int(sum(int(float(a.get('days_pending') or 0)) for a in self._all_alerts_data) / max(len(self._all_alerts_data), 1)) if self._all_alerts_data else 0
        urgent_count = sum(1 for a in self._all_alerts_data if int(float(a.get('days_pending') or 0)) > 30) if self._all_alerts_data else 0

        self._alert_due_raw = f"{self.currency_symbol}{total_due:,.0f}"

        # Check Privacy Shield status
        try:
            from utils.privacy_manager import get_privacy_manager
            is_priv = get_privacy_manager().is_privacy_enabled()
        except Exception:
            is_priv = False

        if is_priv and not getattr(self, '_alert_due_peeked', False):
            total_due_str = f"{self.currency_symbol} ••••••"
        else:
            total_due_str = self._alert_due_raw

        # Update card values
        for card, val in [
            (self.alert_pending_count_card, str(customer_count)),
            (self.alert_total_due_card, total_due_str),
            (self.alert_urgent_card, str(urgent_count)),
            (self.alert_avg_delay_card, f"{avg_delay} Days")
        ]:
            if card:
                vlabel = card.findChild(QLabel, "crmStatValue")
                if vlabel:
                    vlabel.setText(val)

        if hasattr(self, 'pending_badge_label'):
            self.pending_badge_label.setText(f"{customer_count} Pending")

        if hasattr(self, 'alert_record_count_label'):
            self.alert_record_count_label.setText(f"{customer_count} records")

    def _send_whatsapp_reminder(self):
        selected = self.alerts_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a customer row first.")
            return
        row = selected[0].row()
        inv_item = self.alerts_table.item(row, 2)
        if not inv_item:
            QMessageBox.warning(self, "Error", "Could not identify the selected row.")
            return
        invoice_no = inv_item.text().strip()
        start = self._current_page * self._page_size
        page_data = self._all_alerts_data[start:start + self._page_size]
        match = next((a for a in page_data if str(a.get('invoice_number')) == invoice_no), None)
        if not match:
            # Search all alerts if not in current page slice
            match = next((a for a in self._all_alerts_data if str(a.get('invoice_number')) == invoice_no), None)
        if not match:
            QMessageBox.warning(self, "Error", "Could not retrieve customer data.")
            return
        name = match.get('customer_name') or 'N/A'
        mobile = match.get('customer_mobile') or ''
        if not mobile.strip():
            QMessageBox.warning(self, "No Mobile", f"No mobile number for {name}")
            return
        amt = f"{self.currency_symbol}{float(match.get('balance_amount') or 0):,.2f}"
        reply = QMessageBox.question(
            self, "Send Reminder",
            f"Send reminder to {name}?\nMobile: {mobile}\nInvoice: {invoice_no}\nAmount: {amt}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            self._do_send_wa(name, mobile, invoice_no, amt)

    def _do_send_wa(self, name, mobile, invoice, amount):
        try:
            from utils.whatsapp_helper import WhatsAppHelper
            from utils.whatsapp_messages import format_message
            from datetime import datetime
            message = format_message(
                'payment_reminder', name=name, invoice_number=invoice,
                amount=amount.replace(self.currency_symbol, '').replace(',', ''),
                invoice_date=datetime.now().strftime('%d-%m-%Y')
            )
            WhatsAppHelper.send_message(mobile, message)
            self.show_success_message("Payment reminder sent!")
        except Exception as e:
            self.show_error_message(f"WhatsApp error: {str(e)}")

    def _export_pending_payments_to_excel(self):
        """Export pending payments register to Excel with executive dashboard, charts and formulas"""
        from datetime import datetime
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from utils.excel_helper import ExcelExporter

        alerts = getattr(self, '_all_alerts_data', []) or []
        if not alerts:
            QMessageBox.warning(self, "No Data", "No pending payments available to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Pending Payments",
            f"Pending_Payments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel Files (*.xlsx)"
        )
        if not file_path:
            return

        try:
            headers = [
                "Invoice #", "Customer Name", "Mobile Number", "Invoice Date",
                "Total Billed", "Advance Paid", "Pending Due", "Days Pending", "Urgency Status"
            ]
            rows = []
            tot_billed = 0.0
            tot_advance = 0.0
            tot_due = 0.0
            urgent_count = 0
            moderate_count = 0
            recent_count = 0

            for a in alerts:
                inv_no = str(a.get('invoice_number') or 'N/A')
                c_name = str(a.get('customer_name') or 'N/A')
                mobile = str(a.get('customer_mobile') or '')
                inv_date = str(a.get('invoice_date') or '-')
                b_amt = float(a.get('total_amount') or 0)
                bal = float(a.get('balance_amount') or 0)
                adv = max(0.0, b_amt - bal)
                days = int(float(a.get('days_pending') or 0))

                tot_billed += b_amt
                tot_advance += adv
                tot_due += bal

                if days > 30:
                    urgency = "High (>30 Days)"
                    urgent_count += 1
                elif days >= 15:
                    urgency = "Medium (15-30 Days)"
                    moderate_count += 1
                else:
                    urgency = "Recent (<15 Days)"
                    recent_count += 1

                rows.append([
                    inv_no, c_name, mobile, inv_date,
                    b_amt, adv, bal, days, urgency
                ])

            kpis = [
                ("Pending Invoices", len(alerts)),
                ("Total Outstanding", tot_due),
                ("Total Original Billed", tot_billed),
                ("Realized Advance", tot_advance),
                ("Critical Delays (>30d)", urgent_count),
                ("Recovery Target", f"{tot_billed and (tot_due / tot_billed * 100):.1f}%"),
            ]

            charts_data = [
                {
                    'type': 'pie',
                    'title': 'Aging & Urgency Distribution',
                    'categories': ['Critical (>30d)', 'Moderate (15-30d)', 'Recent (<15d)'],
                    'values': [('Invoices', [urgent_count, moderate_count, recent_count])],
                },
                {
                    'type': 'bar',
                    'title': 'Receivables Financial Breakdown',
                    'categories': ['Total Billed', 'Realized Advance', 'Outstanding Due'],
                    'values': [('Amount', [tot_billed, tot_advance, tot_due])],
                    'y_axis': f'Amount ({self.currency_symbol})'
                }
            ]

            wb = ExcelExporter.build_excel(
                sheet_title='Pending Payments',
                title_text='Pending Payments & Collections Register',
                subtitle_text=f'Total: {len(alerts)} pending invoices | Outstanding: {self.currency_symbol}{tot_due:,.2f}',
                headers=headers,
                rows=rows,
                number_cols={5, 6, 7},
                kpis=kpis,
                charts_data=charts_data,
                freeze_col=True
            )

            wb.save(file_path)
            QMessageBox.information(self, "Export Successful", f"✅ Pending payments successfully exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export pending payments:\n{str(e)}")

    def refresh_data(self):
        """Refresh dashboard data"""
        self.load_dashboard_data()

    def reload_ui_settings(self):
        """Reload UI settings from DB - called after settings save"""
        self.currency_symbol = get_setting("currency_symbol", "\u20b9")
        self.refresh_data()
        self.load_analytics_data()
