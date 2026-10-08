"""
AMC HTML Template - Professional Annual Maintenance Contract Agreement & Certificate
Designed for A4 print and PDF generation via QWebEngine / printToPdf
"""
import base64
import os
import hashlib
from html import escape
from datetime import datetime


def get_logo_base64():
    try:
        from utils.logo_helper import get_logo_path
        path = get_logo_path()
        if path and os.path.exists(path):
            with open(path, 'rb') as f:
                return base64.b64encode(f.read()).decode()
    except Exception:
        pass
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
    """Generate clean SVG barcode matching AMC ID"""
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
            svg_bars.append(f'<rect x="{x}" y="1" width="1.6" height="22" fill="#000000" />')
        x += 2.0
    total_w = x + 4
    return f'<svg viewBox="0 0 {total_w} 24" preserveAspectRatio="none" style="width: 130px; height: 24px; display: block;">{"".join(svg_bars)}</svg>'


def generate_amc_html(contract_data, shop_data=None):
    """
    Generate professional A4 HTML for AMC Contract Agreement & Certificate
    """
    c = contract_data or {}
    s = shop_data or {}

    logo_b64 = get_logo_base64()
    barcode_svg = generate_barcode_svg(c.get('amc_id', 'AMC'))

    shop_name = escape(str(s.get('shop_name') or 'AC SERVICE & BILLING EXPERTS'))
    shop_tagline = escape(str(s.get('tagline') or 'Commercial & Residential Air Conditioning Solutions'))
    shop_address = escape(str(s.get('address') or 'Main Market Road, City Center'))
    shop_phone = escape(str(s.get('phone') or s.get('mobile') or s.get('owner_phone') or ''))
    shop_email = escape(str(s.get('email') or ''))
    shop_gst = escape(str(s.get('gst_number') or ''))

    amc_id = escape(str(c.get('amc_id', 'AMC0001')))
    contract_type = escape(str(c.get('contract_type', 'Comprehensive')))
    is_comp = 'comprehensive' in contract_type.lower() and 'non' not in contract_type.lower()
    type_badge_color = "#059669" if is_comp else "#2563eb"
    type_badge_bg = "#ecfdf5" if is_comp else "#eff6ff"
    type_badge_border = "#a7f3d0" if is_comp else "#bfdbfe"

    start_date = escape(str(c.get('start_date', 'N/A')))
    end_date = escape(str(c.get('end_date', 'N/A')))
    duration = escape(str(c.get('contract_duration', 1)))
    status = escape(str(c.get('amc_status', 'Active')).title())

    cust_name = escape(str(c.get('customer_name', 'Customer Name')))
    cust_phone = escape(str(c.get('customer_mobile', 'N/A')))
    cust_email = escape(str(c.get('customer_email', '')))
    cust_addr = escape(str(c.get('customer_address', 'Service Address on Record')))
    cust_landmark = escape(str(c.get('customer_landmark', '')))

    units_count = c.get('no_of_units', 1)
    services_per_year = c.get('services_per_year', 2)
    services_rem = c.get('services_remaining', 2)
    primary_tech = escape(str(c.get('primary_technician', 'Assigned by Service Manager')))

    # Financials
    contract_val = float(c.get('contract_amount') or c.get('total_amount') or 0)
    gst_percent = float(c.get('gst_percent') or c.get('gst_percentage') or 0)
    total_val = float(c.get('total_amount') or contract_val)
    if gst_percent > 0 and total_val == contract_val:
        base_val = round(total_val / (1 + (gst_percent / 100)), 2)
        gst_amt = round(total_val - base_val, 2)
    else:
        base_val = round(contract_val, 2)
        gst_amt = round(total_val - base_val, 2) if total_val > base_val else 0

    advance_paid = float(c.get('advance_paid') or 0)
    balance_amount = float(c.get('balance_amount') or 0)
    payment_mode = escape(str(c.get('payment_mode', 'Pending')))
    payment_status = escape(str(c.get('payment_status', 'Pending')).title())

    units_list = c.get('units') or []
    visits_list = c.get('visits') or []
    notes = escape(str(c.get('notes') or c.get('terms_conditions') or 'Standard periodic maintenance & inspection terms apply.'))

    # Units Table Rows
    units_html_rows = ""
    if units_list:
        for idx, u in enumerate(units_list, 1):
            brand = escape(str(u.get('brand') or 'AC Unit'))
            ac_type = escape(str(u.get('ac_type') or 'Split'))
            ton = escape(str(u.get('ton') or '1.5'))
            model_sr = escape(str(u.get('serial_number') or u.get('model') or '--'))
            loc = escape(str(u.get('indoor_location') or u.get('outdoor_location') or 'Main Premises'))
            units_html_rows += f"""
            <tr>
                <td style="text-align: center; font-weight: 700; color: #2563eb;">Unit #{idx}</td>
                <td style="font-weight: 600;">{brand}</td>
                <td>{ac_type}</td>
                <td style="text-align: center;">{ton} Ton</td>
                <td><code>{model_sr}</code></td>
                <td>{loc}</td>
            </tr>
            """
    else:
        units_html_rows = f"""
        <tr>
            <td style="text-align: center; font-weight: 700; color: #2563eb;">Unit #1</td>
            <td style="font-weight: 600;">Air Conditioner Unit(s)</td>
            <td>Split / Window</td>
            <td style="text-align: center;">1.5 Ton</td>
            <td>Standard Unit</td>
            <td>Customer Site Premises ({units_count} Unit Covered)</td>
        </tr>
        """

    # Visits Table Rows
    visits_html_rows = ""
    if visits_list:
        for v in visits_list:
            v_num = v.get('visit_number', 1)
            v_date = escape(str(v.get('visit_date', 'Scheduled Date')))
            v_tech = escape(str(v.get('technician_name') or 'Service Technician'))
            v_stat = escape(str(v.get('visit_status') or 'Scheduled').title())
            stat_color = "#059669" if v_stat.lower() == 'completed' else "#2563eb"
            stat_bg = "#ecfdf5" if v_stat.lower() == 'completed' else "#eff6ff"
            v_work = escape(str(v.get('work_done') or v.get('notes') or 'Comprehensive preventive maintenance servicing & chemical wash check'))
            visits_html_rows += f"""
            <tr>
                <td style="text-align: center; font-weight: 700;">Visit #{v_num}</td>
                <td style="text-align: center; font-weight: 600;">{v_date}</td>
                <td>{v_tech}</td>
                <td style="text-align: center;">
                    <span style="display: inline-block; padding: 2px 8px; font-size: 8pt; font-weight: 700; color: {stat_color}; background: {stat_bg}; border-radius: 10px;">
                        ● {v_stat}
                    </span>
                </td>
                <td style="font-size: 8.5pt; color: #475569;">{v_work}</td>
            </tr>
            """
    else:
        for i in range(1, int(services_per_year) + 1):
            visits_html_rows += f"""
            <tr>
                <td style="text-align: center; font-weight: 700;">Visit #{i}</td>
                <td style="text-align: center; font-weight: 600;">Periodic Service #{i}</td>
                <td>{primary_tech}</td>
                <td style="text-align: center;">
                    <span style="display: inline-block; padding: 2px 8px; font-size: 8pt; font-weight: 700; color: #2563eb; background: #eff6ff; border-radius: 10px;">
                        ● Scheduled
                    </span>
                </td>
                <td style="font-size: 8.5pt; color: #475569;">Periodic jet pump washing, electrical checks, filter cleaning, and refrigerant inspection</td>
            </tr>
            """

    bal_color = "#dc2626" if balance_amount > 0 else "#059669"
    bal_badge = f'<span style="color: {bal_color}; font-weight: 800;">₹{balance_amount:,.2f}</span>' if balance_amount > 0 else '<span style="color: #059669; font-weight: 800;">Nil (Fully Settled)</span>'

    logo_img_tag = f'<img src="data:image/png;base64,{logo_b64}" style="max-height: 52px; max-width: 170px; object-fit: contain;" />' if logo_b64 else f'<h2 style="margin: 0; color: #1e3a8a; font-size: 16pt;">{shop_name}</h2>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>AMC Contract Agreement - {amc_id}</title>
<style>
    @page {{
        size: A4 portrait;
        margin: 10mm 12mm 10mm 12mm;
    }}
    * {{
        box-sizing: border-box;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }}
    body {{
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', Helvetica, Arial, sans-serif;
        color: #1e293b;
        background-color: #ffffff;
        margin: 0;
        padding: 0;
        font-size: 9pt;
        line-height: 1.4;
    }}
    .document-container {{
        width: 100%;
        max-width: 800px;
        margin: 0 auto;
    }}
    .header-table {{
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 12px;
        border-bottom: 2px solid #2563eb;
        padding-bottom: 10px;
    }}
    .header-table td {{
        vertical-align: top;
    }}
    .shop-title {{
        font-size: 15pt;
        font-weight: 900;
        color: #0f172a;
        letter-spacing: -0.3px;
        margin: 0 0 2px 0;
    }}
    .shop-subtitle {{
        font-size: 8.5pt;
        color: #64748b;
        margin: 0 0 4px 0;
    }}
    .shop-meta {{
        font-size: 8pt;
        color: #475569;
        line-height: 1.35;
    }}
    .meta-cards-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 6px 0;
        margin-bottom: 10px;
    }}
    .meta-card {{
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 6px 10px;
    }}
    .meta-card-label {{
        font-size: 7pt;
        font-weight: 800;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .meta-card-value {{
        font-size: 9pt;
        font-weight: 800;
        color: #0f172a;
        margin-top: 2px;
    }}
    .info-split-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 8px 0;
        margin-bottom: 12px;
    }}
    .info-box {{
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 9px 12px;
        vertical-align: top;
    }}
    .info-box-header {{
        font-size: 8pt;
        font-weight: 800;
        color: #1e3a8a;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-bottom: 1.5px solid #e2e8f0;
        padding-bottom: 4px;
        margin-bottom: 6px;
    }}
    .info-row {{
        font-size: 8.5pt;
        margin-bottom: 3px;
        display: flex;
    }}
    .info-lbl {{
        width: 110px;
        color: #64748b;
        font-weight: 600;
    }}
    .info-val {{
        color: #0f172a;
        font-weight: 700;
        flex: 1;
    }}
    .section-title {{
        font-size: 9pt;
        font-weight: 800;
        color: #0f172a;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin: 12px 0 5px 0;
        display: flex;
        align-items: center;
    }}
    .section-title::after {{
        content: "";
        flex: 1;
        margin-left: 8px;
        height: 1px;
        background-color: #cbd5e1;
    }}
    .data-table {{
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 10px;
        font-size: 8.5pt;
    }}
    .data-table th {{
        background-color: #f1f5f9;
        color: #1e293b;
        border: 1px solid #cbd5e1;
        padding: 5px 8px;
        font-size: 7.5pt;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        text-align: left;
    }}
    .data-table td {{
        border: 1px solid #cbd5e1;
        padding: 5px 8px;
        color: #1e293b;
    }}
    .data-table tr:nth-child(even) {{
        background-color: #f8fafc;
    }}
    .fin-box {{
        background: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 8px 12px;
    }}
    .terms-box {{
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 8px 10px;
        font-size: 7.5pt;
        color: #475569;
        line-height: 1.35;
        margin-bottom: 12px;
    }}
    .terms-box ul {{
        margin: 3px 0 0 0;
        padding-left: 18px;
    }}
    .terms-box li {{
        margin-bottom: 2px;
    }}
    .signatures-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 14px 0;
        margin-top: 14px;
    }}
    .sign-box {{
        border-top: 1.5px dashed #94a3b8;
        padding-top: 4px;
        text-align: center;
        font-size: 8pt;
        color: #475569;
    }}
    .sign-box-title {{
        font-weight: 700;
        color: #0f172a;
    }}
    .footer-note {{
        margin-top: 14px;
        border-top: 1px solid #e2e8f0;
        padding-top: 6px;
        text-align: center;
        font-size: 7.5pt;
        color: #64748b;
    }}
</style>
</head>
<body>
<div class="document-container">

    <!-- 1. Header with Shop Details and Barcode -->
    <table class="header-table">
        <tr>
            <td style="width: 55%;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
                    {logo_img_tag}
                    <div>
                        <div class="shop-title">{shop_name}</div>
                        <div class="shop-subtitle">{shop_tagline}</div>
                    </div>
                </div>
                <div class="shop-meta">
                    📍 {shop_address}<br>
                    📞 <b>Support:</b> {shop_phone} &nbsp;|&nbsp; ✉️ {shop_email}<br>
                    {f"🏛️ <b>GSTIN:</b> {shop_gst}" if shop_gst else ""}
                </div>
            </td>
            <td style="width: 45%; text-align: right;">
                <div style="display: inline-block; text-align: right;">
                    <div style="margin-bottom: 2px;">{barcode_svg}</div>
                    <div style="font-size: 8pt; font-weight: 700; color: #64748b; font-family: monospace;">CONTRACT NO: {amc_id}</div>
                    <div style="margin-top: 4px;">
                        <span style="display: inline-block; padding: 3px 10px; font-size: 8pt; font-weight: 800; border-radius: 12px; background: {type_badge_bg}; color: {type_badge_color}; border: 1px solid {type_badge_border}; text-transform: uppercase;">
                            ● {contract_type} AMC
                        </span>
                    </div>
                </div>
            </td>
        </tr>
    </table>

    <!-- 2. Contract Title Banner -->
    <table style="width: 100%; margin-bottom: 10px;">
        <tr>
            <td style="background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%); color: #ffffff; border-radius: 6px; padding: 7px 12px;">
                <table style="width: 100%; color: #ffffff;">
                    <tr>
                        <td>
                            <div style="font-size: 11pt; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase;">
                                Annual Maintenance Contract (AMC) Agreement & Service Certificate
                            </div>
                            <div style="font-size: 7.5pt; color: #bfdbfe; margin-top: 1px;">
                                Authorized Preventive Maintenance Coverage, Equipment Registry & Service Warranty
                            </div>
                        </td>
                        <td style="text-align: right; font-weight: 800; font-size: 9pt;">
                            Status: <span style="color: #86efac; text-transform: uppercase;">● {status}</span>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>

    <!-- 3. Meta KPI Stats Bar -->
    <table class="meta-cards-table">
        <tr>
            <td class="meta-card">
                <div class="meta-card-label">Contract ID</div>
                <div class="meta-card-value" style="color: #2563eb;">{amc_id}</div>
            </td>
            <td class="meta-card">
                <div class="meta-card-label">Agreement Period</div>
                <div class="meta-card-value">{start_date} → {end_date}</div>
            </td>
            <td class="meta-card">
                <div class="meta-card-label">Duration</div>
                <div class="meta-card-value">{duration} Year(s)</div>
            </td>
            <td class="meta-card">
                <div class="meta-card-label">AC Units Covered</div>
                <div class="meta-card-value" style="color: #0284c7;">❄️ {units_count} Unit(s)</div>
            </td>
            <td class="meta-card">
                <div class="meta-card-label">Preventive Visits</div>
                <div class="meta-card-value" style="color: #059669;">🛠️ {services_per_year} Total ({services_rem} Rem.)</div>
            </td>
        </tr>
    </table>

    <!-- 4. Customer and Service Location Details -->
    <table class="info-split-table">
        <tr>
            <!-- Left: Customer Details -->
            <td class="info-box" style="width: 50%;">
                <div class="info-box-header">👤 Customer & Service Location Details</div>
                <div class="info-row"><span class="info-lbl">Customer Name:</span><span class="info-val">{cust_name}</span></div>
                <div class="info-row"><span class="info-lbl">Mobile Phone:</span><span class="info-val">📞 {cust_phone}</span></div>
                {f'<div class="info-row"><span class="info-lbl">Email Address:</span><span class="info-val">{cust_email}</span></div>' if cust_email else ''}
                <div class="info-row"><span class="info-lbl">Service Site:</span><span class="info-val">📍 {cust_addr}</span></div>
                {f'<div class="info-row"><span class="info-lbl">Landmark:</span><span class="info-val">{cust_landmark}</span></div>' if cust_landmark else ''}
            </td>
            <!-- Right: Contract & Commercial Summary -->
            <td class="info-box" style="width: 50%;">
                <div class="info-box-header">📋 Coverage Specifications & Billing</div>
                <div class="info-row"><span class="info-lbl">Coverage Type:</span><span class="info-val" style="color: {type_badge_color};">{contract_type} AMC</span></div>
                <div class="info-row"><span class="info-lbl">Agreement Start:</span><span class="info-val">{start_date}</span></div>
                <div class="info-row"><span class="info-lbl">Agreement End:</span><span class="info-val">{end_date}</span></div>
                <div class="info-row"><span class="info-lbl">Primary Tech:</span><span class="info-val">{primary_tech}</span></div>
                <div class="info-row"><span class="info-lbl">Payment Status:</span><span class="info-val">{payment_status} ({payment_mode})</span></div>
            </td>
        </tr>
    </table>

    <!-- 5. Covered Air Conditioner Units Registry -->
    <div class="section-title">❄️ Covered Equipment & Air Conditioner Units Registry</div>
    <table class="data-table">
        <thead>
            <tr>
                <th style="width: 12%; text-align: center;">Unit Tag</th>
                <th style="width: 20%;">Brand</th>
                <th style="width: 15%;">AC Type</th>
                <th style="width: 12%; text-align: center;">Tonnage</th>
                <th style="width: 21%;">Serial / Model #</th>
                <th style="width: 20%;">Indoor / Site Location</th>
            </tr>
        </thead>
        <tbody>
            {units_html_rows}
        </tbody>
    </table>

    <!-- 6. Preventive Maintenance Visits Schedule -->
    <div class="section-title">📅 Preventive Maintenance Visits & Service Schedule</div>
    <table class="data-table">
        <thead>
            <tr>
                <th style="width: 12%; text-align: center;">Visit #</th>
                <th style="width: 18%; text-align: center;">Target Date</th>
                <th style="width: 22%;">Allocated Technician</th>
                <th style="width: 16%; text-align: center;">Visit Status</th>
                <th style="width: 32%;">Service Scope / Work Done</th>
            </tr>
        </thead>
        <tbody>
            {visits_html_rows}
        </tbody>
    </table>

    <!-- 7. Financial Breakdown Table -->
    <table style="width: 100%; border-collapse: separate; border-spacing: 8px 0; margin-top: 4px; margin-bottom: 10px;">
        <tr>
            <!-- Left: Scope Notes -->
            <td style="width: 55%; vertical-align: top;" class="fin-box">
                <div style="font-size: 8pt; font-weight: 800; color: #1e3a8a; text-transform: uppercase; margin-bottom: 4px;">
                    📝 Special Scope of Work & Contract Notes:
                </div>
                <div style="font-size: 8pt; color: #334155; line-height: 1.4;">
                    {notes}
                </div>
            </td>
            <!-- Right: Commercial Calculations -->
            <td style="width: 45%; vertical-align: top;" class="fin-box">
                <table style="width: 100%; font-size: 8.5pt;">
                    <tr>
                        <td style="color: #64748b;">Contract Basic Value:</td>
                        <td style="text-align: right; font-weight: 700;">₹{base_val:,.2f}</td>
                    </tr>
                    {f'''
                    <tr>
                        <td style="color: #64748b;">Applicable GST ({gst_percent:.0f}%):</td>
                        <td style="text-align: right; font-weight: 700;">₹{gst_amt:,.2f}</td>
                    </tr>
                    ''' if gst_amt > 0 else ''}
                    <tr style="border-top: 1.5px solid #cbd5e1;">
                        <td style="font-weight: 800; font-size: 9.5pt; color: #0f172a; padding-top: 4px;">Total Agreement Value:</td>
                        <td style="text-align: right; font-weight: 900; font-size: 10.5pt; color: #2563eb; padding-top: 4px;">₹{total_val:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="color: #059669; font-weight: 700;">Advance Amount Paid:</td>
                        <td style="text-align: right; font-weight: 700; color: #059669;">₹{advance_paid:,.2f}</td>
                    </tr>
                    <tr style="border-top: 1px dashed #cbd5e1;">
                        <td style="font-weight: 800;">Balance Due Amount:</td>
                        <td style="text-align: right;">{bal_badge}</td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>

    <!-- 8. Terms & Conditions -->
    <div class="terms-box">
        <b>Standard Service Agreement Terms & Warranty Policies:</b>
        <ul>
            <li><b>Preventive Services:</b> Includes high-pressure chemical/jet wash for indoor & outdoor coils, air filter sanitization, drain tray flushing, electrical wiring & capacitor terminal checks, fan blade inspection, and refrigerant operating pressure verification.</li>
            {'<li><b>Comprehensive Coverage:</b> Covers labor, periodic servicing, compressor repair/replacement, PCB servicing, indoor fan motor, outdoor fan motor, and refrigerant replenishment during the contract term. Physical damage, plastic body parts, sheet metal corrosion, and unauthorized third-party tampering are excluded.</li>' if is_comp else '<li><b>Non-Comprehensive Coverage:</b> Covers all scheduled preventive servicing visits and regular breakdown diagnostic visits. Any required spare parts, compressor replacements, or refrigerant top-ups will be charged separately at standardized company tariff rates.</li>'}
            <li><b>Response Commitment:</b> Breakdown and emergency service requests during the contract tenure will be attended to within 24 to 48 business hours from ticket registration.</li>
            <li><b>Customer Obligations:</b> The customer shall provide safe access to the equipment, appropriate electrical power supply, and running water for coil washing procedures.</li>
        </ul>
    </div>

    <!-- 9. Signatures & Stamp -->
    <table class="signatures-table">
        <tr>
            <td style="width: 45%;">
                <div class="sign-box">
                    <div style="height: 38px;"></div>
                    <div class="sign-box-title">Customer / Authorized Client Signature</div>
                    <div style="font-size: 7.5pt; color: #64748b;">(I accept the contract terms, covered AC inventory & visit schedules)</div>
                </div>
            </td>
            <td style="width: 10%;"></td>
            <td style="width: 45%;">
                <div class="sign-box">
                    <div style="height: 38px;"></div>
                    <div class="sign-box-title">For {shop_name}</div>
                    <div style="font-size: 7.5pt; color: #64748b;">(Authorized Signatory & Official Service Stamp)</div>
                </div>
            </td>
        </tr>
    </table>

    <!-- 10. Footer Note -->
    <div class="footer-note">
        This is a computer-generated Annual Maintenance Contract (AMC) Agreement & Certificate issued by {shop_name}.<br>
        For inquiries, service requests, or scheduling, contact <b>{shop_phone}</b> or email <b>{shop_email}</b>. Thank you for your trust!
    </div>

</div>
</body>
</html>"""
    return html
