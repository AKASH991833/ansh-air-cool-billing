"""
PDF AMC Generator - Professional Annual Maintenance Contract Agreement & Certificate PDF Generator
Generates pixel-perfect A4 AMC Contract PDFs for customer hand-off, preview, and WhatsApp sharing.
"""
import os
from datetime import datetime
from pathlib import Path

from utils.amc_html_template import generate_amc_html
from database.db_connection import DatabaseContext
from utils.formatters import Formatters
from config import PDF_DIR


class PDFAMCGenerator:
    """Enterprise AMC Contract Agreement & Certificate PDF Generator"""

    def __init__(self):
        self.exports_dir = Path(PDF_DIR)
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def load_amc_full_data(self, amc_id_or_num):
        """Fetch all contract data, customer details, units, visits, and shop info"""
        with DatabaseContext() as db:
            # Query AMC Contract and Customer
            if isinstance(amc_id_or_num, int) or str(amc_id_or_num).isdigit():
                where_clause = "ac.id = %s"
                param = int(amc_id_or_num)
            else:
                where_clause = "ac.amc_id = %s"
                param = str(amc_id_or_num).strip()

            q_amc = f"""
                SELECT ac.*, c.name as customer_name, c.mobile as customer_mobile,
                       c.email as customer_email, c.address as customer_address,
                       c.landmark as customer_landmark
                FROM amc_contracts ac
                JOIN customers c ON ac.customer_id = c.id
                WHERE {where_clause}
            """
            amc = db.execute_query(q_amc, (param,), fetch_one=True)
            if not amc:
                raise ValueError(f"AMC Contract {amc_id_or_num} not found")

            amc_db_id = amc['id']

            # Query Covered Units
            q_units = """
                SELECT * FROM amc_units
                WHERE amc_id = %s AND is_active = 1
                ORDER BY id ASC
            """
            units = db.execute_query(q_units, (amc_db_id,), fetch_all=True) or []

            # Query Scheduled Visits
            q_visits = """
                SELECT v.*, t.name as technician_name, t.mobile as technician_mobile
                FROM amc_visits v
                LEFT JOIN technicians t ON v.technician_id = t.id
                WHERE v.amc_id = %s AND v.is_active = 1
                ORDER BY v.visit_date ASC, v.visit_number ASC
            """
            visits = db.execute_query(q_visits, (amc_db_id,), fetch_all=True) or []

            # Shop details
            q_shop = "SELECT * FROM shop_details ORDER BY id DESC LIMIT 1"
            shop = db.execute_query(q_shop, fetch_one=True) or {}

            # Primary technician if available
            primary_tech = ''
            for v in visits:
                if v.get('technician_name'):
                    primary_tech = f"{v['technician_name']}" + (f" ({v['technician_mobile']})" if v.get('technician_mobile') else "")
                    break

            # Calculate duration in years
            start_d_raw = amc.get('start_date')
            end_d_raw = amc.get('end_date')
            duration_years = 1
            try:
                s_dt = datetime.strptime(str(start_d_raw)[:10], '%Y-%m-%d')
                e_dt = datetime.strptime(str(end_d_raw)[:10], '%Y-%m-%d')
                days = (e_dt - s_dt).days
                duration_years = max(1, round(days / 365.25))
            except Exception:
                pass

            formatted_data = {
                'id': amc['id'],
                'amc_id': amc['amc_id'],
                'contract_type': amc.get('contract_type', 'Comprehensive'),
                'start_date': Formatters.format_date(start_d_raw),
                'end_date': Formatters.format_date(end_d_raw),
                'contract_duration': duration_years,
                'amc_status': amc.get('amc_status', 'Active'),
                'customer_name': amc.get('customer_name', 'Customer'),
                'customer_mobile': amc.get('customer_mobile', ''),
                'customer_email': amc.get('customer_email', ''),
                'customer_address': amc.get('customer_address', ''),
                'customer_landmark': amc.get('customer_landmark', ''),
                'no_of_units': amc.get('no_of_units', len(units) or 1),
                'services_per_year': amc.get('services_per_year', len(visits) or 2),
                'services_remaining': amc.get('services_remaining', 0),
                'contract_amount': float(amc.get('contract_amount') or amc.get('total_amount') or 0),
                'gst_percent': float(amc.get('gst_percent') or 0),
                'total_amount': float(amc.get('total_amount') or 0),
                'advance_paid': float(amc.get('advance_paid') or 0),
                'balance_amount': float(amc.get('balance_amount') or 0),
                'payment_mode': amc.get('payment_mode', 'Cash'),
                'payment_status': amc.get('payment_status', 'Pending'),
                'notes': amc.get('notes', ''),
                'primary_technician': primary_tech or 'Assigned by Service Manager',
                'units': [dict(u) for u in units],
                'visits': [
                    {
                        **dict(v),
                        'visit_date': Formatters.format_date(v.get('visit_date'))
                    }
                    for v in visits
                ]
            }

            return formatted_data, dict(shop)

    def generate_html(self, amc_id_or_num):
        """Generate HTML string for the AMC contract"""
        contract_data, shop_data = self.load_amc_full_data(amc_id_or_num)
        return generate_amc_html(contract_data, shop_data)

    def generate_pdf(self, amc_id_or_num, output_path=None, force_regenerate=True):
        """Generate and save the PDF for an AMC contract and return output_path"""
        contract_data, shop_data = self.load_amc_full_data(amc_id_or_num)

        if not output_path:
            safe_name = "".join(c if c.isalnum() or c in ' -_' else '_' for c in contract_data.get('customer_name', 'Customer'))
            amc_id = contract_data.get('amc_id', 'AMC')
            output_path = os.path.join(str(self.exports_dir), f"AMC_Agreement_{safe_name}_{amc_id}.pdf")

        if not force_regenerate and os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            return output_path

        html = generate_amc_html(contract_data, shop_data)
        self._generate_pdf_via_qt(html, output_path)
        return output_path

    def _generate_pdf_via_qt(self, html, output_path):
        """Render HTML to A4 PDF using PySide6 QWebEngineView"""
        from PySide6.QtWidgets import QApplication
        from PySide6.QtWebEngineWidgets import QWebEngineView
        from PySide6.QtGui import QPageLayout, QPageSize
        from PySide6.QtCore import QMarginsF, QEventLoop, QTimer, QCoreApplication, QUrl

        app = QApplication.instance()
        if app is None:
            raise RuntimeError("QApplication is not running")

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
                    print(f"AMC PDF printToPdf failed: {e}")
                    loop.quit()
            else:
                print("QWebEngine page load failed for AMC PDF generation")
                loop.quit()

        def on_timeout():
            if not result[0]:
                print("AMC PDF generation timed out (35s)")
                timed_out[0] = True
                try:
                    view.stop()
                except Exception:
                    pass
                loop.quit()

        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(on_timeout)

        view.loadFinished.connect(on_loaded)
        view.setHtml(html, QUrl.fromLocalFile(os.path.abspath('.')))
        timer.start(35000)

        try:
            loop.exec()
        except Exception as e:
            print(f"AMC PDF event loop error: {e}")
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
            raise RuntimeError("AMC PDF generation timed out (35s)")
        if not result[0] or not os.path.exists(output_path):
            raise RuntimeError("AMC PDF generation failed")
