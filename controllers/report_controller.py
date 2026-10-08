"""
Reports Controller - Profit/Loss, GST, Parts Usage, Team Performance & Multi-Period Analytics
Provides 100% accurate mathematical calculations, cross-linking Invoices, Daily Logs, AMC & Technicians.
"""
from datetime import datetime, date, timedelta
from calendar import monthrange
from decimal import Decimal


class ReportController:
    def __init__(self, db_connection):
        self.db = db_connection

    def _to_date_str(self, val):
        """Convert date, datetime or str to YYYY-MM-DD"""
        if isinstance(val, (datetime, date)):
            return val.strftime('%Y-%m-%d')
        return str(val)[:10]

    def get_period_analytics(self, start_date, end_date, label="Period"):
        """
        Calculate 100% accurate financial metrics for a specific date range [start_date, end_date).
        Properly separates invoice-level totals from item-level breakdowns to prevent
        cartesian multiplication bugs. Links daily logs for petrol expenses and visits.
        """
        start_str = self._to_date_str(start_date)
        end_str = self._to_date_str(end_date)

        # 1. Invoice-Level Aggregations (Single row per invoice -> NO duplication)
        inv_query = """
        SELECT
            COUNT(id) as total_invoices,
            COALESCE(SUM(total_amount), 0) as gross_revenue,
            COALESCE(SUM(advance_payment), 0) as total_collected,
            COALESCE(SUM(balance_amount), 0) as total_pending,
            COALESCE(SUM(subtotal), 0) as taxable_value,
            COALESCE(SUM(gst_amount), 0) as total_gst
        FROM invoices
        WHERE is_active = TRUE
          AND DATE(created_at) >= %s AND DATE(created_at) < %s
        """
        inv_data = self.db.execute_query(inv_query, (start_str, end_str), fetch_one=True) or {}

        # 2. Item-Level Breakdown (Services vs Parts Revenue and Parts Cost)
        items_query = """
        SELECT
            COALESCE(SUM(CASE WHEN ii.item_type = 'service' THEN ii.amount ELSE 0 END), 0) as service_revenue,
            COALESCE(SUM(CASE WHEN ii.item_type = 'part' THEN ii.amount ELSE 0 END), 0) as part_revenue,
            COALESCE(SUM(COALESCE(p.default_rate, 0) * ii.quantity), 0) as parts_cost
        FROM invoice_items ii
        JOIN invoices i ON ii.invoice_id = i.id
        LEFT JOIN parts p ON ii.part_id = p.id
        WHERE i.is_active = TRUE
          AND DATE(i.created_at) >= %s AND DATE(i.created_at) < %s
        """
        items_data = self.db.execute_query(items_query, (start_str, end_str), fetch_one=True) or {}

        # 3. Technician Commissions
        comm_query = """
        SELECT COALESCE(SUM(i.total_amount * COALESCE(t.commission_rate, 0) / 100.0), 0) as total_commission
        FROM invoices i
        JOIN technicians t ON i.technician_id = t.id
        WHERE i.is_active = TRUE
          AND DATE(i.created_at) >= %s AND DATE(i.created_at) < %s
        """
        comm_data = self.db.execute_query(comm_query, (start_str, end_str), fetch_one=True) or {}

        # 4. Daily Logs (Cross-section linking: Petrol Expense, Material Cost & Real Visits)
        dlogs_query = """
        SELECT
            COUNT(id) as daily_visits,
            COALESCE(SUM(petrol_expense), 0) as petrol_cost,
            COALESCE(SUM(material_cost), 0) as daily_material_cost,
            COALESCE(SUM(total_expense), 0) as daily_total_expense
        FROM daily_logs
        WHERE is_active = TRUE
          AND DATE(log_date) >= %s AND DATE(log_date) < %s
        """
        dlogs_data = self.db.execute_query(dlogs_query, (start_str, end_str), fetch_one=True) or {}

        # Extract values
        gross = float(inv_data.get('gross_revenue', 0) or 0)
        collected = float(inv_data.get('total_collected', 0) or 0)
        pending = float(inv_data.get('total_pending', 0) or 0)
        total_invoices = int(inv_data.get('total_invoices', 0) or 0)
        taxable_value = float(inv_data.get('taxable_value', 0) or 0)
        total_gst = float(inv_data.get('total_gst', 0) or 0)

        service_revenue = float(items_data.get('service_revenue', 0) or 0)
        part_revenue = float(items_data.get('part_revenue', 0) or 0)
        parts_cost = float(items_data.get('parts_cost', 0) or 0)

        commission = float(comm_data.get('total_commission', 0) or 0)

        daily_visits = int(dlogs_data.get('daily_visits', 0) or 0)
        petrol_cost = float(dlogs_data.get('petrol_cost', 0) or 0)

        # Total visits: Maximum of daily visits or invoices created (if jobs logged in daily log, count those)
        total_visits = max(daily_visits, total_invoices)

        # Total Expenses = parts cost + petrol expense + technician commissions
        total_expenses = parts_cost + petrol_cost + commission

        # Net Profit = gross revenue - total expenses
        net_profit = gross - total_expenses

        # Margin & Collection rates
        margin_pct = (net_profit / gross * 100.0) if gross > 0 else 0.0
        collection_pct = (collected / gross * 100.0) if gross > 0 else 0.0

        return {
            'label': label,
            'start_date': start_str,
            'end_date': end_str,
            'gross_revenue': gross,
            'service_revenue': service_revenue,
            'part_revenue': part_revenue,
            'total_invoices': total_invoices,
            'total_collected': collected,
            'total_pending': pending,
            'total_visits': total_visits,
            'parts_cost': parts_cost,
            'petrol_cost': petrol_cost,
            'commission': commission,
            'total_expenses': total_expenses,
            'net_profit': net_profit,
            'margin_pct': margin_pct,
            'collection_rate': collection_pct,
            'taxable_value': taxable_value,
            'total_gst': total_gst,
        }

    def get_monthly_profit_loss(self, year, month):
        """Get detailed profit/loss for a single month"""
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1)
        else:
            month_end = date(year, month + 1, 1)

        months_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        label = f"{months_names[month - 1]} {year}"

        data = self.get_period_analytics(month_start, month_end, label=label)
        data['month'] = month
        data['year'] = year
        return data

    def get_yearly_summary(self, year):
        """Get year-wise 12-month summary"""
        months_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        results = []
        for m in range(1, 13):
            month_start = date(year, m, 1)
            if m == 12:
                month_end = date(year + 1, 1, 1)
            else:
                month_end = date(year, m + 1, 1)

            label = f"{months_names[m - 1]} {year}"
            row = self.get_period_analytics(month_start, month_end, label=label)
            row['month'] = m
            row['year'] = year
            results.append(row)
        return results

    def get_quarterly_summary(self, year, quarter):
        """
        Get quarterly summary with months in that quarter (Q1: Jan-Mar, Q2: Apr-Jun, Q3: Jul-Sep, Q4: Oct-Dec)
        """
        months_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        quarter_months = {
            1: [1, 2, 3],
            2: [4, 5, 6],
            3: [7, 8, 9],
            4: [10, 11, 12]
        }
        target_months = quarter_months.get(quarter, [1, 2, 3])

        results = []
        for m in target_months:
            month_start = date(year, m, 1)
            if m == 12:
                month_end = date(year + 1, 1, 1)
            else:
                month_end = date(year, m + 1, 1)

            label = f"{months_names[m - 1]} {year}"
            row = self.get_period_analytics(month_start, month_end, label=label)
            row['month'] = m
            row['year'] = year
            results.append(row)
        return results

    def get_weekly_summary(self, start_date, end_date):
        """
        Break down a custom date range (e.g. This Week, Last Week, 14 Days) day-by-day.
        """
        if isinstance(start_date, str):
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        elif isinstance(start_date, datetime):
            start_dt = start_date.date()
        else:
            start_dt = start_date

        if isinstance(end_date, str):
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
        elif isinstance(end_date, datetime):
            end_dt = end_date.date()
        else:
            end_dt = end_date

        results = []
        curr = start_dt
        while curr <= end_dt:
            next_day = curr + timedelta(days=1)
            label = curr.strftime('%d %b (%a)')
            row = self.get_period_analytics(curr, next_day, label=label)
            row['date'] = curr.strftime('%Y-%m-%d')
            row['month'] = curr.month
            row['year'] = curr.year
            results.append(row)
            curr = next_day
        return results

    def get_parts_usage_combined(self, start_date, end_date):
        """Get parts usage from invoices in the selected date range"""
        start_str = self._to_date_str(start_date)
        end_str = self._to_date_str(end_date)

        q = """
            SELECT 
                p.id as part_id,
                p.part_name,
                p.category,
                SUM(ii.quantity) as qty_used,
                SUM(ii.amount) as total_revenue,
                SUM(COALESCE(p.default_rate, 0) * ii.quantity) as total_cost
            FROM invoice_items ii
            JOIN invoices i ON ii.invoice_id = i.id
            JOIN parts p ON ii.part_id = p.id
            WHERE i.is_active = TRUE AND ii.item_type = 'part'
              AND DATE(i.created_at) >= %s AND DATE(i.created_at) < %s
            GROUP BY p.id, p.part_name, p.category
            ORDER BY total_revenue DESC
            LIMIT 100
        """
        rows = self.db.execute_query(q, (start_str, end_str), fetch_all=True) or []
        result = []
        for r in rows:
            result.append({
                'part_id': r['part_id'],
                'part_name': r['part_name'],
                'category': r.get('category') or 'General',
                'qty_used': int(r['qty_used'] or 0),
                'total_cost': float(r['total_cost'] or 0),
                'total_revenue': float(r['total_revenue'] or 0)
            })
        return result

    def get_technician_performance(self, start_date, end_date):
        """Get technician performance from invoices and daily logs in selected period"""
        start_str = self._to_date_str(start_date)
        end_str = self._to_date_str(end_date)

        query = """
        SELECT
            t.id as technician_id,
            t.name as technician_name,
            t.commission_rate,
            COUNT(DISTINCT i.id) as total_invoices,
            COUNT(DISTINCT i.customer_id) as unique_customers,
            COALESCE(SUM(i.total_amount), 0) as total_payment,
            COALESCE(SUM(i.total_amount * COALESCE(t.commission_rate, 0) / 100.0), 0) as total_expense,
            COALESCE(SUM(i.total_amount - (i.total_amount * COALESCE(t.commission_rate, 0) / 100.0)), 0) as total_profit
        FROM technicians t
        LEFT JOIN invoices i ON t.id = i.technician_id
            AND i.is_active = TRUE
            AND DATE(i.created_at) >= %s AND DATE(i.created_at) < %s
        WHERE t.is_active = TRUE
        GROUP BY t.id, t.name, t.commission_rate
        ORDER BY total_payment DESC
        """
        tech_rows = self.db.execute_query(query, (start_str, end_str), fetch_all=True) or []

        # Get visits count from daily_logs for each technician
        dlogs_tech_query = """
        SELECT technician_id, COUNT(*) as visit_count
        FROM daily_logs
        WHERE is_active = TRUE
          AND DATE(log_date) >= %s AND DATE(log_date) < %s
        GROUP BY technician_id
        """
        dlogs_tech = {
            r['technician_id']: r['visit_count']
            for r in (self.db.execute_query(dlogs_tech_query, (start_str, end_str), fetch_all=True) or [])
        }

        results = []
        for r in tech_rows:
            t_id = r['technician_id']
            inv_count = int(r.get('total_invoices') or 0)
            dlog_count = dlogs_tech.get(t_id, 0)
            total_visits = max(dlog_count, inv_count)

            tot_pay = float(r.get('total_payment') or 0)
            tot_exp = float(r.get('total_expense') or 0)
            tot_pf = float(r.get('total_profit') or 0)
            avg_pf = (tot_pf / total_visits) if total_visits > 0 else 0.0

            results.append({
                'technician_name': r['technician_name'],
                'total_visits': total_visits,
                'unique_customers': int(r.get('unique_customers') or 0),
                'total_payment': tot_pay,
                'total_expense': tot_exp,
                'total_profit': tot_pf,
                'avg_profit_per_visit': avg_pf,
                'total_parts_cost': 0.0,
            })
        return results

    def get_gst_report(self, start_date, end_date):
        """
        Get GST breakdown grouped by month or period.
        Shows: Period, Invoice Count, Taxable Value, CGST (9%), SGST (9%), Total GST.
        """
        start_str = self._to_date_str(start_date)
        end_str = self._to_date_str(end_date)

        query = """
        SELECT
            strftime('%Y-%m', created_at) as month_key,
            COUNT(id) as invoice_count,
            COALESCE(SUM(subtotal), 0) as taxable_value,
            COALESCE(SUM(gst_amount), 0) as total_gst
        FROM invoices
        WHERE is_active = TRUE
          AND DATE(created_at) >= %s AND DATE(created_at) < %s
        GROUP BY strftime('%Y-%m', created_at)
        ORDER BY month_key
        """
        rows = self.db.execute_query(query, (start_str, end_str), fetch_all=True) or []
        results = []
        for r in rows:
            gst_val = float(r.get('total_gst') or 0)
            results.append({
                'month': r['month_key'],
                'invoice_count': int(r.get('invoice_count') or 0),
                'taxable_value': float(r.get('taxable_value') or 0),
                'cgst': gst_val / 2.0,
                'sgst': gst_val / 2.0,
                'total_gst': gst_val,
            })
        return results
