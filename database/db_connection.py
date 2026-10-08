"""
SQLite Database Connection - No server required, no installation
Auto-creates all tables on first run, auto-converts MySQL SQL to SQLite
"""
import sqlite3
import threading
import time
import re
import functools
import datetime
from typing import Optional, Any, Dict, List, Union
from pathlib import Path

from config import DB_CONFIG, DATABASE_NAME

try:
    from utils.logger import get_loggers
    loggers = get_loggers()
    logger = loggers['app']
    db_logger = loggers['database']
    error_logger = loggers['error']
except Exception:
    import logging
    logger = logging.getLogger(__name__)
    db_logger = logger
    error_logger = logger


class DatabaseConnection:
    _instance: Optional['DatabaseConnection'] = None
    _lock = threading.Lock()
    _query_lock = threading.Lock()

    def __new__(cls) -> 'DatabaseConnection':
        with cls._lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance._initialized = False
                try:
                    instance._initialize_connection()
                    instance._initialized = True
                except Exception as e:
                    logger.error(f"Initial DB connection failed: {e}")
                    raise
                cls._instance = instance
        return cls._instance

    def _initialize_connection(self) -> None:
        db_path = DB_CONFIG['database']
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self._connection = sqlite3.connect(
            db_path,
            timeout=DB_CONFIG.get('timeout', 30),
            check_same_thread=DB_CONFIG.get('check_same_thread', False)
        )
        self._connection.row_factory = sqlite3.Row
        self._transaction_active = False
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=NORMAL")
        self._connection.execute("PRAGMA foreign_keys=ON")
        self._connection.execute("PRAGMA busy_timeout=5000")
        self._connection.execute("PRAGMA wal_autocheckpoint=1000")
        self._connection.execute("PRAGMA cache_size=-64000")
        self._connection.execute("PRAGMA temp_store=MEMORY")
        self._connection.execute("PRAGMA mmap_size=268435456")
        self._connection.execute("PRAGMA threads=4")

        # Register MySQL-compatible custom functions for SQLite
        self._connection.create_function("SUBSTRING_INDEX", 3, _substring_index)

        # Create cursor
        self._cursor = self._connection.cursor()

        # Database integrity check — log result but don't block startup on corruption
        try:
            integrity_result = self._cursor.execute("PRAGMA quick_check").fetchone()
            if integrity_result and integrity_result[0] != 'ok':
                error_logger.error(f"Database integrity check FAILED: {integrity_result[0]}")
                error_logger.error("Database may be corrupted. Recommend restoring from backup.")
        except Exception as integrity_err:
            error_logger.warning(f"Integrity check skipped: {integrity_err}")

        logger.info(f"Database connected: {db_path}")
        self._run_migrations()

    @staticmethod
    @functools.lru_cache(maxsize=1024)
    def _mysql_to_sqlite(sql: str) -> str:
        """Convert MySQL-compatible SQL to SQLite syntax (Cached with LRU)"""
        sql = sql.replace('%s', '?')

        # ═══ 1. SPECIFIC PATTERNS (must match before general replacements) ═══

        # MONTH(CURDATE()) / YEAR(CURDATE()) → must match before CURDATE()→date('now')
        sql = re.sub(
            r'MONTH\(CURDATE\(\)\)',
            "CAST(strftime('%m', 'now') AS INTEGER)",
            sql, flags=re.IGNORECASE
        )
        sql = re.sub(
            r'YEAR\(CURDATE\(\)\)',
            "CAST(strftime('%Y', 'now') AS INTEGER)",
            sql, flags=re.IGNORECASE
        )
        sql = re.sub(
            r"MONTH\(DATE_SUB\(CURDATE\(\),\s*INTERVAL\s+(\d+)\s+MONTH\)\)",
            lambda m: f"CAST(strftime('%m', date('now', '-{m.group(1)} months')) AS INTEGER)",
            sql, flags=re.IGNORECASE
        )
        sql = re.sub(
            r"YEAR\(DATE_SUB\(CURDATE\(\),\s*INTERVAL\s+(\d+)\s+MONTH\)\)",
            lambda m: f"CAST(strftime('%Y', date('now', '-{m.group(1)} months')) AS INTEGER)",
            sql, flags=re.IGNORECASE
        )

        # ═══ 2. SCALAR FUNCTIONS (must run BEFORE CURDATE/NOW replacement) ═══

        sql = re.sub(
            r'DATEDIFF\(([^,]+),\s*([^)]+)\)',
            r"CAST((julianday(\1) - julianday(\2)) AS INTEGER)",
            sql, flags=re.IGNORECASE
        )

        # DATE_ADD/DATE_SUB with literal interval
        sql = re.sub(
            r"DATE_ADD\(([^,]+),\s*INTERVAL\s+(\d+)\s+(DAY|MONTH)\)",
            lambda m: f"date({m.group(1)}, '+{m.group(2)} {m.group(3).lower()}s')",
            sql, flags=re.IGNORECASE
        )
        sql = re.sub(
            r"DATE_SUB\(([^,]+),\s*INTERVAL\s+(\d+)\s+(DAY|MONTH)\)",
            lambda m: f"date({m.group(1)}, '-{m.group(2)} {m.group(3).lower()}s')",
            sql, flags=re.IGNORECASE
        )

        # DATE_ADD/DATE_SUB with ? param interval
        sql = re.sub(
            r"DATE_ADD\(([^,]+),\s*INTERVAL\s+\?\s+(DAY|MONTH)\)",
            lambda m: f"date({m.group(1)}, '+' || CAST(? AS TEXT) || ' {m.group(2).lower()}s')",
            sql, flags=re.IGNORECASE
        )
        sql = re.sub(
            r"DATE_SUB\(([^,]+),\s*INTERVAL\s+\?\s+(DAY|MONTH)\)",
            lambda m: f"date({m.group(1)}, '-' || CAST(? AS TEXT) || ' {m.group(2).lower()}s')",
            sql, flags=re.IGNORECASE
        )

        # ═══ 3. FUNCTION REPLACEMENTS ═══

        sql = re.sub(r'(?<![A-Za-z_])CURDATE\(\)', "date('now')", sql, flags=re.IGNORECASE)
        sql = re.sub(r'(?<![A-Za-z_])NOW\(\)', "datetime('now','localtime')", sql, flags=re.IGNORECASE)
        sql = re.sub(r'(?<![A-Za-z_])LAST_INSERT_ID\(\)', 'last_insert_rowid()', sql, flags=re.IGNORECASE)

        # ═══ 4. SYNTAX CLEANUPS ═══

        sql = re.sub(r'\bFOR\s+UPDATE\b', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'ENGINE\s*=\s*\w+(\s+DEFAULT\s+CHARSET\s*=\s*\w+)?', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bBOOLEAN\b', 'INTEGER', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bAUTO_INCREMENT\b', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'CURRENT_TIMESTAMP', "datetime('now','localtime')", sql, flags=re.IGNORECASE)

        # CAST(... AS UNSIGNED) → CAST(... AS INTEGER)
        sql = re.sub(r'\bAS\s+UNSIGNED\b', 'AS INTEGER', sql, flags=re.IGNORECASE)

        # DATE_FORMAT(col, 'fmt') → strftime(fmt, col)
        # Must handle %% → % from Python string interpolation first
        def _replace_date_format(m):
            col = m.group(1).strip()
            fmt = m.group(2).strip()
            sqlite_fmt = fmt.replace('%%', '%')
            sqlite_fmt = sqlite_fmt.replace('%i', '%M').replace('%s', '%S')
            return f"strftime('{sqlite_fmt}', {col})"

        sql = re.sub(
            r"DATE_FORMAT\(([^,]+),\s*'([^']+)'\)",
            _replace_date_format,
            sql, flags=re.IGNORECASE
        )

        # General MONTH(col) / YEAR(col) for simple column references
        sql = re.sub(
            r"MONTH\(([a-zA-Z_][a-zA-Z0-9_.]*)\)",
            r"CAST(strftime('%m', \1) AS INTEGER)",
            sql, flags=re.IGNORECASE
        )
        sql = re.sub(
            r"YEAR\(([a-zA-Z_][a-zA-Z0-9_.]*)\)",
            r"CAST(strftime('%Y', \1) AS INTEGER)",
            sql, flags=re.IGNORECASE
        )

        # GROUP_CONCAT(DISTINCT col SEPARATOR '...') → GROUP_CONCAT(DISTINCT col)
        sql = re.sub(
            r"GROUP_CONCAT\(\s*DISTINCT\s+(.+?)\s+SEPARATOR\s+('[^']*')\s*\)",
            r"GROUP_CONCAT(DISTINCT \1)",
            sql, flags=re.IGNORECASE
        )
        # GROUP_CONCAT(col SEPARATOR '...') → GROUP_CONCAT(col, '...')
        sql = re.sub(
            r"GROUP_CONCAT\((.+?)\s+SEPARATOR\s+('[^']*')\s*\)",
            r"GROUP_CONCAT(\1, \2)",
            sql, flags=re.IGNORECASE
        )

        # CONCAT(a, b, c) → a || b || c
        def _replace_concat(m):
            inner = m.group(1)
            args = _split_top_level(inner)
            return ' || '.join(args)

        sql = re.sub(r'(?<!GROUP_)\bCONCAT\((.+?)\)', _replace_concat, sql, flags=re.IGNORECASE)

        return sql

    def _handle_upsert(self, sql: str, params: tuple) -> tuple:
        """Convert ON DUPLICATE KEY UPDATE to SQLite ON CONFLICT syntax"""
        sql_converted = sql.replace('%s', '?')
        # Use search (not match) so multi-line queries with leading
        # whitespace/indentation are converted correctly
        match = re.search(
            r'INSERT\s+INTO\s+(\w+)\s*(?:\((.+?)\))?\s*VALUES\s*\((.+?)\)\s+ON\s+DUPLICATE\s+KEY\s+UPDATE\s+(.+)',
            sql_converted, re.IGNORECASE | re.DOTALL
        )
        if not match:
            return self._mysql_to_sqlite(sql), params

        table = match.group(1)
        columns_str = match.group(2)
        values_str = match.group(3)
        update_str = match.group(4)

        columns = [c.strip() for c in columns_str.split(',')] if columns_str else []
        value_placeholders_raw = _split_top_level(values_str)
        value_placeholders = [v.strip() for v in value_placeholders_raw]

        insert_param_count = sum(1 for v in value_placeholders if v == '?')
        new_params = list(params[:insert_param_count])

        pk_col = columns[0] if columns else 'setting_key'

        set_parts = []
        update_assignments = _split_top_level(update_str)
        for assignment in update_assignments:
            assignment = assignment.strip()
            if not assignment:
                continue
            if '=' in assignment:
                eq_idx = assignment.index('=')
                col_name = assignment[:eq_idx].strip()
                val_expr = assignment[eq_idx+1:].strip()
                if val_expr.upper() == 'NOW()':
                    set_parts.append(f"{col_name} = datetime('now','localtime')")
                elif col_name in columns:
                    set_parts.append(f"{col_name} = excluded.{col_name}")
                else:
                    set_parts.append(assignment)

        new_values = []
        for v in value_placeholders:
            if v == '?':
                new_values.append('?')
            elif v.upper() == 'NOW()':
                new_values.append("datetime('now','localtime')")
            else:
                new_values.append(v)

        new_sql = (
            f"INSERT INTO {table} ({', '.join(columns)}) "
            f"VALUES ({', '.join(new_values)}) "
            f"ON CONFLICT({pk_col}) DO UPDATE SET {', '.join(set_parts)}"
        )
        return new_sql, tuple(new_params)

    def execute_query(
        self,
        query: str,
        params: Optional[Union[tuple, list]] = None,
        fetch_one: bool = False,
        fetch_all: bool = False
    ) -> Optional[Union[Dict, List[Dict], int]]:
        with self._query_lock:
            start_time = time.time()
            for attempt in range(3):
                try:
                    self._check_connection()

                    if not query or not isinstance(query, str):
                        raise ValueError("Query must be a non-empty string")

                    if 'ON DUPLICATE KEY UPDATE' in query.upper():
                        sqlite_query, sqlite_params = self._handle_upsert(query, params or ())
                    else:
                        sqlite_query = self._mysql_to_sqlite(query)
                        sqlite_params = params

                    if sqlite_params is None:
                        self._cursor.execute(sqlite_query)
                    else:
                        if not isinstance(sqlite_params, (tuple, list)):
                            sqlite_params = (sqlite_params,)
                        # Convert date/datetime objects to ISO strings to avoid Python 3.12+ sqlite3 adapter deprecation warning
                        sqlite_params = tuple(
                            p.isoformat() if isinstance(p, (datetime.date, datetime.datetime)) else p
                            for p in sqlite_params
                        )
                        self._cursor.execute(sqlite_query, sqlite_params)

                    is_write = sqlite_query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE'))

                    def _should_commit():
                        return not self._transaction_active

                    if fetch_one:
                        row = self._cursor.fetchone()
                        if is_write and _should_commit():
                            self._connection.commit()
                        duration = time.time() - start_time
                        db_logger.debug(f"Query in {duration:.3f}s")
                        return dict(row) if row else None

                    elif fetch_all:
                        rows = self._cursor.fetchall()
                        if is_write and _should_commit():
                            self._connection.commit()
                        duration = time.time() - start_time
                        db_logger.debug(f"Query in {duration:.3f}s, rows: {len(rows)}")
                        return [dict(r) for r in rows]

                    elif is_write:
                        if _should_commit():
                            self._connection.commit()
                        row_id = self._cursor.lastrowid
                        duration = time.time() - start_time
                        db_logger.info(f"Query in {duration:.3f}s, row_id: {row_id}")
                        return row_id

                    else:
                        return None

                except sqlite3.Error as e:
                    error_str = str(e)
                    if 'database is locked' in error_str.lower() and attempt < 2:
                        time.sleep(0.5 * (attempt + 1))
                        continue
                    error_logger.error(f"SQLite Error: {error_str}")
                    error_logger.error(f"Query: {query[:200]}")
                    self._connection.rollback()
                    raise
                except Exception as e:
                    error_logger.error(f"Query error: {e}", exc_info=True)
                    if not getattr(self._connection, 'in_transaction', False):
                        self._connection.rollback()
                    raise

            raise ConnectionError("Max retries exceeded for query")

    def execute_many(self, query: str, params_list: List[Union[tuple, list]]) -> int:
        with self._query_lock:
            try:
                if not params_list:
                    logger.warning("execute_many called with empty params_list")
                    return 0

                self._check_connection()
                sqlite_query = self._mysql_to_sqlite(query)

                db_logger.info(f"Batch query with {len(params_list)} param sets")
                self._cursor.executemany(sqlite_query, params_list)
                if not self._transaction_active:
                    self._connection.commit()

                rowcount = self._cursor.rowcount
                logger.info(f"Batch query done, affected rows: {rowcount}")
                return rowcount

            except sqlite3.Error as e:
                error_logger.error(f"SQLite batch error: {e}")
                self._connection.rollback()
                raise
            except Exception as e:
                error_logger.error(f"Batch query error: {e}", exc_info=True)
                self._connection.rollback()
                raise

    def _check_connection(self) -> bool:
        try:
            self._connection.execute("SELECT 1")
            return True
        except Exception as e:
            logger.warning(f"Connection issue: {e}, reconnecting...")
            try:
                self._connection.close()
            except Exception as close_err:
                logger.warning(f"Failed to close stale connection: {close_err}")
            self._initialize_connection()
            return True

    def _run_migrations(self) -> None:
        """Create all tables, indexes, and seed data — transactional, crash-safe"""
        from database.schema import get_all_tables_sql, get_all_indexes_sql, get_seed_data_sql, create_initial_admin

        # WAL checkpoint before migration to minimize WAL file size
        try:
            self._connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        except Exception:
            pass

        # Temporarily disable foreign keys for schema alteration/migration
        self._connection.execute("PRAGMA foreign_keys=OFF")

        try:
            cols = [r[1] for r in self._cursor.execute("PRAGMA table_info(daily_logs)").fetchall()]
            if cols and 'customer_name' not in cols:
                self._cursor.execute("""
                    CREATE TABLE IF NOT EXISTS daily_logs_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        log_date TEXT NOT NULL,
                        customer_name TEXT NOT NULL DEFAULT '',
                        customer_mobile TEXT DEFAULT '',
                        customer_address TEXT DEFAULT '',
                        customer_id INTEGER,
                        technician_id INTEGER,
                        technician_name TEXT DEFAULT '',
                        work_description TEXT DEFAULT '',
                        material_cost REAL DEFAULT 0,
                        petrol_expense REAL DEFAULT 0,
                        total_expense REAL DEFAULT 0,
                        total_payment REAL DEFAULT 0,
                        payment_status TEXT DEFAULT 'Paid to Tech',
                        payment_mode TEXT DEFAULT 'Cash',
                        net_profit REAL DEFAULT 0,
                        notes TEXT DEFAULT '',
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT DEFAULT (datetime('now','localtime')),
                        updated_at TEXT DEFAULT (datetime('now','localtime')),
                        FOREIGN KEY (customer_id) REFERENCES customers(id),
                        FOREIGN KEY (technician_id) REFERENCES technicians(id)
                    )
                """)
                self._cursor.execute("""
                    INSERT INTO daily_logs_new (
                        id, log_date, customer_name, customer_mobile, customer_address,
                        customer_id, technician_id, technician_name, work_description,
                        material_cost, petrol_expense, total_expense, total_payment,
                        payment_status, payment_mode, net_profit, notes, is_active, created_at, updated_at
                    )
                    SELECT 
                        dl.id,
                        COALESCE(dl.log_date, date('now')),
                        COALESCE(c.name, 'Customer #' || COALESCE(dl.customer_id, 0)),
                        COALESCE(c.mobile, ''),
                        COALESCE(dl.site_address, c.address, ''),
                        dl.customer_id,
                        dl.technician_id,
                        COALESCE(t.name, ''),
                        COALESCE(dl.parts_used, dl.service_type, 'Service / Repair'),
                        COALESCE(dl.parts_cost, 0),
                        COALESCE(dl.petrol_expense, 0),
                        COALESCE(dl.total_expense, 0),
                        COALESCE(dl.payment_received, 0),
                        CASE WHEN COALESCE(dl.payment_received, 0) > 0 THEN 'Paid to Tech' ELSE 'Pending' END,
                        COALESCE(dl.payment_mode, 'Cash'),
                        COALESCE(dl.profit, 0),
                        COALESCE(dl.notes, ''),
                        COALESCE(dl.is_active, 1),
                        COALESCE(dl.created_at, datetime('now','localtime')),
                        datetime('now','localtime')
                    FROM daily_logs dl
                    LEFT JOIN customers c ON dl.customer_id = c.id
                    LEFT JOIN technicians t ON dl.technician_id = t.id
                """)
                self._cursor.execute("DROP TABLE daily_logs")
                self._cursor.execute("ALTER TABLE daily_logs_new RENAME TO daily_logs")
                self._connection.commit()
        except Exception as mig_e:
            self._connection.rollback()
            error_logger.warning(f"daily_logs migration check: {mig_e}")

        # Ensure all modern columns exist on daily_logs
        try:
            cols = [r[1] for r in self._cursor.execute("PRAGMA table_info(daily_logs)").fetchall()]
            if cols:
                expected_cols = {
                    'total_billed': "REAL DEFAULT 0",
                    'advance_payment': "REAL DEFAULT 0",
                    'advance_receiver': "TEXT DEFAULT 'Tech (Cash)'",
                    'final_payment': "REAL DEFAULT 0",
                    'final_receiver': "TEXT DEFAULT 'Tech (Cash)'",
                    'pending_amount': "REAL DEFAULT 0",
                }
                for col_name, col_def in expected_cols.items():
                    if col_name not in cols:
                        self._cursor.execute(f"ALTER TABLE daily_logs ADD COLUMN {col_name} {col_def}")
                self._connection.commit()
        except Exception as col_err:
            error_logger.warning(f"daily_logs column check note: {col_err}")

        # Wrap ALL migrations in a single transaction.
        # If power is lost mid-migration, the DB reverts to pre-migration state.
        try:
            self._connection.execute("BEGIN IMMEDIATE")
        except Exception:
            pass

        try:
            for create_sql in get_all_tables_sql():
                try:
                    sqlite_sql = self._mysql_to_sqlite(create_sql)
                    self._cursor.execute(sqlite_sql)
                except Exception as e:
                    error_logger.warning(f"Schema migration note: {e}")

            for index_sql in get_all_indexes_sql():
                try:
                    self._cursor.execute(index_sql)
                except Exception as e:
                    error_logger.warning(f"Index creation note: {e}")

            try:
                create_initial_admin(self._cursor)
            except Exception as e:
                error_logger.warning(f"Admin seed note: {e}")

            for seed_sql in get_seed_data_sql():
                try:
                    self._cursor.execute(seed_sql)
                except Exception as e:
                    error_logger.warning(f"Seed data note: {e}")

            self._seed_software_schema()
            self._connection.commit()
            logger.info("Migrations completed successfully")
        except Exception as migration_err:
            self._connection.rollback()
            error_logger.critical(f"Migrations failed, database rolled back: {migration_err}", exc_info=True)
            raise RuntimeError(f"Database migration failed: {migration_err}") from migration_err
        finally:
            try:
                self._connection.execute("PRAGMA foreign_keys=ON")
            except Exception:
                pass

    def _seed_software_schema(self) -> None:
        tables = [
            ('users', 'software', 'App users'),
            ('customers', 'software', 'Customer records'),
            ('invoices', 'software', 'Service invoices'),
            ('invoice_items', 'software', 'Invoice line items'),
            ('payments', 'software', 'Payment records'),
            ('technicians', 'software', 'Service technicians'),
            ('technician_work', 'software', 'Technician work log'),
            ('technician_attendance', 'software', 'Technician attendance'),
            ('services', 'software', 'Service types'),
            ('parts', 'software', 'Inventory parts'),
            ('ac_brands', 'software', 'AC brands'),
            ('amc_contracts', 'software', 'AMC contracts'),
            ('amc_invoices', 'software', 'AMC invoices'),
            ('amc_units', 'software', 'AMC units'),
            ('amc_visits', 'software', 'AMC visits'),
            ('daily_logs', 'software', 'Daily work and cost logs'),
            ('shop_details', 'software', 'Shop/business details'),
            ('app_settings', 'software', 'Application settings'),
            ('payment_modes', 'software', 'Payment modes list'),
            ('whatsapp_templates', 'software', 'WhatsApp message templates'),
            ('ac_types', 'software', 'AC type masters'),
            ('ac_capacities', 'software', 'AC ton capacities'),
            ('ac_stars', 'software', 'AC star ratings'),
            ('inventory_units', 'software', 'Inventory unit masters'),
            ('technician_statuses', 'software', 'Technician status masters'),
            ('audit_log', 'software', 'Audit trail'),
            ('software_schema', 'software', 'Schema metadata'),
            ('contact_messages', 'software', 'Online requests'),
            ('service_requests', 'software', 'Website service inquiries'),
            ('stock_movements', 'software', 'Inventory movements'),
        ]
        for tbl, cat, desc in tables:
            try:
                self._cursor.execute(
                    "INSERT OR IGNORE INTO software_schema (table_name, category, description) VALUES (?, ?, ?)",
                    (tbl, cat, desc)
                )
            except Exception as se_err:
                logger.warning(f"Schema seed note for {tbl}: {se_err}")
        self._connection.commit()
        logger.info("Schema initialized")

    def wal_checkpoint(self, mode: str = "PASSIVE") -> None:
        """Run WAL checkpoint. Call periodically and on shutdown."""
        try:
            self._connection.execute(f"PRAGMA wal_checkpoint({mode})")
            db_logger.debug(f"WAL checkpoint ({mode}) completed")
        except Exception as e:
            error_logger.warning(f"WAL checkpoint failed: {e}")

    def begin_transaction(self) -> None:
        """Begin an explicit transaction for an atomic multi-step operation."""
        with self._query_lock:
            if self._transaction_active:
                raise RuntimeError("A database transaction is already active")
            self._connection.execute("BEGIN IMMEDIATE")
            self._transaction_active = True

    def commit(self) -> None:
        """Commit an explicit transaction."""
        with self._query_lock:
            self._connection.commit()
            self._transaction_active = False

    def rollback(self) -> None:
        """Roll back an explicit transaction."""
        with self._query_lock:
            self._connection.rollback()
            self._transaction_active = False

    def close(self) -> None:
        try:
            if self._transaction_active:
                self.rollback()
            self.wal_checkpoint("TRUNCATE")
            if self._cursor:
                self._cursor.close()
            if self._connection:
                self._connection.close()
                logger.info("Database disconnected")
        except Exception as e:
            error_logger.error(f"Close error: {e}")

    @property
    def connection(self) -> Any:
        return self._connection

    @property
    def cursor(self) -> Any:
        return self._cursor

    @property
    def autocommit(self) -> bool:
        return True


class DatabaseContext:
    def __init__(self):
        self.db = DatabaseConnection()

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            error_logger.error(f"DB context error: {exc_val}")
        return False


def _substring_index(s: str, delim: str, count: int) -> str:
    """MySQL-compatible SUBSTRING_INDEX for SQLite"""
    if not s or not delim:
        return s or ''
    parts = s.split(delim)
    if count > 0:
        if count >= len(parts):
            return s
        return delim.join(parts[:count])
    elif count < 0:
        abs_count = abs(count)
        if abs_count >= len(parts):
            return s
        return delim.join(parts[-abs_count:])
    return ''


def _split_top_level(s: str) -> list:
    """Split string by top-level commas (not inside parentheses)"""
    parts = []
    depth = 0
    current = ''
    for c in s:
        if c == '(':
            depth += 1
            current += c
        elif c == ')':
            depth -= 1
            current += c
        elif c == ',' and depth == 0:
            parts.append(current.strip())
            current = ''
        else:
            current += c
    if current.strip():
        parts.append(current.strip())
    return parts
