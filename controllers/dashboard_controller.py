"""
Dashboard controller for analytics
"""
from datetime import datetime, timedelta

class DashboardController:
    def __init__(self, db_connection):
        self.db = db_connection

    def get_dashboard_stats(self, period='today'):
        """Get dashboard statistics - OPTIMIZED: Single query for main stats"""
        start_date, end_date = self._get_date_range(period)
        
        # OPTIMIZED: Get all main stats in ONE query instead of 7 separate queries
        main_stats = self._get_combined_main_stats(start_date, end_date)
        
        # Get today's summary (still needs separate queries for date-specific data)
        today_summary = self._get_today_summary_optimized()
        
        # Get AMC stats (optimized with combined query)
        amc_stats = self._get_amc_stats_optimized()
        
        # Online requests count (already optimized with subquery)
        online_requests = self._get_online_requests_count()
        
        # Pending payments (needed as list, can't optimize further)
        pending_payments = self._get_pending_payments()
        
        return {
            'total_customers': main_stats['total_customers'],
            'total_invoices': main_stats['total_invoices'],
            'total_revenue': main_stats['total_revenue'],
            'pending_payments': pending_payments,
            'today_summary': today_summary,
            'period': period,
            'amc_stats': amc_stats,
            'online_requests': online_requests
        }

    def _get_combined_main_stats(self, start_date, end_date):
        """
        OPTIMIZED: Get customers, invoices, and revenue in single query
        Previously: 7 separate queries (N+1 problem)
        Now: 1 combined query
        """
        try:
            if start_date and end_date:
                end_date_plus = end_date + timedelta(days=1)
                query = """
                SELECT
                    (SELECT COUNT(*) FROM customers WHERE is_active = TRUE) as total_customers,
                    (SELECT COUNT(*) FROM invoices WHERE is_active = TRUE AND created_at >= %s AND created_at < %s) as total_invoices,
                    (SELECT COALESCE(SUM(total_amount), 0) FROM invoices WHERE is_active = TRUE AND created_at >= %s AND created_at < %s) as total_revenue
                """
                result = self.db.execute_query(query, (start_date, end_date_plus, start_date, end_date_plus), fetch_one=True)
            else:
                query = """
                SELECT
                    (SELECT COUNT(*) FROM customers WHERE is_active = TRUE) as total_customers,
                    (SELECT COUNT(*) FROM invoices WHERE is_active = TRUE) as total_invoices,
                    (SELECT COALESCE(SUM(total_amount), 0) FROM invoices WHERE is_active = TRUE) as total_revenue
                """
                result = self.db.execute_query(query, fetch_one=True)
            
            return {
                'total_customers': result['total_customers'] if result else 0,
                'total_invoices': result['total_invoices'] if result else 0,
                'total_revenue': float(result['total_revenue']) if result and result['total_revenue'] else 0.0
            }
        except Exception as e:
            print(f"Error getting combined stats: {e}")
            return {'total_customers': 0, 'total_invoices': 0, 'total_revenue': 0.0}

    def _get_amc_stats_optimized(self):
        """
        OPTIMIZED: Get all AMC stats in single query
        Previously: 4 separate queries
        Now: 1 combined query
        """
        try:
            query = """
            SELECT
                (SELECT COUNT(*) FROM amc_contracts WHERE amc_status = 'Active' AND is_active = TRUE) as total_active,
                (SELECT COUNT(*) FROM amc_contracts WHERE amc_status = 'Active' AND is_active = TRUE 
                    AND end_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)) as expiring_soon,
                (SELECT COUNT(*) FROM amc_visits WHERE visit_status = 'Scheduled' AND is_active = TRUE 
                    AND visit_date >= CURDATE()) as upcoming_visits,
                (SELECT COALESCE(SUM(total_amount), 0) FROM amc_contracts WHERE is_active = TRUE) as total_revenue
            """
            result = self.db.execute_query(query, fetch_one=True)
            
            return {
                'total_active': result['total_active'] if result else 0,
                'expiring_soon': result['expiring_soon'] if result else 0,
                'upcoming_visits': result['upcoming_visits'] if result else 0,
                'total_revenue': float(result['total_revenue']) if result and result['total_revenue'] else 0.0
            }
        except Exception as e:
            print(f"Error getting AMC stats: {e}")
            return {
                'total_active': 0,
                'expiring_soon': 0,
                'upcoming_visits': 0,
                'total_revenue': 0
            }

    def _get_today_summary_optimized(self):
        """
        OPTIMIZED: Get today's summary in single query
        Previously: 3 separate queries
        Now: 1 combined query
        """
        today = datetime.now().date()
        
        try:
            today_plus = today + timedelta(days=1)
            query = """
            SELECT
                (SELECT COUNT(*) FROM invoices WHERE is_active = TRUE AND created_at >= %s AND created_at < %s) as services_done,
                (SELECT COALESCE(SUM(advance_payment), 0) FROM invoices WHERE is_active = TRUE 
                    AND created_at >= %s AND created_at < %s) as payment_received,
                (SELECT COUNT(*) FROM customers WHERE is_active = TRUE AND created_at >= %s AND created_at < %s) as new_customers
            """
            result = self.db.execute_query(query, (today, today_plus, today, today_plus, today, today_plus), fetch_one=True)
            
            return {
                'services_done': result['services_done'] if result else 0,
                'payment_received': float(result['payment_received']) if result and result['payment_received'] else 0.0,
                'new_customers': result['new_customers'] if result else 0
            }
        except Exception as e:
            print(f"Error getting today summary: {e}")
            return {
                'services_done': 0,
                'payment_received': 0.0,
                'new_customers': 0
            }

    def _get_online_requests_count(self):
        """Get count of pending online requests"""
        try:
            query = """
            SELECT COUNT(*) as total
            FROM contact_messages
            WHERE status IN ('Pending', 'unread')
            """
            result = self.db.execute_query(query, fetch_one=True)
            return result['total'] if result else 0
        except Exception as e:
            print(f"Error getting online requests count: {e}")
            return 0

    def _get_pending_payments(self):
        """Get pending payments list"""
        query = """
        SELECT
            c.name as customer_name,
            i.balance_amount,
            DATE(i.created_at) as invoice_date,
            i.invoice_number,
            i.id as invoice_id
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        WHERE i.is_active = TRUE
        AND i.balance_amount > 0
        AND i.payment_status != 'Paid'
        ORDER BY i.created_at DESC
        LIMIT 20
        """
        return self.db.execute_query(query, fetch_all=True)

    def _get_date_range(self, period):
        """Return (start_date, end_date) tuple for period filter, or (None, None) if no match"""
        today = datetime.now().date()
        
        if period in ('today',):
            return today, today
        elif period in ('this_week', 'weekly'):
            start = today - timedelta(days=today.weekday())
            return start, today
        elif period in ('this_month', 'monthly'):
            start = today.replace(day=1)
            return start, today
        elif period in ('this_year', 'yearly'):
            start = today.replace(month=1, day=1)
            return start, today
        else:
            return None, None
    
    def get_service_summary(self, period='today'):
        """Get service-wise summary"""
        start_date, end_date = self._get_date_range(period)
        
        if start_date and end_date:
            end_date_plus = end_date + timedelta(days=1)
            query = """
            SELECT 
                s.service_name,
                COUNT(ii.id) as count,
                COALESCE(SUM(ii.amount), 0) as revenue
            FROM invoice_items ii
            JOIN services s ON ii.service_id = s.id
            JOIN invoices i ON ii.invoice_id = i.id
            WHERE i.is_active = TRUE 
            AND ii.item_type = 'service'
            AND i.created_at >= %s AND i.created_at < %s
            GROUP BY s.service_name
            ORDER BY revenue DESC
            """
            return self.db.execute_query(query, (start_date, end_date_plus), fetch_all=True)
        else:
            query = """
            SELECT 
                s.service_name,
                COUNT(ii.id) as count,
                COALESCE(SUM(ii.amount), 0) as revenue
            FROM invoice_items ii
            JOIN services s ON ii.service_id = s.id
            JOIN invoices i ON ii.invoice_id = i.id
            WHERE i.is_active = TRUE 
            AND ii.item_type = 'service'
            GROUP BY s.service_name
            ORDER BY revenue DESC
            """
            return self.db.execute_query(query, fetch_all=True)
    
    def get_part_summary(self, period='today'):
        """Get part-wise summary"""
        start_date, end_date = self._get_date_range(period)
        
        if start_date and end_date:
            end_date_plus = end_date + timedelta(days=1)
            query = """
            SELECT 
                p.part_name,
                SUM(ii.quantity) as quantity_sold,
                COALESCE(SUM(ii.amount), 0) as revenue
            FROM invoice_items ii
            JOIN parts p ON ii.part_id = p.id
            JOIN invoices i ON ii.invoice_id = i.id
            WHERE i.is_active = TRUE 
            AND ii.item_type = 'part'
            AND i.created_at >= %s AND i.created_at < %s
            GROUP BY p.part_name
            ORDER BY revenue DESC
            """
            return self.db.execute_query(query, (start_date, end_date_plus), fetch_all=True)
        else:
            query = """
            SELECT 
                p.part_name,
                SUM(ii.quantity) as quantity_sold,
                COALESCE(SUM(ii.amount), 0) as revenue
            FROM invoice_items ii
            JOIN parts p ON ii.part_id = p.id
            JOIN invoices i ON ii.invoice_id = i.id
            WHERE i.is_active = TRUE 
            AND ii.item_type = 'part'
            GROUP BY p.part_name
            ORDER BY revenue DESC
            """
            return self.db.execute_query(query, fetch_all=True)
    
    def get_technician_performance(self, start_date=None, end_date=None):
        """Get technician performance summary"""
        if not start_date:
            start_date = datetime.now().replace(day=1).date()  # Month start
        if not end_date:
            end_date = datetime.now().date()
        
        end_date_plus = end_date + timedelta(days=1)
        query = """
        SELECT 
            t.name,
            t.mobile,
            COUNT(i.id) as services_done,
            COALESCE(SUM(i.total_amount), 0) as total_revenue,
            COALESCE(SUM(i.advance_payment), 0) as amount_collected,
            COALESCE(SUM(i.balance_amount), 0) as pending_amount
        FROM technicians t
        LEFT JOIN invoices i ON t.id = i.technician_id
            AND i.is_active = TRUE
            AND i.created_at >= %s AND i.created_at < %s
        WHERE t.is_active = TRUE
        GROUP BY t.id, t.name, t.mobile
        ORDER BY services_done DESC
        """
        
        return self.db.execute_query(query, (start_date, end_date_plus), fetch_all=True)
    
    def get_revenue_trend(self, days=30):
        """Get revenue trend for last N days"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)

        end_date_plus = end_date + timedelta(days=1)
        query = """
        SELECT
            DATE(created_at) as date,
            COUNT(*) as invoice_count,
            COALESCE(SUM(total_amount), 0) as daily_revenue,
            COALESCE(SUM(advance_payment), 0) as daily_collection
        FROM invoices
        WHERE is_active = TRUE
        AND created_at >= %s AND created_at < %s
        GROUP BY DATE(created_at)
        ORDER BY date
        """

        return self.db.execute_query(query, (start_date, end_date_plus), fetch_all=True)

    def get_top_services(self, limit=10, period='monthly'):
        """Get top services by revenue"""
        start_date, end_date = self._get_date_range(period)
        
        if start_date and end_date:
            end_date_plus = end_date + timedelta(days=1)
            query = """
            SELECT
                s.service_name,
                s.default_rate as service_price,
                COUNT(ii.id) as times_sold,
                COALESCE(SUM(ii.amount), 0) as total_revenue
            FROM invoice_items ii
            JOIN services s ON ii.service_id = s.id
            JOIN invoices i ON ii.invoice_id = i.id
            WHERE i.is_active = TRUE
            AND ii.item_type = 'service'
            AND i.created_at >= %s AND i.created_at < %s
            GROUP BY s.id, s.service_name, s.default_rate
            ORDER BY total_revenue DESC
            LIMIT %s
            """
            return self.db.execute_query(query, (start_date, end_date_plus, limit), fetch_all=True)
        else:
            query = """
            SELECT
                s.service_name,
                s.default_rate as service_price,
                COUNT(ii.id) as times_sold,
                COALESCE(SUM(ii.amount), 0) as total_revenue
            FROM invoice_items ii
            JOIN services s ON ii.service_id = s.id
            JOIN invoices i ON ii.invoice_id = i.id
            WHERE i.is_active = TRUE
            AND ii.item_type = 'service'
            GROUP BY s.id, s.service_name, s.default_rate
            ORDER BY total_revenue DESC
            LIMIT %s
            """
            return self.db.execute_query(query, (limit,), fetch_all=True)

    def get_customer_retention_rate(self, period='yearly'):
        """Calculate customer retention rate"""
        from dateutil.relativedelta import relativedelta
        from datetime import date as date_type

        # Get date range
        if period == 'monthly':
            months_ago = 1
        elif period == 'quarterly':
            months_ago = 3
        elif period == 'yearly':
            months_ago = 12
        else:
            months_ago = 12

        today = date_type.today()
        # Previous period boundaries
        prev_start = today - relativedelta(months=months_ago * 2)
        prev_end = today - relativedelta(months=months_ago)
        # Current period boundaries
        curr_start = today - relativedelta(months=months_ago)
        curr_end = today + timedelta(days=1)

        # Calculate previous period customers
        query = """
        SELECT COUNT(DISTINCT customer_id) as count FROM invoices
        WHERE is_active = TRUE
        AND created_at >= %s AND created_at < %s
        """
        result = self.db.execute_query(query, (prev_start, prev_end), fetch_one=True)
        previous_customers = result['count'] if result else 0

        # Calculate current period customers
        query = """
        SELECT COUNT(DISTINCT customer_id) as count FROM invoices
        WHERE is_active = TRUE
        AND created_at >= %s AND created_at < %s
        """
        result = self.db.execute_query(query, (curr_start, curr_end), fetch_one=True)
        current_customers = result['count'] if result else 0

        # Calculate retention rate
        if previous_customers > 0:
            # Get customers who repeated (had invoice in BOTH periods)
            query = """
            SELECT COUNT(*) as count FROM (
                SELECT customer_id FROM invoices
                WHERE is_active = TRUE AND created_at >= %s AND created_at < %s
                INTERSECT
                SELECT customer_id FROM invoices
                WHERE is_active = TRUE AND created_at >= %s AND created_at < %s
            )
            """
            result = self.db.execute_query(query, (prev_start, prev_end, curr_start, curr_end), fetch_one=True)
            repeat_customers = result['count'] if result else 0

            retention_rate = (repeat_customers / previous_customers) * 100 if previous_customers > 0 else 0
        else:
            repeat_customers = 0
            retention_rate = 0

        return {
            'retention_rate': round(retention_rate, 2),
            'previous_customers': previous_customers,
            'current_customers': current_customers,
            'repeat_customers': repeat_customers
        }

    def get_monthly_comparison(self):
        """Compare current month vs previous month"""
        from dateutil.relativedelta import relativedelta
        from datetime import date as date_type

        today = date_type.today()
        # Current month: [first of month, first of next month)
        curr_start = today.replace(day=1)
        curr_end = curr_start + relativedelta(months=1)

        # Previous month: [first of prev month, first of current month)
        prev_start = curr_start - relativedelta(months=1)
        prev_end = curr_start

        current_month_query = """
        SELECT 
            COUNT(*) as invoice_count,
            COALESCE(SUM(total_amount), 0) as revenue,
            COALESCE(SUM(advance_payment), 0) as collected,
            COALESCE(SUM(balance_amount), 0) as pending
        FROM invoices
        WHERE is_active = TRUE
        AND created_at >= %s AND created_at < %s
        """
        current = self.db.execute_query(current_month_query, (curr_start, curr_end), fetch_one=True) or {}
        current.setdefault('invoice_count', 0)
        current.setdefault('revenue', 0)
        current.setdefault('collected', 0)
        current.setdefault('pending', 0)

        previous_month_query = """
        SELECT 
            COUNT(*) as invoice_count,
            COALESCE(SUM(total_amount), 0) as revenue,
            COALESCE(SUM(advance_payment), 0) as collected,
            COALESCE(SUM(balance_amount), 0) as pending
        FROM invoices
        WHERE is_active = TRUE
        AND created_at >= %s AND created_at < %s
        """
        previous = self.db.execute_query(previous_month_query, (prev_start, prev_end), fetch_one=True) or {}
        previous.setdefault('invoice_count', 0)
        previous.setdefault('revenue', 0)
        previous.setdefault('collected', 0)
        previous.setdefault('pending', 0)

        current_revenue = float(current['revenue'] or 0)
        previous_revenue = float(previous['revenue'] or 0)

        if previous_revenue > 0:
            revenue_growth = ((current_revenue - previous_revenue) / previous_revenue) * 100
        else:
            revenue_growth = 100 if current_revenue > 0 else 0

        current_count = int(current['invoice_count'] or 0)
        previous_count = int(previous['invoice_count'] or 0)

        if previous_count > 0:
            count_growth = ((current_count - previous_count) / previous_count) * 100
        else:
            count_growth = 100 if current_count > 0 else 0

        return {
            'current_month': {
                'invoice_count': current_count,
                'revenue': current_revenue,
                'collected': float(current['collected'] or 0),
                'pending': float(current['pending'] or 0)
            },
            'previous_month': {
                'invoice_count': previous_count,
                'revenue': previous_revenue,
                'collected': float(previous['collected'] or 0),
                'pending': float(previous['pending'] or 0)
            },
            'revenue_growth': round(revenue_growth, 2),
            'count_growth': round(count_growth, 2)
        }

    def get_payment_mode_distribution(self, period='this_week'):
        """Get payment mode distribution for pie chart"""
        start_date, end_date = self._get_date_range(period)
        try:
            if start_date and end_date:
                query = """
                SELECT payment_mode, COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
                FROM invoices
                WHERE is_active = TRUE AND created_at BETWEEN %s AND %s AND payment_mode IS NOT NULL
                GROUP BY payment_mode
                ORDER BY count DESC
                """
                return self.db.execute_query(query, (start_date, end_date), fetch_all=True)
            else:
                query = """
                SELECT payment_mode, COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total
                FROM invoices
                WHERE is_active = TRUE AND payment_mode IS NOT NULL
                GROUP BY payment_mode
                ORDER BY count DESC
                """
                return self.db.execute_query(query, fetch_all=True)
        except Exception as e:
            print(f"Error getting payment mode distribution: {e}")
            return []

    def get_profit_trend(self, days=30):
        """Get daily profit trend for line/bar chart"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days - 1)
        try:
            query = """
            SELECT
                DATE(created_at) as date,
                COALESCE(SUM(total_amount), 0) as daily_profit,
                COALESCE(COUNT(*), 0) as visit_count
            FROM invoices
            WHERE is_active = TRUE AND DATE(created_at) BETWEEN %s AND %s
            GROUP BY DATE(created_at)
            ORDER BY date
            """
            return self.db.execute_query(query, (start_date, end_date), fetch_all=True)
        except Exception as e:
            print(f"Error getting profit trend: {e}")
            return []

    def get_technician_chart_data(self, period='this_week'):
        """Get technician performance data for chart"""
        start_date, end_date = self._get_date_range(period)
        try:
            if start_date and end_date:
                query = """
                SELECT
                    COALESCE(t.name, 'Unassigned') as name,
                    COUNT(i.id) as job_count,
                    COALESCE(SUM(i.total_amount), 0) as total_revenue,
                    COALESCE(SUM(i.total_amount - (i.total_amount * t.commission_rate / 100)), 0) as total_profit
                FROM invoices i
                LEFT JOIN technicians t ON i.technician_id = t.id
                WHERE i.is_active = TRUE AND i.created_at BETWEEN %s AND %s
                GROUP BY t.name
                ORDER BY total_revenue DESC
                LIMIT 8
                """
                return self.db.execute_query(query, (start_date, end_date), fetch_all=True)
            else:
                query = """
                SELECT
                    COALESCE(t.name, 'Unassigned') as name,
                    COUNT(i.id) as job_count,
                    COALESCE(SUM(i.total_amount), 0) as total_revenue,
                    COALESCE(SUM(i.total_amount - (i.total_amount * t.commission_rate / 100)), 0) as total_profit
                FROM invoices i
                LEFT JOIN technicians t ON i.technician_id = t.id
                WHERE i.is_active = TRUE
                GROUP BY t.name
                ORDER BY total_revenue DESC
                LIMIT 8
                """
                return self.db.execute_query(query, fetch_all=True)
        except Exception as e:
            print(f"Error getting technician chart data: {e}")
            return []

    def get_payment_pending_alerts(self, limit=200):
        """Get list of pending payments with alerts"""
        query = """
        SELECT
            c.name as customer_name,
            c.mobile as customer_mobile,
            i.invoice_number,
            i.balance_amount,
            i.total_amount,
            DATE(i.created_at) as invoice_date,
            DATEDIFF(CURDATE(), i.created_at) as days_pending,
            i.payment_status,
            i.id as invoice_id
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        WHERE i.is_active = TRUE
        AND i.balance_amount > 0
        AND i.payment_status != 'Paid'
        ORDER BY days_pending DESC, i.balance_amount DESC
        """
        if limit is not None:
            query += " LIMIT %s"
            return self.db.execute_query(query, (limit,), fetch_all=True)
        return self.db.execute_query(query, fetch_all=True)