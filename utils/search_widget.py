"""
Quick Customer Search Widget - Search as you type
Displays customer suggestions while typing phone/name
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QLabel, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from database.db_connection import DatabaseConnection


class QuickCustomerSearch(QFrame):
    """Search customers by phone/name with instant results"""

    customer_selected = Signal(dict)  # Emitted when customer is clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("quickSearchFrame")
        self.setStyleSheet("""
            QFrame#quickSearchFrame {
                background-color: transparent;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Search input
        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        icon_label = QLabel("\U0001F50D")
        icon_label.setStyleSheet("font-size: 14pt; background: transparent;")
        search_row.addWidget(icon_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name, phone, email or address...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMinimumWidth(280)
        self.search_input.setMaximumWidth(400)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 8px 14px;
                color: white;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border: 1px solid #22d3ee;
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        search_row.addWidget(self.search_input)
        layout.addLayout(search_row)

        # Results dropdown
        self.results_list = QListWidget()
        self.results_list.setMaximumHeight(250)
        self.results_list.setMinimumWidth(320)
        self.results_list.setStyleSheet("""
            QListWidget {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 4px;
                color: #f1f5f9;
            }
            QListWidget::item {
                padding: 10px 14px;
                border-radius: 6px;
                border-bottom: 1px solid #334155;
            }
            QListWidget::item:hover {
                background-color: #334155;
            }
            QListWidget::item:selected {
                background-color: #22d3ee;
                color: #0f172a;
            }
        """)
        self.results_list.hide()
        self.results_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.results_list)

        # Debounce timer
        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.timeout.connect(self._do_search)
        self.search_input.textChanged.connect(self._on_text_changed)

        self._customers_cache = []

    def _on_text_changed(self, text):
        if len(text) >= 2:
            self._debounce.start(300)
        else:
            self.results_list.hide()

    def _do_search(self):
        term = self.search_input.text().strip()
        if len(term) < 2:
            return

        db = DatabaseConnection()
        query = """
        SELECT id, name, mobile, email, address,
            (SELECT COUNT(*) FROM invoices WHERE customer_id = c.id AND is_active = TRUE) as total_services
        FROM customers c
        WHERE c.is_active = TRUE
        AND (c.name LIKE %s OR c.mobile LIKE %s OR c.email LIKE %s OR c.address LIKE %s)
        ORDER BY c.name
        LIMIT 15
        """
        results = db.execute_query(query, (f"%{term}%", f"%{term}%", f"%{term}%", f"%{term}%"), fetch_all=True)
        self._customers_cache = results or []

        self.results_list.clear()
        if self._customers_cache:
            for c in self._customers_cache:
                name = c.get('name', 'Unknown')
                mobile = c.get('mobile', '')
                email = c.get('email', '')
                address = c.get('address', '')
                services = c.get('total_services', 0)
                parts = [name, mobile]
                if email: parts.append(email)
                if address: parts.append(address[:30])
                parts.append(f"{services} services")
                text = "  |  ".join(parts)
                item = QListWidgetItem(text)
                item.setData(Qt.UserRole, c.get('id'))
                self.results_list.addItem(item)
            self.results_list.show()
        else:
            no_result = QListWidgetItem("No customers found")
            no_result.setFlags(no_result.flags() & ~Qt.ItemIsSelectable)
            self.results_list.addItem(no_result)
            self.results_list.show()

    def _on_item_clicked(self, item):
        customer_id = item.data(Qt.UserRole)
        if customer_id is None:
            self.results_list.hide()
            return
        for c in self._customers_cache:
            if c.get('id') == customer_id:
                self.customer_selected.emit(c)
                break
        self.results_list.hide()
        self.search_input.clear()
