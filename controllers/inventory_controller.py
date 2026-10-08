from datetime import datetime


class InventoryController:
    def __init__(self, db_connection):
        self.db = db_connection

    def get_all_parts(self, search=None, low_stock_only=False, category=None):
        q = "SELECT * FROM parts WHERE is_active = TRUE"
        params = []
        if search:
            q += " AND part_name LIKE %s"
            params.append(f"%{search}%")
        if category:
            q += " AND category = %s"
            params.append(category)
        q += " ORDER BY part_name"
        results = self.db.execute_query(q, tuple(params) if params else None, fetch_all=True) or []
        if low_stock_only:
            results = [p for p in results if (p.get('stock_quantity', 0) or 0) <= (p.get('stock_alert_level', 5) or 5)]
        return results

    def get_part_by_id(self, part_id):
        return self.db.execute_query("SELECT * FROM parts WHERE id=%s AND is_active=TRUE", (part_id,), fetch_one=True)

    def add_part(self, data):
        return self.db.execute_query("""
            INSERT INTO parts (part_name, default_rate, description, category, stock_quantity, stock_alert_level, unit, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
        """, (data['name'], data['rate'], data.get('description', ''), data.get('category', 'General'),
              data.get('stock_qty', 0), data.get('alert_level', 5), data.get('unit', 'pcs')))

    def update_part(self, part_id, data):
        self.db.execute_query("""
            UPDATE parts SET part_name=%s, default_rate=%s, description=%s, category=%s,
                stock_quantity=%s, stock_alert_level=%s, unit=%s, updated_at=NOW()
            WHERE id=%s
        """, (data['name'], data['rate'], data.get('description', ''), data.get('category', 'General'),
              data.get('stock_qty', 0), data.get('alert_level', 5), data.get('unit', 'pcs'), part_id))

    def delete_part(self, part_id):
        self.db.execute_query("UPDATE parts SET is_active=FALSE WHERE id=%s", (part_id,))

    def adjust_stock(self, part_id, quantity_change, reason=''):
        current = self.db.execute_query("SELECT stock_quantity FROM parts WHERE id=%s", (part_id,), fetch_one=True)
        if current:
            old_qty = current['stock_quantity'] or 0
            new_qty = old_qty + quantity_change
            if new_qty < 0:
                new_qty = 0
            self.db.execute_query("UPDATE parts SET stock_quantity=%s, updated_at=NOW() WHERE id=%s", (new_qty, part_id))
            self.db.execute_query("""
                INSERT INTO stock_movements (part_id, quantity_change, old_quantity, new_quantity, reason, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (part_id, quantity_change, old_qty, new_qty, reason))

    def get_stock_movements(self, part_id=None, limit=100, days=None):
        q = """
            SELECT sm.*, p.part_name, p.stock_alert_level
            FROM stock_movements sm
            JOIN parts p ON sm.part_id = p.id
            WHERE p.is_active = TRUE
        """
        params = []
        if part_id:
            q += " AND sm.part_id = %s"
            params.append(part_id)
        if days:
            q += " AND sm.created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)"
            params.append(days)
        q += " ORDER BY sm.created_at DESC LIMIT %s"
        params.append(limit)
        return self.db.execute_query(q, tuple(params), fetch_all=True) or []

    def get_low_stock_parts(self):
        return self.db.execute_query("""
            SELECT * FROM parts WHERE is_active = TRUE
            AND stock_quantity <= stock_alert_level
            ORDER BY (stock_quantity * 1.0 / NULLIF(stock_alert_level, 0)) ASC, stock_quantity ASC
        """, fetch_all=True) or []

    def get_stock_summary(self):
        total = self.db.execute_query("SELECT COUNT(*) as count FROM parts WHERE is_active=TRUE", fetch_one=True)
        low = self.get_low_stock_parts()
        total_qty = self.db.execute_query("SELECT COALESCE(SUM(stock_quantity),0) as qty FROM parts WHERE is_active=TRUE", fetch_one=True)
        stock_value = self.db.execute_query("SELECT COALESCE(SUM(stock_quantity * default_rate),0) as value FROM parts WHERE is_active=TRUE", fetch_one=True)
        
        # Dynamic categories
        categories = self.db.execute_query("""
            SELECT category, COUNT(*) as count 
            FROM parts 
            WHERE is_active = TRUE AND category IS NOT NULL 
            GROUP BY category
            ORDER BY count DESC
        """, fetch_all=True) or []
        
        return {
            'total_parts': total['count'] if total else 0,
            'low_stock': len(low),
            'low_stock_parts': low,
            'total_quantity': int(total_qty['qty']) if total_qty and total_qty['qty'] else 0,
            'stock_value': float(stock_value['value'] or 0) if stock_value else 0,
            'categories': categories,
        }

    def get_categories(self):
        """Get unique categories list from DB"""
        results = self.db.execute_query("SELECT DISTINCT category FROM parts WHERE is_active=TRUE AND category IS NOT NULL", fetch_all=True)
        return [r['category'] for r in results] if results else []

    def get_reorder_suggestions(self):
        return self.db.execute_query("""
            SELECT id, part_name, stock_quantity, stock_alert_level,
                   default_rate, (stock_alert_level - stock_quantity) as suggested_order_qty,
                   (stock_alert_level - stock_quantity) * default_rate as estimated_cost
            FROM parts WHERE is_active=TRUE
            AND stock_quantity < stock_alert_level
            ORDER BY estimated_cost DESC
        """, fetch_all=True) or []
