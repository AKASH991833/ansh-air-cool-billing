"""
AMC Contract Preview & Share Dialog
Provides live interactive inspection, System PDF opening, Disk Export, Printing,
and 1-Click WhatsApp sharing for AMC Contract Agreements & Certificates.
"""
import os
import subprocess
import platform
import urllib.parse
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox, QFrame, QSizePolicy, QWidget
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QColor
from PySide6.QtWebEngineWidgets import QWebEngineView

from utils.pdf_amc_generator import PDFAMCGenerator
from utils.unified_theme import UnifiedTheme

FONT_FAMILY = "'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif"

ENTERPRISE_COLORS = {
    'primary': '#2563eb',
    'primary_hover': '#1d4ed8',
    'primary_light': '#eff6ff',
    'primary_border': '#bfdbfe',
    'success': '#059669',
    'success_hover': '#047857',
    'success_light': '#ecfdf5',
    'border': '#cbd5e1',
    'text': '#0f172a',
    'text_muted': '#64748b',
    'bg': '#f8fafc'
}


class AMCContractPreviewDialog(QDialog):
    """Modern enterprise dialog to preview, download, print, and WhatsApp share AMC Contracts"""

    def __init__(self, amc_id_or_num, parent=None):
        super().__init__(parent)
        self.amc_id = amc_id_or_num
        self.generator = PDFAMCGenerator()
        self.pdf_path = None
        self.contract_data = None
        self.shop_data = None

        self.setWindowTitle(f"AMC Contract Agreement & Service Certificate - {self.amc_id}")
        self.resize(1020, 860)
        self.setMinimumSize(880, 680)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {ENTERPRISE_COLORS['bg']};
                font-family: {FONT_FAMILY};
            }}
        """)

        self._setup_ui()
        self._load_and_preview()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(12)

        # Top Control Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet(f"""
            QFrame#amc_toolbar {{
                background-color: #ffffff;
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 10px;
            }}
        """)
        toolbar.setObjectName("amc_toolbar")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(14, 10, 14, 10)
        tb_layout.setSpacing(10)

        # Title Info
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.title_lbl = QLabel(f"AMC Agreement: {self.amc_id}")
        self.title_lbl.setStyleSheet(f"font-size: 11.5pt; font-weight: 800; color: {ENTERPRISE_COLORS['text']}; font-family: {FONT_FAMILY}; background: transparent; border: none;")
        self.sub_lbl = QLabel("Inspect contract terms, equipment registry & visit schedule before sharing")
        self.sub_lbl.setStyleSheet(f"font-size: 8pt; color: {ENTERPRISE_COLORS['text_muted']}; font-family: {FONT_FAMILY}; background: transparent; border: none;")
        title_box.addWidget(self.title_lbl)
        title_box.addWidget(self.sub_lbl)
        tb_layout.addLayout(title_box)

        tb_layout.addStretch()

        # Action 1: View in System Viewer
        self.btn_open_pdf = QPushButton("👁️  Open PDF Viewer")
        self.btn_open_pdf.setToolTip("Open generated PDF in your default system PDF reader (Acrobat, Edge, Chrome)")
        self.btn_open_pdf.setCursor(Qt.PointingHandCursor)
        self.btn_open_pdf.setStyleSheet(f"""
            QPushButton {{
                background-color: {ENTERPRISE_COLORS['primary_light']};
                color: {ENTERPRISE_COLORS['primary']};
                border: 1px solid {ENTERPRISE_COLORS['primary_border']};
                border-radius: 8px;
                padding: 7px 14px;
                font-size: 9pt;
                font-weight: 700;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: {ENTERPRISE_COLORS['primary']};
                color: #ffffff;
            }}
        """)
        self.btn_open_pdf.clicked.connect(self._open_in_system_viewer)
        tb_layout.addWidget(self.btn_open_pdf)

        # Action 2: Download / Save PDF
        self.btn_download = QPushButton("📥  Save / Download PDF")
        self.btn_download.setToolTip("Save a copy of this AMC Agreement to your computer or pendrive")
        self.btn_download.setCursor(Qt.PointingHandCursor)
        self.btn_download.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                color: #334155;
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                padding: 7px 14px;
                font-size: 9pt;
                font-weight: 600;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{
                border-color: {ENTERPRISE_COLORS['primary']};
                color: {ENTERPRISE_COLORS['primary']};
            }}
        """)
        self.btn_download.clicked.connect(self._download_pdf)
        tb_layout.addWidget(self.btn_download)

        # Action 3: Print
        self.btn_print = QPushButton("🖨️  Print")
        self.btn_print.setToolTip("Send this agreement directly to printer")
        self.btn_print.setCursor(Qt.PointingHandCursor)
        self.btn_print.setStyleSheet(f"""
            QPushButton {{
                background-color: #ffffff;
                color: #334155;
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 8px;
                padding: 7px 14px;
                font-size: 9pt;
                font-weight: 600;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{
                border-color: {ENTERPRISE_COLORS['primary']};
                color: {ENTERPRISE_COLORS['primary']};
            }}
        """)
        self.btn_print.clicked.connect(self._print_contract)
        tb_layout.addWidget(self.btn_print)

        # Action 4: WhatsApp Share (Special Green)
        self.btn_whatsapp = QPushButton("💬  Share on WhatsApp")
        self.btn_whatsapp.setToolTip("Open WhatsApp Web with pre-formatted AMC contract details for this customer")
        self.btn_whatsapp.setCursor(Qt.PointingHandCursor)
        self.btn_whatsapp.setStyleSheet(f"""
            QPushButton {{
                background-color: #059669;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 7px 16px;
                font-size: 9pt;
                font-weight: 700;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{
                background-color: #047857;
            }}
        """)
        self.btn_whatsapp.clicked.connect(self._share_whatsapp)
        tb_layout.addWidget(self.btn_whatsapp)

        # Action 5: Close
        self.btn_close = QPushButton("✕")
        self.btn_close.setToolTip("Close Preview")
        self.btn_close.setFixedSize(32, 32)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: #f1f5f9;
                color: #64748b;
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 6px;
                font-size: 11pt;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #e2e8f0;
                color: #0f172a;
            }}
        """)
        self.btn_close.clicked.connect(self.close)
        tb_layout.addWidget(self.btn_close)

        main_layout.addWidget(toolbar)

        # WebEngine Preview Frame
        preview_container = QFrame()
        preview_container.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 1px solid {ENTERPRISE_COLORS['border']};
                border-radius: 10px;
            }}
        """)
        pc_layout = QVBoxLayout(preview_container)
        pc_layout.setContentsMargins(0, 0, 0, 0)

        self.web_view = QWebEngineView()
        self.web_view.setStyleSheet("background-color: #ffffff; border-radius: 10px;")
        pc_layout.addWidget(self.web_view)

        main_layout.addWidget(preview_container, 1)

    def _load_and_preview(self):
        """Generate HTML and PDF and render live in WebEngineView"""
        try:
            self.contract_data, self.shop_data = self.generator.load_amc_full_data(self.amc_id)
            amc_no = self.contract_data.get('amc_id', self.amc_id)
            c_name = self.contract_data.get('customer_name', 'Customer')
            self.title_lbl.setText(f"📄 AMC Contract: {amc_no}")
            self.sub_lbl.setText(f"Customer: {c_name} • Terms, Equipment & Schedule")

            # Generate HTML string for interactive preview
            html_content = self.generator.generate_html(self.amc_id)
            self.web_view.setHtml(html_content, QUrl.fromLocalFile(os.path.abspath('.')))

        except Exception as e:
            QMessageBox.critical(self, "Error Loading AMC Contract", f"Could not load contract details:\n{str(e)}")

    def _get_or_create_pdf(self):
        """Lazily ensure PDF is generated and return its path"""
        if not self.pdf_path or not os.path.exists(self.pdf_path):
            self.pdf_path = self.generator.generate_pdf(self.amc_id, force_regenerate=False)
        return self.pdf_path

    def _open_in_system_viewer(self):
        """Open generated PDF in system viewer"""
        try:
            pdf_path = self._get_or_create_pdf()
            if not pdf_path or not os.path.exists(pdf_path):
                raise FileNotFoundError("Could not locate or generate contract PDF.")

            abs_path = os.path.abspath(pdf_path)
            opened = QDesktopServices.openUrl(QUrl.fromLocalFile(abs_path))
            if not opened:
                if platform.system() == 'Windows':
                    os.startfile(abs_path)
                elif platform.system() == 'Darwin':
                    subprocess.run(['open', abs_path])
                else:
                    subprocess.run(['xdg-open', abs_path])
        except Exception as e:
            QMessageBox.warning(self, "Error Opening PDF", f"Could not open PDF viewer:\n{str(e)}")

    def _download_pdf(self):
        """Save PDF to user selected file location"""
        try:
            pdf_path = self._get_or_create_pdf()
            if not pdf_path or not os.path.exists(pdf_path):
                raise FileNotFoundError("Could not locate or generate contract PDF.")

            c_name = self.contract_data.get('customer_name', 'Customer') if self.contract_data else 'Customer'
            amc_no = self.contract_data.get('amc_id', self.amc_id) if self.contract_data else self.amc_id
            safe_name = "".join(c if c.isalnum() or c in ' -_' else '_' for c in c_name)
            default_name = f"AMC_Agreement_{safe_name}_{amc_no}.pdf"

            dest_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save AMC Contract Agreement PDF",
                default_name,
                "PDF Files (*.pdf)"
            )
            if dest_path:
                import shutil
                shutil.copy2(self.pdf_path, dest_path)
                QMessageBox.information(self, "PDF Saved", f"AMC Contract PDF successfully saved to:\n{dest_path}")
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Could not save PDF:\n{str(e)}")

    def _print_contract(self):
        """Send contract to system print dialog"""
        try:
            if self.web_view:
                # Use QWebEngine's native print
                from PySide6.QtPrintSupport import QPrinter, QPrintDialog
                printer = QPrinter(QPrinter.HighResolution)
                printer.setPageOrientation(printer.pageLayout().orientation())
                dialog = QPrintDialog(printer, self)
                if dialog.exec() == QPrintDialog.Accepted:
                    # Print page
                    self.web_view.page().print(printer, lambda ok: None)
            else:
                self._open_in_system_viewer()
        except Exception:
            # Fallback to system viewer printing
            self._open_in_system_viewer()

    def _share_whatsapp(self):
        """Send comprehensive AMC details to customer on WhatsApp"""
        try:
            if not self.contract_data:
                self.contract_data, self.shop_data = self.generator.load_amc_full_data(self.amc_id)

            c = self.contract_data
            s = self.shop_data or {}
            c_name = c.get('customer_name', 'Valued Customer')
            c_mob = str(c.get('customer_mobile', '')).strip()
            amc_no = c.get('amc_id', 'AMC')
            ctype = c.get('contract_type', 'Comprehensive')
            start_d = c.get('start_date', 'N/A')
            end_d = c.get('end_date', 'N/A')
            units_cnt = c.get('no_of_units', 1)
            tot_s = c.get('services_per_year', 2)
            tot_amt = float(c.get('total_amount') or 0)
            paid_amt = float(c.get('advance_paid') or 0)
            bal_amt = float(c.get('balance_amount') or 0)
            shop_n = s.get('shop_name') or 'AC Service Billing Experts'
            shop_p = s.get('phone') or s.get('mobile') or s.get('owner_phone') or ''

            # Equipment info summary
            units_info = []
            for u in c.get('units', []):
                b = u.get('brand', 'AC')
                t = u.get('ton', '1.5')
                typ = u.get('ac_type', 'Split')
                units_info.append(f"• {b} {typ} ({t} Ton)")
            units_text = "\n".join(units_info) if units_info else f"• {units_cnt} Covered AC Unit(s)"

            msg = (
                f"🌟 *ANNUAL MAINTENANCE CONTRACT (AMC) AGREEMENT* 🌟\n\n"
                f"Dear *{c_name}*,\n"
                f"Your AC Maintenance Agreement with *{shop_n}* is officially confirmed and active!\n\n"
                f"📋 *Contract ID:* {amc_no}\n"
                f"🛡️ *Coverage Plan:* {ctype} AMC\n"
                f"📅 *Validity:* {start_d} to {end_d} ({c.get('contract_duration', 1)} Year)\n"
                f"❄️ *Covered Units:* {units_cnt} Unit(s)\n"
                f"{units_text}\n"
                f"🛠️ *Preventive Visits Included:* {tot_s} Periodic Services\n\n"
                f"💰 *Total Agreement Value:* ₹{tot_amt:,.2f}\n"
                f"✅ *Advance Paid:* ₹{paid_amt:,.2f}\n"
                f"📌 *Balance Due:* ₹{bal_amt:,.2f}\n\n"
                f"✨ *Key Inclusions:*\n"
                f"• High-pressure jet pump coil washing & chemical clean\n"
                f"• Air filter sanitization & drain flushing\n"
                f"• Electrical wiring, capacitor & motor inspection\n"
                f"• Refrigerant operating pressure verification\n"
                f"• Priority emergency breakdown support\n\n"
                f"📞 *Customer Support:* {shop_p}\n\n"
                f"Thank you for choosing {shop_n} for reliable air conditioning care! ❄️"
            )

            encoded_msg = urllib.parse.quote(msg)
            # Standardize phone number for India
            clean_mob = "".join(filter(str.isdigit, c_mob))
            if len(clean_mob) == 10:
                clean_mob = f"91{clean_mob}"

            url = f"https://web.whatsapp.com/send?phone={clean_mob}&text={encoded_msg}" if clean_mob else f"https://web.whatsapp.com/send?text={encoded_msg}"
            QDesktopServices.openUrl(QUrl(url))

            # Inform user where PDF is located for manual attachment
            try:
                pdf_path = self._get_or_create_pdf()
            except Exception:
                pdf_path = None

            if pdf_path and os.path.exists(pdf_path):
                QMessageBox.information(
                    self,
                    "WhatsApp Web Launched",
                    f"WhatsApp Web has been opened with your pre-formatted contract summary message.\n\n"
                    f"📄 The complete signed PDF agreement is ready at:\n{pdf_path}\n\n"
                    f"You can attach this PDF in WhatsApp with 1 click."
                )
        except Exception as e:
            QMessageBox.warning(self, "WhatsApp Error", f"Could not launch WhatsApp:\n{str(e)}")
