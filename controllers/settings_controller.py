"""
Settings and master data controller - Improved with transactional safety and full feature support
"""
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SettingsController:
    def __init__(self, db_connection):
        self.db = db_connection
    
    # ========== SERVICES MANAGEMENT ==========
    def get_all_services(self):
        """Get all services"""
        query = "SELECT * FROM services ORDER BY service_name"
        return self.db.execute_query(query, fetch_all=True) or []
    
    def get_active_services(self):
        """Get active services only"""
        query = "SELECT * FROM services WHERE is_active = TRUE ORDER BY service_name"
        return self.db.execute_query(query, fetch_all=True) or []
    
    def add_service(self, service_name, description, default_rate):
        """Add new service"""
        check_query = "SELECT id FROM services WHERE service_name = %s"
        existing = self.db.execute_query(check_query, (service_name,), fetch_one=True)
        if existing:
            return False, "Service with this name already exists"
        
        query = "INSERT INTO services (service_name, description, default_rate, is_active) VALUES (%s, %s, %s, TRUE)"
        try:
            self.db.execute_query(query, (service_name, description, float(default_rate)))
            return True, "Service added successfully"
        except Exception as e:
            return False, f"Failed to add service: {str(e)}"
    
    def update_service(self, service_id, service_name, description, default_rate, is_active):
        """Update service"""
        check_query = "SELECT id FROM services WHERE service_name = %s AND id != %s"
        existing = self.db.execute_query(check_query, (service_name, service_id), fetch_one=True)
        if existing:
            return False, "Service with this name already exists"
        
        query = "UPDATE services SET service_name = %s, description = %s, default_rate = %s, is_active = %s WHERE id = %s"
        try:
            self.db.execute_query(query, (service_name, description, float(default_rate), is_active, service_id))
            return True, "Service updated successfully"
        except Exception as e:
            return False, f"Failed to update service: {str(e)}"
    
    def delete_service(self, service_id):
        """Soft delete service"""
        check_query = "SELECT COUNT(*) as count FROM invoice_items WHERE service_id = %s"
        result = self.db.execute_query(check_query, (service_id,), fetch_one=True)
        if result and result['count'] > 0:
            return False, "Cannot delete service that is used in invoices"
        
        query = "UPDATE services SET is_active = FALSE WHERE id = %s"
        try:
            self.db.execute_query(query, (service_id,))
            return True, "Service deleted successfully"
        except Exception as e:
            return False, f"Failed to delete service: {str(e)}"
    
    # ========== PARTS MANAGEMENT ==========
    def get_all_parts(self):
        """Get all parts"""
        query = "SELECT * FROM parts ORDER BY part_name"
        return self.db.execute_query(query, fetch_all=True) or []
    
    def get_active_parts(self):
        """Get active parts only"""
        query = "SELECT * FROM parts WHERE is_active = TRUE ORDER BY part_name"
        return self.db.execute_query(query, fetch_all=True) or []
    
    def add_part(self, part_name, description, default_rate, stock_quantity):
        """Add new part"""
        check_query = "SELECT id FROM parts WHERE part_name = %s"
        existing = self.db.execute_query(check_query, (part_name,), fetch_one=True)
        if existing:
            return False, "Part with this name already exists"
        
        query = "INSERT INTO parts (part_name, description, default_rate, stock_quantity, is_active) VALUES (%s, %s, %s, %s, TRUE)"
        try:
            self.db.execute_query(query, (part_name, description, float(default_rate), int(stock_quantity)))
            return True, "Part added successfully"
        except Exception as e:
            return False, f"Failed to add part: {str(e)}"
    
    def update_part(self, part_id, part_name, description, default_rate, stock_quantity, is_active):
        """Update part"""
        check_query = "SELECT id FROM parts WHERE part_name = %s AND id != %s"
        existing = self.db.execute_query(check_query, (part_name, part_id), fetch_one=True)
        if existing:
            return False, "Part with this name already exists"
        
        query = "UPDATE parts SET part_name=%s, description=%s, default_rate=%s, stock_quantity=%s, is_active=%s WHERE id=%s"
        try:
            self.db.execute_query(query, (part_name, description, float(default_rate), int(stock_quantity), is_active, part_id))
            return True, "Part updated successfully"
        except Exception as e:
            return False, f"Failed to update part: {str(e)}"
    
    def delete_part(self, part_id):
        """Soft delete part"""
        check_query = "SELECT COUNT(*) as count FROM invoice_items WHERE part_id = %s"
        result = self.db.execute_query(check_query, (part_id,), fetch_one=True)
        if result and result['count'] > 0:
            return False, "Cannot delete part that is used in invoices"
        
        query = "UPDATE parts SET is_active = FALSE WHERE id = %s"
        try:
            self.db.execute_query(query, (part_id,))
            return True, "Part deleted successfully"
        except Exception as e:
            return False, f"Failed to delete part: {str(e)}"
    
    # ========== AC BRANDS MANAGEMENT ==========
    def get_all_ac_brands(self):
        """Get all AC brands"""
        query = "SELECT * FROM ac_brands ORDER BY brand_name"
        return self.db.execute_query(query, fetch_all=True) or []
    
    def get_active_ac_brands(self):
        """Get active AC brands only"""
        query = "SELECT * FROM ac_brands WHERE is_active = TRUE ORDER BY brand_name"
        return self.db.execute_query(query, fetch_all=True) or []
    
    def add_ac_brand(self, brand_name):
        """Add new AC brand"""
        check_query = "SELECT id FROM ac_brands WHERE brand_name = %s"
        existing = self.db.execute_query(check_query, (brand_name,), fetch_one=True)
        if existing:
            return False, "Brand with this name already exists"
        
        query = "INSERT INTO ac_brands (brand_name, is_active) VALUES (%s, TRUE)"
        try:
            self.db.execute_query(query, (brand_name,))
            return True, "Brand added successfully"
        except Exception as e:
            return False, f"Failed to add brand: {str(e)}"
    
    def update_ac_brand(self, brand_id, brand_name, is_active):
        """Update AC brand"""
        check_query = "SELECT id FROM ac_brands WHERE brand_name = %s AND id != %s"
        existing = self.db.execute_query(check_query, (brand_name, brand_id), fetch_one=True)
        if existing:
            return False, "Brand with this name already exists"
        
        query = "UPDATE ac_brands SET brand_name = %s, is_active = %s WHERE id = %s"
        try:
            self.db.execute_query(query, (brand_name, is_active, brand_id))
            return True, "Brand updated successfully"
        except Exception as e:
            return False, f"Failed to update brand: {str(e)}"
    
    def delete_ac_brand(self, brand_id):
        """Soft delete AC brand"""
        check_query = "SELECT COUNT(*) as count FROM invoices WHERE ac_brand_id = %s"
        result = self.db.execute_query(check_query, (brand_id,), fetch_one=True)
        if result and result['count'] > 0:
            return False, "Cannot delete brand that is used in invoices"
        
        query = "UPDATE ac_brands SET is_active = FALSE WHERE id = %s"
        try:
            self.db.execute_query(query, (brand_id,))
            return True, "Brand deleted successfully"
        except Exception as e:
            return False, f"Failed to delete brand: {str(e)}"

    # ========== PAYMENT MODES MANAGEMENT ==========
    def get_all_payment_modes(self):
        """Get all payment modes from DB"""
        query = "SELECT * FROM payment_modes ORDER BY mode_name"
        return self.db.execute_query(query, fetch_all=True) or []

    def get_active_payment_modes(self):
        """Get active payment modes only"""
        query = "SELECT * FROM payment_modes WHERE is_active = TRUE ORDER BY mode_name"
        return self.db.execute_query(query, fetch_all=True) or []

    def add_payment_mode(self, mode_name):
        """Add new payment mode"""
        check_query = "SELECT id FROM payment_modes WHERE mode_name = %s"
        existing = self.db.execute_query(check_query, (mode_name,), fetch_one=True)
        if existing:
            return False, "Payment mode already exists"
        
        query = "INSERT INTO payment_modes (mode_name, is_active) VALUES (%s, TRUE)"
        try:
            self.db.execute_query(query, (mode_name,))
            return True, "Payment mode added successfully"
        except Exception as e:
            return False, f"Failed to add payment mode: {str(e)}"

    def update_payment_mode(self, mode_id, mode_name, is_active):
        """Update payment mode"""
        check_query = "SELECT id FROM payment_modes WHERE mode_name = %s AND id != %s"
        existing = self.db.execute_query(check_query, (mode_name, mode_id), fetch_one=True)
        if existing:
            return False, "Payment mode name already exists"
        
        query = "UPDATE payment_modes SET mode_name = %s, is_active = %s WHERE id = %s"
        try:
            self.db.execute_query(query, (mode_name, is_active, mode_id))
            return True, "Payment mode updated successfully"
        except Exception as e:
            return False, f"Failed to update payment mode: {str(e)}"

    def delete_payment_mode(self, mode_id):
        """Soft delete payment mode"""
        # Check if used in invoices
        check_query = "SELECT COUNT(*) as count FROM invoices WHERE payment_mode = (SELECT mode_name FROM payment_modes WHERE id = %s)"
        result = self.db.execute_query(check_query, (mode_id,), fetch_one=True)
        if result and result['count'] > 0:
            return False, "Cannot delete payment mode that has associated invoices"
        
        query = "UPDATE payment_modes SET is_active = FALSE WHERE id = %s"
        try:
            self.db.execute_query(query, (mode_id,))
            return True, "Payment mode deactivated successfully"
        except Exception as e:
            return False, f"Failed to delete payment mode: {str(e)}"
    
    # ========== DYNAMIC MASTERS MANAGEMENT ==========
    VALID_MASTER_TABLES = [
        'ac_types', 'ac_capacities', 'ac_stars',
        'inventory_units', 'technician_statuses', 'whatsapp_templates'
    ]

    def _validate_master_table(self, table_name):
        """Whitelist table_name to prevent SQL injection"""
        return table_name in self.VALID_MASTER_TABLES

    def _get_valid_columns(self, table_name):
        """Return column names for a whitelisted master table.
        Caller MUST validate table_name via _validate_master_table first."""
        schema = {
            'ac_types': ['id', 'type_name', 'is_active'],
            'ac_capacities': ['id', 'capacity_value', 'is_active'],
            'ac_stars': ['id', 'star_label', 'is_active'],
            'inventory_units': ['id', 'unit_name', 'is_active'],
            'technician_statuses': ['id', 'status_name', 'is_active'],
            'whatsapp_templates': ['id', 'template_key', 'template_body', 'description', 'updated_at'],
        }
        return schema.get(table_name, [])

    def get_master_data(self, table_name):
        """Generic method to get data from master tables"""
        if not self._validate_master_table(table_name):
            return []

        query = f"SELECT * FROM {table_name}"
        cols = self._get_valid_columns(table_name)
        if table_name == 'whatsapp_templates':
            query += " ORDER BY template_key"
        elif 'type_name' in cols:
            query += " ORDER BY type_name"
        return self.db.execute_query(query, fetch_all=True) or []

    def _get_columns(self, table_name):
        """Get column names from DB via PRAGMA.
        Safe because caller has already validated table_name against whitelist."""
        res = self.db.execute_query(f"PRAGMA table_info({table_name})", fetch_all=True)
        return [r['name'] for r in res] if res else []

    def add_master_item(self, table_name, field_name, value):
        """Add item to master table"""
        if not self._validate_master_table(table_name):
            return False, "Invalid table name"
        valid_cols = self._get_valid_columns(table_name)
        if field_name not in valid_cols:
            return False, f"Invalid field name '{field_name}' for table '{table_name}'"

        query = f"INSERT INTO {table_name} ({field_name}) VALUES (%s)"
        try:
            self.db.execute_query(query, (value,))
            return True, "Item added successfully"
        except Exception as e:
            return False, str(e)

    def update_master_item(self, table_name, field_name, value, item_id):
        """Update item in master table"""
        if not self._validate_master_table(table_name):
            return False, "Invalid table name"
        valid_cols = self._get_valid_columns(table_name)
        if field_name not in valid_cols:
            return False, f"Invalid field name '{field_name}' for table '{table_name}'"

        query = f"UPDATE {table_name} SET {field_name} = %s WHERE id = %s"
        try:
            self.db.execute_query(query, (value, item_id))
            return True, "Item updated successfully"
        except Exception as e:
            return False, str(e)

    def delete_master_item(self, table_name, item_id):
        """Deactivate item in master table (soft delete)"""
        if not self._validate_master_table(table_name):
            return False, "Invalid table name"

        query = f"UPDATE {table_name} SET is_active = FALSE WHERE id = %s"
        try:
            self.db.execute_query(query, (item_id,))
            return True, "Item deactivated successfully"
        except Exception as e:
            return False, str(e)

    def update_whatsapp_template(self, template_id, body):
        """Update WhatsApp template body"""
        query = "UPDATE whatsapp_templates SET template_body = %s WHERE id = %s"
        try:
            self.db.execute_query(query, (body, template_id))
            return True, "Template updated successfully"
        except Exception as e:
            return False, str(e)
    
    # ========== APPLICATION SETTINGS ==========
    def get_application_settings(self):
        """Get application settings from database with robust error handling"""
        # Hardcoded application-wide defaults
        settings = {
            'invoice_prefix': 'INV',
            'starting_invoice_number': 1001,
            'default_gst_percentage': 18.0,
            'theme_mode': 'light',
            'language': 'en',
            'opening_time': '09:00',
            'closing_time': '20:00',
            'terms_conditions': '1. Goods once sold will not be taken back.\n2. Warranty as per company policy.\n3. Payment due within 7 days.\n4. Service warranty only on selected parts.',
            'thank_you_note': 'Thank you for your business!',
            'invoice_watermark': 'INVOICE',
            'app_name': 'AC Service Billing',
            'company_name': 'Your Company Name',
            'currency_symbol': '\u20b9',
            'date_format': 'dd-MM-yyyy',
            'default_notes': 'All Work Done',
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': '587',
            'smtp_username': '',
            'smtp_password': '',
            'smtp_from_email': 'your@email.com',
            'smtp_from_name': 'Your Company Name',
            'email_subject': 'Invoice #{invoice_number} - {company_name}',
            'email_body': 'Dear {customer_name},\n\nPlease find attached invoice #{invoice_number}.\n\nThank you for your business!\n{company_name}',
            'discount_before_gst': False,
            'service_types': 'AC Service,Installation,Repair,Gas Refilling,AMC Visit,AC Rent Delivery,AC Rent Pickup,Other',
            'ac_types': 'Split,Window,Cassette,Tower,Other',
            'ac_ton_capacities': '1.0,1.5,2.0,3.0,Other',
            'ac_inverter_options': 'No,Yes',
            'star_ratings': 'N/A,1,2,3,4,5',
            'privacy_mode_enabled': True,
        }
        try:
            query = "SELECT setting_key, setting_value FROM app_settings"
            rows = self.db.execute_query(query, fetch_all=True)
            if rows:
                print(f"[SETTINGS] Loaded {len(rows)} settings from database")
                for row in rows:
                    key = row['setting_key']
                    val = row['setting_value']
                    
                    if key in settings:
                        # Convert to original type
                        orig_type = type(settings[key])
                        try:
                            if orig_type == bool:
                                settings[key] = val.lower() in ('true', '1', 'yes')
                            elif orig_type == float:
                                settings[key] = float(val)
                            elif orig_type == int:
                                settings[key] = int(val)
                            else:
                                settings[key] = val
                        except (ValueError, TypeError):
                            settings[key] = val
                    else:
                        settings[key] = val
            else:
                print("[SETTINGS] No settings found in DB, using defaults")
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            print(f"[ERROR] Settings load failed: {e}")
        return settings
    
    def save_setting(self, key, value):
        """Save a single setting to database"""
        return self.save_application_settings({key: value})

    def save_application_settings(self, settings_dict):
        """Save application settings to database"""
        try:
            print(f"[SETTINGS] Saving settings: {settings_dict}")
            for key, value in settings_dict.items():
                val_str = str(value)
                # Use insert or update compatible with SQLite and MySQL
                check_query = "SELECT setting_key FROM app_settings WHERE setting_key = %s"
                existing = self.db.execute_query(check_query, (key,), fetch_one=True)
                if existing:
                    query = "UPDATE app_settings SET setting_value = %s, updated_at = CURRENT_TIMESTAMP WHERE setting_key = %s"
                    self.db.execute_query(query, (val_str, key))
                else:
                    query = "INSERT INTO app_settings (setting_key, setting_value) VALUES (%s, %s)"
                    self.db.execute_query(query, (key, val_str))

            return True, "Settings saved successfully"
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            print(f"[ERROR] Settings save failed: {e}")
            return False, f"Failed to save settings: {str(e)}"
    
    # ========== BACKUP & RESTORE ==========
    def create_backup(self, custom_path=None):
        """Create database backup as JSON (streaming write, chunked reads)"""
        import os
        import json
        from datetime import datetime
        
        try:
            if not custom_path:
                backups_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
                if not os.path.exists(backups_dir):
                    os.makedirs(backups_dir)
                filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                custom_path = os.path.join(backups_dir, filename)

            # Get list of software tables from schema
            software_tables_query = "SELECT table_name FROM software_schema WHERE category = 'software'"
            tables_result = self.db.execute_query(software_tables_query, fetch_all=True)
            tables = [r['table_name'] for r in tables_result] if tables_result else []
            
            if not tables:
                tables_res = self.db.execute_query(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
                    fetch_all=True
                )
                tables = [r['name'] for r in tables_res] if tables_res else []

            CHUNK_SIZE = 500
            conn = self.db._connection

            with open(custom_path, 'w', encoding='utf-8') as f:
                f.write('{\n')
                f.write(f'  "info": {{\n')
                f.write(f'    "created_at": "{datetime.now().isoformat()}",\n')
                f.write(f'    "app_version": "1.0.0"\n')
                f.write(f'  }},\n')
                f.write(f'  "tables": {{\n')

                first_table = True
                for table in tables:
                    try:
                        cursor = conn.cursor()
                        cursor.execute(f"SELECT * FROM [{table}]")
                        columns = [desc[0] for desc in cursor.description] if cursor.description else []

                        rows = cursor.fetchmany(CHUNK_SIZE)
                        if not rows:
                            cursor.close()
                            continue

                        if not first_table:
                            f.write(',\n')
                        first_table = False
                        f.write(f'    "{table}": [\n')

                        first_row = True
                        while rows:
                            for row in rows:
                                row_dict = dict(zip(columns, row))
                                json_row = json.dumps(row_dict, default=str, ensure_ascii=False)
                                if not first_row:
                                    f.write(',\n')
                                first_row = False
                                f.write(f'      {json_row}')
                            rows = cursor.fetchmany(CHUNK_SIZE)

                        f.write('\n    ]')
                        cursor.close()
                    except Exception as e:
                        logger.warning(f"Could not backup table {table}: {e}")

                f.write('\n  }\n')
                f.write('}\n')

            return custom_path
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise
    
    def restore_backup(self, backup_path):
        """Restore database from JSON backup with TRANSACTIONAL SAFETY (chunked insert)"""
        import json
        
        BATCH_SIZE = 500
        
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            tables = backup_data.get('tables', {})
            if not tables:
                raise ValueError("Backup file contains no data")

            conn = self.db._connection
            cursor = conn.cursor()

            try:
                cursor.execute("PRAGMA foreign_keys = OFF")
                cursor.execute("BEGIN")

                for table, rows in tables.items():
                    if not rows:
                        continue

                    cursor.execute(f"DELETE FROM [{table}]")

                    columns = list(rows[0].keys())
                    col_names = ", ".join([f"[{c}]" for c in columns])
                    placeholders = ", ".join(["?"] * len(columns))
                    insert_query = f"INSERT INTO [{table}] ({col_names}) VALUES ({placeholders})"

                    batch = []
                    for row in rows:
                        batch.append([row.get(c) for c in columns])
                        if len(batch) >= BATCH_SIZE:
                            cursor.executemany(insert_query, batch)
                            batch = []
                    if batch:
                        cursor.executemany(insert_query, batch)

                conn.commit()
                logger.info(f"Successfully restored data from {backup_path}")
                return True, "Data restored successfully"

            except Exception as e:
                conn.rollback()
                logger.error(f"Restore failed, rolled back: {e}")
                raise e
            finally:
                cursor.execute("PRAGMA foreign_keys = ON")
                cursor.close()

        except Exception as e:
            logger.error(f"Critical error during restore: {e}")
            raise
