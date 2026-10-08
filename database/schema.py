"""
SQLite Schema - Auto-creates all tables on first run
"""
def get_all_tables_sql():
    return [
        # ── USERS ──────────────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL DEFAULT '',
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            role TEXT DEFAULT 'admin',
            is_active INTEGER DEFAULT 1,
            failed_attempts INTEGER DEFAULT 0,
            locked_until TEXT,
            last_login TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        )""",

        # ── CUSTOMERS ───────────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            email TEXT DEFAULT '',
            address TEXT DEFAULT '',
            landmark TEXT DEFAULT '',
            city TEXT DEFAULT '',
            pincode TEXT DEFAULT '',
            customer_type TEXT DEFAULT 'Regular',
            notes TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        )""",

        # ── INVOICES ────────────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT NOT NULL,
            customer_id INTEGER NOT NULL,
            ac_brand_id INTEGER,
            ac_type TEXT DEFAULT '',
            star_rating TEXT DEFAULT 'N/A',
            ton_capacity TEXT DEFAULT '',
            ac_inverter TEXT DEFAULT 'No',
            technician_id INTEGER,
            subtotal REAL DEFAULT 0,
            gst_percentage REAL DEFAULT 18,
            gst_amount REAL DEFAULT 0,
            discount_type TEXT DEFAULT 'percent',
            discount_value REAL DEFAULT 0,
            discount_amount REAL DEFAULT 0,
            total_amount REAL DEFAULT 0,
            advance_payment REAL DEFAULT 0,
            balance_amount REAL DEFAULT 0,
            payment_mode TEXT DEFAULT 'Cash',
            payment_status TEXT DEFAULT 'Pending',
            notes TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            service_date TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )""",

        # ── INVOICE ITEMS ───────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            item_type TEXT NOT NULL,
            service_id INTEGER,
            part_id INTEGER,
            description TEXT DEFAULT '',
            quantity INTEGER DEFAULT 1,
            rate REAL DEFAULT 0,
            amount REAL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
        )""",

        # ── PAYMENTS ──────────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            amount REAL DEFAULT 0,
            payment_mode TEXT DEFAULT 'Cash',
            payment_date TEXT NOT NULL,
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
        )""",

        # ── SERVICES ────────────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_name TEXT NOT NULL,
            description TEXT DEFAULT '',
            default_rate REAL DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )""",

        # ── PARTS (INVENTORY) ──────────────────────────────────
        """CREATE TABLE IF NOT EXISTS parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_name TEXT NOT NULL,
            description TEXT DEFAULT '',
            default_rate REAL DEFAULT 0,
            stock_quantity INTEGER DEFAULT 0,
            stock_alert_level INTEGER DEFAULT 5,
            unit TEXT DEFAULT 'pcs',
            category TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        )""",

        # ── AC BRANDS ───────────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS ac_brands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_name TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )""",

        # ── TECHNICIANS ─────────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS technicians (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            email TEXT DEFAULT '',
            address TEXT DEFAULT '',
            specialization TEXT DEFAULT '',
            commission_rate REAL DEFAULT 10,
            territory TEXT DEFAULT '',
            availability_status TEXT DEFAULT 'Available',
            joining_date TEXT,
            emergency_contact TEXT DEFAULT '',
            photo TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        )""",

        # ── TECHNICIAN WORK ────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS technician_work (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            technician_id INTEGER NOT NULL,
            invoice_id INTEGER NOT NULL,
            work_date TEXT NOT NULL,
            service_type TEXT DEFAULT '',
            amount_collected REAL DEFAULT 0,
            pending_amount REAL DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (technician_id) REFERENCES technicians(id),
            FOREIGN KEY (invoice_id) REFERENCES invoices(id)
        )""",

        # ── TECHNICIAN ATTENDANCE ──────────────────────────────
        """CREATE TABLE IF NOT EXISTS technician_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            technician_id INTEGER NOT NULL,
            attendance_date TEXT NOT NULL,
            status TEXT DEFAULT 'Present',
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (technician_id) REFERENCES technicians(id)
        )""",

        # ── AMC CONTRACTS ──────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS amc_contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amc_id TEXT NOT NULL UNIQUE,
            customer_id INTEGER NOT NULL,
            contract_type TEXT DEFAULT 'Comprehensive',
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            no_of_units INTEGER DEFAULT 1,
            services_per_year INTEGER DEFAULT 2,
            services_remaining INTEGER DEFAULT 2,
            contract_amount REAL DEFAULT 0,
            gst_percent REAL DEFAULT 18,
            total_amount REAL DEFAULT 0,
            advance_paid REAL DEFAULT 0,
            balance_amount REAL DEFAULT 0,
            payment_mode TEXT DEFAULT 'Pending',
            payment_status TEXT DEFAULT 'Pending',
            next_due_date TEXT,
            amc_status TEXT DEFAULT 'Active',
            grace_period INTEGER DEFAULT 7,
            renewal_reminder_date TEXT,
            notes TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )""",

        # ── AMC UNITS ──────────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS amc_units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amc_id INTEGER NOT NULL,
            brand TEXT DEFAULT 'Unknown',
            ac_type TEXT DEFAULT 'Split',
            ton TEXT DEFAULT '1.0',
            star_rating TEXT DEFAULT 'N/A',
            inverter TEXT DEFAULT 'Not Specified',
            model TEXT DEFAULT '',
            serial_number TEXT DEFAULT '',
            indoor_location TEXT DEFAULT '',
            outdoor_location TEXT DEFAULT '',
            installation_date TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (amc_id) REFERENCES amc_contracts(id) ON DELETE CASCADE
        )""",

        # ── AMC VISITS ─────────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS amc_visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amc_id INTEGER NOT NULL,
            visit_number INTEGER DEFAULT 1,
            visit_date TEXT NOT NULL,
            technician_id INTEGER,
            work_done TEXT DEFAULT '',
            parts_replaced TEXT DEFAULT '',
            extra_charge REAL DEFAULT 0,
            next_due_date TEXT,
            visit_status TEXT DEFAULT 'Scheduled',
            notes TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (amc_id) REFERENCES amc_contracts(id) ON DELETE CASCADE
        )""",

        # ── AMC INVOICES ──────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS amc_invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amc_contract_id INTEGER NOT NULL,
            invoice_number TEXT NOT NULL UNIQUE,
            invoice_date TEXT NOT NULL,
            subtotal REAL DEFAULT 0,
            gst_percent REAL DEFAULT 18,
            gst_amount REAL DEFAULT 0,
            total_amount REAL DEFAULT 0,
            advance_payment REAL DEFAULT 0,
            balance_amount REAL DEFAULT 0,
            payment_mode TEXT DEFAULT 'Pending',
            payment_status TEXT DEFAULT 'Pending',
            notes TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (amc_contract_id) REFERENCES amc_contracts(id) ON DELETE CASCADE
        )""",

        # ── DAILY WORK & COST LOGS ─────────────────────────────
        """CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            customer_mobile TEXT DEFAULT '',
            customer_address TEXT DEFAULT '',
            customer_id INTEGER,
            technician_id INTEGER,
            technician_name TEXT DEFAULT '',
            work_description TEXT DEFAULT '',
            total_billed REAL DEFAULT 0,
            advance_payment REAL DEFAULT 0,
            advance_receiver TEXT DEFAULT 'Tech (Cash)',
            final_payment REAL DEFAULT 0,
            final_receiver TEXT DEFAULT 'Tech (Cash)',
            total_payment REAL DEFAULT 0,
            pending_amount REAL DEFAULT 0,
            material_cost REAL DEFAULT 0,
            petrol_expense REAL DEFAULT 0,
            total_expense REAL DEFAULT 0,
            payment_status TEXT DEFAULT 'Paid',
            payment_mode TEXT DEFAULT 'Cash',
            net_profit REAL DEFAULT 0,
            notes TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (technician_id) REFERENCES technicians(id)
        )""",

        # ── VISITOR LOG ────────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS visitor_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_date TEXT NOT NULL,
            name TEXT NOT NULL,
            mobile TEXT DEFAULT '',
            purpose TEXT DEFAULT '',
            whom_to_meet TEXT DEFAULT '',
            in_time TEXT,
            out_time TEXT,
            notes TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )""",

        # ── SHOP DETAILS ───────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS shop_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_name TEXT DEFAULT '',
            owner_name TEXT DEFAULT '',
            owner_phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            email TEXT DEFAULT '',
            tagline TEXT DEFAULT 'AC SALES & SERVICE MANAGEMENT',
            services TEXT DEFAULT 'Sales | Installation | AMC | Repairing | Gas Refilling',
            gst_number TEXT DEFAULT '',
            logo_path TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )""",

        # ── APP SETTINGS ───────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS app_settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT NOT NULL,
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        )""",

        # ── PAYMENT MODES ─────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS payment_modes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mode_name TEXT NOT NULL UNIQUE,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )""",

        # ── WHATSAPP TEMPLATES ─────────────────────────────────
        """CREATE TABLE IF NOT EXISTS whatsapp_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_key TEXT NOT NULL UNIQUE,
            template_body TEXT NOT NULL,
            description TEXT DEFAULT '',
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        )""",

        # ── AC TYPES ──────────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS ac_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_name TEXT NOT NULL UNIQUE,
            is_active INTEGER DEFAULT 1
        )""",

        # ── AC CAPACITIES ─────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS ac_capacities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            capacity_value TEXT NOT NULL UNIQUE,
            is_active INTEGER DEFAULT 1
        )""",

        # ── AC STARS ──────────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS ac_stars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            star_label TEXT NOT NULL UNIQUE,
            is_active INTEGER DEFAULT 1
        )""",

        # ── INVENTORY UNITS ───────────────────────────────────
        """CREATE TABLE IF NOT EXISTS inventory_units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_name TEXT NOT NULL UNIQUE,
            is_active INTEGER DEFAULT 1
        )""",

        # ── TECHNICIAN STATUSES ───────────────────────────────
        """CREATE TABLE IF NOT EXISTS technician_statuses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status_name TEXT NOT NULL UNIQUE,
            is_active INTEGER DEFAULT 1
        )""",

        # ── STOCK MOVEMENTS ───────────────────────────────────
        """CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_id INTEGER NOT NULL,
            quantity_change INTEGER DEFAULT 0,
            new_quantity INTEGER DEFAULT 0,
            old_quantity INTEGER DEFAULT 0,
            reason TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (part_id) REFERENCES parts(id) ON DELETE CASCADE
        )""",

        # ── AUDIT LOG ─────────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT DEFAULT '',
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER,
            details TEXT DEFAULT '',
            ip_address TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )""",

        # ── SOFTWARE SCHEMA ──────────────────────────────────
        """CREATE TABLE IF NOT EXISTS software_schema (
            table_name TEXT PRIMARY KEY,
            category TEXT DEFAULT 'software',
            description TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )""",

        # ── CONTACT MESSAGES (Online Requests) ────────────────
        """CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT DEFAULT '',
            message TEXT DEFAULT '',
            service_type TEXT DEFAULT '',
            preferred_date TEXT,
            time_slot TEXT DEFAULT '',
            address TEXT DEFAULT '',
            status TEXT DEFAULT 'unread',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )""",

        # ── SERVICE REQUESTS (Website Inquiries) ──────────────
        """CREATE TABLE IF NOT EXISTS service_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            customer_email TEXT DEFAULT '',
            service_type TEXT DEFAULT '',
            message TEXT DEFAULT '',
            request_status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )""",
    ]


import secrets

import bcrypt


def create_initial_admin(cursor):
    """Create the first admin user with a random one-time password (only if no users exist)."""
    cursor.execute("SELECT COUNT(*) FROM users")
    row = cursor.fetchone()
    if row and row[0]:
        return
    initial_password = secrets.token_urlsafe(12)
    password_hash = bcrypt.hashpw(initial_password.encode(), bcrypt.gensalt()).decode()
    cursor.execute(
        "INSERT OR IGNORE INTO users (id, username, password_hash, full_name, email, phone, role, is_active) "
        "VALUES (1, 'admin', ?, 'Administrator', '', '', 'admin', 1)",
        (password_hash,),
    )
    print("=" * 60)
    print("FIRST RUN: initial admin password (shown once, change it in Settings):")
    print(f"  username: admin   password: {initial_password}")
    print("=" * 60)


def get_seed_data_sql():
    return [
        # Default shop details
        """INSERT OR IGNORE INTO shop_details (id, shop_name, owner_name, address, phone, email, gst_number)
        VALUES (1, 'Ansh Air Cool', 'Owner', 'Your Address', '', 'shop@email.com', '')""",

        # Default payment modes
        """INSERT OR IGNORE INTO payment_modes (mode_name) VALUES ('Cash')""",
        """INSERT OR IGNORE INTO payment_modes (mode_name) VALUES ('Card')""",
        """INSERT OR IGNORE INTO payment_modes (mode_name) VALUES ('UPI')""",
        """INSERT OR IGNORE INTO payment_modes (mode_name) VALUES ('Bank Transfer')""",
        """INSERT OR IGNORE INTO payment_modes (mode_name) VALUES ('Pending')""",

        # AC types
        """INSERT OR IGNORE INTO ac_types (type_name) VALUES ('Split')""",
        """INSERT OR IGNORE INTO ac_types (type_name) VALUES ('Window')""",
        """INSERT OR IGNORE INTO ac_types (type_name) VALUES ('Cassette')""",
        """INSERT OR IGNORE INTO ac_types (type_name) VALUES ('Tower')""",
        """INSERT OR IGNORE INTO ac_types (type_name) VALUES ('Other')""",

        # AC capacities
        """INSERT OR IGNORE INTO ac_capacities (capacity_value) VALUES ('0.75')""",
        """INSERT OR IGNORE INTO ac_capacities (capacity_value) VALUES ('1.0')""",
        """INSERT OR IGNORE INTO ac_capacities (capacity_value) VALUES ('1.5')""",
        """INSERT OR IGNORE INTO ac_capacities (capacity_value) VALUES ('2.0')""",
        """INSERT OR IGNORE INTO ac_capacities (capacity_value) VALUES ('2.5')""",
        """INSERT OR IGNORE INTO ac_capacities (capacity_value) VALUES ('3.0')""",
        """INSERT OR IGNORE INTO ac_capacities (capacity_value) VALUES ('4.0')""",
        """INSERT OR IGNORE INTO ac_capacities (capacity_value) VALUES ('5.0')""",

        # AC stars
        """INSERT OR IGNORE INTO ac_stars (star_label) VALUES ('1 Star')""",
        """INSERT OR IGNORE INTO ac_stars (star_label) VALUES ('2 Star')""",
        """INSERT OR IGNORE INTO ac_stars (star_label) VALUES ('3 Star')""",
        """INSERT OR IGNORE INTO ac_stars (star_label) VALUES ('4 Star')""",
        """INSERT OR IGNORE INTO ac_stars (star_label) VALUES ('5 Star')""",
        """INSERT OR IGNORE INTO ac_stars (star_label) VALUES ('Inverter')""",
        """INSERT OR IGNORE INTO ac_stars (star_label) VALUES ('Non-Inverter')""",

        # Inventory units
        """INSERT OR IGNORE INTO inventory_units (unit_name) VALUES ('pcs')""",
        """INSERT OR IGNORE INTO inventory_units (unit_name) VALUES ('units')""",
        """INSERT OR IGNORE INTO inventory_units (unit_name) VALUES ('kg')""",
        """INSERT OR IGNORE INTO inventory_units (unit_name) VALUES ('litre')""",
        """INSERT OR IGNORE INTO inventory_units (unit_name) VALUES ('meter')""",
        """INSERT OR IGNORE INTO inventory_units (unit_name) VALUES ('set')""",
        """INSERT OR IGNORE INTO inventory_units (unit_name) VALUES ('box')""",

        # Technician statuses
        """INSERT OR IGNORE INTO technician_statuses (status_name) VALUES ('Available')""",
        """INSERT OR IGNORE INTO technician_statuses (status_name) VALUES ('Busy')""",
        """INSERT OR IGNORE INTO technician_statuses (status_name) VALUES ('On Leave')""",
        """INSERT OR IGNORE INTO technician_statuses (status_name) VALUES ('Off Duty')""",

        # WhatsApp templates
        """INSERT OR IGNORE INTO whatsapp_templates (template_key, template_body) VALUES ('service_confirm', '✅ *Service Request Confirmed*\n\nNamaste {name}!\n\nAapka service request humne receive kar liya hai.\n\n🔧 Service: {service_type}\n📍 Location: {location}\n\nHamara technician aapse jald contact karega.\n\nDhanyavaad! 🙏\n*{company_name}*')""",
        """INSERT OR IGNORE INTO whatsapp_templates (template_key, template_body) VALUES ('payment_reminder', '💳 *Payment Reminder*\n\nNamaste {name},\n\nAapka payment abhi tak pending hai.\n\n📄 Invoice: {invoice_number}\n💰 Amount: ₹{amount}\n\nPlease payment clear karein.\n\nDhanyavaad! 🙏\n*{company_name}*')""",
        """INSERT OR IGNORE INTO whatsapp_templates (template_key, template_body) VALUES ('thank_you', '🌟 *Thank You!*\n\nNamaste {name},\n\nHumara service use karne ke liye dhanyavaad!\n\nAapki feedback humare liye important hai.\n\n*{company_name}*')""",
    ]


def get_all_indexes_sql():
    """Return CREATE INDEX statements for all foreign key and filter columns.
    Run AFTER tables exist (existing databases apply via migration script)."""
    return [
        # ── CUSTOMERS ───────────────────────────────────────────
        "CREATE INDEX IF NOT EXISTS idx_customers_mobile ON customers(mobile)",
        "CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name)",
        "CREATE INDEX IF NOT EXISTS idx_customers_active ON customers(is_active)",

        # ── INVOICES (High frequency queries) ───────────────────
        "CREATE INDEX IF NOT EXISTS idx_invoices_customer_id ON invoices(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_invoices_technician_id ON invoices(technician_id)",
        "CREATE INDEX IF NOT EXISTS idx_invoices_invoice_number ON invoices(invoice_number)",
        "CREATE INDEX IF NOT EXISTS idx_invoices_created_at ON invoices(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_invoices_payment_status ON invoices(payment_status)",
        "CREATE INDEX IF NOT EXISTS idx_invoices_active_created ON invoices(is_active, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_invoices_customer_active ON invoices(customer_id, is_active)",

        # ── INVOICE ITEMS ─────────────────────────────────────────
        "CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice_id ON invoice_items(invoice_id)",
        "CREATE INDEX IF NOT EXISTS idx_invoice_items_service_id ON invoice_items(service_id)",
        "CREATE INDEX IF NOT EXISTS idx_invoice_items_part_id ON invoice_items(part_id)",

        # ── SERVICES & PARTS ──────────────────────────────────────
        "CREATE INDEX IF NOT EXISTS idx_services_name ON services(service_name)",
        "CREATE INDEX IF NOT EXISTS idx_parts_name ON parts(part_name)",

        # ── TECHNICIANS ───────────────────────────────────────────
        "CREATE INDEX IF NOT EXISTS idx_technicians_mobile ON technicians(mobile)",
        "CREATE INDEX IF NOT EXISTS idx_technicians_active ON technicians(is_active)",

        # ── PAYMENTS ──────────────────────────────────────────────
        "CREATE INDEX IF NOT EXISTS idx_payments_invoice_id ON payments(invoice_id)",

        # ── AMC CONTRACTS ─────────────────────────────────────────
        "CREATE INDEX IF NOT EXISTS idx_amc_contracts_customer_id ON amc_contracts(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_amc_contracts_end_date ON amc_contracts(end_date)",
        "CREATE INDEX IF NOT EXISTS idx_amc_contracts_active_end ON amc_contracts(is_active, end_date)",

        # ── AMC UNITS ─────────────────────────────────────────────
        "CREATE INDEX IF NOT EXISTS idx_amc_units_amc_id ON amc_units(amc_id)",

        # ── AMC VISITS ────────────────────────────────────────────
        "CREATE INDEX IF NOT EXISTS idx_amc_visits_amc_id ON amc_visits(amc_id)",

        # ── AMC INVOICES ──────────────────────────────────────────
        "CREATE INDEX IF NOT EXISTS idx_amc_invoices_contract_id ON amc_invoices(amc_contract_id)",

        # ── TECHNICIAN WORK ───────────────────────────────────────
        "CREATE INDEX IF NOT EXISTS idx_technician_work_technician_id ON technician_work(technician_id)",
        "CREATE INDEX IF NOT EXISTS idx_technician_work_invoice_id ON technician_work(invoice_id)",

        # ── TECHNICIAN ATTENDANCE ─────────────────────────────────
        "CREATE INDEX IF NOT EXISTS idx_technician_attendance_technician_id ON technician_attendance(technician_id)",

        # ── STOCK MOVEMENTS ───────────────────────────────────────
        "CREATE INDEX IF NOT EXISTS idx_stock_movements_part_id ON stock_movements(part_id)",

        # ── AUDIT LOG ─────────────────────────────────────────────
        "CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id)",

        # ── CONTACT MESSAGES ──────────────────────────────────────
        "CREATE INDEX IF NOT EXISTS idx_contact_messages_status ON contact_messages(status)",

        # ── DAILY LOGS ────────────────────────────────────────────
        "CREATE INDEX IF NOT EXISTS idx_daily_logs_date ON daily_logs(log_date)",
        "CREATE INDEX IF NOT EXISTS idx_daily_logs_tech ON daily_logs(technician_id)",
        "CREATE INDEX IF NOT EXISTS idx_daily_logs_active_date ON daily_logs(is_active, log_date DESC)",

        # ── SERVICE REQUESTS ──────────────────────────────────────
        "CREATE INDEX IF NOT EXISTS idx_service_requests_status ON service_requests(request_status)",
    ]
