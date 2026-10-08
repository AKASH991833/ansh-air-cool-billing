import base64
import os
import hashlib
from html import escape
from datetime import datetime


def get_qr_base64():
    try:
        from config import RESOURCE_DIR
        path = os.path.join(str(RESOURCE_DIR), 'assets', 'Qr.jpeg')
    except Exception:
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'Qr.jpeg')
    if os.path.exists(path):
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None


def get_logo_base64():
    try:
        from utils.logo_helper import get_logo_path
        path = get_logo_path()
        if path and os.path.exists(path):
            with open(path, 'rb') as f:
                return base64.b64encode(f.read()).decode()
    except Exception:
        pass
    # Fallback to project Logo.png
    try:
        from config import RESOURCE_DIR
        path = os.path.join(str(RESOURCE_DIR), 'assets', 'Logo.png')
    except Exception:
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'Logo.png')
    if os.path.exists(path):
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None


def generate_barcode_svg(code_str):
    """Generate crisp clean SVG barcode matching invoice number"""
    h = hashlib.md5(str(code_str).encode()).hexdigest()
    pattern = "101001101101"
    for c in h[:14]:
        v = int(c, 16)
        pattern += bin(v)[2:].zfill(4)
    pattern += "11010110001011"

    x = 4
    svg_bars = []
    for bit in pattern:
        if bit == '1':
            svg_bars.append(f'<rect x="{x}" y="1" width="1.6" height="24" fill="#000000" />')
        x += 2.0
    total_w = x + 4
    return f'<svg viewBox="0 0 {total_w} 26" preserveAspectRatio="none" style="width: 100%; height: 26px; display: block;">{"".join(svg_bars)}</svg>'


def amount_to_words(amount):
    if amount < 0:
        amount = abs(amount)
    num = int(amount)
    paise = int(round((amount - num) * 100))
    if paise >= 100:
        num += 1
        paise = 0
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
            "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
            "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def _convert(n):
        if n == 0:
            return ""
        if n < 20:
            return ones[n]
        elif n < 100:
            return tens[n // 10] + (" " + ones[n % 10] if n % 10 else "")
        elif n < 1000:
            return ones[n // 100] + " Hundred" + (" " + _convert(n % 100) if n % 100 else "")
        elif n < 100000:
            return _convert(n // 1000) + " Thousand" + (" " + _convert(n % 1000) if n % 1000 else "")
        elif n < 10000000:
            return _convert(n // 100000) + " Lakh" + (" " + _convert(n % 100000) if n % 100000 else "")
        else:
            return _convert(n // 10000000) + " Crore" + (" " + _convert(n % 10000000) if n % 10000000 else "")

    if num == 0 and paise == 0:
        return "Zero Rupees Only"
    result = ""
    if num > 0:
        result = _convert(num) + " Rupees"
    if paise > 0:
        result += " and " + _convert(paise) + " Paise"
    return result + " Only"


def generate_invoice_html(data):
    """
    Generate professional Indian GST Tax Invoice HTML matching assets/inovice_design.jpeg
    Pixel-perfect A4 styling, responsive card structures, and crisp print typography.
    """
    # Dynamic shop details fallback
    shop_name = escape(str(data.get('shop_name') or '').strip() or 'ANSH AIR COOL')
    shop_tagline = escape(str(data.get('shop_tagline') or '').strip() or 'AC SALES & SERVICE MANAGEMENT')
    shop_services = escape(str(data.get('shop_services') or '').strip() or 'Sales | Installation | Gas Refilling | AMC | Repairing')

    raw_phone = str(data.get('shop_phone') or '').strip()
    raw_email = str(data.get('shop_email') or '').strip()
    raw_address = str(data.get('shop_address') or '').strip()
    raw_gstin = str(data.get('shop_gstin') or '').strip()

    if not raw_phone or not raw_address or not raw_gstin:
        try:
            from database.db_connection import DatabaseContext
            with DatabaseContext() as db:
                s_row = db.execute_query("SELECT * FROM shop_details ORDER BY id DESC LIMIT 1", fetch_one=True)
                if s_row:
                    if not raw_phone:
                        raw_phone = str(s_row.get('phone') or s_row.get('owner_phone') or s_row.get('mobile') or '').strip()
                    if not raw_email and s_row.get('email'):
                        raw_email = str(s_row.get('email') or '').strip()
                    if not raw_address and s_row.get('address'):
                        raw_address = str(s_row.get('address') or '').strip()
                    if not raw_gstin and s_row.get('gst_number'):
                        raw_gstin = str(s_row.get('gst_number') or '').strip()
                    if shop_name == 'ANSH AIR COOL' and s_row.get('shop_name'):
                        shop_name = escape(str(s_row.get('shop_name') or '').strip())
                    if shop_tagline == 'AC SALES & SERVICE MANAGEMENT' and s_row.get('tagline'):
                        shop_tagline = escape(str(s_row.get('tagline') or '').strip())
                    if shop_services == 'Sales | Installation | Gas Refilling | AMC | Repairing' and s_row.get('services'):
                        shop_services = escape(str(s_row.get('services') or '').strip())
        except Exception:
            pass

    shop_phone = escape(raw_phone if raw_phone else '+91 90000 00000')
    shop_email = escape(raw_email if raw_email else 'shop@email.com')
    shop_address = escape(raw_address if raw_address else 'Your Shop Address, City - 000000')
    shop_gstin = escape(raw_gstin)

    inv_no = escape(str(data.get('invoice_no') or data.get('invoice_number', 'INV-2026-001')))
    inv_date = escape(str(data.get('invoice_date', datetime.now().strftime('%d-%m-%Y'))))
    due_date = escape(str(data.get('due_date', inv_date)))
    pay_status = escape(str(data.get('payment_status', 'PAID')))
    pay_mode = escape(str(data.get('payment_mode', 'UPI')))

    cust_name = escape(str(data.get('customer_name', 'Customer')))
    cust_mobile = escape(str(data.get('customer_mobile', 'N/A')))
    cust_email = escape(str(data.get('customer_email', '')))
    cust_addr = escape(str(data.get('customer_address', 'N/A')))

    svc_type = escape(str(data.get('service_type') or 'Installation & Service'))
    tech_name = escape(str(data.get('technician_name') or 'Rahul Sharma'))
    work_loc = escape(str(data.get('work_location') or cust_addr))

    barcode_svg = generate_barcode_svg(inv_no)

    # Logo
    logo_b64 = get_logo_base64()
    if logo_b64:
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="max-height: 52px; max-width: 110px; object-fit: contain;" alt="Logo" />'
    else:
        # Default SVG snowflake AC logo
        logo_html = '''
        <svg width="60" height="48" viewBox="0 0 120 90" fill="none" xmlns="http://www.w3.org/2000/svg">
          <g stroke="#0070ba" stroke-width="3.5" stroke-linecap="round">
            <line x1="60" y1="4" x2="60" y2="24"/>
            <line x1="50" y1="14" x2="70" y2="14"/>
            <line x1="53" y1="7" x2="67" y2="21"/>
            <line x1="67" y1="7" x2="53" y2="21"/>
          </g>
          <rect x="12" y="28" width="96" height="34" rx="6" fill="#002b55" />
          <rect x="22" y="42" width="76" height="4" rx="2" fill="#ffffff" />
          <g stroke="#0070ba" stroke-width="3.5" stroke-linecap="round">
            <line x1="60" y1="66" x2="60" y2="86"/>
            <line x1="50" y1="76" x2="70" y2="76"/>
            <line x1="53" y1="69" x2="67" y2="83"/>
            <line x1="67" y1="69" x2="53" y2="83"/>
          </g>
        </svg>
        '''

    # QR
    qr_b64 = get_qr_base64()
    if qr_b64:
        qr_img_html = f'<img src="data:image/jpeg;base64,{qr_b64}" style="width: 106px; height: 106px; object-fit: contain; border-radius: 4px;" alt="Scan & Pay" />'
    else:
        qr_img_html = '<div style="width: 106px; height: 106px; background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 11px; color: #64748b; font-weight: 600;">Scan UPI</div>'

    # Payment status color
    st_upper = pay_status.upper()
    if 'PAID' in st_upper and 'UNPAID' not in st_upper and 'PART' not in st_upper:
        st_color = '#16a34a'
    elif 'PART' in st_upper:
        st_color = '#d97706'
    else:
        st_color = '#dc2626'

    # Items
    items = data.get('items', [])
    items_rows = ''
    total_calc = 0.0
    for i, it in enumerate(items, 1):
        desc = escape(str(it.get('service_name') or it.get('part_name') or it.get('description', 'Service')))
        qty = it.get('quantity', 1)
        rate = float(it.get('rate', 0))
        gst_p = float(it.get('gst_percent', 18))
        amt = float(it.get('amount', qty * rate))
        total_calc += amt

        items_rows += f'''
        <tr>
            <td style="text-align: center; font-weight: 600;">{i}</td>
            <td style="text-align: left; font-weight: 600;">{desc}</td>
            <td style="text-align: center; font-weight: 600;">{qty}</td>
            <td style="text-align: right;">{rate:,.2f}</td>
            <td style="text-align: center;">{int(gst_p)}%</td>
            <td style="text-align: right; font-weight: 600;">{amt:,.2f}</td>
        </tr>
        '''

    # Summary calculations
    subtotal = float(data.get('subtotal', total_calc))
    discount = float(data.get('discount', 0))
    taxable = float(data.get('taxable', subtotal - discount))
    cgst_rate = float(data.get('cgst_rate', 9.0))
    cgst_amount = float(data.get('cgst_amount', 0))
    sgst_rate = float(data.get('sgst_rate', 9.0))
    sgst_amount = float(data.get('sgst_amount', 0))
    grand_total = float(data.get('total') or data.get('total_amount', subtotal - discount + cgst_amount + sgst_amount))
    words = amount_to_words(grand_total)

    # Dynamic Terms
    terms_raw = str(data.get('terms_conditions', '1. Goods once sold will not be taken back.\n2. Warranty is applicable as per company policy.\n3. Payment to be made within the due date.\n4. Interest will be charged @ 18% p.a. on overdue.'))
    terms_lines = [l.strip() for l in terms_raw.splitlines() if l.strip()]
    terms_items_html = ''
    for t_line in terms_lines:
        clean_line = t_line
        if clean_line and clean_line[0].isdigit():
            clean_line = clean_line.lstrip('0123456789.-) ')
        terms_items_html += f'<li>{escape(clean_line)}</li>'
    if not terms_items_html:
        terms_items_html = '''
        <li>Goods once sold will not be taken back.</li>
        <li>Warranty is applicable as per company policy.</li>
        <li>Payment to be made within the due date.</li>
        <li>Interest will be charged @ 18% p.a. on overdue.</li>
        '''

    # Thank you note
    thanks_note = escape(str(data.get('thank_you_note', 'For your trust in our services.')))
    if not thanks_note or thanks_note == 'Thank you for your business!':
        thanks_note = 'For your trust in our services.'

    gst_line_html = f'<div style="font-weight: 700; color: #ffffff; margin-top: 4px; font-size: 9.5px; letter-spacing: 0.4px;">GSTIN : {shop_gstin}</div>' if shop_gstin else ''
    first_name_cust = cust_name.split()[0] if cust_name else 'Customer'
    tech_first = tech_name.split()[0] if tech_name else 'Technician'

    clean_phone_upi = raw_phone.replace(' ', '').replace('+91', '') if raw_phone else '9000000000'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tax Invoice #{inv_no}</title>
<style>
    @page {{
        size: A4 portrait;
        margin: 0;
    }}
    * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }}
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        background: #ffffff;
        color: #1e293b;
        font-size: 9.5pt;
        line-height: 1.35;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }}
    .sheet {{
        width: 210mm;
        height: 296mm;
        padding: 8mm 10mm 6mm 10mm;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        margin: 0 auto;
        position: relative;
        background: #ffffff;
    }}

    /* ── Top Header ── */
    .header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
    }}
    .brand-col {{
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    .brand-info .b-title {{
        font-size: 24px;
        font-weight: 900;
        color: #0b3c6d;
        letter-spacing: 0.8px;
        line-height: 1.1;
    }}
    .brand-info .b-sub {{
        font-size: 10.5px;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        margin-top: 3px;
    }}
    .brand-info .b-services {{
        font-size: 9.5px;
        font-weight: 600;
        color: #0052cc;
        margin-top: 3px;
        letter-spacing: 0.2px;
    }}

    .shop-box {{
        background: #0b2e59;
        color: #ffffff;
        border-radius: 8px;
        padding: 8px 14px;
        font-size: 8.5pt;
        line-height: 1.45;
        min-width: 250px;
        text-align: left;
    }}
    .shop-row {{
        display: flex;
        align-items: flex-start;
        gap: 6px;
    }}
    .shop-row .icon {{
        font-size: 9pt;
        opacity: 0.9;
        flex-shrink: 0;
    }}

    .divider-blue {{
        height: 3px;
        background: #0052cc;
        border-radius: 2px;
        margin: 8px 0 10px 0;
    }}

    /* ── Invoice Title & Badge Bar ── */
    .title-row {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
    }}
    .inv-title-col h1 {{
        font-size: 26px;
        font-weight: 900;
        color: #0052cc;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }}
    .meta-table {{
        font-size: 9pt;
        border-collapse: collapse;
    }}
    .meta-table td {{
        padding: 1.5px 0;
    }}
    .meta-table .lbl {{
        font-weight: 700;
        color: #0f172a;
        width: 120px;
    }}
    .meta-table .sep {{
        width: 14px;
        text-align: center;
        font-weight: 700;
    }}
    .meta-table .val {{
        font-weight: 600;
        color: #1e293b;
    }}

    .inv-badge-box {{
        width: 180px;
        text-align: center;
    }}
    .inv-badge-top {{
        background: #0052cc;
        color: #ffffff;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        padding: 4px 8px;
    }}
    .inv-badge-top .b-lbl {{
        font-size: 8pt;
        opacity: 0.95;
    }}
    .inv-badge-top .b-num {{
        font-size: 13pt;
        font-weight: 800;
        letter-spacing: 0.5px;
    }}
    .inv-badge-bottom {{
        background: #ffffff;
        border: 1.5px solid #0052cc;
        border-top: none;
        border-bottom-left-radius: 8px;
        border-bottom-right-radius: 8px;
        padding: 4px 8px 3px 8px;
    }}

    /* ── Customer & Service Cards ── */
    .cards-row {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-top: 10px;
    }}
    .info-card {{
        border: 1.5px solid #0052cc;
        border-radius: 8px;
        padding: 8px 12px;
        background: #ffffff;
    }}
    .card-head {{
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 9.5pt;
        font-weight: 800;
        color: #0052cc;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
        padding-bottom: 4px;
        border-bottom: 1px solid #e2e8f0;
    }}
    .card-head-icon {{
        font-size: 10pt;
    }}
    .card-table {{
        width: 100%;
        font-size: 8.5pt;
        border-collapse: collapse;
    }}
    .card-table td {{
        padding: 1.5px 0;
        vertical-align: top;
    }}
    .card-table .c-lbl {{
        font-weight: 700;
        color: #0f172a;
        width: 90px;
    }}
    .card-table .c-sep {{
        width: 12px;
        text-align: center;
        font-weight: 700;
    }}
    .card-table .c-val {{
        font-weight: 500;
        color: #1e293b;
    }}

    /* ── Items Table ── */
    .items-table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        font-size: 8.5pt;
        border: 1.5px solid #002b55;
    }}
    .items-table thead {{
        background: #002b55;
        color: #ffffff;
    }}
    .items-table thead th {{
        padding: 6px 8px;
        font-weight: 700;
        letter-spacing: 0.3px;
        border-right: 1px solid rgba(255,255,255,0.2);
    }}
    .items-table thead th:last-child {{
        border-right: none;
    }}
    .items-table tbody td {{
        padding: 5px 8px;
        border: 1px solid #cbd5e1;
    }}
    .items-table tbody tr:nth-child(even) {{
        background: #f8fafc;
    }}

    /* ── QR & Summary Section ── */
    .mid-section {{
        display: grid;
        grid-template-columns: 210px 1fr;
        gap: 12px;
        margin-top: 10px;
        align-items: start;
    }}
    .qr-card {{
        border: 1px solid #94a3b8;
        border-radius: 8px;
        padding: 8px;
        text-align: center;
        background: #ffffff;
    }}
    .qr-title {{
        font-size: 9.5pt;
        font-weight: 800;
        color: #002b55;
        letter-spacing: 0.5px;
    }}
    .qr-sub {{
        font-size: 7.5pt;
        color: #475569;
        margin-top: 1px;
        margin-bottom: 5px;
        font-family: monospace;
    }}
    .qr-apps {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        margin-top: 4px;
        font-size: 7.5pt;
        font-weight: 700;
    }}

    .summary-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 9pt;
        border: 1px solid #cbd5e1;
    }}
    .summary-table td {{
        padding: 4px 10px;
        border-bottom: 1px solid #e2e8f0;
    }}
    .summary-table .s-lbl {{
        font-weight: 600;
        color: #1e293b;
    }}
    .summary-table .s-val {{
        font-weight: 700;
        text-align: right;
    }}
    .summary-table .gt-row {{
        background: #0052cc;
        color: #ffffff;
    }}
    .summary-table .gt-row td {{
        padding: 7px 10px;
        border: none;
    }}
    .summary-table .gt-lbl {{
        font-size: 10pt;
        font-weight: 800;
        letter-spacing: 0.5px;
    }}
    .summary-table .gt-val {{
        font-size: 13pt;
        font-weight: 900;
        text-align: right;
    }}

    .words-bar {{
        margin-top: 4px;
        font-size: 8.5pt;
        text-align: right;
        padding-top: 4px;
    }}
    .words-bar .w-lbl {{
        font-weight: 800;
        color: #0052cc;
    }}
    .words-bar .w-val {{
        font-weight: 600;
        color: #0f172a;
    }}

    /* ── Terms & Thank You ── */
    .bottom-info {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-top: 8px;
        align-items: center;
    }}
    .terms-box {{
        border: 1px solid #94a3b8;
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 7.5pt;
        color: #334155;
        line-height: 1.4;
    }}
    .terms-title {{
        font-weight: 800;
        color: #002b55;
        font-size: 8pt;
        margin-bottom: 3px;
        letter-spacing: 0.4px;
    }}
    .terms-box ol {{
        margin-left: 14px;
        padding: 0;
    }}

    .thanks-box {{
        text-align: center;
    }}
    .thanks-script {{
        font-family: 'Brush Script MT', 'Segoe Script', 'Lucida Handwriting', 'Caveat', cursive;
        font-size: 30pt;
        color: #0052cc;
        font-weight: 700;
        line-height: 1;
    }}
    .thanks-sub {{
        font-size: 8.5pt;
        font-weight: 600;
        color: #1e293b;
        margin-top: 4px;
    }}

    /* ── Dark Navy Footer Bar ── */
    .footer-bar {{
        background: #002244;
        color: #ffffff;
        border-radius: 6px;
        padding: 8px 16px;
        margin-top: 8px;
        display: grid;
        grid-template-columns: 1fr 1fr 1.3fr;
        gap: 12px;
        align-items: center;
    }}
    .sig-col {{
        text-align: center;
        font-size: 8pt;
    }}
    .sig-col .sig-lbl {{
        opacity: 0.85;
        margin-bottom: 2px;
    }}
    .sig-col .sig-line {{
        border-bottom: 1px solid rgba(255,255,255,0.6);
        height: 22px;
        display: flex;
        align-items: flex-end;
        justify-content: center;
        font-family: 'Brush Script MT', 'Segoe Script', cursive;
        font-size: 13pt;
        color: #ffffff;
        padding-bottom: 2px;
    }}

    .company-sig-col {{
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 10px;
    }}
    .for-company {{
        font-size: 9pt;
        font-weight: 800;
        letter-spacing: 0.5px;
        text-align: right;
    }}
    .stamp-circle {{
        width: 44px;
        height: 44px;
        border: 2px dashed rgba(255,255,255,0.7);
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        font-size: 5.5pt;
        font-weight: 800;
        line-height: 1.1;
        letter-spacing: 0.3px;
        flex-shrink: 0;
        background: rgba(255,255,255,0.05);
    }}
</style>
</head>
<body>
<div class="sheet">
    <div>
        <!-- ═══ HEADER ═══ -->
        <div class="header">
            <div class="brand-col">
                {logo_html}
                <div class="brand-info">
                    <div class="b-title">{shop_name}</div>
                    <div class="b-sub">{shop_tagline}</div>
                    <div class="b-services">{shop_services}</div>
                </div>
            </div>
            <div class="shop-box">
                <div class="shop-row">
                    <span class="icon">&#9742;</span>
                    <span style="font-weight: 600;">{shop_phone}</span>
                </div>
                <div class="shop-row" style="margin-top: 2px;">
                    <span class="icon">&#9993;</span>
                    <span>{shop_email}</span>
                </div>
                <div class="shop-row" style="margin-top: 2px;">
                    <span class="icon">&#128205;</span>
                    <span>{shop_address}</span>
                </div>
                {gst_line_html}
            </div>
        </div>

        <div class="divider-blue"></div>

        <!-- ═══ TITLE & BADGE ═══ -->
        <div class="title-row">
            <div class="inv-title-col">
                <h1>INVOICE</h1>
                <table class="meta-table">
                    <tr>
                        <td class="lbl">Invoice Date</td>
                        <td class="sep">:</td>
                        <td class="val">{inv_date}</td>
                    </tr>
                    <tr>
                        <td class="lbl">Due Date</td>
                        <td class="sep">:</td>
                        <td class="val">{due_date}</td>
                    </tr>
                    <tr>
                        <td class="lbl">Payment Status</td>
                        <td class="sep">:</td>
                        <td class="val" style="color: {st_color}; font-weight: 800;">{pay_status}</td>
                    </tr>
                    <tr>
                        <td class="lbl">Payment Method</td>
                        <td class="sep">:</td>
                        <td class="val">{pay_mode}</td>
                    </tr>
                </table>
            </div>
            <div class="inv-badge-box">
                <div class="inv-badge-top">
                    <div class="b-lbl">Invoice No.</div>
                    <div class="b-num">{inv_no}</div>
                </div>
                <div class="inv-badge-bottom">
                    {barcode_svg}
                </div>
            </div>
        </div>

        <!-- ═══ CUSTOMER & SERVICE CARDS ═══ -->
        <div class="cards-row">
            <div class="info-card">
                <div class="card-head">
                    <span class="card-head-icon">&#128100;</span>
                    <span>CUSTOMER DETAILS</span>
                </div>
                <table class="card-table">
                    <tr>
                        <td class="c-lbl">Name</td>
                        <td class="c-sep">:</td>
                        <td class="c-val" style="font-weight: 700;">{cust_name}</td>
                    </tr>
                    <tr>
                        <td class="c-lbl">Mobile</td>
                        <td class="c-sep">:</td>
                        <td class="c-val">{cust_mobile}</td>
                    </tr>
                    <tr>
                        <td class="c-lbl">Email</td>
                        <td class="c-sep">:</td>
                        <td class="c-val">{cust_email if cust_email else '&mdash;'}</td>
                    </tr>
                    <tr>
                        <td class="c-lbl">Address</td>
                        <td class="c-sep">:</td>
                        <td class="c-val">{cust_addr}</td>
                    </tr>
                </table>
            </div>

            <div class="info-card">
                <div class="card-head">
                    <span class="card-head-icon">&#128295;</span>
                    <span>SERVICE DETAILS</span>
                </div>
                <table class="card-table">
                    <tr>
                        <td class="c-lbl">Service Type</td>
                        <td class="c-sep">:</td>
                        <td class="c-val">{svc_type}</td>
                    </tr>
                    <tr>
                        <td class="c-lbl">Technician</td>
                        <td class="c-sep">:</td>
                        <td class="c-val">{tech_name if tech_name else 'Unassigned'}</td>
                    </tr>
                    <tr>
                        <td class="c-lbl">Visit Date</td>
                        <td class="c-sep">:</td>
                        <td class="c-val">{inv_date}</td>
                    </tr>
                    <tr>
                        <td class="c-lbl">Work Location</td>
                        <td class="c-sep">:</td>
                        <td class="c-val">{work_loc}</td>
                    </tr>
                </table>
            </div>
        </div>

        <!-- ═══ ITEMS TABLE ═══ -->
        <table class="items-table">
            <thead>
                <tr>
                    <th style="width: 6%;">Sr.</th>
                    <th style="width: 48%; text-align: left;">Item / Service</th>
                    <th style="width: 8%;">Qty.</th>
                    <th style="width: 15%; text-align: right;">Unit Price (&#8377;)</th>
                    <th style="width: 8%;">GST %</th>
                    <th style="width: 15%; text-align: right;">Amount (&#8377;)</th>
                </tr>
            </thead>
            <tbody>
                {items_rows}
            </tbody>
        </table>

        <!-- ═══ MID SECTION (QR & SUMMARY) ═══ -->
        <div class="mid-section">
            <div class="qr-card">
                <div class="qr-title">SCAN & PAY</div>
                <div class="qr-sub">UPI: {clean_phone_upi}@upi</div>
                {qr_img_html}
                <div class="qr-apps">
                    <span style="color: #4285f4;">GPay</span> &bull;
                    <span style="color: #5f259f;">PhonePe</span> &bull;
                    <span style="color: #00b9f5;">Paytm</span> &bull;
                    <span style="color: #ea580c;">UPI</span>
                </div>
            </div>

            <div>
                <table class="summary-table">
                    <tr>
                        <td class="s-lbl">Sub Total (&#8377;)</td>
                        <td class="s-val">{subtotal:,.2f}</td>
                    </tr>
                    {'<tr><td class="s-lbl" style="color: #16a34a;">Discount (&#8377;)</td><td class="s-val" style="color: #16a34a;">- ' + f'{discount:,.2f}' + '</td></tr>' if discount > 0 else ''}
                    <tr>
                        <td class="s-lbl">Taxable Amount (&#8377;)</td>
                        <td class="s-val">{taxable:,.2f}</td>
                    </tr>
                    {'<tr><td class="s-lbl">CGST (' + f'{cgst_rate:.0f}%' + ')</td><td class="s-val">' + f'{cgst_amount:,.2f}' + '</td></tr>' if cgst_amount > 0 else ''}
                    {'<tr><td class="s-lbl">SGST (' + f'{sgst_rate:.0f}%' + ')</td><td class="s-val">' + f'{sgst_amount:,.2f}' + '</td></tr>' if sgst_amount > 0 else ''}
                    <tr class="gt-row">
                        <td class="gt-lbl">Grand Total (&#8377;)</td>
                        <td class="gt-val">&#8377;{grand_total:,.2f}</td>
                    </tr>
                </table>
                <div class="words-bar">
                    <span class="w-lbl">Amount in Words : </span>
                    <span class="w-val">{words}</span>
                </div>
            </div>
        </div>

        <!-- ═══ TERMS & THANK YOU ═══ -->
        <div class="bottom-info">
            <div class="terms-box">
                <div class="terms-title">TERMS & CONDITIONS</div>
                <ol>
                    {terms_items_html}
                </ol>
            </div>
            <div class="thanks-box">
                <div class="thanks-script">Thank You!</div>
                <div class="thanks-sub">{thanks_note}</div>
            </div>
        </div>
    </div>

    <!-- ═══ DARK NAVY FOOTER BAR ═══ -->
    <div class="footer-bar">
        <div class="sig-col">
            <div class="sig-lbl">Technician Signature</div>
            <div class="sig-line">{tech_first}</div>
        </div>
        <div class="sig-col">
            <div class="sig-lbl">Customer Signature</div>
            <div class="sig-line">{first_name_cust}</div>
        </div>
        <div class="company-sig-col">
            <div class="for-company">
                <div>For {shop_name}</div>
                <div style="font-size: 6.5pt; opacity: 0.75; font-weight: normal; margin-top: 2px;">Authorized Signatory</div>
            </div>
            <div class="stamp-circle">
                <span>{shop_name[:8]}</span>
                <span style="font-size: 4.5pt; opacity: 0.85;">★ SEAL ★</span>
            </div>
        </div>
    </div>
</div>
</body>
</html>'''