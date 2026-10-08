"""
Daily Log Controller - Manages Daily Work, Cost & Technician Expense Tracking
Matches Excel Register Structure with Auto Calculations and Month-End Reconciliation
"""
from datetime import datetime, timedelta, date
from decimal import Decimal
import os


class DailyLogController:
    def __init__(self, db_connection):
        self.db = db_connection

    def add_log(self, data: dict) -> int:
        """Add a new daily work & cost log entry with advance payment support"""
        log_date = data.get('log_date')
        if isinstance(log_date, (datetime, date)):
            log_date = log_date.strftime('%Y-%m-%d')
        elif not log_date:
            log_date = datetime.now().strftime('%Y-%m-%d')

        customer_name = str(data.get('customer_name', '') or '').strip()
        customer_mobile = str(data.get('customer_mobile', '') or '').strip()
        customer_address = str(data.get('customer_address', '') or '').strip()
        customer_id = data.get('customer_id')

        technician_id = data.get('technician_id')
        technician_name = str(data.get('technician_name', '') or '').strip()

        # If tech_id is provided but no name, lookup tech name
        if technician_id and not technician_name:
            t = self.db.execute_query(
                "SELECT name FROM technicians WHERE id = %s",
                (technician_id,), fetch_one=True
            )
            if t:
                technician_name = t['name']

        work_description = str(data.get('work_description', '') or '').strip()

        total_billed = float(Decimal(str(data.get('total_billed', 0) or 0)))
        advance_payment = float(Decimal(str(data.get('advance_payment', 0) or 0)))
        advance_receiver = str(data.get('advance_receiver', 'Tech (Cash)') or 'Tech (Cash)').strip()

        final_payment = float(Decimal(str(data.get('final_payment', 0) or 0)))
        final_receiver = str(data.get('final_receiver', 'Tech (Cash)') or 'Tech (Cash)').strip()

        # Fallback if legacy total_payment provided without advance/final
        if total_billed == 0 and (advance_payment > 0 or final_payment > 0):
            total_billed = advance_payment + final_payment
        elif total_billed == 0 and float(data.get('total_payment', 0) or 0) > 0:
            total_billed = float(data.get('total_payment', 0) or 0)
            final_payment = total_billed

        total_payment = advance_payment + final_payment
        if total_payment == 0 and float(data.get('total_payment', 0) or 0) > 0:
            total_payment = float(data.get('total_payment', 0) or 0)

        pending_amount = max(0.0, total_billed - total_payment)

        material_cost = float(Decimal(str(data.get('material_cost', 0) or 0)))
        petrol_expense = float(Decimal(str(data.get('petrol_expense', 0) or 0)))
        total_expense = material_cost + petrol_expense
        net_profit = total_payment - total_expense

        # Automatic status determination if not explicitly overridden
        custom_status = data.get('payment_status')
        if custom_status:
            payment_status = str(custom_status).strip()
        elif pending_amount <= 0 and total_payment > 0:
            payment_status = 'Paid'
        elif advance_payment > 0 and pending_amount > 0:
            payment_status = 'Partial (Advance Paid)'
        elif total_payment == 0:
            payment_status = 'Pending'
        else:
            payment_status = 'Paid'

        payment_mode = str(data.get('payment_mode', 'Cash') or 'Cash').strip()
        notes = str(data.get('notes', '') or '').strip()

        query = """
        INSERT INTO daily_logs (
            log_date, customer_name, customer_mobile, customer_address,
            customer_id, technician_id, technician_name, work_description,
            total_billed, advance_payment, advance_receiver,
            final_payment, final_receiver, total_payment, pending_amount,
            material_cost, petrol_expense, total_expense,
            payment_status, payment_mode, net_profit, notes, is_active,
            created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s, 1,
            datetime('now','localtime'), datetime('now','localtime')
        )
        """
        params = (
            log_date, customer_name, customer_mobile, customer_address,
            customer_id, technician_id, technician_name, work_description,
            total_billed, advance_payment, advance_receiver,
            final_payment, final_receiver, total_payment, pending_amount,
            material_cost, petrol_expense, total_expense,
            payment_status, payment_mode, net_profit, notes
        )
        return self.db.execute_query(query, params)

    def update_log(self, log_id: int, data: dict) -> bool:
        """Update existing daily work & cost log entry"""
        log_date = data.get('log_date')
        if isinstance(log_date, (datetime, date)):
            log_date = log_date.strftime('%Y-%m-%d')
        elif not log_date:
            log_date = datetime.now().strftime('%Y-%m-%d')

        customer_name = str(data.get('customer_name', '') or '').strip()
        customer_mobile = str(data.get('customer_mobile', '') or '').strip()
        customer_address = str(data.get('customer_address', '') or '').strip()
        customer_id = data.get('customer_id')

        technician_id = data.get('technician_id')
        technician_name = str(data.get('technician_name', '') or '').strip()
        if technician_id and not technician_name:
            t = self.db.execute_query(
                "SELECT name FROM technicians WHERE id = %s",
                (technician_id,), fetch_one=True
            )
            if t:
                technician_name = t['name']

        work_description = str(data.get('work_description', '') or '').strip()

        total_billed = float(Decimal(str(data.get('total_billed', 0) or 0)))
        advance_payment = float(Decimal(str(data.get('advance_payment', 0) or 0)))
        advance_receiver = str(data.get('advance_receiver', 'Tech (Cash)') or 'Tech (Cash)').strip()

        final_payment = float(Decimal(str(data.get('final_payment', 0) or 0)))
        final_receiver = str(data.get('final_receiver', 'Tech (Cash)') or 'Tech (Cash)').strip()

        if total_billed == 0 and (advance_payment > 0 or final_payment > 0):
            total_billed = advance_payment + final_payment
        elif total_billed == 0 and float(data.get('total_payment', 0) or 0) > 0:
            total_billed = float(data.get('total_payment', 0) or 0)
            final_payment = total_billed

        total_payment = advance_payment + final_payment
        if total_payment == 0 and float(data.get('total_payment', 0) or 0) > 0:
            total_payment = float(data.get('total_payment', 0) or 0)

        pending_amount = max(0.0, total_billed - total_payment)

        material_cost = float(Decimal(str(data.get('material_cost', 0) or 0)))
        petrol_expense = float(Decimal(str(data.get('petrol_expense', 0) or 0)))
        total_expense = material_cost + petrol_expense
        net_profit = total_payment - total_expense

        custom_status = data.get('payment_status')
        if custom_status:
            payment_status = str(custom_status).strip()
        elif pending_amount <= 0 and total_payment > 0:
            payment_status = 'Paid'
        elif advance_payment > 0 and pending_amount > 0:
            payment_status = 'Partial (Advance Paid)'
        elif total_payment == 0:
            payment_status = 'Pending'
        else:
            payment_status = 'Paid'

        payment_mode = str(data.get('payment_mode', 'Cash') or 'Cash').strip()
        notes = str(data.get('notes', '') or '').strip()

        query = """
        UPDATE daily_logs SET
            log_date = %s,
            customer_name = %s,
            customer_mobile = %s,
            customer_address = %s,
            customer_id = %s,
            technician_id = %s,
            technician_name = %s,
            work_description = %s,
            total_billed = %s,
            advance_payment = %s,
            advance_receiver = %s,
            final_payment = %s,
            final_receiver = %s,
            total_payment = %s,
            pending_amount = %s,
            material_cost = %s,
            petrol_expense = %s,
            total_expense = %s,
            payment_status = %s,
            payment_mode = %s,
            net_profit = %s,
            notes = %s,
            updated_at = datetime('now','localtime')
        WHERE id = %s AND is_active = 1
        """
        params = (
            log_date, customer_name, customer_mobile, customer_address,
            customer_id, technician_id, technician_name, work_description,
            total_billed, advance_payment, advance_receiver,
            final_payment, final_receiver, total_payment, pending_amount,
            material_cost, petrol_expense, total_expense,
            payment_status, payment_mode, net_profit, notes,
            log_id
        )
        self.db.execute_query(query, params)
        return True

    def delete_log(self, log_id: int) -> bool:
        """Soft delete a log entry"""
        query = "UPDATE daily_logs SET is_active = 0, updated_at = datetime('now','localtime') WHERE id = %s"
        self.db.execute_query(query, (log_id,))
        return True

    def get_log(self, log_id: int) -> dict:
        """Get a single log entry by ID"""
        query = "SELECT * FROM daily_logs WHERE id = %s AND is_active = 1"
        return self.db.execute_query(query, (log_id,), fetch_one=True) or {}

    def get_logs(self, start_date=None, end_date=None, technician_id=None, search_term=None, limit=2000) -> list:
        """Fetch logs with optional date range, tech filter, and search text"""
        where_clauses = ["is_active = 1"]
        params = []

        if start_date:
            if isinstance(start_date, (datetime, date)):
                start_date = start_date.strftime('%Y-%m-%d')
            where_clauses.append("log_date >= %s")
            params.append(start_date)

        if end_date:
            if isinstance(end_date, (datetime, date)):
                end_date = end_date.strftime('%Y-%m-%d')
            where_clauses.append("log_date <= %s")
            params.append(end_date)

        if technician_id:
            where_clauses.append("technician_id = %s")
            params.append(technician_id)

        if search_term and search_term.strip():
            term = f"%{search_term.strip()}%"
            where_clauses.append("(customer_name LIKE %s OR customer_mobile LIKE %s OR customer_address LIKE %s OR work_description LIKE %s OR technician_name LIKE %s OR notes LIKE %s)")
            params.extend([term, term, term, term, term, term])

        where_sql = " AND ".join(where_clauses)
        query = f"""
        SELECT * FROM daily_logs
        WHERE {where_sql}
        ORDER BY log_date DESC, id DESC
        LIMIT {int(limit)}
        """
        return self.db.execute_query(query, tuple(params), fetch_all=True) or []

    def get_summary(self, start_date=None, end_date=None, technician_id=None) -> dict:
        """Get aggregate metrics for selected filters"""
        where_clauses = ["is_active = 1"]
        params = []

        if start_date:
            if isinstance(start_date, (datetime, date)):
                start_date = start_date.strftime('%Y-%m-%d')
            where_clauses.append("log_date >= %s")
            params.append(start_date)

        if end_date:
            if isinstance(end_date, (datetime, date)):
                end_date = end_date.strftime('%Y-%m-%d')
            where_clauses.append("log_date <= %s")
            params.append(end_date)

        if technician_id:
            where_clauses.append("technician_id = %s")
            params.append(technician_id)

        where_sql = " AND ".join(where_clauses)
        query = f"""
        SELECT
            COUNT(*) as total_entries,
            COALESCE(SUM(total_billed), SUM(total_payment), 0) as total_billed,
            COALESCE(SUM(advance_payment), 0) as total_advance,
            COALESCE(SUM(final_payment), 0) as total_final,
            COALESCE(SUM(total_payment), 0) as total_payment,
            COALESCE(SUM(pending_amount), 0) as total_pending,
            COALESCE(SUM(material_cost), 0) as total_material,
            COALESCE(SUM(petrol_expense), 0) as total_petrol,
            COALESCE(SUM(total_expense), 0) as total_expense,
            COALESCE(SUM(net_profit), 0) as net_profit,
            COALESCE(SUM(
                CASE 
                    WHEN (advance_receiver LIKE '%%Tech%%' OR advance_receiver LIKE '%%Cash%%') THEN advance_payment ELSE 0 END +
                CASE 
                    WHEN (final_receiver LIKE '%%Tech%%' OR final_receiver LIKE '%%Cash%%') THEN final_payment ELSE 0 END
            ), 0) as total_tech_cash,
            COALESCE(SUM(
                CASE 
                    WHEN (advance_receiver LIKE '%%Seth%%' OR advance_receiver LIKE '%%Owner%%' OR advance_receiver LIKE '%%Direct%%') THEN advance_payment ELSE 0 END +
                CASE 
                    WHEN (final_receiver LIKE '%%Seth%%' OR final_receiver LIKE '%%Owner%%' OR final_receiver LIKE '%%Direct%%') THEN final_payment ELSE 0 END
            ), 0) as total_seth_direct
        FROM daily_logs
        WHERE {where_sql}
        """
        res = self.db.execute_query(query, tuple(params), fetch_one=True) or {}
        return {
            'total_entries': int(res.get('total_entries', 0) or 0),
            'total_billed': float(res.get('total_billed', 0) or 0),
            'total_advance': float(res.get('total_advance', 0) or 0),
            'total_final': float(res.get('total_final', 0) or 0),
            'total_payment': float(res.get('total_payment', 0) or 0),
            'total_pending': float(res.get('total_pending', 0) or 0),
            'total_material': float(res.get('total_material', 0) or 0),
            'total_petrol': float(res.get('total_petrol', 0) or 0),
            'total_expense': float(res.get('total_expense', 0) or 0),
            'net_profit': float(res.get('net_profit', 0) or 0),
            'total_tech_cash': float(res.get('total_tech_cash', 0) or 0),
            'total_seth_direct': float(res.get('total_seth_direct', 0) or 0),
        }

    def get_month_reconciliation(self, year: int, month: int) -> dict:
        """Month-end auto-reconciliation with advance breakdown and per-technician settlements"""
        from calendar import monthrange
        start_date = f"{year}-{month:02d}-01"
        _, last_day = monthrange(year, month)
        end_date = f"{year}-{month:02d}-{last_day:02d}"

        overall = self.get_summary(start_date, end_date)

        # Per technician breakdown
        tech_query = """
        SELECT
            COALESCE(t.id, dl.technician_id, 0) as tech_id,
            COALESCE(t.name, dl.technician_name, 'Unassigned') as tech_name,
            COALESCE(t.mobile, '') as tech_mobile,
            COUNT(dl.id) as total_jobs,
            COALESCE(SUM(dl.total_billed), SUM(dl.total_payment), 0) as total_billed,
            COALESCE(SUM(dl.advance_payment), 0) as total_advance,
            COALESCE(SUM(
                CASE WHEN (dl.advance_receiver LIKE '%%Tech%%' OR dl.advance_receiver LIKE '%%Cash%%') THEN dl.advance_payment ELSE 0 END
            ), 0) as tech_advance_collected,
            COALESCE(SUM(
                CASE WHEN (dl.final_receiver LIKE '%%Tech%%' OR dl.final_receiver LIKE '%%Cash%%') THEN dl.final_payment ELSE 0 END
            ), 0) as tech_final_collected,
            COALESCE(SUM(
                CASE WHEN (dl.advance_receiver LIKE '%%Tech%%' OR dl.advance_receiver LIKE '%%Cash%%') THEN dl.advance_payment ELSE 0 END +
                CASE WHEN (dl.final_receiver LIKE '%%Tech%%' OR dl.final_receiver LIKE '%%Cash%%') THEN dl.final_payment ELSE 0 END
            ), 0) as cash_collected,
            COALESCE(SUM(
                CASE WHEN (dl.advance_receiver LIKE '%%Seth%%' OR dl.advance_receiver LIKE '%%Owner%%' OR dl.advance_receiver LIKE '%%Direct%%') THEN dl.advance_payment ELSE 0 END +
                CASE WHEN (dl.final_receiver LIKE '%%Seth%%' OR dl.final_receiver LIKE '%%Owner%%' OR dl.final_receiver LIKE '%%Direct%%') THEN dl.final_payment ELSE 0 END
            ), 0) as direct_seth,
            COALESCE(SUM(dl.pending_amount), 0) as pending_amount,
            COALESCE(SUM(dl.material_cost), 0) as total_material,
            COALESCE(SUM(dl.petrol_expense), 0) as total_petrol,
            COALESCE(SUM(dl.total_expense), 0) as total_expense,
            COALESCE(SUM(dl.net_profit), 0) as net_profit
        FROM daily_logs dl
        LEFT JOIN technicians t ON dl.technician_id = t.id
        WHERE dl.is_active = 1 AND dl.log_date >= %s AND dl.log_date <= %s
        GROUP BY tech_id, tech_name, tech_mobile
        ORDER BY cash_collected DESC, total_billed DESC
        """
        tech_rows = self.db.execute_query(tech_query, (start_date, end_date), fetch_all=True) or []

        tech_settlements = []
        for r in tech_rows:
            cash = float(r['cash_collected'] or 0)
            exp = float(r['total_expense'] or 0)
            # Net cash tech has to hand over to Seth = Cash Collected - Tech Kharcha
            net_due_to_seth = cash - exp
            tech_settlements.append({
                'tech_id': r['tech_id'],
                'tech_name': r['tech_name'],
                'tech_mobile': r['tech_mobile'],
                'total_jobs': int(r['total_jobs'] or 0),
                'total_billed': float(r['total_billed'] or 0),
                'total_advance': float(r['total_advance'] or 0),
                'tech_advance_collected': float(r['tech_advance_collected'] or 0),
                'tech_final_collected': float(r['tech_final_collected'] or 0),
                'cash_collected': cash,
                'direct_seth': float(r['direct_seth'] or 0),
                'pending_amount': float(r['pending_amount'] or 0),
                'total_material': float(r['total_material'] or 0),
                'total_petrol': float(r['total_petrol'] or 0),
                'total_expense': exp,
                'net_profit': float(r['net_profit'] or 0),
                'net_due_to_seth': net_due_to_seth
            })

        return {
            'year': year,
            'month': month,
            'start_date': start_date,
            'end_date': end_date,
            'overall': overall,
            'technicians': tech_settlements
        }

    def search_customers(self, query_str: str) -> list:
        """Search existing customers to auto-fill address and phone in daily logs"""
        if not query_str or len(query_str.strip()) < 1:
            return []
        term = f"%{query_str.strip()}%"
        q = """
        SELECT id, name, mobile, address, landmark, city
        FROM customers
        WHERE is_active = 1 AND (name LIKE %s OR mobile LIKE %s OR address LIKE %s)
        ORDER BY name ASC
        LIMIT 10
        """
        return self.db.execute_query(q, (term, term, term), fetch_all=True) or []

    def get_all_technicians_list(self) -> list:
        """Get all technicians who have records in technicians table or daily logs"""
        query = """
        SELECT DISTINCT COALESCE(t.id, 0) as id, COALESCE(t.name, dl.technician_name) as name, COALESCE(t.mobile, '') as mobile
        FROM daily_logs dl
        LEFT JOIN technicians t ON dl.technician_id = t.id
        WHERE dl.is_active = 1 AND COALESCE(t.name, dl.technician_name, '') != ''
        UNION
        SELECT id, name, mobile
        FROM technicians
        WHERE is_active = 1
        ORDER BY name ASC
        """
        return self.db.execute_query(query, fetch_all=True) or []

    def get_technician_dossier(self, technician_name: str = None, technician_id: int = None, start_date=None, end_date=None) -> dict:
        """Fetch complete performance, advance, expense, and all site visits for a technician"""
        where_clauses = ["dl.is_active = 1"]
        params = []

        if technician_id:
            where_clauses.append("dl.technician_id = %s")
            params.append(technician_id)
        elif technician_name and technician_name.strip() and technician_name.strip() != "-- Select or Type Technician --":
            where_clauses.append("LOWER(dl.technician_name) = LOWER(%s)")
            params.append(technician_name.strip())

        if start_date:
            if isinstance(start_date, (datetime, date)):
                start_date = start_date.strftime('%Y-%m-%d')
            where_clauses.append("dl.log_date >= %s")
            params.append(start_date)

        if end_date:
            if isinstance(end_date, (datetime, date)):
                end_date = end_date.strftime('%Y-%m-%d')
            where_clauses.append("dl.log_date <= %s")
            params.append(end_date)

        where_sql = " AND ".join(where_clauses)

        sum_query = f"""
        SELECT
            COUNT(dl.id) as total_jobs,
            COALESCE(SUM(dl.total_billed), SUM(dl.total_payment), 0) as total_billed,
            COALESCE(SUM(dl.advance_payment), 0) as total_advance,
            COALESCE(SUM(
                CASE WHEN (dl.advance_receiver LIKE '%%Tech%%' OR dl.advance_receiver LIKE '%%Cash%%') THEN dl.advance_payment ELSE 0 END +
                CASE WHEN (dl.final_receiver LIKE '%%Tech%%' OR dl.final_receiver LIKE '%%Cash%%') THEN dl.final_payment ELSE 0 END
            ), 0) as cash_collected,
            COALESCE(SUM(
                CASE WHEN (dl.advance_receiver LIKE '%%Seth%%' OR dl.advance_receiver LIKE '%%Owner%%' OR dl.advance_receiver LIKE '%%Direct%%') THEN dl.advance_payment ELSE 0 END +
                CASE WHEN (dl.final_receiver LIKE '%%Seth%%' OR dl.final_receiver LIKE '%%Owner%%' OR dl.final_receiver LIKE '%%Direct%%') THEN dl.final_payment ELSE 0 END
            ), 0) as direct_seth,
            COALESCE(SUM(dl.final_payment), 0) as total_final,
            COALESCE(SUM(dl.total_payment), 0) as total_received,
            COALESCE(SUM(dl.pending_amount), 0) as pending_amount,
            COALESCE(SUM(dl.material_cost), 0) as total_material,
            COALESCE(SUM(dl.petrol_expense), 0) as total_petrol,
            COALESCE(SUM(dl.total_expense), 0) as total_expense,
            COALESCE(SUM(dl.net_profit), 0) as net_profit,
            COUNT(DISTINCT dl.customer_address) as unique_sites
        FROM daily_logs dl
        WHERE {where_sql}
        """
        summary_row = self.db.execute_query(sum_query, tuple(params), fetch_one=True) or {}

        detail_query = f"""
        SELECT dl.*
        FROM daily_logs dl
        WHERE {where_sql}
        ORDER BY dl.log_date DESC, dl.id DESC
        """
        jobs = self.db.execute_query(detail_query, tuple(params), fetch_all=True) or []

        cash = float(summary_row.get('cash_collected', 0) or 0)
        exp = float(summary_row.get('total_expense', 0) or 0)
        net_handover = cash - exp

        return {
            'technician_name': technician_name,
            'technician_id': technician_id,
            'total_jobs': int(summary_row.get('total_jobs', 0) or 0),
            'unique_sites': int(summary_row.get('unique_sites', 0) or 0),
            'total_billed': float(summary_row.get('total_billed', 0) or 0),
            'total_advance': float(summary_row.get('total_advance', 0) or 0),
            'total_final': float(summary_row.get('total_final', 0) or 0),
            'total_received': float(summary_row.get('total_received', 0) or 0),
            'cash_collected': cash,
            'direct_seth': float(summary_row.get('direct_seth', 0) or 0),
            'pending_amount': float(summary_row.get('pending_amount', 0) or 0),
            'total_material': float(summary_row.get('total_material', 0) or 0),
            'total_petrol': float(summary_row.get('total_petrol', 0) or 0),
            'total_expense': exp,
            'net_profit': float(summary_row.get('net_profit', 0) or 0),
            'net_handover_to_seth': net_handover,
            'jobs': jobs
        }

    def get_customer_dossier(self, customer_query: str = None, start_date=None, end_date=None) -> dict:
        """Fetch complete service history, advances, pending dues, and technicians for a customer"""
        where_clauses = ["dl.is_active = 1"]
        params = []

        if customer_query and customer_query.strip():
            term = f"%{customer_query.strip()}%"
            where_clauses.append("(dl.customer_name LIKE %s OR dl.customer_mobile LIKE %s OR dl.customer_address LIKE %s)")
            params.extend([term, term, term])

        if start_date:
            if isinstance(start_date, (datetime, date)):
                start_date = start_date.strftime('%Y-%m-%d')
            where_clauses.append("dl.log_date >= %s")
            params.append(start_date)

        if end_date:
            if isinstance(end_date, (datetime, date)):
                end_date = end_date.strftime('%Y-%m-%d')
            where_clauses.append("dl.log_date <= %s")
            params.append(end_date)

        where_sql = " AND ".join(where_clauses)

        sum_query = f"""
        SELECT
            COUNT(dl.id) as total_visits,
            COALESCE(SUM(dl.total_billed), SUM(dl.total_payment), 0) as total_billed,
            COALESCE(SUM(dl.advance_payment), 0) as total_advance,
            COALESCE(SUM(dl.final_payment), 0) as total_final,
            COALESCE(SUM(dl.total_payment), 0) as total_paid,
            COALESCE(SUM(dl.pending_amount), 0) as pending_balance,
            COALESCE(SUM(dl.material_cost), 0) as total_material,
            COALESCE(SUM(dl.petrol_expense), 0) as total_petrol,
            COALESCE(SUM(dl.total_expense), 0) as total_expense,
            COALESCE(SUM(dl.net_profit), 0) as net_profit,
            COUNT(DISTINCT dl.technician_name) as distinct_techs
        FROM daily_logs dl
        WHERE {where_sql}
        """
        summary_row = self.db.execute_query(sum_query, tuple(params), fetch_one=True) or {}

        detail_query = f"""
        SELECT dl.*
        FROM daily_logs dl
        WHERE {where_sql}
        ORDER BY dl.log_date DESC, dl.id DESC
        """
        visits = self.db.execute_query(detail_query, tuple(params), fetch_all=True) or []

        return {
            'customer_query': customer_query,
            'total_visits': int(summary_row.get('total_visits', 0) or 0),
            'distinct_techs': int(summary_row.get('distinct_techs', 0) or 0),
            'total_billed': float(summary_row.get('total_billed', 0) or 0),
            'total_advance': float(summary_row.get('total_advance', 0) or 0),
            'total_final': float(summary_row.get('total_final', 0) or 0),
            'total_paid': float(summary_row.get('total_paid', 0) or 0),
            'pending_balance': float(summary_row.get('pending_balance', 0) or 0),
            'total_material': float(summary_row.get('total_material', 0) or 0),
            'total_petrol': float(summary_row.get('total_petrol', 0) or 0),
            'total_expense': float(summary_row.get('total_expense', 0) or 0),
            'net_profit': float(summary_row.get('net_profit', 0) or 0),
            'visits': visits
        }

    def export_to_excel(self, logs: list, filepath: str) -> str:
        """Export logs to beautifully styled Excel (.xlsx) file in clean English with executive dashboard and charts"""
        from datetime import datetime
        from utils.excel_helper import ExcelExporter

        headers = [
            "Date", "Customer Name", "Mobile Number", "Address / Site",
            "Technician", "Work / Material Details", "Total Billed",
            "Advance Paid", "Advance To", "Final Paid", "Final To",
            "Total Received", "Pending Due", "Material Cost",
            "Petrol Cost", "Total Expense", "Payment Status", "Net Profit", "Notes"
        ]

        rows = []
        tot_billed = 0.0
        tot_adv = 0.0
        tot_fin = 0.0
        tot_rec = 0.0
        tot_pend = 0.0
        tot_mat = 0.0
        tot_pet = 0.0
        tot_exp = 0.0
        tot_prof = 0.0
        paid_cnt = 0
        pending_cnt = 0
        partial_cnt = 0

        for log in logs:
            b = float(log.get('total_billed', 0) or log.get('total_payment', 0) or 0)
            adv = float(log.get('advance_payment', 0) or 0)
            fin = float(log.get('final_payment', 0) or 0)
            rec = float(log.get('total_payment', 0) or 0)
            pend = float(log.get('pending_amount', 0) or max(0.0, b - rec))
            mat = float(log.get('material_cost', 0) or 0)
            pet = float(log.get('petrol_expense', 0) or 0)
            exp = float(log.get('total_expense', 0) or (mat + pet))
            prof = float(log.get('net_profit', 0) or (rec - exp))
            st = str(log.get('payment_status') or 'Paid').strip().capitalize()

            tot_billed += b
            tot_adv += adv
            tot_fin += fin
            tot_rec += rec
            tot_pend += pend
            tot_mat += mat
            tot_pet += pet
            tot_exp += exp
            tot_prof += prof

            if 'paid' in st.lower():
                paid_cnt += 1
            elif 'pend' in st.lower():
                pending_cnt += 1
            else:
                partial_cnt += 1

            rows.append([
                log.get('log_date', ''),
                log.get('customer_name', ''),
                log.get('customer_mobile', ''),
                log.get('customer_address', ''),
                log.get('technician_name', ''),
                log.get('work_description', ''),
                b, adv, log.get('advance_receiver', ''),
                fin, log.get('final_receiver', ''),
                rec, pend, mat, pet, exp,
                st, prof, log.get('notes', '')
            ])

        kpis = [
            ("Total Logs", len(logs)),
            ("Total Billed", tot_billed),
            ("Total Received", tot_rec),
            ("Pending Due", tot_pend),
            ("Total Expense", tot_exp),
            ("Net Profit", tot_prof),
        ]

        charts_data = [
            {
                'type': 'pie',
                'title': 'Payment Status Distribution',
                'categories': ['Paid', 'Pending', 'Partial'],
                'values': [('Count', [paid_cnt, pending_cnt, partial_cnt])],
            },
            {
                'type': 'bar',
                'title': 'Financial Summary & Profitability',
                'categories': ['Total Billed', 'Collections', 'Pending Due', 'Expenses', 'Net Profit'],
                'values': [('Amount', [tot_billed, tot_rec, tot_pend, tot_exp, tot_prof])],
                'y_axis': 'Amount (₹)'
            }
        ]

        wb = ExcelExporter.build_excel(
            sheet_title="Daily Work Logs",
            title_text="Daily Work, Advance & Cost Register",
            subtitle_text=f"Total: {len(logs)} jobs logged | Profit: ₹{tot_prof:,.2f} | Generated: {datetime.now().strftime('%d-%b-%Y %H:%M')}",
            headers=headers,
            rows=rows,
            number_cols={7, 8, 10, 12, 13, 14, 15, 16, 18},
            kpis=kpis,
            charts_data=charts_data,
            freeze_col=True
        )

        wb.save(filepath)
        return filepath
