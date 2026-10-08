"""Seed a clearly fake demo dataset (fake names, 90000xxxxx mobiles) for screenshots and testing."""
import os
import random
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_connection import DatabaseConnection  # noqa: E402

random.seed(7)
FIRST = ["Aarav", "Diya", "Kabir", "Meera", "Rohan", "Isha", "Arjun", "Nisha", "Vihaan", "Tara", "Dev", "Anaya"]
LAST = ["Demo", "Sample", "Test"]
CITIES = ["Mumbai", "Navi Mumbai", "Thane"]


def main(n_customers=40, n_invoices=70):
    db = DatabaseConnection()
    conn = db.connection if hasattr(db, "connection") else db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM customers")
    if cur.fetchone()[0]:
        print("customers already present, skipping")
        return
    for i in range(1, n_customers + 1):
        name = f"{random.choice(FIRST)} {random.choice(LAST)} {i:02d}"
        cur.execute("INSERT INTO customers (name, mobile, address, city) VALUES (?,?,?,?)",
                    (name, f"90000{i:05d}", f"Demo Address {i}", random.choice(CITIES)))
    cur.execute("INSERT INTO technicians (name, mobile, specialization) VALUES ('Demo Technician A','9000099991','Split AC')")
    cur.execute("INSERT INTO technicians (name, mobile, specialization) VALUES ('Demo Technician B','9000099992','Window AC')")
    items = [("Gas Refill", 2200), ("General Service", 600), ("Deep Cleaning", 1200), ("Installation", 1800), ("PCB Repair", 2500)]
    today = date.today()
    for k in range(1, n_invoices + 1):
        cid = random.randint(1, n_customers)
        d = today - timedelta(days=random.randint(0, 120))
        its = random.sample(items, random.randint(1, 3))
        sub = float(sum(r for _, r in its))
        total = sub
        paid = random.choice([total, total, total * 0.5, 0])
        status = "Paid" if paid >= total else ("Partial" if paid else "Pending")
        cur.execute("""INSERT INTO invoices (invoice_number, customer_id, subtotal, gst_percentage, gst_amount,
                       total_amount, advance_payment, balance_amount, payment_mode, payment_status, service_date, technician_id)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (f"INV-{1000 + k}", cid, sub, 0, 0, total, paid, total - paid,
                     random.choice(["Cash", "UPI"]), status, d.isoformat(), random.choice([1, 2])))
        iid = cur.lastrowid
        for desc, rate in its:
            cur.execute("INSERT INTO invoice_items (invoice_id, item_type, description, quantity, rate, amount) VALUES (?,?,?,?,?,?)",
                        (iid, "service", desc, 1, rate, rate))
    for j in range(1, 9):
        s = today - timedelta(days=random.randint(10, 300))
        cur.execute("""INSERT INTO amc_contracts (amc_id, customer_id, start_date, end_date, no_of_units, contract_amount,
                       total_amount, payment_status, next_due_date, amc_status) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (f"AMC-{100 + j}", j, s.isoformat(), (s + timedelta(days=365)).isoformat(), random.randint(1, 3),
                     4000, 4000, "Paid", (today + timedelta(days=random.randint(5, 90))).isoformat(), "Active"))
    parts = [("Copper Pipe 1/4 inch (per m)", "Pipes", 450, 38, 10), ("Gas R32 (kg)", "Gas", 2500, 6, 8),
             ("Gas R410A (kg)", "Gas", 2800, 12, 8), ("Capacitor 35uF", "Electrical", 450, 4, 10),
             ("Drain Pipe 5m", "Pipes", 150, 25, 10), ("Wall Bracket Pair", "Hardware", 350, 18, 6),
             ("Remote Universal", "Electrical", 280, 3, 8), ("Contactor 3-pole", "Electrical", 950, 9, 5),
             ("Insulation Tape", "Consumables", 40, 60, 20), ("PCB Universal Split", "Electrical", 2200, 2, 4)]
    for name, cat, rate, qty, alert in parts:
        cur.execute("INSERT INTO parts (part_name, category, default_rate, stock_quantity, stock_alert_level) VALUES (?,?,?,?,?)",
                    (name, cat, rate, qty, alert))
    conn.commit()
    from scripts.seed_1000_daily_logs import seed_daily_logs  # fake names; mobiles are replaced below
    seed_daily_logs(70)
    conn = db.connection if hasattr(db, "connection") else db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM daily_logs")
    for n, (log_id,) in enumerate(cur.fetchall(), 1):
        conn.execute("UPDATE daily_logs SET customer_mobile=? WHERE id=?", (f"90001{n:05d}", log_id))
        conn.execute("UPDATE daily_logs SET customer_name=?, customer_address=? WHERE id=?",
                     (f"Demo Site {n:02d}", f"Demo Address {n:02d}, Sample City", log_id))
    conn.commit()
    print("Demo data seeded (fake names, 90000xxxxx mobiles).")


if __name__ == "__main__":
    main()
