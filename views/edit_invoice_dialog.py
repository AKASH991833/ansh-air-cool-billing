"""
Edit Invoice Dialog - Complete invoice editing with all fields
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QTabWidget,
    QScrollArea, QWidget, QGroupBox
)
from PySide6.QtCore import Qt
from decimal import Decimal
from utils.app_settings import get_setting


class EditInvoiceDialog(QDialog):
    """Dialog for editing existing invoices"""

    def __init__(self, parent=None, invoice_data=None):
        super().__init__(parent)
        self.invoice_data = invoice_data
        self.invoice_items = []
        self.services_list = []
        self.parts_list = []

        self.setWindowTitle(f"Edit Invoice - {invoice_data.get('invoice_number', 'N/A')}")
        self.setMinimumSize(900, 700)

        self._setup_ui()
        self._load_invoice_data()

    def update_theme_colors(self):
        """Update theme colors for proper dark theme support"""
        from utils.unified_theme import UnifiedTheme
        theme_manager = UnifiedTheme()
        colors = theme_manager.get_colors()
        
        # Apply QPalette colors
        theme_manager.apply_palette(self)
        
        # Apply theme directly to table for proper alternating colors
        if hasattr(self, 'items_table'):
            theme_manager.apply_table_theme(self.items_table)

    def _setup_ui(self):
        """Setup edit dialog UI"""
        self.currency_symbol = get_setting("currency_symbol", "₹")
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Tab 1: Customer & AC Details
        self.tab1 = self._create_customer_tab()
        self.tabs.addTab(self.tab1, "Customer & AC Details")
        
        # Tab 2: Items
        self.tab2 = self._create_items_tab()
        self.tabs.addTab(self.tab2, "Items")
        
        # Tab 3: Payment
        self.tab3 = self._create_payment_tab()
        self.tabs.addTab(self.tab3, "Payment & Summary")
        
        layout.addWidget(self.tabs)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6B7280;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 11pt;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4B5563;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 Save Changes")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 11pt;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #047857;
            }
        """)
        save_btn.clicked.connect(self._save_changes)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _create_customer_tab(self):
        """Create customer and AC details tab"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(15)
        
        # Customer Details
        customer_group = QGroupBox("👤 Customer Details")
        customer_layout = QFormLayout()
        
        self.customer_name_input = QLineEdit()
        customer_layout.addRow("Name *:", self.customer_name_input)
        
        self.customer_mobile_input = QLineEdit()
        customer_layout.addRow("Mobile *:", self.customer_mobile_input)
        
        self.customer_email_input = QLineEdit()
        customer_layout.addRow("Email:", self.customer_email_input)
        
        self.customer_landmark_input = QLineEdit()
        customer_layout.addRow("Landmark:", self.customer_landmark_input)
        
        self.customer_address_input = QTextEdit()
        self.customer_address_input.setMaximumHeight(80)
        customer_layout.addRow("Address:", self.customer_address_input)
        
        customer_group.setLayout(customer_layout)
        layout.addWidget(customer_group)
        
        # AC Details
        self.ac_group = QGroupBox("❄️ AC Details")
        ac_layout = QFormLayout()
        
        self.ac_brand_combo = QComboBox()
        self.ac_brand_combo.addItem("Select Brand", "")
        ac_layout.addRow("Brand *:", self.ac_brand_combo)
        
        self.ac_type_combo = QComboBox()
        self.ac_type_combo.addItems(get_setting('ac_types', 'Split,Window,Cassette,Tower,Other').split(','))
        ac_layout.addRow("Type:", self.ac_type_combo)
        
        self.ac_ton_combo = QComboBox()
        self.ac_ton_combo.addItems(get_setting('ac_tonnages', '0.75,1.0,1.5,2.0,3.0,Other').split(','))
        ac_layout.addRow("Capacity (Ton):", self.ac_ton_combo)
        
        self.ac_star_combo = QComboBox()
        self.ac_star_combo.addItems(get_setting('star_ratings', 'Not Applicable,1 Star,2 Star,3 Star,4 Star,5 Star').split(','))
        ac_layout.addRow("Star Rating:", self.ac_star_combo)
        
        self.ac_inverter_combo = QComboBox()
        self.ac_inverter_combo.addItems(get_setting('inverter_types', 'Not Specified,Inverter,Non-Inverter').split(','))
        ac_layout.addRow("Inverter Type:", self.ac_inverter_combo)
        
        self.ac_gas_combo = QComboBox()
        self.ac_gas_combo.addItems(["R22", "R32", "R410A", "Other"])
        ac_layout.addRow("Gas Type:", self.ac_gas_combo)
        
        self.ac_group.setLayout(ac_layout)
        self.ac_group.setVisible(get_setting('shop_type', 'AC Service') == 'AC Service')
        layout.addWidget(self.ac_group)
        layout.addStretch()
        
        scroll.setWidget(content)
        return scroll
    
    def _create_items_tab(self):
        """Create items tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Items table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels(['Type', 'Description', 'Qty', f'Rate ({self.currency_symbol})', f'Amount ({self.currency_symbol})'])

        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        self.items_table.setAlternatingRowColors(True)
        self.items_table.verticalHeader().setVisible(False)
        layout.addWidget(self.items_table)

        layout.addWidget(QLabel("ℹ️ Note: To add/remove items, please use the main invoice creation form"))

        return widget
    
    def _create_payment_tab(self):
        """Create payment tab"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(15)
        
        # Technician
        tech_group = QGroupBox("🔧 Technician")
        tech_layout = QFormLayout()
        
        self.technician_combo = QComboBox()
        self.technician_combo.addItem("Select Technician", "")
        tech_layout.addRow("Assigned Technician:", self.technician_combo)
        tech_group.setLayout(tech_layout)
        layout.addWidget(tech_group)
        
        # Payment Details
        payment_group = QGroupBox("💰 Payment Details")
        payment_layout = QFormLayout()
        
        self.subtotal_label = QLabel(f"{self.currency_symbol}0.00")
        self.subtotal_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        payment_layout.addRow("Subtotal:", self.subtotal_label)
        
        # GST
        gst_layout = QHBoxLayout()
        self.gst_checkbox = QCheckBox("Apply GST")
        self.gst_checkbox.stateChanged.connect(lambda: self._calculate_totals())
        gst_layout.addWidget(self.gst_checkbox)

        self.gst_rate_combo = QComboBox()
        self.gst_rate_combo.addItems(["5%", "12%", "18%", "28%"])
        self.gst_rate_combo.setCurrentIndex(2)
        self.gst_rate_combo.setEnabled(False)
        self.gst_rate_combo.currentTextChanged.connect(lambda: self._calculate_totals())
        gst_layout.addWidget(self.gst_rate_combo)
        gst_layout.addStretch()
        payment_layout.addRow(gst_layout)
        
        self.gst_amount_label = QLabel(f"{self.currency_symbol}0.00")
        self.gst_amount_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #d97706;")
        payment_layout.addRow("GST Amount:", self.gst_amount_label)
        
        # Discount
        disc_layout = QHBoxLayout()
        self.disc_checkbox = QCheckBox("Apply Discount")
        self.disc_checkbox.stateChanged.connect(lambda: self._update_discount_ui())
        disc_layout.addWidget(self.disc_checkbox)

        self.disc_type_combo = QComboBox()
        self.disc_type_combo.addItems(["%", self.currency_symbol])
        self.disc_type_combo.setEnabled(False)
        self.disc_type_combo.currentTextChanged.connect(lambda: self._calculate_totals())
        disc_layout.addWidget(self.disc_type_combo)

        self.disc_value_spin = QDoubleSpinBox()
        self.disc_value_spin.setRange(0, 999999)
        self.disc_value_spin.setDecimals(2)
        self.disc_value_spin.setEnabled(False)
        self.disc_value_spin.setValue(0)
        self.disc_value_spin.valueChanged.connect(lambda: self._calculate_totals())
        disc_layout.addWidget(self.disc_value_spin)
        disc_layout.addStretch()
        payment_layout.addRow("Discount:", disc_layout)

        self.discount_amount_label = QLabel(f"{self.currency_symbol}0.00")
        self.discount_amount_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #dc2626;")
        payment_layout.addRow("Discount Amount:", self.discount_amount_label)

        self.total_amount_label = QLabel(f"{self.currency_symbol}0.00")
        self.total_amount_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: #1e40af;")
        payment_layout.addRow("Total Amount:", self.total_amount_label)
        
        self.advance_input = QDoubleSpinBox()
        self.advance_input.setRange(0, 999999)
        self.advance_input.setPrefix(self.currency_symbol + " ")
        self.advance_input.setDecimals(2)
        self.advance_input.valueChanged.connect(self._calculate_balance)
        payment_layout.addRow("Advance Payment:", self.advance_input)
        
        self.balance_label = QLabel(f"{self.currency_symbol}0.00")
        self.balance_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        payment_layout.addRow("Balance Amount:", self.balance_label)
        
        self.payment_mode_combo = QComboBox()
        self._load_payment_modes()
        payment_layout.addRow("Payment Mode:", self.payment_mode_combo)
        
        self.payment_status_combo = QComboBox()
        self.payment_status_combo.addItems(["Paid", "Partial", "Pending"])
        payment_layout.addRow("Payment Status:", self.payment_status_combo)
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Enter invoice notes or remarks")
        self.notes_input.setMaximumHeight(80)
        payment_layout.addRow("Notes:", self.notes_input)
        
        payment_group.setLayout(payment_layout)
        layout.addWidget(payment_group)
        
        layout.addStretch()
        scroll.setWidget(content)
        return scroll

    def _load_payment_modes(self):
        """Load payment modes from database"""
        from database.db_connection import DatabaseContext
        with DatabaseContext() as db:
            modes = db.execute_query("SELECT mode_name FROM payment_modes WHERE is_active = TRUE", fetch_all=True)
            if modes:
                self.payment_mode_combo.clear()
                for m in modes:
                    self.payment_mode_combo.addItem(m['mode_name'])
    
    def _update_discount_ui(self):
        """Enable/disable discount controls based on checkbox state"""
        enabled = self.disc_checkbox.isChecked()
        self.disc_type_combo.setEnabled(enabled)
        self.disc_value_spin.setEnabled(enabled)
        self._calculate_totals()

    def _load_invoice_data(self):
        """Load invoice data into form"""
        if not self.invoice_data:
            return

        # Block signals during loading to prevent premature calculations
        self.gst_checkbox.blockSignals(True)
        self.gst_rate_combo.blockSignals(True)
        self.advance_input.blockSignals(True)
        self.disc_checkbox.blockSignals(True)
        self.disc_type_combo.blockSignals(True)
        self.disc_value_spin.blockSignals(True)

        # Load customer details
        self.customer_name_input.setText(self.invoice_data.get('name', ''))
        self.customer_mobile_input.setText(self.invoice_data.get('mobile', ''))
        self.customer_email_input.setText(self.invoice_data.get('email', '') or '')
        self.customer_landmark_input.setText(self.invoice_data.get('landmark', '') or '')
        self.customer_address_input.setPlainText(self.invoice_data.get('address', '') or '')

        # Load AC details
        ac_brand = self.invoice_data.get('brand_name', '')
        index = self.ac_brand_combo.findText(ac_brand)
        if index >= 0:
            self.ac_brand_combo.setCurrentIndex(index)

        ac_type = self.invoice_data.get('ac_type', 'Split')
        index = self.ac_type_combo.findText(ac_type)
        if index >= 0:
            self.ac_type_combo.setCurrentIndex(index)

        ac_ton = self.invoice_data.get('ton_capacity', '1.0')
        index = self.ac_ton_combo.findText(ac_ton)
        if index >= 0:
            self.ac_ton_combo.setCurrentIndex(index)

        ac_star = self.invoice_data.get('star_rating', 'Not Applicable')
        index = self.ac_star_combo.findText(ac_star)
        if index >= 0:
            self.ac_star_combo.setCurrentIndex(index)

        ac_inverter = self.invoice_data.get('ac_inverter', 'Not Specified')
        index = self.ac_inverter_combo.findText(ac_inverter)
        if index >= 0:
            self.ac_inverter_combo.setCurrentIndex(index)

        # Load payment details
        self.advance_input.setValue(float(self.invoice_data.get('advance_payment', 0)))

        payment_mode = self.invoice_data.get('payment_mode', 'Cash')
        index = self.payment_mode_combo.findText(payment_mode)
        if index >= 0:
            self.payment_mode_combo.setCurrentIndex(index)

        payment_status = self.invoice_data.get('payment_status', 'Pending')
        index = self.payment_status_combo.findText(payment_status)
        if index >= 0:
            self.payment_status_combo.setCurrentIndex(index)

        self.notes_input.setPlainText(self.invoice_data.get('notes', '') or '')

        # Load GST settings
        gst_percentage = self.invoice_data.get('gst_percentage', 0)
        if gst_percentage and gst_percentage > 0:
            self.gst_checkbox.setChecked(True)
            gst_rate_str = f"{int(gst_percentage)}%"
            index = self.gst_rate_combo.findText(gst_rate_str)
            if index >= 0:
                self.gst_rate_combo.setCurrentIndex(index)
        else:
            self.gst_checkbox.setChecked(False)

        # Load discount values
        discount_type = self.invoice_data.get('discount_type', '')
        discount_value = float(self.invoice_data.get('discount_value', 0))
        discount_amount = float(self.invoice_data.get('discount_amount', 0))
        if discount_type and discount_value > 0:
            self.disc_checkbox.setChecked(True)
            display_type = '%' if discount_type == 'percentage' else self.currency_symbol
            idx = self.disc_type_combo.findText(display_type)
            if idx >= 0:
                self.disc_type_combo.setCurrentIndex(idx)
            self.disc_value_spin.setValue(discount_value)

        # Load items
        self._load_items()

        # Unblock signals after loading
        self.gst_checkbox.blockSignals(False)
        self.gst_rate_combo.blockSignals(False)
        self.advance_input.blockSignals(False)
        self.disc_checkbox.blockSignals(False)
        self.disc_type_combo.blockSignals(False)
        self.disc_value_spin.blockSignals(False)

        # Calculate totals
        self._calculate_totals()
    
    def _load_items(self):
        """Load invoice items into table"""
        from database.db_connection import DatabaseContext
        
        with DatabaseContext() as db:
            query = """
                SELECT ii.*, s.service_name, p.part_name
                FROM invoice_items ii
                LEFT JOIN services s ON ii.service_id = s.id
                LEFT JOIN parts p ON ii.part_id = p.id
                WHERE ii.invoice_id = %s
            """
            items = db.execute_query(query, (self.invoice_data['id'],), fetch_all=True)
            
            if items:
                for item in items:
                    row = self.items_table.rowCount()
                    self.items_table.insertRow(row)
                    
                    item_type = item['item_type']
                    description = item['service_name'] or item['part_name'] or 'N/A'
                    qty = item['quantity']
                    rate = float(item.get('rate') or 0)
                    amount = float(item.get('amount') or 0)
                    
                    self.items_table.setItem(row, 0, QTableWidgetItem(item_type.title()))
                    self.items_table.setItem(row, 1, QTableWidgetItem(description))
                    self.items_table.setItem(row, 2, QTableWidgetItem(str(qty)))
                    self.items_table.setItem(row, 3, QTableWidgetItem(f"{self.currency_symbol}{rate:,.2f}"))
                    self.items_table.setItem(row, 4, QTableWidgetItem(f"{self.currency_symbol}{amount:,.2f}"))
                    
                    self.invoice_items.append({
                        'id': item['id'],
                        'type': item_type,
                        'service_id': item['service_id'],
                        'part_id': item['part_id'],
                        'description': description,
                        'quantity': qty,
                        'rate': rate,
                        'amount': amount
                    })
    
    def _calculate_totals(self):
        """Calculate totals including discount"""
        from utils.app_settings import get_setting
        # Enable/disable GST rate and discount controls
        self.gst_rate_combo.setEnabled(self.gst_checkbox.isChecked())
        self.disc_type_combo.setEnabled(self.disc_checkbox.isChecked())
        self.disc_value_spin.setEnabled(self.disc_checkbox.isChecked())

        discount_before_gst = get_setting('discount_before_gst', False)

        # Calculate subtotal
        subtotal = sum(item['amount'] for item in self.invoice_items)
        subtotal_decimal = Decimal(str(subtotal))
        self.subtotal_label.setText(f"{self.currency_symbol}{subtotal:,.2f}")

        # Calculate discount (base is always subtotal; legacy mode recalculates below)
        discount_amount = Decimal('0.00')
        disc_val = Decimal('0')
        if self.disc_checkbox.isChecked():
            disc_val = Decimal(str(self.disc_value_spin.value()))
            base_for_disc = subtotal_decimal
            if self.disc_type_combo.currentText() == '%':
                discount_amount = base_for_disc * disc_val / Decimal('100')
            else:
                discount_amount = disc_val

        # Calculate GST (on discounted subtotal if GST-compliant mode)
        gst_amount = Decimal('0.00')
        if self.gst_checkbox.isChecked():
            gst_rate_text = self.gst_rate_combo.currentText()
            gst_rate = Decimal(gst_rate_text.replace('%', ''))
            if discount_before_gst:
                gst_base = subtotal_decimal - discount_amount
                if gst_base < 0:
                    gst_base = Decimal('0')
                gst_amount = gst_base * gst_rate / Decimal('100')
            else:
                gst_amount = subtotal_decimal * gst_rate / Decimal('100')

        self.gst_amount_label.setText(f"{self.currency_symbol}{gst_amount:,.2f}")

        # Recalculate discount for legacy mode (discount on subtotal+GST)
        if self.disc_checkbox.isChecked() and not discount_before_gst:
            total_before_disc = subtotal_decimal + gst_amount
            if self.disc_type_combo.currentText() == '%':
                discount_amount = total_before_disc * disc_val / Decimal('100')

        if self.disc_checkbox.isChecked():
            self.discount_amount_label.setText(f"{self.currency_symbol}{discount_amount:,.2f}")
        else:
            self.discount_amount_label.setText(f"{self.currency_symbol}0.00")

        # Calculate total
        total = subtotal_decimal + gst_amount - discount_amount
        self.total_amount_label.setText(f"{self.currency_symbol}{total:,.2f}")

        # Calculate balance
        self._calculate_balance()
    
    def _calculate_balance(self):
        """Calculate balance"""
        total_text = self.total_amount_label.text().replace(self.currency_symbol, '').replace(',', '')
        try:
            total = Decimal(total_text) if total_text else Decimal('0.00')
        except Exception:
            total = Decimal('0.00')
        
        advance = Decimal(str(self.advance_input.value()))
        balance = total - advance
        
        self.balance_label.setText(f"{self.currency_symbol}{balance:,.2f}")
        
        # Update color
        if balance <= 0:
            self.balance_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #059669;")
        elif advance > 0:
            self.balance_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #d97706;")
        else:
            self.balance_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #dc2626;")
    
    def _save_changes(self):
        """Save changes to invoice"""
        try:
            # Validate
            if not self.customer_name_input.text().strip():
                QMessageBox.warning(self, "Validation Error", "Customer name is required")
                return
            
            if not self.customer_mobile_input.text().strip():
                QMessageBox.warning(self, "Validation Error", "Customer mobile is required")
                return
            
            # Get updated data
            updated_data = {
                'customer_name': self.customer_name_input.text().strip(),
                'customer_mobile': self.customer_mobile_input.text().strip(),
                'customer_email': self.customer_email_input.text().strip(),
                'customer_landmark': self.customer_landmark_input.text().strip(),
                'customer_address': self.customer_address_input.toPlainText().strip(),
                'ac_brand': self.ac_brand_combo.currentText(),
                'ac_type': self.ac_type_combo.currentText(),
                'ac_ton': self.ac_ton_combo.currentText(),
                'ac_star': self.ac_star_combo.currentText(),
                'ac_inverter': self.ac_inverter_combo.currentText(),
                'ac_gas': self.ac_gas_combo.currentText(),
                'payment_mode': self.payment_mode_combo.currentText(),
                'payment_status': self.payment_status_combo.currentText(),
                'notes': self.notes_input.toPlainText().strip(),
                'advance_payment': float(self.advance_input.value()),
                'gst_applied': self.gst_checkbox.isChecked(),
                'gst_rate': self.gst_rate_combo.currentText() if self.gst_checkbox.isChecked() else '0%',
            }
            
            # Show confirmation
            reply = QMessageBox.question(
                self,
                "Confirm Save",
                "Are you sure you want to save these changes?\n\nNote: Only customer details, AC details, payment details, and notes will be updated.\nTo add/remove items, please create a new invoice.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                from controllers.invoice_controller import InvoiceController
                from database.db_connection import DatabaseContext

                with DatabaseContext() as db:
                    controller = InvoiceController(db)
                    ac_type = self.ac_type_combo.currentText()
                    ac_ton = self.ac_ton_combo.currentText()
                    ac_star = self.ac_star_combo.currentText()
                    ac_inverter = self.ac_inverter_combo.currentText()

                    from utils.app_settings import get_setting
                    discount_before_gst = get_setting('discount_before_gst', False)

                    gst_applied = self.gst_checkbox.isChecked()
                    gst_rate_str = self.gst_rate_combo.currentText()
                    gst_percentage = float(gst_rate_str.replace('%', '')) if gst_applied else 0.0
                    subtotal = sum(item['amount'] for item in self.invoice_items)

                    disc_applied = self.disc_checkbox.isChecked()
                    raw_type = self.disc_type_combo.currentText() if disc_applied else ''
                    disc_type = 'percentage' if raw_type == '%' else 'fixed' if raw_type else ''
                    disc_value = float(self.disc_value_spin.value()) if disc_applied else 0.0
                    disc_amount = 0.0

                    if disc_applied:
                        if discount_before_gst:
                            if disc_type == 'percentage':
                                disc_amount = subtotal * disc_value / 100.0
                            else:
                                disc_amount = disc_value
                            gst_base = subtotal - disc_amount
                            if gst_base < 0:
                                gst_base = 0.0
                            gst_amount = gst_base * (gst_percentage / 100.0)
                        else:
                            gst_amount = subtotal * (gst_percentage / 100.0)
                            if disc_type == 'percentage':
                                disc_amount = (subtotal + gst_amount) * disc_value / 100.0
                            else:
                                disc_amount = disc_value

                    total_amount = subtotal + gst_amount - disc_amount
                    advance = float(self.advance_input.value())
                    balance = total_amount - advance

                    ac_brand_name = updated_data.get('ac_brand', '')
                    invoice_data = {
                        'customer': {
                            'name': updated_data['customer_name'],
                            'mobile': updated_data['customer_mobile'],
                            'email': updated_data['customer_email'],
                            'address': updated_data['customer_address'],
                            'landmark': updated_data['customer_landmark'],
                        },
                        'ac_details': {
                            'brand': ac_brand_name if ac_brand_name != 'Select Brand' else '',
                            'type': ac_type,
                            'ton': ac_ton,
                            'star_rating': ac_star,
                            'ac_inverter': ac_inverter,
                        },
                        'technician': '',
                        'items': self.invoice_items,
                        'totals': {
                            'subtotal': round(subtotal, 2),
                            'gst_percentage': gst_percentage,
                            'gst_amount': round(gst_amount, 2),
                            'discount_type': disc_type,
                            'discount_value': disc_value,
                            'discount_amount': round(disc_amount, 2),
                            'total_amount': round(total_amount, 2),
                            'advance_payment': advance,
                            'balance_amount': max(round(balance, 2), 0.0),
                        },
                        'payment': {
                            'mode': updated_data['payment_mode'],
                            'status': updated_data['payment_status'],
                        },
                        'notes': updated_data['notes'],
                    }

                    invoice_id_num = self.invoice_data.get('id')
                    result_id, error = controller.update_invoice(invoice_id_num, invoice_data)
                    if error:
                        QMessageBox.critical(self, "Error", f"Failed to update: {error}")
                        return

                self.accept()
                QMessageBox.information(self, "Success", "Invoice updated successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving changes: {str(e)}")
