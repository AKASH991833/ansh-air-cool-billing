"""
Professional A4 GST-Compliant Invoice PDF Generator
AC Service & AMC Billing Software
Now using HTML+CSS professional design via QWebEngine
"""

import os
from datetime import datetime
from utils.professional_invoice_generator import ProfessionalInvoiceGenerator


class PDFGenerator:
    def generate_invoice(self, invoice_data, shop_data, output_path):
        mapped = self._map_data(invoice_data, shop_data)
        gen = ProfessionalInvoiceGenerator()
        gen.generate_pdf(mapped, shop_data, output_path)

    @staticmethod
    def _to_float(val, default=0):
        if val is None:
            return float(default)
        try:
            return float(val)
        except (TypeError, ValueError):
            return float(default)

    def _map_data(self, inv, shop):
        data = dict(inv or {})
        items_raw = inv.get('items', [])
        mapped_items = []
        for item in items_raw:
            desc = item.get('service_name') or item.get('part_name') or item.get('description', 'Item')
            qty = self._to_float(item.get('quantity', item.get('qty', 1)))
            rate = self._to_float(item.get('rate', 0))
            gst_p = self._to_float(item.get('gst_percent', item.get('gst', 18)))
            amt = self._to_float(item.get('amount', qty * rate))
            hsn = item.get('hsn', item.get('hsn_sac', ''))
            mapped_items.append({
                'service_name': desc,
                'quantity': qty,
                'rate': rate,
                'gst_percent': gst_p,
                'amount': amt,
                'hsn': hsn,
                'unit': item.get('unit') or 'pcs',
            })
        data['items'] = mapped_items

        gst_rate = self._to_float(inv.get('gst_percentage', inv.get('gst_rate', 18)))
        gst_amt = self._to_float(inv.get('gst_amount', 0))
        if 'cgst_rate' not in data or not data.get('cgst_rate'):
            data['cgst_rate'] = gst_rate / 2
        if 'sgst_rate' not in data or not data.get('sgst_rate'):
            data['sgst_rate'] = gst_rate / 2
        if 'cgst_amount' not in data or not data.get('cgst_amount'):
            data['cgst_amount'] = gst_amt / 2
        if 'sgst_amount' not in data or not data.get('sgst_amount'):
            data['sgst_amount'] = gst_amt / 2

        data['discount'] = self._to_float(inv.get('discount', 0))
        data['work_location'] = inv.get('work_location', inv.get('customer_address', ''))

        if 'total' not in data:
            data['total'] = self._to_float(inv.get('total_amount', 0))
        if 'amount_paid' not in data:
            data['amount_paid'] = self._to_float(inv.get('advance_payment', inv.get('amount_paid', 0)))
        if 'balance_due' not in data:
            data['balance_due'] = self._to_float(inv.get('balance_amount', data['total'] - data['amount_paid']))

        if not shop:
            try:
                from database.db_connection import DatabaseContext
                with DatabaseContext() as db:
                    shop = db.execute_query("SELECT * FROM shop_details ORDER BY id DESC LIMIT 1", fetch_one=True)
            except Exception:
                shop = None

        gstin = (shop.get('gst_number') or shop.get('gstin', '')) if shop else ''
        phone = (shop.get('phone') or shop.get('owner_phone') or shop.get('mobile') or '') if shop else ''
        email = (shop.get('email') or '') if shop else ''
        addr = (shop.get('address') or '') if shop else ''
        data['shop_phone'] = phone
        data['shop_email'] = email
        data['shop_address'] = addr
        data['shop_gstin'] = gstin
        if shop:
            data['shop_name'] = shop.get('shop_name', 'Your Shop Name')
            data['shop_tagline'] = shop.get('tagline', 'Your Tagline Here')
            data['shop_services'] = shop.get('services', 'Your Services Here')

        if 'terms_conditions' not in data:
            data['terms_conditions'] = inv.get('terms_conditions', '')
        if 'thank_you_note' not in data:
            data['thank_you_note'] = inv.get('thank_you_note', '')
        if 'invoice_watermark' not in data:
            data['invoice_watermark'] = inv.get('invoice_watermark', '')

        return data
