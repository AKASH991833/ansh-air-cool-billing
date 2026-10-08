"""Render main screens to docs/screenshots (run after scripts/seed_demo_data.py)."""
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
from PySide6.QtWidgets import QApplication  # noqa: E402
from database.db_connection import DatabaseContext  # noqa: E402
from controllers.dashboard_controller import DashboardController  # noqa: E402
from views.enhanced_dashboard_view import EnhancedDashboardView  # noqa: E402
from views.invoice_management_view import InvoiceManagementView  # noqa: E402
from views.customer_view import CustomerView  # noqa: E402
from views.inventory_view import InventoryView  # noqa: E402
from views.amc_view import AMCView  # noqa: E402
from views.daily_log_view import DailyLogView  # noqa: E402
from views.report_view import ReportView  # noqa: E402
from views.technician_view import TechnicianView  # noqa: E402
from views.invoice_view import InvoiceView  # noqa: E402
from views.settings_view import SettingsView  # noqa: E402
import subprocess  # noqa: E402

from utils.privacy_manager import get_privacy_manager  # noqa: E402
get_privacy_manager().set_privacy_enabled(False)
app = QApplication.instance() or QApplication(sys.argv)
out = os.path.join(root, "docs", "screenshots")
os.makedirs(out, exist_ok=True)


def snap(w, name, size=(1300, 820)):
    w.resize(*size)
    w.show()
    import time
    end = time.time() + 2.0
    while time.time() < end:
        app.processEvents()
        time.sleep(0.02)
    w.grab().save(os.path.join(out, name))
    w.close()
    print("saved", name)


with DatabaseContext() as db:
    user = {"id": 1, "username": "admin", "role": "admin"}
    snap(EnhancedDashboardView(user, db, DashboardController(db)), "dashboard.png", (1300, 860))
snap(InvoiceManagementView(), "invoices.png")
snap(CustomerView(), "customers.png")
snap(InventoryView(), "inventory.png")

snap(InvoiceView(), "new_invoice.png", (1300, 900))
amc = AMCView()
from PySide6.QtWidgets import QTabWidget  # noqa: E402
_tabs = amc.findChildren(QTabWidget)
if _tabs:
    _tabs[0].setCurrentIndex(2)
snap(amc, "amc.png", (1750, 900))

snap(DailyLogView(), "daily_log.png")
dl = DailyLogView()
dl.stack.setCurrentIndex(1)
dl._load_settlement_data()
snap(dl, "settlement.png")
snap(TechnicianView(), "technicians.png")
snap(ReportView(), "reports.png", (1350, 850))
sv = SettingsView({"id": 1, "full_name": "Admin", "role": "admin"})
sv._nav_btns[1].click()
snap(sv, "settings.png", (1350, 850))

# Invoice PDF rendered to PNG (the app prints via Qt WebEngine; here headless Chrome stands in)
import tempfile  # noqa: E402
from utils.professional_invoice_generator import ProfessionalInvoiceGenerator  # noqa: E402


def _chrome_pdf(self, html, output_path):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
    subprocess.run(["google-chrome", "--headless", "--no-sandbox", "--disable-gpu", f"--print-to-pdf={output_path}",
                    "--no-pdf-header-footer", "file://" + f.name], check=False, capture_output=True)


if subprocess.run(["which", "google-chrome"], capture_output=True).returncode == 0:
    ProfessionalInvoiceGenerator._generate_pdf_via_qt = _chrome_pdf
imv = InvoiceManagementView()
pdf = imv._build_pdf_for_invoice(1, force_regenerate=True)
if pdf and os.path.exists(pdf):
    subprocess.run(["pdftoppm", "-png", "-r", "80", "-f", "1", "-l", "1", "-singlefile", pdf,
                    os.path.join(out, "invoice_pdf")], check=False)
    print("saved invoice_pdf.png from", pdf)
