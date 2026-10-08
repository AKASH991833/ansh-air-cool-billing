"""
WhatsApp Direct Share Dialog

One-click invoice sharing flow:
  1. PDF is copied to the clipboard as a REAL FILE (Ctrl+V pastes it as attachment)
  2. Customer's WhatsApp chat opens directly (Desktop app, else wa.me web)
  3. Auto Ctrl+V + Enter pastes & sends the PDF into the chat
  4. Message text (caption) is also copied to clipboard as a backup

Reusable for any module that has a PDF + customer mobile number.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QFrame, QMessageBox, QApplication
)
from PySide6.QtCore import Qt


class WhatsAppShareDialog(QDialog):
    """Direct 'Send to WhatsApp' dialog with clipboard-based PDF sharing."""

    WA_GREEN = "#25D366"
    WA_DARK = "#128C7E"

    def __init__(self, parent, customer_name, mobile, message, pdf_path,
                 invoice_number=""):
        super().__init__(parent)
        self.customer_name = customer_name or "Customer"
        self.mobile = mobile or ""
        self.message = message or ""
        self.pdf_path = pdf_path
        self.invoice_number = invoice_number

        self.setWindowTitle("📤 Direct WhatsApp Share")
        self.setMinimumWidth(460)
        self.setModal(True)
        self._setup_ui()

    # ------------------------------------------------------------------ UI
    def _setup_ui(self):
        self.setStyleSheet("QDialog { background-color: #ffffff; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(14)

        title = QLabel("📤 Direct WhatsApp Share")
        title.setStyleSheet(
            f"font-size: 16pt; font-weight: bold; color: {self.WA_DARK};")
        layout.addWidget(title)

        info = QLabel(
            f"Bill <b>{self.invoice_number}</b> for <b>{self.customer_name}</b> "
            f"is ready to send.")
        info.setTextFormat(Qt.RichText)
        info.setWordWrap(True)
        layout.addWidget(info)

        steps = QLabel(
            "<b>How it works:</b><br>"
            "1. Click <b>'🚀 Open Chat & Paste'</b> below<br>"
            "2. Customer's WhatsApp chat opens <b>directly</b><br>"
            "3. PDF is <b>auto-pasted (Ctrl+V)</b> and sent automatically<br><br>"
            "<font color='green'>✔ PDF already copied to clipboard — "
            "if auto-paste is missed, just press <b>Ctrl+V</b> in the chat.</font>")
        steps.setTextFormat(Qt.RichText)
        steps.setWordWrap(True)
        steps.setStyleSheet("color: #374151; font-size: 10pt;")
        layout.addWidget(steps)

        # Auto-paste option
        self.auto_paste_cb = QCheckBox("⚡ Auto-paste & send (recommended)")
        self.auto_paste_cb.setChecked(True)
        self.auto_paste_cb.setStyleSheet("font-weight: 600;")
        layout.addWidget(self.auto_paste_cb)

        # Caption option
        self.caption_cb = QCheckBox("📝 Also copy message text (backup)")
        self.caption_cb.setChecked(True)
        layout.addWidget(self.caption_cb)

        layout.addSpacing(6)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.send_btn = QPushButton("🚀 Open Chat & Paste")
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.WA_GREEN}; color: white; border: none;
                border-radius: 8px; padding: 12px 22px;
                font-size: 11pt; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {self.WA_DARK}; }}
        """)
        self.send_btn.clicked.connect(self._do_share)
        btn_row.addWidget(self.send_btn, 1)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6; color: #374151; border: 1px solid #d1d5db;
                border-radius: 8px; padding: 12px 18px; font-size: 11pt;
            }
            QPushButton:hover { background-color: #e5e7eb; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        layout.addLayout(btn_row)

        # Prepare clipboard immediately so the user can also paste manually
        self._prepare_clipboard()

    # ------------------------------------------------------------- actions
    def _prepare_clipboard(self):
        """Copy PDF file to clipboard right away so user can paste manually if needed.

        NOTE: We do NOT call clipboard.setText() here because it would immediately
        overwrite and destroy the file (CF_HDROP / URLs) we just placed there.
        The caption message is included as the text component of the same QMimeData
        object inside copy_file_to_clipboard via the module-level keep-alive.
        """
        from utils.whatsapp_clipboard import copy_file_to_clipboard
        copy_file_to_clipboard(self.pdf_path)

    def _do_share(self):
        if not self.mobile:
            QMessageBox.warning(self, "No Mobile Number",
                                "Customer mobile number is missing.\n"
                                "Add a mobile number to the customer first.")
            return

        from utils.whatsapp_clipboard import open_direct_chat_with_message

        # Re-copy PDF to clipboard (ensures it's still there after dialog interactions).
        # Do NOT call setText() — it would wipe the PDF file from clipboard.
        from utils.whatsapp_clipboard import copy_file_to_clipboard
        copy_file_to_clipboard(self.pdf_path)

        ok = open_direct_chat_with_message(
            self.mobile,
            self.message,
            paste_file=self.auto_paste_cb.isChecked(),
            file_path=self.pdf_path,
        )

        if ok:
            QMessageBox.information(
                self, "Sent 🎉",
                f"WhatsApp chat opened for {self.customer_name}.\n\n"
                "PDF attach ho gaya / paste ho jayega (Ctrl+V).\n"
                "Agar auto-send nahi hua to Enter dabayein.")
            self.accept()
        else:
            QMessageBox.warning(
                self, "Failed",
                "WhatsApp chat open nahi ho paya.\n"
                "WhatsApp Desktop install hai ya browser default set hai, "
                "check karein.")
