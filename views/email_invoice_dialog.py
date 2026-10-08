"""
Email Invoice Dialog - Send invoice PDF via email
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from utils.unified_theme import UnifiedTheme
from utils.app_settings import get_setting
from database.db_connection import DatabaseContext


class EmailInvoiceDialog(QDialog):
    def __init__(self, invoice_id, parent=None):
        super().__init__(parent)
        self.invoice_id = invoice_id
        self.theme_manager = UnifiedTheme()
        self.colors = self.theme_manager.get_colors()
        self.setWindowTitle("📧 Email Invoice")
        self.setMinimumWidth(500)
        self.setModal(True)
        self.pdf_path = None
        self._setup_ui()
        self._load_invoice()

    def _setup_ui(self):
        self.setStyleSheet(f"QDialog {{ background-color: {self.colors['bg']}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("📧 Email Invoice")
        title.setStyleSheet(f"font-size: 16pt; font-weight: bold; color: {self.colors['primary']};")
        layout.addWidget(title)

        form_layout = QVBoxLayout()

        form_layout.addWidget(QLabel("To:"))
        self.to_input = QLineEdit()
        self.to_input.setPlaceholderText("customer@email.com")
        self.to_input.setStyleSheet(f"""
            QLineEdit {{ background-color: {self.colors['card_bg']}; color: {self.colors['fg']};
                border: 1px solid {self.colors['border']}; border-radius: 6px; padding: 8px; }}
        """)
        form_layout.addWidget(self.to_input)

        form_layout.addWidget(QLabel("Subject:"))
        self.subject_input = QLineEdit()
        self.subject_input.setStyleSheet(f"""
            QLineEdit {{ background-color: {self.colors['card_bg']}; color: {self.colors['fg']};
                border: 1px solid {self.colors['border']}; border-radius: 6px; padding: 8px; }}
        """)
        form_layout.addWidget(self.subject_input)

        form_layout.addWidget(QLabel("Message:"))
        self.msg_input = QTextEdit()
        self.msg_input.setMinimumHeight(120)
        self.msg_input.setStyleSheet(f"""
            QTextEdit {{ background-color: {self.colors['card_bg']}; color: {self.colors['fg']};
                border: 1px solid {self.colors['border']}; border-radius: 6px; padding: 8px; }}
        """)
        form_layout.addWidget(self.msg_input)

        layout.addLayout(form_layout)

        # PDF attachment
        pdf_layout = QHBoxLayout()
        self.pdf_label = QLabel("No PDF attached")
        self.pdf_label.setStyleSheet(f"color: {self.colors['muted']};")
        pdf_layout.addWidget(self.pdf_label, 1)
        browse_btn = QPushButton("Browse PDF")
        browse_btn.clicked.connect(self._browse_pdf)
        pdf_layout.addWidget(browse_btn)
        generate_btn = QPushButton("Generate PDF")
        generate_btn.clicked.connect(self._generate_pdf)
        pdf_layout.addWidget(generate_btn)
        layout.addLayout(pdf_layout)

        # Buttons
        btn_l = QHBoxLayout()
        btn_l.addStretch()
        send_btn = QPushButton("📤 Send Email")
        send_btn.setStyleSheet("""
            QPushButton { background-color: #3b82f6; color: white; border: none;
                border-radius: 8px; padding: 10px 24px; font-size: 11pt; font-weight: bold; }
            QPushButton:hover { background-color: #2563eb; }
        """)
        send_btn.clicked.connect(self._send_email)
        btn_l.addWidget(send_btn)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_l.addWidget(cancel_btn)
        layout.addLayout(btn_l)

    def _load_invoice(self):
        """Pre-fill To/Subject/Message from the invoice record"""
        with DatabaseContext() as db:
            query = """
                SELECT i.invoice_number, c.name as customer_name,
                       c.email as customer_email, c.mobile as customer_mobile
                FROM invoices i
                JOIN customers c ON i.customer_id = c.id
                WHERE i.id = %s
            """
            inv = db.execute_query(query, (self.invoice_id,), fetch_one=True)
        if inv:
            company = get_setting('company_name', 'Your Company Name')
            to = inv['customer_email'] or ''
            subject = get_setting('email_subject', 'Invoice #{invoice_number} - {company_name}').format(invoice_number=inv['invoice_number'], company_name=company)
            body = get_setting('email_body', 'Dear {customer_name},\n\nPlease find attached invoice #{invoice_number}.\n\nThank you for your business!\n{company_name}').format(customer_name=inv['customer_name'], invoice_number=inv['invoice_number'], company_name=company)
            self.to_input.setText(to)
            self.subject_input.setText(subject)
            self.msg_input.setPlainText(body)

    def _browse_pdf(self):
        """Pick an existing PDF to attach"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Invoice PDF", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self.pdf_path = file_path
            self.pdf_label.setText(os.path.basename(file_path))

    def _generate_pdf(self):
        """Generate the invoice PDF for the current invoice"""
        try:
            from controllers.invoice_controller import InvoiceController
            from database.db_connection import DatabaseConnection
            db = DatabaseConnection()
            controller = InvoiceController(db)
            invoice_data = controller.get_invoice(self.invoice_id)
            if not invoice_data:
                QMessageBox.warning(self, "Error", "Invoice not found")
                return
            invoice_data['items'] = controller.get_invoice_items(self.invoice_id) or []
            from utils.pdf_invoice_generator import PDFInvoiceGenerator
            pdf_path = PDFInvoiceGenerator().generate_invoice(invoice_data)
            if pdf_path:
                self.pdf_path = str(pdf_path)
                self.pdf_label.setText(os.path.basename(self.pdf_path))
            else:
                QMessageBox.warning(self, "Error", "Could not generate PDF")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to generate PDF: {str(e)}")

    def _send_email(self):
        """Send the prepared email with the attached invoice PDF"""
        to = self.to_input.text().strip()
        if not to:
            QMessageBox.warning(self, "Error", "Please enter a recipient email address")
            return
        if not self.pdf_path:
            QMessageBox.warning(self, "Error", "Please attach or generate an invoice PDF first")
            return
        try:
            subject = self.subject_input.text().strip() or "Invoice"
            body = self.msg_input.toPlainText()
            from_email = get_setting('smtp_from_email', 'your@email.com')
            from_name = get_setting('smtp_from_name', 'Your Company Name')
            smtp_server = get_setting('smtp_server', 'smtp.gmail.com')
            smtp_port = get_setting('smtp_port', '587')
            smtp_username = get_setting('smtp_username', '')
            smtp_password = get_setting('smtp_password', '')

            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            with open(self.pdf_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(self.pdf_path)}"')
                msg.attach(part)

            if smtp_username and smtp_password:
                server = smtplib.SMTP(smtp_server, int(smtp_port))
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
                server.quit()
                QMessageBox.information(self, "Email Sent",
                    f"Invoice emailed successfully to {to}!")
                self.accept()
            else:
                QMessageBox.information(self, "Email Ready",
                    f"Email prepared for {to}\n\n"
                    f"Subject: {subject}\n"
                    f"Attachment: {os.path.basename(self.pdf_path)}\n\n"
                    f"To send, configure SMTP credentials in Settings > Application:\n"
                    f"  SMTP Username: your_email@gmail.com\n"
                    f"  SMTP Password: your_app_password\n"
                    f"  SMTP Server: smtp.gmail.com\n"
                    f"  SMTP Port: 587")
                self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to send email: {str(e)}")
