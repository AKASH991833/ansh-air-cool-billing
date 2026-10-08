"""
AUTH CONTROLLER - SECURE PASSWORD HASHING WITH SHOP DETAILS
Includes: Password validation, Failed login tracking, Session management
"""
import bcrypt
import re
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AuthController:
    def __init__(self, db_connection):
        self.db = db_connection

    @staticmethod
    def validate_password_strength(password):
        """
        Validate password strength
        Rules:
        - Minimum 8 characters
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 1 number
        - At least 1 special character
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"

        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"

        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"

        if not re.search(r"\d", password):
            return False, "Password must contain at least one number"

        if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:',.<>?/\\]", password):
            return False, "Password must contain at least one special character (!@#$%^&*...)"

        return True, "Password is strong"

    def login(self, username, password):
        """Secure login with password hashing and failed login tracking"""
        try:
            # Check if account is locked due to too many failed attempts
            lock_query = """
            SELECT failed_attempts, locked_until 
            FROM users 
            WHERE username = %s AND is_active = TRUE
            """
            user_lock = self.db.execute_query(lock_query, (username,), fetch_one=True)
            
            if user_lock and user_lock.get('locked_until'):
                locked_until = user_lock['locked_until']
                if isinstance(locked_until, datetime) and locked_until > datetime.now():
                    return None, f"Account temporarily locked. Try again after {locked_until.strftime('%Y-%m-%d %H:%M:%S')}"
                # Lock period expired, reset attempts
                self.db.execute_query(
                    "UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE username = %s",
                    (username,)
                )
            
            # Get user
            query = "SELECT * FROM users WHERE username = %s AND is_active = TRUE"
            user = self.db.execute_query(query, (username,), fetch_one=True)

            if not user:
                return None, "Invalid username or password. Please enter valid credentials."

            # Verify hashed password (guard against NULL password_hash)
            password_hash = user.get('password_hash')
            if not password_hash:
                return None, "Account has no password set. Contact administrator."
            if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                # Login successful - reset failed attempts
                self.db.execute_query(
                    "UPDATE users SET failed_attempts = 0, locked_until = NULL, last_login = NOW() WHERE id = %s",
                    (user['id'],)
                )
                
                user.pop('password_hash', None)  # Remove hash from response
                user.pop('failed_attempts', None)
                user.pop('locked_until', None)
                return user, None
            else:
                # Failed login - increment attempt counter
                failed_attempts = (user.get('failed_attempts') or 0) + 1
                
                if failed_attempts >= 5:
                    # Lock account for 15 minutes
                    locked_until = datetime.now() + timedelta(minutes=15)
                    self.db.execute_query(
                        "UPDATE users SET failed_attempts = %s, locked_until = %s WHERE id = %s",
                        (failed_attempts, locked_until, user['id'])
                    )
                    return None, "Account locked due to too many failed attempts. Try again after 15 minutes."
                else:
                    self.db.execute_query(
                        "UPDATE users SET failed_attempts = %s WHERE id = %s",
                        (failed_attempts, user['id'])
                    )
                    remaining = 5 - failed_attempts
                    return None, f"Incorrect password. {remaining} attempt(s) remaining."

        except Exception as e:
            logger.error(f"Login error: {e}")
            return None, f"Error: {str(e)}"

    def change_username(self, user_id, old_password, new_username):
        """Change username with password verification"""
        try:
            if not new_username or not new_username.strip():
                return False, "Username cannot be empty"

            if len(new_username) < 3:
                return False, "Username must be at least 3 characters long"

            if not re.match(r"^[a-zA-Z0-9_]+$", new_username):
                return False, "Username can only contain letters, numbers, and underscores"

            # Verify current password
            query = "SELECT id, password_hash FROM users WHERE id = %s"
            user = self.db.execute_query(query, (user_id,), fetch_one=True)

            if not user:
                return False, "User not found"

            stored_hash = user.get('password_hash')
            if not stored_hash:
                return False, "Account has no password set. Cannot verify identity."
            if not bcrypt.checkpw(old_password.encode('utf-8'), stored_hash.encode('utf-8')):
                return False, "Current password is incorrect"

            # Check if new username already exists
            check_query = "SELECT id FROM users WHERE username = %s AND id != %s"
            existing = self.db.execute_query(check_query, (new_username, user_id), fetch_one=True)

            if existing:
                return False, "Username is already taken"

            # Update username
            query = "UPDATE users SET username = %s, updated_at = NOW() WHERE id = %s"
            self.db.execute_query(query, (new_username, user_id))
            
            # CRITICAL: Force commit
            if hasattr(self.db, 'connection') and self.db.connection:
                self.db.connection.commit()
                
            return True, "Username changed successfully"
        except Exception as e:
            logger.error(f"Change username error: {e}")
            return False, f"Error: {str(e)}"

    def change_password(self, user_id, old_password, new_password):
        """Change user password with proper validation"""
        try:
            # First, get the current password hash
            query = "SELECT password_hash FROM users WHERE id = %s"
            user = self.db.execute_query(query, (user_id,), fetch_one=True)

            if not user:
                return False, "User not found"

            stored_hash = user.get('password_hash')
            if not stored_hash:
                return False, "Account has no password set. Cannot verify identity."
            # Verify old password
            if not bcrypt.checkpw(old_password.encode('utf-8'), stored_hash.encode('utf-8')):
                return False, "Current password is incorrect"

            # Validate new password strength (using static method)
            is_valid, message = AuthController.validate_password_strength(new_password)
            if not is_valid:
                return False, message

            # Hash the new password
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

            # Update with new hashed password
            query = "UPDATE users SET password_hash = %s, updated_at = NOW() WHERE id = %s"
            self.db.execute_query(query, (hashed_password.decode('utf-8'), user_id))
            try:
                from utils.audit import log_password_change
                log_password_change(user_id)
            except Exception as audit_err:
                logger.warning(f"Password change audit log failed: {audit_err}")
            return True, "Password changed successfully"
        except Exception as e:
            logger.error(f"Change password error: {e}")
            return False, f"Error: {str(e)}"
    
    def update_profile(self, user_id, full_name, email, phone):
        """Update user profile with explicit commit and session refresh support"""
        try:
            # Validate input
            if not full_name or not full_name.strip():
                return False, "Full name is required", None

            query = "UPDATE users SET full_name = %s, email = %s, phone = %s, updated_at = NOW() WHERE id = %s"
            self.db.execute_query(query, (full_name, email, phone, user_id))

            # CRITICAL: Ensure explicit commit after UPDATE
            # Even though autocommit=True by default, we explicitly commit to be safe
            if hasattr(self.db, 'connection') and self.db.connection:
                try:
                    # Always commit to ensure data is saved
                    self.db.connection.commit()
                    logger.info(f"[DB] Profile update committed for user {user_id}")
                except Exception as commit_error:
                    logger.error(f"[DB] Commit failed: {commit_error}")
                    raise

            # Log success
            logger.info(f"[PROFILE] User {user_id} profile updated: name={full_name}, email={email}, phone={phone}")

            # Fetch and return FRESH user data for session refresh
            # This ensures the caller gets the latest data from database
            fetch_query = """
                SELECT id, username, full_name, email, phone, is_active, created_at, updated_at
                FROM users
                WHERE id = %s
            """
            updated_user = self.db.execute_query(fetch_query, (user_id,), fetch_one=True)

            if updated_user:
                logger.info(f"[PROFILE] Fetched fresh user data for session refresh: {updated_user}")
            else:
                logger.warning(f"[PROFILE] User {user_id} not found after update")

            return True, "Profile updated successfully", updated_user

        except Exception as e:
            logger.error(f"[PROFILE] Update failed for user {user_id}: {e}")
            # Rollback if there was an error during transaction
            if hasattr(self.db, 'connection') and self.db.connection:
                try:
                    self.db.connection.rollback()
                except Exception as rb_err:
                    logger.warning(f"Profile update rollback failed: {rb_err}")
            return False, f"Error: {str(e)}", None
    
    def get_shop_details(self):
        """Get shop details"""
        try:
            return self.db.execute_query(
                "SELECT * FROM shop_details ORDER BY id DESC LIMIT 1",
                fetch_one=True
            )
        except Exception as e:
            logger.error(f"Error getting shop details: {e}")
            return None
    
    def update_shop_details(self, shop_data):
        """Update shop details with explicit commit"""
        try:
            existing = self.get_shop_details()
            logo_path = shop_data.get('logo_path', '')
            
            if existing:
                query = """
                UPDATE shop_details 
                SET shop_name = %s, address = %s, phone = %s, email = %s, 
                    gst_number = %s, tagline = %s, services = %s,
                    owner_name = %s, owner_phone = %s, logo_path = %s
                WHERE id = %s
                """
                self.db.execute_query(query, (
                    shop_data['shop_name'],
                    shop_data['address'],
                    shop_data['phone'],
                    shop_data['email'],
                    shop_data['gst_number'],
                    shop_data.get('tagline', ''),
                    shop_data.get('services', ''),
                    shop_data['owner_name'],
                    shop_data['owner_phone'],
                    logo_path,
                    existing['id']
                ))
            else:
                query = """
                INSERT INTO shop_details (shop_name, address, phone, email, gst_number, tagline, services, owner_name, owner_phone, logo_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                self.db.execute_query(query, (
                    shop_data['shop_name'],
                    shop_data['address'],
                    shop_data['phone'],
                    shop_data['email'],
                    shop_data['gst_number'],
                    shop_data.get('tagline', ''),
                    shop_data.get('services', ''),
                    shop_data['owner_name'],
                    shop_data['owner_phone'],
                    logo_path
                ))
            
            # Explicit commit for safety
            if hasattr(self.db, 'connection') and self.db.connection:
                try:
                    self.db.connection.commit()
                    logger.info("[DB] Shop details committed successfully")
                except Exception as commit_error:
                    logger.error(f"[DB] Commit failed for shop details: {commit_error}")
                    raise

            msg = "Shop details updated successfully" if existing else "Shop details saved successfully"
            return True, msg
                
        except Exception as e:
            logger.error(f"Failed to save shop details: {e}")
            if hasattr(self.db, 'connection') and self.db.connection:
                try:
                    self.db.connection.rollback()
                except Exception as rb_err:
                    logger.warning(f"Shop details rollback failed: {rb_err}")
            return False, f"Failed to save shop details: {str(e)}"
    
    def add_shop_details(self, shop_data):
        """Add new shop details"""
        try:
            query = """
            INSERT INTO shop_details (shop_name, address, phone, email, gst_number, owner_name, owner_phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            self.db.execute_query(query, (
                shop_data['shop_name'],
                shop_data['address'],
                shop_data['phone'],
                shop_data['email'],
                shop_data['gst_number'],
                shop_data['owner_name'],
                shop_data['owner_phone']
            ))
            return True, "Shop details added successfully"
        except Exception as e:
            return False, f"Failed to add shop details: {str(e)}"