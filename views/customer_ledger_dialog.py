"""
Customer Ledger Dialog - Full Account Statement
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from datetime import datetime, timedelta

from utils.unified_theme import UnifiedTheme
from database.db_connection import DatabaseContext
from utils.formatters import Formatters


class CustomerLedgerDialog(QDialog):
    def __init__(self, customer_id, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.theme_manager = UnifiedTheme()
        self.colors = self.theme_manager.get_colors()
        self.setWindowTitle("📒 Customer Ledger")
        self.setMinimumSize(800, 500)
        self.setModal(True)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        self.setStyleSheet(f"QDialog {{ background-color: {self.colors['bg']}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        self.header_label = QLabel("📒 Customer Ledger")
        self.header_label.setStyleSheet(f"font-size: 18pt; font-weight: bold; color: {self.colors['primary']};")
        layout.addWidget(self.header_label)

        self.customer_info = QLabel("")
        self.customer_info.setStyleSheet(f"color: {self.colors['muted']}; font-size: 10pt;")
        layout.addWidget(self.customer_info)

        # Summary cards
        sum_frame = QFrame()
        sum_frame.setObjectName("cardFrame")
        sum_frame.setStyleSheet(f"""
            QFrame#cardFrame {{
                background-color: {self.colors['card_bg']};
                border: 1px solid {self.colors['border']};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        sum_l = QHBoxLayout(sum_frame)

        self.total_billed_label = QLabel("Total Billed: ₹0")
        self.total_billed_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #3b82f6;")
        sum_l.addWidget(self.total_billed_label)

        self.total_paid_label = QLabel("Total Paid: ₹0")
        self.total_paid_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #059669;")
        sum_l.addWidget(self.total_paid_label)

        self.balance_label = QLabel("Balance: ₹0")
        self.balance_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #dc2626;")
        sum_l.addWidget(self.balance_label)

        self.invoice_count_label = QLabel("Invoices: 0")
        self.invoice_count_label.setStyleSheet(f"font-size: 12pt; font-weight: bold; color: {self.colors['muted']};")
        sum_l.addWidget(self.invoice_count_label)
        sum_l.addStretch()
        layout.addWidget(sum_frame)

        # Date filter
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("From:"))
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addMonths(-6))
        self.from_date.setCalendarPopup(True)
        date_layout.addWidget(self.from_date)
        date_layout.addWidget(QLabel("To:"))
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        date_layout.addWidget(self.to_date)
        filter_btn = QPushButton("Filter")
        filter_btn.setObjectName("primaryButton")
        filter_btn.clicked.connect(self._load_data)
        date_layout.addWidget(filter_btn)
        date_layout.addStretch()
        layout.addLayout(date_layout)

        # Ledger table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            'Date', 'Type', 'Description', 'Debit (₹)', 'Credit (₹)', 'Balance (₹)'
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for i in range(3, 6):
            h.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.theme_manager.apply_table_theme(self.table)
        layout.addWidget(self.table, 1)

    def _load_data(self):
        from_date = self.from_date.date().toString('yyyy-MM-dd')
        to_date = self.to_date.date().toString('yyyy-MM-dd')

        with DatabaseContext() as db:
            # Customer info
            cust = db.execute_query("SELECT name, mobile, address FROM customers WHERE id=%s",
                                    (self.customer_id,), fetch_one=True)
            if cust:
                self.customer_info.setText(f"{cust['name']} | 📱 {cust['mobile']} | {cust.get('address', '') or ''}")

            # Invoices as debit entries
            query = """
                SELECT i.created_at as date, 'Invoice' as type,
                       i.invoice_number as ref, i.total_amount as debit,
                       i.advance_payment as credit, i.balance_amount,
                       i.payment_status as status
                FROM invoices i
                WHERE i.customer_id = %s AND i.is_active = TRUE
                AND DATE(i.created_at) BETWEEN %s AND %s
                UNION ALL
                SELECT p.payment_date as date, 'Payment' as type,
                       CONCAT('Payment for #', i.invoice_number) as ref,
                       0 as debit, p.amount as credit, 0 as balance,
                       'Paid' as status
                FROM payments p
                JOIN invoices i ON p.invoice_id = i.id
                WHERE i.customer_id = %s
                AND DATE(p.payment_date) BETWEEN %s AND %s
                ORDER BY date ASC
            """
            entries = db.execute_query(query, (self.customer_id, from_date, to_date,
                                               self.customer_id, from_date, to_date), fetch_all=True) or []

            # Summary
            summary = db.execute_query("""
                SELECT COUNT(*) as inv_count,
                       COALESCE(SUM(i.total_amount), 0) as total_billed,
                       COALESCE(SUM(i.advance_payment), 0) as total_paid,
                       COALESCE(SUM(i.balance_amount), 0) as total_balance
                FROM invoices i
                WHERE i.customer_id = %s AND i.is_active = TRUE
            """, (self.customer_id,), fetch_one=True) or {}

        self.table.setRowCount(0)
        running_balance = 0
        total_billed = float(summary.get('total_billed', 0) or 0)
        total_paid = float(summary.get('total_paid', 0) or 0)
        total_balance = float(summary.get('total_balance', 0) or 0)

        for e in entries:
            row = self.table.rowCount()
            self.table.insertRow(row)

            date_str = Formatters.format_date(e.get('date'))
            self.table.setItem(row, 0, QTableWidgetItem(date_str))
            self.table.setItem(row, 1, QTableWidgetItem(e.get('type', '')))

            desc = e.get('ref', '')
            if e.get('status'):
                desc += f" ({e['status']})"
            self.table.setItem(row, 2, QTableWidgetItem(desc))

            debit = float(e.get('debit', 0) or 0)
            credit = float(e.get('credit', 0) or 0)

            if debit > 0:
                d_item = QTableWidgetItem(f"₹{debit:,.0f}")
                d_item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(row, 3, d_item)
                running_balance += debit
            else:
                self.table.setItem(row, 3, QTableWidgetItem(""))

            if credit > 0:
                c_item = QTableWidgetItem(f"₹{credit:,.0f}")
                c_item.setForeground(Qt.GlobalColor.green)
                self.table.setItem(row, 4, c_item)
                running_balance -= credit
            else:
                self.table.setItem(row, 4, QTableWidgetItem(""))

            bal_item = QTableWidgetItem(f"₹{running_balance:,.0f}")
            bal_item.setForeground(Qt.GlobalColor.red if running_balance > 0 else Qt.GlobalColor.green)
            self.table.setItem(row, 5, bal_item)

        self.total_billed_label.setText(f"Total Billed: ₹{total_billed:,.0f}")
        self.total_paid_label.setText(f"Total Paid: ₹{total_paid:,.0f}")
        bal_color = '#dc2626' if total_balance > 0 else '#059669'
        self.balance_label.setStyleSheet(f"font-size: 12pt; font-weight: bold; color: {bal_color};")
        self.balance_label.setText(f"Balance: ₹{total_balance:,.0f}")
        self.invoice_count_label.setText(f"Invoices: {summary.get('inv_count', 0)}")

        if not entries:
            self.table.setRowCount(1)
            self.table.setSpan(0, 0, 1, 6)
            msg = QLabel("No transactions found in selected period")
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg.setStyleSheet(f"color: {self.colors['muted']}; padding: 30px;")
            self.table.setCellWidget(0, 0, msg)
