import os
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, numbers
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, PieChart, LineChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.series import DataPoint
from openpyxl.chart.layout import Layout, ManualLayout
from openpyxl.formatting.rule import DataBarRule, ColorScaleRule, IconSetRule


class ExcelExporter:
    """
    Enterprise Data-Analyst Grade Excel Exporter.
    Generates multi-sheet professional workbooks featuring:
      - Sheet 1: Executive Analytics Dashboard (Active tab upon opening)
        * Sleek corporate header & metadata banner
        * Clickable cross-sheet hyperlink directly to detailed records
        * Executive KPI scorecards with colored accent borders
        * Native interactive openpyxl charts (Pie, Clustered Bar/Column, Trend Line)
        * Clean formatted summary tables feeding the chart engine
      - Sheet 2: Detailed Data Ledger
        * Return navigation hyperlink to Dashboard
        * Styled dark header row with center/clean typography
        * Alternating zebra rows (soft tinted)
        * Currency, date, integer, and status pill formatting
        * Double-underline accounting total row with live Excel =SUM() formulas
        * Auto-filter enabled on all columns & frozen header row
        * Auto-fitted column widths
    """

    COMPANY = 'Cooling Point AC Services'
    TAGLINE = 'Enterprise Service & Billing Management'
    CURRENT_USER = 'Admin'

    # Typography & Themes
    FONT_FAMILY = 'Segoe UI'
    TITLE_FONT = Font(bold=True, size=13, color='FFFFFF', name=FONT_FAMILY)
    SUBTITLE_FONT = Font(size=9, color='94A3B8', name=FONT_FAMILY)
    HEADER_FONT = Font(bold=True, size=10, color='FFFFFF', name=FONT_FAMILY)
    DATA_FONT = Font(size=9.5, color='1E293B', name=FONT_FAMILY)
    TOTAL_FONT = Font(bold=True, size=10, color='0F172A', name=FONT_FAMILY)
    KPI_VALUE_FONT = Font(bold=True, size=15, color='0F172A', name=FONT_FAMILY)
    KPI_LABEL_FONT = Font(bold=True, size=8.5, color='64748B', name=FONT_FAMILY)

    # Color Fills
    BANNER_FILL = PatternFill('solid', fgColor='0F172A')       # Slate 900
    SUB_BANNER_FILL = PatternFill('solid', fgColor='1E293B')   # Slate 800
    HEADER_FILL = PatternFill('solid', fgColor='0F172A')       # Dark Slate Header
    ALT_FILL = PatternFill('solid', fgColor='F8FAFC')          # Ultra soft grey
    WHITE_FILL = PatternFill('solid', fgColor='FFFFFF')
    TOTAL_FILL = PatternFill('solid', fgColor='EFF6FF')        # Soft Blue Total
    NAV_FILL = PatternFill('solid', fgColor='EEF2FF')          # Soft Indigo Link
    
    # Status Pill Fills & Fonts
    PAID_FILL = PatternFill('solid', fgColor='DCFCE7')         # Emerald 100
    PAID_FONT = Font(bold=True, size=9, color='15803D', name=FONT_FAMILY)
    PENDING_FILL = PatternFill('solid', fgColor='FEE2E2')      # Rose 100
    PENDING_FONT = Font(bold=True, size=9, color='B91C1C', name=FONT_FAMILY)
    PARTIAL_FILL = PatternFill('solid', fgColor='FEF3C7')      # Amber 100
    PARTIAL_FONT = Font(bold=True, size=9, color='B45309', name=FONT_FAMILY)

    # Alignments
    HEADER_ALIGN = Alignment(horizontal='center', vertical='center', wrap_text=True)
    LEFT_ALIGN = Alignment(horizontal='left', vertical='center')
    RIGHT_ALIGN = Alignment(horizontal='right', vertical='center')
    CENTER_ALIGN = Alignment(horizontal='center', vertical='center')

    # Borders
    THIN_BORDER = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0'),
    )
    TOTAL_BORDER = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='double', color='0F172A'),
    )

    # Formats
    CURRENCY_FMT = '₹#,##0.00'
    NUMBER_FMT = '#,##0'
    DATE_FMT = 'DD-MMM-YYYY'
    DATE_FMT_SHORT = 'DD-MM-YYYY'
    PERCENT_FMT = '0.0%'

    CHART_COLORS = ['2563EB', '059669', 'D97706', 'DC2626', '7C3AED', '0891B2',
                    '0F766E', '1D4ED8', '9333EA', 'EA580C']
    KPI_ACCENT_COLORS = ['2563EB', '059669', 'D97706', 'DC2626', '7C3AED', '0891B2']

    @classmethod
    def get_company_info(cls):
        """Retrieve dynamic company branding from database/settings if available"""
        try:
            from utils.app_settings import get_setting
            c_name = get_setting('company_name', cls.COMPANY) or cls.COMPANY
            c_tag = get_setting('company_tagline', cls.TAGLINE) or cls.TAGLINE
            c_curr = get_setting('currency_symbol', '₹') or '₹'
            return c_name, c_tag, c_curr
        except Exception:
            return cls.COMPANY, cls.TAGLINE, '₹'

    @classmethod
    def new_workbook(cls, sheet_title='Report'):
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_title[:31]
        ws.sheet_properties.tabColor = '0891B2'
        cls._setup_page(ws)
        return wb, ws

    @classmethod
    def _setup_page(cls, ws):
        try:
            ws.page_setup.orientation = 'landscape'
            ws.page_setup.paperSize = ws.PAPERSIZE_A4
            ws.page_setup.fitToWidth = 1
            ws.page_setup.fitToHeight = 0
            ws.page_margins.left = 0.5
            ws.page_margins.right = 0.5
            ws.page_margins.top = 0.6
            ws.page_margins.bottom = 0.6
            ws.oddHeader.center.text = f'{cls.COMPANY} | Report'
            ws.oddHeader.center.font = 'Segoe UI,8'
            ws.oddFooter.left.text = f'Generated by: {cls.CURRENT_USER}'
            ws.oddFooter.left.font = 'Segoe UI,7'
            ws.oddFooter.center.text = 'Page &P of &N'
            ws.oddFooter.center.font = 'Segoe UI,7'
            ws.oddFooter.right.text = '&D &T'
            ws.oddFooter.right.font = 'Segoe UI,7'
        except Exception:
            pass

    @classmethod
    def write_brand_header(cls, ws, max_col=8, row=1):
        c_name, c_tag, _ = cls.get_company_info()
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=max_col)
        cell = ws.cell(row=row, column=1, value=f'{c_name} - {c_tag}')
        cell.font = Font(bold=True, size=14, color='0F172A', name=cls.FONT_FAMILY)
        cell.alignment = Alignment(horizontal='left', vertical='center')
        ws.row_dimensions[row].height = 28
        r = row + 1
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=max_col)
        cell = ws.cell(row=r, column=1, value='')
        ws.row_dimensions[r].height = 4
        return r + 1

    @classmethod
    def write_title(cls, ws, title, subtitle=None, max_col=8, row=1):
        cls.write_brand_header(ws, max_col, row)
        r = row + 2
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=max_col)
        cell = ws.cell(row=r, column=1, value=title)
        cell.font = Font(bold=True, size=13, color='0891B2', name=cls.FONT_FAMILY)
        cell.alignment = Alignment(horizontal='left', vertical='center')
        ws.row_dimensions[r].height = 28
        r += 1
        if subtitle:
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=max_col)
            cell = ws.cell(row=r, column=1, value=subtitle)
            cell.font = cls.SUBTITLE_FONT
            cell.alignment = Alignment(horizontal='left', vertical='center')
            ws.row_dimensions[r].height = 18
            r += 1
        return r

    @classmethod
    def write_headers(cls, ws, headers, row=1):
        ws.row_dimensions[row].height = 28
        for c, h in enumerate(headers, 1):
            cell = ws.cell(row=row, column=c, value=h)
            cell.font = cls.HEADER_FONT
            cell.fill = cls.HEADER_FILL
            cell.alignment = cls.HEADER_ALIGN
            cell.border = cls.THIN_BORDER

    @classmethod
    def write_rows(cls, ws, data, start_row=2, number_cols=None, cond_rules=None,
                   col_formats=None, subtotal_rows=None):
        row_count = 0
        _, _, curr_sym = cls.get_company_info()
        curr_fmt = f'{curr_sym}#,##0.00'

        for i, row_data in enumerate(data):
            row_count = i + 1
            r = start_row + i
            ws.row_dimensions[r].height = 22
            is_subtotal = subtotal_rows and i in subtotal_rows
            is_alt = (i % 2 == 1)
            row_fill = cls.ALT_FILL if is_alt else cls.WHITE_FILL

            for c, value in enumerate(row_data, 1):
                cell = ws.cell(row=r, column=c, value=value)
                cell.border = cls.THIN_BORDER
                cell.font = cls.DATA_FONT
                cell.fill = row_fill

                # Formatting
                if col_formats and c in col_formats and isinstance(value, (int, float)):
                    cell.number_format = col_formats[c]
                    cell.alignment = cls.RIGHT_ALIGN
                elif number_cols and c in number_cols and isinstance(value, (int, float)):
                    cell.number_format = curr_fmt
                    cell.alignment = cls.RIGHT_ALIGN
                elif isinstance(value, float):
                    cell.number_format = curr_fmt
                    cell.alignment = cls.RIGHT_ALIGN
                elif isinstance(value, int) and not isinstance(value, bool) and abs(value) > 999:
                    cell.number_format = cls.NUMBER_FMT
                    cell.alignment = cls.RIGHT_ALIGN
                elif isinstance(value, datetime):
                    cell.number_format = cls.DATE_FMT
                    cell.alignment = cls.CENTER_ALIGN
                elif isinstance(value, str):
                    sval = value.strip().lower()
                    if sval in ('paid', 'active', 'completed', 'converted', 'ok'):
                        cell.fill = cls.PAID_FILL
                        cell.font = cls.PAID_FONT
                        cell.alignment = cls.CENTER_ALIGN
                    elif sval in ('pending', 'unpaid', 'overdue', 'expired', 'low stock', 'critical'):
                        cell.fill = cls.PENDING_FILL
                        cell.font = cls.PENDING_FONT
                        cell.alignment = cls.CENTER_ALIGN
                    elif sval in ('partial', 'in progress', 'contacted', 'read'):
                        cell.fill = cls.PARTIAL_FILL
                        cell.font = cls.PARTIAL_FONT
                        cell.alignment = cls.CENTER_ALIGN
                    else:
                        cell.alignment = cls.LEFT_ALIGN
                else:
                    cell.alignment = cls.LEFT_ALIGN

            # Custom cond_rules override if passed
            if cond_rules and not is_subtotal:
                for col_idx, rule in cond_rules:
                    if col_idx <= len(row_data):
                        cell = ws.cell(row=r, column=col_idx)
                        val = row_data[col_idx - 1]
                        sval = str(val).strip().lower()
                        if rule == 'paid' and sval in ('paid', 'active', 'completed', 'converted', 'ok'):
                            cell.fill = cls.PAID_FILL
                            cell.font = cls.PAID_FONT
                        elif rule == 'pending' and sval in ('pending', 'unpaid', 'expired', 'unread', 'low stock'):
                            cell.fill = cls.PENDING_FILL
                            cell.font = cls.PENDING_FONT
                        elif rule == 'partial' and sval in ('partial', 'read', 'contacted', 'in progress'):
                            cell.fill = cls.PARTIAL_FILL
                            cell.font = cls.PARTIAL_FONT

        return row_count

    @classmethod
    def write_total_row(cls, ws, data, row, number_cols=None, col_formats=None):
        ws.row_dimensions[row].height = 26
        _, _, curr_sym = cls.get_company_info()
        curr_fmt = f'{curr_sym}#,##0.00'

        for c, value in enumerate(data, 1):
            cell = ws.cell(row=row, column=c, value=value)
            cell.font = cls.TOTAL_FONT
            cell.fill = cls.TOTAL_FILL
            cell.border = cls.TOTAL_BORDER
            if col_formats and c in col_formats and isinstance(value, (int, float)):
                cell.number_format = col_formats[c]
                cell.alignment = cls.RIGHT_ALIGN
            elif number_cols and c in number_cols:
                cell.number_format = curr_fmt
                cell.alignment = cls.RIGHT_ALIGN
            elif isinstance(value, float):
                cell.number_format = curr_fmt
                cell.alignment = cls.RIGHT_ALIGN
            else:
                cell.alignment = cls.LEFT_ALIGN

    @classmethod
    def auto_width(cls, ws, headers, min_width=12, max_width=45):
        for c in range(1, len(headers) + 1):
            col_letter = get_column_letter(c)
            max_len = len(str(headers[c - 1] or ''))
            for row_cells in ws.iter_rows(min_col=c, max_col=c, min_row=2, values_only=True):
                val = row_cells[0]
                if val is not None:
                    max_len = max(max_len, len(str(val)))
            width = min(max(max_len + 4, min_width), max_width)
            ws.column_dimensions[col_letter].width = width

    @classmethod
    def freeze_and_filter(cls, ws, headers, header_row=1, freeze_col=False):
        if ws.max_row > header_row:
            if freeze_col:
                ws.freeze_panes = ws.cell(row=header_row + 1, column=2).coordinate
            else:
                ws.freeze_panes = ws.cell(row=header_row + 1, column=1).coordinate
        last_col = get_column_letter(len(headers))
        ws.auto_filter.ref = f'A{header_row}:{last_col}{max(header_row, ws.max_row)}'

    @classmethod
    def _apply_chart_style(cls, chart, chart_type, num_series, num_data_points=0):
        chart.style = 10
        colors = cls.CHART_COLORS
        if chart_type == 'pie':
            if chart.series:
                for si, ser in enumerate(chart.series):
                    for pt_idx in range(num_data_points):
                        pt = DataPoint(idx=pt_idx)
                        pt.graphicalProperties.solidFill = colors[pt_idx % len(colors)]
                        ser.data_points.append(pt)
            if chart.dataLabels:
                chart.dataLabels.showVal = True
                chart.dataLabels.showPercent = True
                chart.dataLabels.showCatName = True
                chart.dataLabels.separator = ' - '
        elif chart_type in ('bar', 'col'):
            if chart.series:
                for si, ser in enumerate(chart.series):
                    color = colors[si % len(colors)]
                    ser.graphicalProperties.solidFill = color
            if chart.dataLabels:
                chart.dataLabels.showVal = True
        elif chart_type == 'line':
            if chart.series:
                for si, ser in enumerate(chart.series):
                    color = colors[si % len(colors)]
                    ser.graphicalProperties.solidFill = color
                    ser.graphicalProperties.line.solidFill = color
                    ser.marker.symbol = 'circle'
                    ser.marker.size = 5

    @classmethod
    def add_charts_sheet(cls, wb, title, charts_data):
        ws = wb.create_sheet(title='Charts')
        ws.sheet_properties.tabColor = '7C3AED'
        cls._setup_page(ws)
        cls.write_brand_header(ws, max_col=6)
        r = 4
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
        c = ws.cell(row=r, column=1, value='VISUAL ANALYTICS')
        c.font = Font(bold=True, size=13, color='7C3AED', name=cls.FONT_FAMILY)
        ws.row_dimensions[r].height = 28
        r += 1
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
        gen = ws.cell(row=r, column=1, value=f'{len(charts_data)} chart(s) | Generated: {datetime.now().strftime("%d-%m-%Y %H:%M")}')
        gen.font = cls.SUBTITLE_FONT
        ws.row_dimensions[r].height = 18

        ref_row = r + 2
        for ci, ch in enumerate(charts_data):
            ctype = ch.get('type', 'bar')
            chart_title = ch.get('title', 'Chart')
            categories = ch.get('categories', [])
            values_series = ch.get('values', [])
            if not categories or not values_series:
                continue

            data_start_row = ref_row
            header_fill = PatternFill('solid', fgColor='F1F5F9')
            hcell = ws.cell(row=data_start_row, column=1, value=chart_title)
            hcell.font = Font(bold=True, size=11, color='1E293B', name=cls.FONT_FAMILY)
            hcell.fill = header_fill
            ws.merge_cells(start_row=data_start_row, start_column=1,
                           end_row=data_start_row, end_column=1 + len(values_series))
            ws.row_dimensions[data_start_row].height = 24
            data_start_row += 1

            ws.cell(row=data_start_row, column=1, value='Category').font = Font(bold=True, size=9, color='475569')
            for si, (sname, _) in enumerate(values_series):
                sc = ws.cell(row=data_start_row, column=2 + si, value=sname)
                sc.font = Font(bold=True, size=9, color=cls.CHART_COLORS[si % len(cls.CHART_COLORS)])
            data_start_row += 1

            for ci_idx, cat in enumerate(categories):
                ws.cell(row=data_start_row + ci_idx, column=1, value=cat).font = Font(size=9, color='64748B')
                for si, (_, svals) in enumerate(values_series):
                    val = svals[ci_idx] if ci_idx < len(svals) else 0
                    vc = ws.cell(row=data_start_row + ci_idx, column=2 + si, value=val)
                    vc.font = Font(size=9, color='1E293B')

            data_end_row = data_start_row + len(categories) - 1

            if ctype == 'pie':
                chart = PieChart()
                chart.title = chart_title
                labels = Reference(ws, min_col=1, min_row=data_start_row, max_row=data_end_row)
                data_ref = Reference(ws, min_col=2, min_row=data_start_row - 1, max_row=data_end_row)
                chart.add_data(data_ref, titles_from_data=True)
                chart.set_categories(labels)
                chart.dataLabels = DataLabelList()
                cls._apply_chart_style(chart, 'pie', len(values_series), num_data_points=len(categories))
            elif ctype == 'line':
                chart = LineChart()
                chart.title = chart_title
                chart.y_axis.title = ch.get('y_axis', '')
                chart.x_axis.title = ch.get('x_axis', '')
                labels = Reference(ws, min_col=1, min_row=data_start_row, max_row=data_end_row)
                for si in range(len(values_series)):
                    data_ref = Reference(ws, min_col=2 + si, min_row=data_start_row - 1, max_row=data_end_row)
                    chart.add_data(data_ref, titles_from_data=True)
                chart.set_categories(labels)
                chart.dataLabels = DataLabelList()
                cls._apply_chart_style(chart, 'line', len(values_series))
            else:
                chart = BarChart()
                chart.type = 'col'
                chart.grouping = 'clustered'
                chart.title = chart_title
                chart.y_axis.title = ch.get('y_axis', '')
                chart.x_axis.title = ch.get('x_axis', '')
                labels = Reference(ws, min_col=1, min_row=data_start_row, max_row=data_end_row)
                for si in range(len(values_series)):
                    data_ref = Reference(ws, min_col=2 + si, min_row=data_start_row - 1, max_row=data_end_row)
                    chart.add_data(data_ref, titles_from_data=True)
                chart.set_categories(labels)
                chart.dataLabels = DataLabelList()
                cls._apply_chart_style(chart, 'bar', len(values_series))

            chart.width = 20
            chart.height = 13
            chart.legend.position = 'b'
            ws.add_chart(chart, f'A{data_end_row + 3}')
            ref_row = data_end_row + 3 + 20

        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 15
        return ws

    @classmethod
    def add_summary_sheet(cls, wb, title, kpis, max_col=6, charts_data=None):
        ws2 = wb.create_sheet(title='Dashboard')
        ws2.sheet_properties.tabColor = '059669'
        cls._setup_page(ws2)
        cls.write_brand_header(ws2, max_col)
        r = 4
        ws2.merge_cells(start_row=r, start_column=1, end_row=r, end_column=max_col)
        c = ws2.cell(row=r, column=1, value='KEY PERFORMANCE INDICATORS')
        c.font = Font(bold=True, size=14, color='059669', name=cls.FONT_FAMILY)
        ws2.row_dimensions[r].height = 30
        return ws2

    @classmethod
    def _auto_detect_kpis_and_charts(cls, headers, rows, number_cols=None):
        """Auto-detect KPI metrics and charts from raw data if caller didn't supply them"""
        kpis = [('Total Records', len(rows))]
        status_counts = {}
        col_sums = {}
        num_indices = set(number_cols or [])

        for r in rows:
            for c_idx, val in enumerate(r):
                # Number check
                if c_idx + 1 in num_indices or isinstance(val, (int, float)) and not isinstance(val, bool):
                    try:
                        col_sums[c_idx] = col_sums.get(c_idx, 0.0) + float(val)
                    except (ValueError, TypeError):
                        pass
                elif isinstance(val, str):
                    sval = val.strip()
                    if sval.lower() in ('paid', 'pending', 'partial', 'active', 'inactive', 'completed', 'ok', 'low stock', 'unpaid', 'overdue'):
                        cap = sval.capitalize()
                        status_counts[cap] = status_counts.get(cap, 0) + 1

        # Add top numeric sums to KPIs
        for c_idx, tot in col_sums.items():
            if c_idx < len(headers):
                h_name = headers[c_idx]
                if not any(ign in h_name.lower() for ign in ('id', 'mobile', 'phone', 'pin', 'code')):
                    kpis.append((h_name, tot))

        # Build charts
        charts_data = []
        if status_counts:
            charts_data.append({
                'type': 'pie',
                'title': 'Status Distribution Breakdown',
                'categories': list(status_counts.keys()),
                'values': [('Count', list(status_counts.values()))]
            })

        if col_sums:
            metric_headers = []
            metric_values = []
            for c_idx, tot in col_sums.items():
                if c_idx < len(headers):
                    h_name = headers[c_idx]
                    if not any(ign in h_name.lower() for ign in ('id', 'mobile', 'phone', 'pin', 'code', 'rate')):
                        metric_headers.append(h_name)
                        metric_values.append(tot)
            if metric_headers:
                charts_data.append({
                    'type': 'bar',
                    'title': 'Financial & Metric Aggregates',
                    'categories': metric_headers[:5],
                    'values': [('Aggregate', metric_values[:5])],
                    'y_axis': 'Value'
                })

        return kpis[:6], charts_data

    @classmethod
    def build_excel(cls, sheet_title, title_text, subtitle_text, headers, rows,
                    total_row=None, number_cols=None, kpis=None, cond_rules=None,
                    col_formats=None, charts_data=None, freeze_col=False,
                    subtotal_rows=None):
        """
        Builds a Senior Data-Analyst Grade multi-sheet workbook.
        Sheet 1: 'Executive Dashboard' with KPI scorecards, interactive charts & links.
        Sheet 2: 'Data Records' (or sheet_title) with formatted tables, =SUM() formulas & pills.
        """
        col_count = len(headers)
        if isinstance(rows, (list, tuple)):
            for i, row in enumerate(rows):
                if len(row) != col_count:
                    raise ValueError(f"Row {i} has {len(row)} columns, expected {col_count}")
        if total_row and len(total_row) != col_count:
            raise ValueError(f"Total row has {len(total_row)} columns, expected {col_count}")

        comp_name, comp_tag, curr_sym = cls.get_company_info()
        curr_fmt = f'{curr_sym}#,##0.00'

        # Auto-detect KPIs and charts if not provided
        if not kpis or not charts_data:
            auto_kpis, auto_charts = cls._auto_detect_kpis_and_charts(headers, rows, number_cols)
            if not kpis:
                kpis = auto_kpis
            if not charts_data:
                charts_data = auto_charts

        wb = Workbook()

        # ════════════════════════════════════════════════════════════
        # 1. SHEET 1: EXECUTIVE DASHBOARD (Active View)
        # ════════════════════════════════════════════════════════════
        ws_dash = wb.active
        ws_dash.title = "Executive Dashboard"
        ws_dash.sheet_properties.tabColor = "0D9488" # Teal / Emerald
        ws_dash.views.sheetView[0].showGridLines = True

        # Determine detailed sheet title (avoid collision with Executive Dashboard)
        data_sheet_title = "Data Records" if sheet_title in ("Executive Dashboard", "Dashboard", "Report") else sheet_title[:31]

        # Top Executive Banner
        ws_dash.merge_cells("A1:L2")
        b1 = ws_dash["A1"]
        b1.value = f"{comp_name.upper()}  |  EXECUTIVE ANALYTICS DASHBOARD"
        b1.font = Font(name=cls.FONT_FAMILY, size=13, bold=True, color="FFFFFF")
        b1.fill = cls.BANNER_FILL
        b1.alignment = Alignment(horizontal="center", vertical="center")
        ws_dash.row_dimensions[1].height = 22
        ws_dash.row_dimensions[2].height = 22

        now_str = datetime.now().strftime("%d-%b-%Y %H:%M")
        ws_dash.merge_cells("A3:L3")
        b2 = ws_dash["A3"]
        b2.value = f"{title_text}  •  Generated: {now_str}  •  Prepared by: {cls.CURRENT_USER}"
        b2.font = Font(name=cls.FONT_FAMILY, size=9, color="94A3B8")
        b2.fill = cls.SUB_BANNER_FILL
        b2.alignment = Alignment(horizontal="center", vertical="center")
        ws_dash.row_dimensions[3].height = 20

        # Clickable Hyperlink Navigation to Sheet 2
        ws_dash.merge_cells("A5:L5")
        nav_cell = ws_dash["A5"]
        nav_cell.value = f"👉 Click to View Full Detailed Records (Sheet: '{data_sheet_title}') →"
        nav_cell.hyperlink = f"#'{data_sheet_title}'!A1"
        nav_cell.font = Font(name=cls.FONT_FAMILY, size=10, bold=True, color="2563EB", underline="single")
        nav_cell.fill = cls.NAV_FILL
        nav_cell.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        ws_dash.row_dimensions[5].height = 24

        # KPI Scorecards Strip (Rows 7-9)
        kpi_cols = [("A", "B"), ("C", "D"), ("E", "F"), ("G", "H"), ("I", "J"), ("K", "L")]
        if kpis:
            for idx, (label, val) in enumerate(kpis[:6]):
                c_start, c_end = kpi_cols[idx]
                color = cls.KPI_ACCENT_COLORS[idx % len(cls.KPI_ACCENT_COLORS)]

                # Label (Row 7)
                ws_dash.merge_cells(f"{c_start}7:{c_end}7")
                top_c = ws_dash[f"{c_start}7"]
                top_c.value = str(label).upper()
                top_c.font = Font(name=cls.FONT_FAMILY, size=8.5, bold=True, color="64748B")
                top_c.fill = cls.ALT_FILL
                top_c.alignment = Alignment(horizontal="center", vertical="center")

                # Value (Row 8)
                ws_dash.merge_cells(f"{c_start}8:{c_end}8")
                mid_c = ws_dash[f"{c_start}8"]
                mid_c.value = val
                mid_c.font = Font(name=cls.FONT_FAMILY, size=15, bold=True, color=color)
                mid_c.fill = cls.ALT_FILL
                mid_c.alignment = Alignment(horizontal="center", vertical="center")

                if isinstance(val, float):
                    mid_c.number_format = curr_fmt
                elif isinstance(val, int) and not isinstance(val, bool):
                    mid_c.number_format = cls.NUMBER_FMT
                elif isinstance(val, str) and '%' in val:
                    try:
                        p_val = float(val.replace('%', '').strip()) / 100.0
                        mid_c.value = p_val
                        mid_c.number_format = cls.PERCENT_FMT
                    except ValueError:
                        pass

                # Subtext (Row 9)
                ws_dash.merge_cells(f"{c_start}9:{c_end}9")
                bot_c = ws_dash[f"{c_start}9"]
                bot_c.value = "Verified Metric"
                bot_c.font = Font(name=cls.FONT_FAMILY, size=7.5, color="94A3B8")
                bot_c.fill = cls.ALT_FILL
                bot_c.alignment = Alignment(horizontal="center", vertical="center")

                # Accent top border & clean bounding boxes
                accent_top = Side(style="medium", color=color)
                thin_side = Side(style="thin", color="E2E8F0")
                for r in range(7, 10):
                    for c_letter in (c_start, c_end):
                        cell = ws_dash[f"{c_letter}{r}"]
                        cell.border = Border(
                            left=thin_side, right=thin_side,
                            top=accent_top if r == 7 else thin_side,
                            bottom=thin_side
                        )

            ws_dash.row_dimensions[7].height = 19
            ws_dash.row_dimensions[8].height = 30
            ws_dash.row_dimensions[9].height = 17

        # Section Header for Visual Analytics
        ws_dash.merge_cells("A11:L11")
        s_title = ws_dash["A11"]
        s_title.value = "📊 EXECUTIVE INTERACTIVE CHARTS & VISUAL ANALYTICS"
        s_title.font = Font(name=cls.FONT_FAMILY, size=11, bold=True, color="0F172A")
        s_title.alignment = Alignment(horizontal="left", vertical="center")
        ws_dash.row_dimensions[11].height = 26

        # Reference Tables & Native Charts on Dashboard
        ref_table_col_offset = 1
        charts_to_render = []

        if charts_data:
            for ch_idx, ch in enumerate(charts_data[:3]):
                ctype = ch.get('type', 'bar')
                chart_title = ch.get('title', 'Metric Chart')
                categories = ch.get('categories', [])
                values_series = ch.get('values', [])
                if not categories or not values_series:
                    continue

                col_start = ref_table_col_offset
                col_end = col_start + len(values_series)
                
                # Table header
                h_cell = ws_dash.cell(row=13, column=col_start, value="Category")
                h_cell.font = Font(name=cls.FONT_FAMILY, size=9, bold=True, color="FFFFFF")
                h_cell.fill = PatternFill("solid", fgColor="1E293B")
                h_cell.alignment = Alignment(horizontal="left", vertical="center")

                for s_i, (s_name, _) in enumerate(values_series):
                    sc_cell = ws_dash.cell(row=13, column=col_start + 1 + s_i, value=s_name)
                    sc_cell.font = Font(name=cls.FONT_FAMILY, size=9, bold=True, color="FFFFFF")
                    sc_cell.fill = PatternFill("solid", fgColor="1E293B")
                    sc_cell.alignment = Alignment(horizontal="right", vertical="center")

                # Table rows
                for cat_i, cat in enumerate(categories):
                    r_num = 14 + cat_i
                    c_cell = ws_dash.cell(row=r_num, column=col_start, value=str(cat))
                    c_cell.font = Font(name=cls.FONT_FAMILY, size=9, color="334155")
                    c_cell.alignment = Alignment(horizontal="left", vertical="center")
                    for s_i, (_, s_vals) in enumerate(values_series):
                        val = s_vals[cat_i] if cat_i < len(s_vals) else 0
                        v_cell = ws_dash.cell(row=r_num, column=col_start + 1 + s_i, value=val)
                        v_cell.font = Font(name=cls.FONT_FAMILY, size=9, bold=True, color="0F172A")
                        v_cell.alignment = Alignment(horizontal="right", vertical="center")
                        if isinstance(val, float):
                            v_cell.number_format = curr_fmt

                charts_to_render.append({
                    'type': ctype,
                    'title': chart_title,
                    'y_axis': ch.get('y_axis', ''),
                    'x_axis': ch.get('x_axis', ''),
                    'min_row': 14,
                    'max_row': 13 + len(categories),
                    'cat_col': col_start,
                    'val_col_start': col_start + 1,
                    'val_col_end': col_end,
                    'series_count': len(values_series),
                    'point_count': len(categories),
                })
                ref_table_col_offset += len(values_series) + 2

        # Create Openpyxl Charts
        chart_positions = ["A19", "G19", "A34", "G34"]
        for idx, ch_info in enumerate(charts_to_render[:4]):
            ctype = ch_info['type']
            pos = chart_positions[idx]
            
            if ctype == 'pie':
                pie = PieChart()
                pie.title = ch_info['title']
                labels = Reference(ws_dash, min_col=ch_info['cat_col'], min_row=ch_info['min_row'], max_row=ch_info['max_row'])
                data = Reference(ws_dash, min_col=ch_info['val_col_start'], min_row=ch_info['min_row'] - 1, max_row=ch_info['max_row'])
                pie.add_data(data, titles_from_data=True)
                pie.set_categories(labels)
                pie.width = 16
                pie.height = 12
                pie.dataLabels = DataLabelList()
                pie.dataLabels.showPercent = True
                pie.dataLabels.showVal = True
                pie.dataLabels.separator = ' - '
                cls._apply_chart_style(pie, 'pie', ch_info['series_count'], ch_info['point_count'])
                ws_dash.add_chart(pie, pos)

            elif ctype == 'line':
                line = LineChart()
                line.title = ch_info['title']
                line.y_axis.title = ch_info['y_axis']
                line.x_axis.title = ch_info['x_axis']
                labels = Reference(ws_dash, min_col=ch_info['cat_col'], min_row=ch_info['min_row'], max_row=ch_info['max_row'])
                for s_idx in range(ch_info['series_count']):
                    val_col = ch_info['val_col_start'] + s_idx
                    data = Reference(ws_dash, min_col=val_col, min_row=ch_info['min_row'] - 1, max_row=ch_info['max_row'])
                    line.add_data(data, titles_from_data=True)
                line.set_categories(labels)
                line.width = 18
                line.height = 12
                line.dataLabels = DataLabelList()
                line.dataLabels.showVal = True
                cls._apply_chart_style(line, 'line', ch_info['series_count'])
                ws_dash.add_chart(line, pos)

            else: # bar / column
                bar = BarChart()
                bar.type = "col"
                bar.grouping = "clustered"
                bar.title = ch_info['title']
                bar.y_axis.title = ch_info['y_axis']
                labels = Reference(ws_dash, min_col=ch_info['cat_col'], min_row=ch_info['min_row'], max_row=ch_info['max_row'])
                for s_idx in range(ch_info['series_count']):
                    val_col = ch_info['val_col_start'] + s_idx
                    data = Reference(ws_dash, min_col=val_col, min_row=ch_info['min_row'] - 1, max_row=ch_info['max_row'])
                    bar.add_data(data, titles_from_data=True)
                bar.set_categories(labels)
                bar.width = 18
                bar.height = 12
                bar.dataLabels = DataLabelList()
                bar.dataLabels.showVal = True
                if ch_info['series_count'] == 1:
                    bar.legend = None
                cls._apply_chart_style(bar, 'col', ch_info['series_count'])
                ws_dash.add_chart(bar, pos)

        # Dashboard column widths
        for c in range(1, 14):
            ws_dash.column_dimensions[get_column_letter(c)].width = 14

        # ════════════════════════════════════════════════════════════
        # 2. SHEET 2: DETAILED DATA LEDGER
        # ════════════════════════════════════════════════════════════
        ws_data = wb.create_sheet(title=data_sheet_title)
        ws_data.sheet_properties.tabColor = "2563EB" # Sapphire Blue
        ws_data.views.sheetView[0].showGridLines = True
        cls._setup_page(ws_data)

        # Back Navigation Link
        ws_data["A1"] = "📊 ← Return to Executive Dashboard"
        ws_data["A1"].hyperlink = "#'Executive Dashboard'!A1"
        ws_data["A1"].font = Font(name=cls.FONT_FAMILY, size=10, bold=True, color="2563EB", underline="single")
        ws_data["A1"].fill = PatternFill("solid", fgColor="EFF6FF")
        ws_data.row_dimensions[1].height = 24

        # Table Header Banner
        ws_data["A2"] = f"{title_text.upper()}  •  DETAILED DATA LEDGER"
        ws_data["A2"].font = Font(name=cls.FONT_FAMILY, size=11, bold=True, color="0F172A")
        ws_data.row_dimensions[2].height = 20

        # Column Headers (Row 4)
        header_row = 4
        cls.write_headers(ws_data, headers, row=header_row)

        # Data Rows (Row 5 to N)
        data_start_row = header_row + 1
        num_cols_set = set(number_cols or [])
        written_count = cls.write_rows(
            ws_data, rows, start_row=data_start_row,
            number_cols=num_cols_set, cond_rules=cond_rules,
            col_formats=col_formats, subtotal_rows=subtotal_rows
        )

        # Grand Total Row with Real Excel =SUM() Formulas
        total_row_idx = data_start_row + written_count
        ws_data.row_dimensions[total_row_idx].height = 26

        # Auto detect numeric columns if not supplied
        if not num_cols_set and rows:
            for c_idx in range(len(headers)):
                vals = [r[c_idx] for r in rows if r[c_idx] is not None]
                if vals and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in vals):
                    num_cols_set.add(c_idx + 1)

        for col_idx in range(1, len(headers) + 1):
            cell = ws_data.cell(row=total_row_idx, column=col_idx)
            cell.fill = cls.TOTAL_FILL
            cell.border = cls.TOTAL_BORDER

            if col_idx == 1:
                lbl = total_row[0] if (total_row and total_row[0]) else "GRAND TOTAL"
                cell.value = str(lbl).upper()
                cell.font = cls.TOTAL_FONT
                cell.alignment = Alignment(horizontal="left", vertical="center")
            elif col_idx in num_cols_set:
                col_letter = get_column_letter(col_idx)
                if written_count > 0:
                    cell.value = f"=SUM({col_letter}{data_start_row}:{col_letter}{total_row_idx - 1})"
                else:
                    cell.value = 0
                cell.font = cls.TOTAL_FONT
                cell.number_format = curr_fmt
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                # If total_row had a custom value here, use it
                if total_row and col_idx - 1 < len(total_row) and total_row[col_idx - 1]:
                    val = total_row[col_idx - 1]
                    cell.value = val
                    cell.font = cls.TOTAL_FONT
                    cell.alignment = Alignment(horizontal="right" if isinstance(val, (int, float)) else "center", vertical="center")
                else:
                    cell.value = ""

        # Auto width & Freeze panes
        cls.auto_width(ws_data, headers)
        cls.freeze_and_filter(ws_data, headers, header_row=header_row, freeze_col=freeze_col)

        # Set Executive Dashboard as Active Tab
        wb.active = 0
        return wb

    @classmethod
    def build_excel_streaming(cls, sheet_title, title_text, subtitle_text, headers, row_generator,
                              total_row=None, number_cols=None, kpis=None, cond_rules=None,
                              col_formats=None, charts_data=None, freeze_col=False):
        # Convert generator to list for full analytical processing
        rows = list(row_generator) if not isinstance(row_generator, (list, tuple)) else row_generator
        return cls.build_excel(
            sheet_title, title_text, subtitle_text, headers, rows,
            total_row=total_row, number_cols=number_cols, kpis=kpis,
            cond_rules=cond_rules, col_formats=col_formats, charts_data=charts_data,
            freeze_col=freeze_col, subtotal_rows=None
        )
