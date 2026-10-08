import os
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS', '--disable-gpu --no-sandbox')
from datetime import datetime
from pathlib import Path
from utils.invoice_html_template import generate_invoice_html

try:
    from utils.logger import get_loggers
    _loggers = get_loggers()
    _error_logger = _loggers['error']
except Exception:
    import logging
    _error_logger = logging.getLogger(__name__)


class ProfessionalInvoiceGenerator:

    @staticmethod
    def _get_exports_dir():
        from config import PDF_DIR
        exports = Path(PDF_DIR)
        exports.mkdir(parents=True, exist_ok=True)
        return str(exports)

    def _load_app_settings(self):
        try:
            from database.db_connection import DatabaseConnection
            from controllers.settings_controller import SettingsController
            db = DatabaseConnection()
            sc = SettingsController(db)
            return sc.get_application_settings()
        except Exception as e:
            _error_logger.warning(f"Could not load app settings for invoice: {e}")
            return {}

    def _load_shop_details(self):
        try:
            from database.db_connection import DatabaseContext
            with DatabaseContext() as db:
                row = db.execute_query("SELECT * FROM shop_details ORDER BY id DESC LIMIT 1", fetch_one=True)
                return dict(row) if row else {}
        except Exception as e:
            _error_logger.warning(f"Could not fetch shop details for invoice: {e}")
            return {}

    def generate_html(self, invoice_data, shop_data=None):
        data = dict(invoice_data or {})
        
        # If shop_data not provided, load real-time from database
        if not shop_data:
            shop_data = self._load_shop_details()
            
        if shop_data:
            phone_val = str(shop_data.get('phone') or shop_data.get('owner_phone') or shop_data.get('mobile') or '').strip()
            data.update({
                'shop_name': shop_data.get('shop_name', 'Your Shop Name'),
                'shop_tagline': shop_data.get('tagline', 'Your Tagline Here'),
                'shop_services': shop_data.get('services', 'Your Services Here'),
                'shop_phone': phone_val,
                'shop_email': shop_data.get('email', ''),
                'shop_address': shop_data.get('address', ''),
                'shop_gstin': shop_data.get('gst_number') or shop_data.get('gstin', ''),
            })
            
        app_settings = self._load_app_settings()
        if 'terms_conditions' not in data:
            data['terms_conditions'] = app_settings.get('terms_conditions', 'Goods once sold will not be taken back.\nWarranty as per company policy.\nPayment due within 7 days.\nService warranty only on selected parts.')
        if 'thank_you_note' not in data:
            data['thank_you_note'] = app_settings.get('thank_you_note', 'Thank you for your business!')
        if 'invoice_watermark' not in data:
            data['invoice_watermark'] = app_settings.get('invoice_watermark', 'INVOICE')
        return generate_invoice_html(data)

    def save_html(self, invoice_data, shop_data=None, output_path=None):
        html = self.generate_html(invoice_data, shop_data)
        if not output_path:
            safe_name = "".join(c if c.isalnum() or c in ' -_' else '_' for c in invoice_data.get('customer_name', 'Customer'))
            inv_no = invoice_data.get('invoice_no', 'INV')
            exports_dir = self._get_exports_dir()
            output_path = os.path.join(exports_dir, f"{safe_name}_{inv_no}.html")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return output_path

    def generate_pdf(self, invoice_data, shop_data=None, output_path=None):
        if not output_path:
            safe_name = "".join(c if c.isalnum() or c in ' -_' else '_' for c in invoice_data.get('customer_name', 'Customer'))
            inv_no = invoice_data.get('invoice_no', 'INV')
            exports_dir = self._get_exports_dir()
            output_path = os.path.join(exports_dir, f"{safe_name}_{inv_no}.pdf")

        html = self.generate_html(invoice_data, shop_data)
        self._generate_pdf_via_qt(html, output_path)
        return output_path

    def _generate_pdf_via_qt(self, html, output_path):
        from PySide6.QtWidgets import QApplication
        from PySide6.QtWebEngineWidgets import QWebEngineView
        from PySide6.QtGui import QPageLayout, QPageSize
        from PySide6.QtCore import QMarginsF, QEventLoop, QTimer, QCoreApplication

        app = QApplication.instance()
        if app is None:
            _error_logger.critical("PDF generation called before QApplication exists")
            raise RuntimeError("Application not initialized")

        view = QWebEngineView()
        loop = QEventLoop()
        result = [None]
        timed_out = [False]

        def on_pdf(pdf_data):
            if not result[0]:
                os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(pdf_data)
                result[0] = output_path
            loop.quit()

        def on_loaded(ok):
            if ok:
                try:
                    layout = QPageLayout(QPageSize(QPageSize.A4), QPageLayout.Portrait, QMarginsF(0, 0, 0, 0))
                    view.page().printToPdf(on_pdf, layout)
                except Exception as e:
                    _error_logger.error(f"PDF printToPdf failed: {e}")
                    loop.quit()
            else:
                _error_logger.error("QWebEngine page load failed for PDF generation")
                loop.quit()

        def on_timeout():
            if not result[0]:
                _error_logger.error("PDF generation timed out (15s) — QWebEngine may be stuck")
                timed_out[0] = True
                try:
                    view.stop()
                except Exception:
                    pass
                loop.quit()

        from PySide6.QtCore import QMarginsF, QEventLoop, QTimer, QCoreApplication, QUrl

        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(on_timeout)

        view.loadFinished.connect(on_loaded)
        view.setHtml(html, QUrl.fromLocalFile(os.path.abspath('.')))
        timer.start(35000)

        try:
            loop.exec()
        except Exception as e:
            _error_logger.error(f"PDF event loop error: {e}")
        finally:
            timer.stop()
            try:
                view.stop()
                view.close()
                view.deleteLater()
                QCoreApplication.processEvents()
            except Exception:
                pass

        if timed_out[0]:
            raise RuntimeError("PDF generation timed out (35s)")
        if not result[0]:
            raise RuntimeError("PDF generation via Qt failed")

