"""
PDF Invoice Generator - Quick invoice PDF generation for sharing
Wraps PDFGenerator with simpler interface for WhatsApp and bulk operations
"""
import os
from datetime import datetime
from utils.pdf_generator import PDFGenerator
from utils.app_settings import get_setting
from database.db_connection import DatabaseContext


class PDFInvoiceGenerator:
    """Simple invoice PDF generator wrapping PDFGenerator"""

    def __init__(self):
        self.generator = PDFGenerator()

    def generate_invoice(self, invoice_data, output_path=None):
        """Generate PDF invoice and return file path"""
        if not output_path:
            from config import PDF_DIR
            exports_dir = str(PDF_DIR)
            os.makedirs(exports_dir, exist_ok=True)
            safe_name = "".join(c if c.isalnum() or c in ' -_' else '_' for c in invoice_data.get('customer_name', 'Customer'))
            output_path = os.path.join(exports_dir, f"{safe_name}_{invoice_data['invoice_number']}.pdf")

        from database.db_connection import DatabaseContext

        with DatabaseContext() as db:
            shop_query = "SELECT * FROM shop_details ORDER BY id DESC LIMIT 1"
            shop_data = db.execute_query(shop_query, fetch_one=True)

            if not shop_data:
                shop_data = {
                    'shop_name': 'Your Shop Name',
                    'address': 'Shop Address Not Provided',
                    'phone': 'N/A',
                    'email': 'N/A',
                    'tagline': 'Your Tagline Here',
                    'services': 'Your Services Here',
                    'gst_number': '',
                    'footer_message': get_setting('thank_you_note', 'Thank you for your business!')
                }

            if shop_data:
                shop_data['mobile'] = shop_data.get('phone') or shop_data.get('owner_phone') or ''
                if not shop_data.get('footer_message'):
                    shop_data['footer_message'] = get_setting('thank_you_note', 'Thank you for your business!')

        pdf_invoice_data = {
            'invoice_no': invoice_data.get('invoice_number', 'N/A'),
            'invoice_date': invoice_data.get('invoice_date', datetime.now().strftime('%d-%m-%Y')),
            'due_date': invoice_data.get('invoice_date', 'N/A'),
            'invoice_type': 'Regular',
            'payment_mode': invoice_data.get('payment_mode', 'N/A'),
            'payment_status': invoice_data.get('payment_status', 'Pending'),
            'customer_name': invoice_data.get('customer_name', 'N/A'),
            'customer_address': invoice_data.get('customer_address', 'N/A'),
            'customer_mobile': invoice_data.get('customer_mobile', 'N/A'),
            'customer_email': invoice_data.get('customer_email', ''),
            'landmark': invoice_data.get('landmark', ''),
            'ac_brand': invoice_data.get('ac_brand', 'N/A'),
            'ac_type': invoice_data.get('ac_type', 'N/A'),
            'ac_ton': invoice_data.get('ac_ton', invoice_data.get('ton_capacity', 'N/A')),
            'ac_star': invoice_data.get('ac_star', invoice_data.get('star_rating', 'N/A')),
            'ac_inverter': invoice_data.get('ac_inverter', invoice_data.get('inverter_type', 'N/A')),
            'ac_gas': invoice_data.get('ac_gas', 'N/A'),
            'ac_serial': invoice_data.get('ac_serial', 'N/A'),
            'technician_name': invoice_data.get('technician_name', ''),
            'technician_mobile': invoice_data.get('technician_mobile', ''),
            'service_date': invoice_data.get('invoice_date', 'N/A'),
            'service_type': get_setting('service_types', 'AC Service,Installation,Repair,Gas Refilling,AMC Visit,AC Rent Delivery,AC Rent Pickup,Other').split(',')[0],
            'items': [
                {
                    'service_name': item.get('description', 'Service'),
                    'part_name': None,
                    'description': item.get('description', 'Service'),
                    'quantity': item.get('quantity', 1),
                    'rate': float(item.get('rate', 0)),
                    'gst_percent': float(invoice_data.get('gst_percentage', 0)),
                    'amount': float(item.get('amount', 0)),
                    'unit': item.get('unit', 'pcs')
                }
                for item in invoice_data.get('items', [])
            ] if invoice_data.get('items') else [],
            'subtotal': float(invoice_data.get('subtotal', invoice_data.get('total_amount', 0))),
            'discount': float(invoice_data.get('discount_amount', 0)),
            'cgst_rate': (float(invoice_data.get('gst_percentage') or 0)) / 2,
            'cgst_amount': (float(invoice_data.get('gst_amount') or 0)) / 2,
            'sgst_rate': (float(invoice_data.get('gst_percentage') or 0)) / 2,
            'sgst_amount': (float(invoice_data.get('gst_amount') or 0)) / 2,
            'igst_amount': 0,
            'total': float(invoice_data.get('total_amount', 0)),
            'amount_paid': float(invoice_data.get('paid_amount', invoice_data.get('advance_payment', 0))),
            'balance_due': float(invoice_data.get('balance_amount', 0)),
            'notes': get_setting('thank_you_note', 'Thank you for your business!')
        }

        self.generator.generate_invoice(pdf_invoice_data, shop_data, output_path)
        return output_path
