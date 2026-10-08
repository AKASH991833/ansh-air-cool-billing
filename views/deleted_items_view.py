"""
Deleted Items (Recycle Bin) View - Enterprise Standard
Displays all soft-deleted records across all software sections:
AC Brands, Customers, Technicians, Services, Inventory Parts, Invoices, AMC Contracts, and Daily Logs.
Includes full human-readable joins, formatted currency/dates, real-time search, and instant restoration.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFrame, QTabWidget, QAbstractItemView, QLineEdit, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QCursor

from database.db_connection import DatabaseContext
from utils.unified_theme import UnifiedTheme
from utils.formatters import Formatters
from utils.app_settings import get_setting


class DeletedTableView(QWidget):
    """A single table view for one category of deleted records with real-time search and restoration"""
    data_restored = Signal(str, int)  # table_name, record_id

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.theme_manager = UnifiedTheme()
        self.raw_records = []
        self.filtered_records = []
        self.currency_symbol = get_setting("currency_symbol", "₹")
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        colors = self.theme_manager.get_colors()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # Header with icon, label and counter
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        icon_lbl = QLabel(self.config['icon'])
        icon_lbl.setStyleSheet("font-size: 16pt; background: transparent;")
        header_row.addWidget(icon_lbl)

        title_lbl = QLabel(f"Deleted {self.config['label']}")
        title_lbl.setStyleSheet(f"font-size: 13pt; font-weight: 700; color: {colors['fg']}; background: transparent;")
        header_row.addWidget(title_lbl)

        header_row.addStretch()

        self.count_badge = QLabel("0 deleted")
        self.count_badge.setStyleSheet("""
            font-size: 8.5pt; font-weight: 700;
            color: #b91c1c; background-color: #fee2e2;
            border: 1px solid #fecaca; border-radius: 12px;
            padding: 3px 12px;
        """)
        header_row.addWidget(self.count_badge)
        layout.addLayout(header_row)

        # Table Widget
        self.table = QTableWidget()
        cols = self.config['columns'] + ['Actions']
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(42)
        self.table.setShowGrid(True)
        self.table.setGridStyle(Qt.PenStyle.SolidLine)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Clean enterprise styling (No harsh red/yellow)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #ffffff;
                color: #0f172a;
                border: 1px solid {colors['border']};
                border-radius: 8px;
                gridline-color: #e2e8f0;
                selection-background-color: #eff6ff;
                selection-color: #0f172a;
                alternate-background-color: #f8fafc;
            }}
            QHeaderView::section {{
                background-color: #f1f5f9;
                color: #334155;
                font-weight: 700;
                font-size: 8.5pt;
                padding: 8px 10px;
                border: none;
                border-bottom: 2px solid #cbd5e1;
                border-right: 1px solid #e2e8f0;
                letter-spacing: 0.2px;
            }}
            QHeaderView::section:last {{
                border-right: none;
            }}
            QTableWidget::item {{
                padding: 6px 10px;
                border-bottom: 1px solid #e2e8f0;
                font-size: 8.5pt;
            }}
        """)

        th = self.table.horizontalHeader()
        th.setStretchLastSection(False)
        th.setHighlightSections(False)
        th.setMinimumSectionSize(70)

        # Set column widths based on config
        for i, w in enumerate(self.config.get('col_widths', [])):
            self.table.setColumnWidth(i, w)
        # Last column (Actions)
        self.table.setColumnWidth(len(cols) - 1, 140)
        th.setSectionResizeMode(QHeaderView.Interactive)

        layout.addWidget(self.table)

        # Empty state
        self.empty_state = self._make_empty_state()
        self.empty_state.setVisible(False)
        layout.addWidget(self.empty_state)

    def _make_empty_state(self):
        colors = self.theme_manager.get_colors()
        container = QFrame()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 40, 0, 40)

        icon_lbl = QLabel("✨")
        icon_lbl.setStyleSheet("font-size: 32pt; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_lbl)

        msg_lbl = QLabel(f"No deleted {self.config['label']} found")
        msg_lbl.setStyleSheet(f"color: {colors['fg']}; font-size: 11pt; font-weight: 700; background: transparent;")
        msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg_lbl)

        hint_lbl = QLabel("All records in this category are active and healthy.")
        hint_lbl.setStyleSheet(f"color: {colors['muted']}; font-size: 8.5pt; background: transparent;")
        hint_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_lbl)
        return container

    def _load_data(self, search_text=""):
        try:
            with DatabaseContext() as db:
                query = self.config.get('query')
                if not query:
                    query = f"SELECT * FROM {self.config['table']} WHERE is_active = FALSE ORDER BY id DESC"
                records = db.execute_query(query, fetch_all=True) or []
        except Exception as e:
            print(f"Error loading deleted {self.config['table']}: {e}")
            records = []

        self.raw_records = records
        self._filter_and_render(search_text)

    def _filter_and_render(self, search_text=""):
        st = search_text.strip().lower()
        if st:
            self.filtered_records = []
            for r in self.raw_records:
                match = False
                for k, v in r.items():
                    if v and st in str(v).lower():
                        match = True
                        break
                if match:
                    self.filtered_records.append(r)
        else:
            self.filtered_records = self.raw_records

        cnt = len(self.filtered_records)
        raw_cnt = len(self.raw_records)
        if raw_cnt == 0:
            self.count_badge.setText("All Clear (0)")
            self.count_badge.setStyleSheet("""
                font-size: 8.5pt; font-weight: 700;
                color: #059669; background-color: #ecfdf5;
                border: 1px solid #a7f3d0; border-radius: 12px;
                padding: 3px 12px;
            """)
        else:
            self.count_badge.setText(f"{raw_cnt} deleted record{'s' if raw_cnt != 1 else ''}")
            self.count_badge.setStyleSheet("""
                font-size: 8.5pt; font-weight: 700;
                color: #b91c1c; background-color: #fee2e2;
                border: 1px solid #fecaca; border-radius: 12px;
                padding: 3px 12px;
            """)

        if not self.filtered_records:
            self.table.setVisible(False)
            self.empty_state.setVisible(True)
            return

        self.table.setVisible(True)
        self.empty_state.setVisible(False)
        self.table.setRowCount(0)

        sym = self.currency_symbol

        for row, rec in enumerate(self.filtered_records):
            self.table.insertRow(row)

            for col, extractor in enumerate(self.config['extractors']):
                text, align, is_badge, is_currency = extractor(rec, sym)
                item = QTableWidgetItem(text)
                item.setTextAlignment(align | Qt.AlignVCenter)
                item.setToolTip(text)

                if is_badge:
                    item.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                    item.setForeground(QColor("#b91c1c"))
                    item.setBackground(QColor("#fee2e2"))
                elif is_currency:
                    item.setFont(QFont("Segoe UI", 8.5, QFont.Weight.Bold))
                    item.setForeground(QColor("#0284c7"))

                self.table.setItem(row, col, item)

            # Actions cell with Restore Button
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(6, 2, 6, 2)
            action_layout.setSpacing(6)

            restore_btn = QPushButton("♻️ Restore")
            restore_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            restore_btn.setFixedHeight(28)
            restore_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #059669, stop:1 #047857);
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    padding: 0 14px;
                    font-size: 8.5pt;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #10b981, stop:1 #059669);
                }
            """)
            record_id = rec.get(self.config['id_field'], rec.get('id'))
            item_name = rec.get(self.config.get('identifier_field', 'name'), f"ID #{record_id}")
            restore_btn.clicked.connect(lambda checked, rid=record_id, iname=item_name: self._restore_record(rid, iname))
            action_layout.addWidget(restore_btn)

            self.table.setCellWidget(row, len(self.config['columns']), action_widget)

    def _restore_record(self, record_id, item_name):
        res = QMessageBox.question(
            self,
            "Confirm Restore",
            f"Are you sure you want to restore:\n\n{self.config['label']}: {item_name}\n\nThis record will immediately become active across the software.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if res != QMessageBox.StandardButton.Yes:
            return

        try:
            with DatabaseContext() as db:
                db.execute_query(
                    f"UPDATE {self.config['table']} SET is_active = TRUE WHERE {self.config['id_field']} = %s",
                    (record_id,)
                )

            # Fire real-time notification
            try:
                from utils.event_bus import EventBus
                eb = EventBus()
                eb.emit_master_data_updated(self.config['table'])
            except Exception:
                pass

            QMessageBox.information(self, "Record Restored", f"Successfully restored '{item_name}' into {self.config['label']}.")
            self._load_data()
            self.data_restored.emit(self.config['table'], record_id)
        except Exception as e:
            QMessageBox.critical(self, "Restore Error", f"Failed to restore record: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# FIELD EXTRACTOR HELPERS (HUMAN-READABLE FORMATTING FOR ALL SUB-SECTIONS)
# ─────────────────────────────────────────────────────────────────────────────
def _ex_str(field, align=Qt.AlignLeft):
    return lambda r, s: (str(r.get(field, '') or ''), align, False, False)

def _ex_date(field):
    return lambda r, s: (Formatters.format_date(r.get(field)) if r.get(field) else '', Qt.AlignCenter, False, False)

def _ex_mobile(field):
    return lambda r, s: (Formatters.format_mobile(str(r.get(field, '') or '')) if r.get(field) else '', Qt.AlignCenter, False, False)

def _ex_curr(field):
    def _fn(r, s):
        val = float(r.get(field, 0) or 0)
        return (f"{s}{val:,.2f}", Qt.AlignRight, False, True)
    return _fn

def _ex_pct(field):
    return lambda r, s: (f"{float(r.get(field, 0) or 0):.1f}%", Qt.AlignCenter, False, False)

def _ex_status():
    return lambda r, s: ("● Deleted", Qt.AlignCenter, True, False)


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION FOR ALL 8 SUB-SECTIONS
# ─────────────────────────────────────────────────────────────────────────────
SECTION_CONFIG = [
    {
        'table': 'ac_brands',
        'label': 'AC Brands',
        'icon': '🏷️',
        'columns': ['ID', 'Brand Name', 'Date Added', 'Status'],
        'col_widths': [80, 240, 140, 110],
        'id_field': 'id',
        'identifier_field': 'brand_name',
        'query': "SELECT id, brand_name, created_at, is_active FROM ac_brands WHERE is_active = FALSE ORDER BY id DESC",
        'extractors': [
            _ex_str('id', Qt.AlignCenter),
            _ex_str('brand_name', Qt.AlignLeft),
            _ex_date('created_at'),
            _ex_status(),
        ]
    },
    {
        'table': 'customers',
        'label': 'Customers',
        'icon': '👤',
        'columns': ['ID', 'Customer Name', 'Mobile Number', 'City / Location', 'Email', 'Status'],
        'col_widths': [75, 170, 130, 220, 170, 110],
        'id_field': 'id',
        'identifier_field': 'name',
        'query': "SELECT id, name, mobile, address, city, email, is_active FROM customers WHERE is_active = FALSE ORDER BY id DESC",
        'extractors': [
            _ex_str('id', Qt.AlignCenter),
            _ex_str('name', Qt.AlignLeft),
            _ex_mobile('mobile'),
            lambda r, s: (f"{r.get('city') or ''} {r.get('address') or ''}".strip(), Qt.AlignLeft, False, False),
            _ex_str('email', Qt.AlignLeft),
            _ex_status(),
        ]
    },
    {
        'table': 'technicians',
        'label': 'Technicians',
        'icon': '🔧',
        'columns': ['ID', 'Technician Name', 'Mobile Number', 'Specialization', 'Commission', 'Status'],
        'col_widths': [75, 180, 130, 200, 110, 110],
        'id_field': 'id',
        'identifier_field': 'name',
        'query': "SELECT id, name, mobile, specialization, commission_rate, is_active FROM technicians WHERE is_active = FALSE ORDER BY id DESC",
        'extractors': [
            _ex_str('id', Qt.AlignCenter),
            _ex_str('name', Qt.AlignLeft),
            _ex_mobile('mobile'),
            _ex_str('specialization', Qt.AlignLeft),
            _ex_pct('commission_rate'),
            _ex_status(),
        ]
    },
    {
        'table': 'services',
        'label': 'Services',
        'icon': '🛠️',
        'columns': ['ID', 'Service Title', 'Description', 'Standard Rate (₹)', 'Status'],
        'col_widths': [75, 220, 260, 130, 110],
        'id_field': 'id',
        'identifier_field': 'service_name',
        'query': "SELECT id, service_name, description, default_rate, is_active FROM services WHERE is_active = FALSE ORDER BY id DESC",
        'extractors': [
            _ex_str('id', Qt.AlignCenter),
            _ex_str('service_name', Qt.AlignLeft),
            _ex_str('description', Qt.AlignLeft),
            _ex_curr('default_rate'),
            _ex_status(),
        ]
    },
    {
        'table': 'parts',
        'label': 'Parts (Inventory)',
        'icon': '📦',
        'columns': ['ID', 'Part Name', 'Category', 'Unit Rate (₹)', 'Stock Qty', 'Status'],
        'col_widths': [75, 220, 150, 130, 100, 110],
        'id_field': 'id',
        'identifier_field': 'part_name',
        'query': "SELECT id, part_name, category, default_rate, stock_quantity, unit, is_active FROM parts WHERE is_active = FALSE ORDER BY id DESC",
        'extractors': [
            _ex_str('id', Qt.AlignCenter),
            _ex_str('part_name', Qt.AlignLeft),
            _ex_str('category', Qt.AlignCenter),
            _ex_curr('default_rate'),
            lambda r, s: (f"{int(r.get('stock_quantity', 0) or 0)} {r.get('unit', '')}", Qt.AlignCenter, False, False),
            _ex_status(),
        ]
    },
    {
        'table': 'invoices',
        'label': 'Invoices',
        'icon': '📄',
        'columns': ['ID', 'Invoice Number', 'Customer Name', 'Mobile Number', 'Invoice Date', 'Total Amount (₹)', 'Payment Status', 'Status'],
        'col_widths': [75, 140, 160, 120, 105, 125, 115, 110],
        'id_field': 'id',
        'identifier_field': 'invoice_number',
        'query': """
            SELECT i.id, i.invoice_number, c.name as customer_name, c.mobile as customer_mobile,
                   i.created_at, i.total_amount, i.payment_status, i.is_active
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            WHERE i.is_active = FALSE
            ORDER BY i.id DESC
        """,
        'extractors': [
            _ex_str('id', Qt.AlignCenter),
            _ex_str('invoice_number', Qt.AlignCenter),
            _ex_str('customer_name', Qt.AlignLeft),
            _ex_mobile('customer_mobile'),
            _ex_date('created_at'),
            _ex_curr('total_amount'),
            _ex_str('payment_status', Qt.AlignCenter),
            _ex_status(),
        ]
    },
    {
        'table': 'amc_contracts',
        'label': 'AMC Contracts',
        'icon': '🛡️',
        'columns': ['ID', 'Contract No', 'Customer Name', 'Mobile Number', 'Plan Type', 'Start Date', 'End Date', 'Contract Value (₹)', 'Contract Status', 'Status'],
        'col_widths': [70, 115, 160, 115, 130, 95, 95, 125, 115, 110],
        'id_field': 'id',
        'identifier_field': 'amc_id',
        'query': """
            SELECT a.id, a.amc_id, c.name as customer_name, c.mobile as customer_mobile,
                   a.contract_type as plan_type, a.start_date, a.end_date, a.total_amount, a.amc_status, a.is_active
            FROM amc_contracts a
            LEFT JOIN customers c ON a.customer_id = c.id
            WHERE a.is_active = FALSE
            ORDER BY a.id DESC
        """,
        'extractors': [
            _ex_str('id', Qt.AlignCenter),
            _ex_str('amc_id', Qt.AlignCenter),
            _ex_str('customer_name', Qt.AlignLeft),
            _ex_mobile('customer_mobile'),
            _ex_str('plan_type', Qt.AlignCenter),
            _ex_date('start_date'),
            _ex_date('end_date'),
            _ex_curr('total_amount'),
            _ex_str('amc_status', Qt.AlignCenter),
            _ex_status(),
        ]
    },
    {
        'table': 'daily_logs',
        'label': 'Daily Logs',
        'icon': '📋',
        'columns': ['ID', 'Visit Date', 'Customer Name', 'Mobile Number', 'Site Address', 'Technician', 'Billed Amount (₹)', 'Collected (₹)', 'Status'],
        'col_widths': [75, 100, 150, 120, 200, 140, 120, 120, 110],
        'id_field': 'id',
        'identifier_field': 'customer_name',
        'query': """
            SELECT id, log_date, customer_name, customer_mobile, customer_address, technician_name,
                   total_billed, total_payment, is_active
            FROM daily_logs
            WHERE is_active = FALSE
            ORDER BY id DESC
        """,
        'extractors': [
            _ex_str('id', Qt.AlignCenter),
            _ex_date('log_date'),
            _ex_str('customer_name', Qt.AlignLeft),
            _ex_mobile('customer_mobile'),
            _ex_str('customer_address', Qt.AlignLeft),
            _ex_str('technician_name', Qt.AlignLeft),
            _ex_curr('total_billed'),
            _ex_curr('total_payment'),
            _ex_status(),
        ]
    },
]


class DeletedItemsView(QWidget):
    """Enterprise Master View for all Soft-Deleted Records across the entire business suite"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_manager = UnifiedTheme()
        self.table_views = []
        self._setup_ui()

    def update_theme_colors(self):
        colors = self.theme_manager.get_colors()
        self.theme_manager.apply_palette(self)
        self.setStyleSheet(self.theme_manager.get_main_stylesheet())
        self.refresh_data()

    def _setup_ui(self):
        colors = self.theme_manager.get_colors()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Row
        header_row = QHBoxLayout()
        header_row.setSpacing(14)

        header_icon = QLabel("🗑️")
        header_icon.setStyleSheet("font-size: 24pt; background: transparent;")
        header_row.addWidget(header_icon)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        page_title = QLabel("Deleted Items & Recycle Bin")
        page_title.setStyleSheet(f"font-size: 18pt; font-weight: 800; color: {colors['fg']}; letter-spacing: -0.4px;")
        title_box.addWidget(page_title)

        desc = QLabel("Centralized safety recovery center: Review and restore accidentally deleted records across all software sections.")
        desc.setStyleSheet(f"font-size: 8.5pt; color: {colors['muted']}; font-weight: 500;")
        title_box.addWidget(desc)
        header_row.addLayout(title_box)

        header_row.addStretch()

        # Real-time search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search deleted records (name, mobile, invoice...)...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setFixedWidth(320)
        self.search_input.setFixedHeight(36)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors['card_bg']};
                color: {colors['fg']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                padding: 0 12px;
                font-size: 9pt;
            }}
            QLineEdit:focus {{
                border-color: {colors['primary']};
            }}
        """)
        self.search_input.textChanged.connect(self._on_search_changed)
        header_row.addWidget(self.search_input)

        # Refresh button
        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_refresh.setFixedHeight(36)
        btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['card_bg']};
                color: {colors['fg']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                padding: 0 16px;
                font-weight: 600;
                font-size: 9pt;
            }}
            QPushButton:hover {{
                border-color: {colors['primary']};
                color: {colors['primary']};
            }}
        """)
        btn_refresh.clicked.connect(self.refresh_data)
        header_row.addWidget(btn_refresh)

        layout.addLayout(header_row)

        # Content Card with Tabs
        content_frame = QFrame()
        content_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['card_bg']};
                border: 1px solid {colors['border']};
                border-radius: 12px;
            }}
        """)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(10, 8, 10, 10)
        content_layout.setSpacing(6)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: transparent;
                margin-top: 2px;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {colors['muted']};
                padding: 8px 16px;
                font-weight: 600;
                font-size: 9pt;
                border: none;
                border-bottom: 2.5px solid transparent;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                color: #b91c1c;
                font-weight: 700;
                border-bottom: 2.5px solid #dc2626;
            }}
            QTabBar::tab:hover:!selected {{
                color: {colors['fg']};
                background: {colors['hover']}50;
                border-radius: 6px 6px 0 0;
            }}
        """)
        content_layout.addWidget(self.tabs)
        layout.addWidget(content_frame, 1)

        # Initialize all 8 sub-sections
        for cfg in SECTION_CONFIG:
            tv = DeletedTableView(cfg, parent=self)
            tv.data_restored.connect(self._on_item_restored)
            self.tabs.addTab(tv, f"{cfg['icon']}  {cfg['label']}")
            self.table_views.append(tv)

        self._update_tab_badges()

    def _on_search_changed(self, text):
        idx = self.tabs.currentIndex()
        if 0 <= idx < len(self.table_views):
            self.table_views[idx]._filter_and_render(text)

    def _update_tab_badges(self):
        for idx, tv in enumerate(self.table_views):
            cnt = len(tv.raw_records)
            icon = tv.config['icon']
            label = tv.config['label']
            badge = f" ({cnt})" if cnt > 0 else ""
            self.tabs.setTabText(idx, f"{icon}  {label}{badge}")

    def _on_item_restored(self, table_name, record_id):
        self.refresh_data()

    def refresh_data(self):
        """Refresh all deleted tables and update badges"""
        search_query = self.search_input.text()
        for tv in self.table_views:
            tv._load_data(search_query)
        self._update_tab_badges()
