"""
Main entry point for AC Service Billing Software - PySide6 Edition
Professional Qt-based UI with modern design
"""
import sys
import os
import traceback
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS', '--disable-gpu --no-sandbox')

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1 — GLOBAL CRASH HANDLER (installed before ANY other code)
# ═══════════════════════════════════════════════════════════════════════════
_CRASH_LOG_PATH = None

def _get_crash_log_path():
    global _CRASH_LOG_PATH
    if _CRASH_LOG_PATH is None:
        try:
            from config import DATA_DIR
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            _CRASH_LOG_PATH = str(DATA_DIR / 'crash.log')
        except Exception:
            _CRASH_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crash.log')
    return _CRASH_LOG_PATH

def _write_crash_log(exc_type, exc_value, exc_tb):
    """Write crash details to crash.log"""
    try:
        with open(_get_crash_log_path(), 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"CRASH: {exc_type.__name__}: {exc_value}\n")
            f.write(f"Time: {__import__('datetime').datetime.now().isoformat()}\n")
            traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
            f.write(f"{'='*60}\n")
    except Exception:
        pass  # Cannot log if filesystem is broken

def _show_fatal_error_dialog(title, message):
    """Show a fatal error dialog. Safe to call before QApplication exists."""
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        QMessageBox.critical(None, title, message)
    except Exception:
        pass  # Ultimate fallback — silent failure

def global_excepthook(exc_type, exc_value, exc_traceback):
    """Never let an exception go unhandled — log, notify, then die."""
    _write_crash_log(exc_type, exc_value, exc_traceback)
    _show_fatal_error_dialog(
        "Fatal Error",
        f"An unexpected error occurred and the application must close.\n\n"
        f"{exc_type.__name__}: {exc_value}\n\n"
        f"Please contact support with the crash log file:\n{_get_crash_log_path()}"
    )
    sys.exit(1)

sys.excepthook = global_excepthook

def thread_excepthook(args):
    """Handle unhandled exceptions in threads."""
    try:
        with open(_get_crash_log_path(), 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"THREAD CRASH: {args.exc_type.__name__}: {args.exc_value}\n")
            f.write(f"Thread: {args.thread.name if args.thread else 'unknown'}\n")
            f.write(f"Time: {__import__('datetime').datetime.now().isoformat()}\n")
            traceback.print_exception(args.exc_type, args.exc_value, args.exc_traceback, file=f)
            f.write(f"{'='*60}\n")
    except Exception:
        pass

threading_module = __import__('threading')
if hasattr(threading_module, 'excepthook'):
    threading_module.excepthook = thread_excepthook

# Suppress unraisable exceptions (harmless __del__ warnings)
if hasattr(sys, 'unraisablehook'):
    sys.unraisablehook = lambda args: None

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2 — STARTUP VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

def _validate_startup():
    """Validate all required directories and files before starting the app."""
    from config import BASE_DIR, DATA_DIR, EXPORT_DIR, PDF_DIR, LOGO_PATH

    checks = []

    # Data directory
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        test_file = DATA_DIR / '.write_test'
        test_file.write_text('')
        test_file.unlink()
        checks.append(('Data directory', True, ''))
    except Exception as e:
        checks.append(('Data directory', False, str(e)))

    # Log directory
    log_dir = DATA_DIR / 'logs'
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        test_file = log_dir / '.write_test'
        test_file.write_text('')
        test_file.unlink()
        checks.append(('Log directory', True, ''))
    except Exception as e:
        checks.append(('Log directory', False, str(e)))

    # Export directory
    try:
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        checks.append(('Export directory', True, ''))
    except Exception as e:
        checks.append(('Export directory', False, str(e)))

    # PDF directory
    try:
        PDF_DIR.mkdir(parents=True, exist_ok=True)
        checks.append(('PDF directory', True, ''))
    except Exception as e:
        checks.append(('PDF directory', False, str(e)))

    # Logo file
    logo_exists = LOGO_PATH.exists()
    checks.append(('Logo file', logo_exists, '' if logo_exists else f'Not found: {LOGO_PATH}'))

    # Database file (may not exist on first run — that's OK)
    from config import DB_PATH
    checks.append(('Database path', True, str(DB_PATH)))

    failures = [c for c in checks if not c[1]]
    if failures:
        error_msg = "Startup validation failed:\n\n"
        for name, ok, detail in failures:
            error_msg += f"  ❌ {name}"
            if detail:
                error_msg += f" — {detail}"
            error_msg += "\n"
        error_msg += "\nThe application may not function correctly."
        _write_crash_log(type(error_msg), Exception(error_msg), None)
        _show_fatal_error_dialog("Startup Error", error_msg)
        return False

    return True

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3 — SINGLE INSTANCE PROTECTION
# ═══════════════════════════════════════════════════════════════════════════

_SHARED_MEMORY_KEY = "AC_Billing_Software_SingleInstance_2024"

def _acquire_single_instance_lock():
    """Prevent multiple EXE instances using QSharedMemory."""
    from PySide6.QtCore import QSharedMemory
    shared_mem = QSharedMemory(_SHARED_MEMORY_KEY)
    if not shared_mem.create(1):
        if shared_mem.error() == QSharedMemory.SharedMemoryError.AlreadyExists:
            # Attach to existing — if it works, another instance is running
            if shared_mem.attach():
                _show_fatal_error_dialog(
                    "Application Already Running",
                    "The application is already running.\n\n"
                    "Only one instance can run at a time."
                )
                sys.exit(0)
        # If we get here, clean up stale shared memory
        if shared_mem.error() == QSharedMemory.SharedMemoryError.AlreadyExists:
            shared_mem.attach()
            shared_mem.detach()
            if not shared_mem.create(1):
                _write_crash_log(type(Exception), Exception(f"Could not create shared memory: {shared_mem.error()}"), None)
                sys.exit(1)
    return shared_mem  # Keep reference alive for app lifetime

# ═══════════════════════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════════════════════

from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPixmap

from config import APP_NAME, APP_VERSION, BASE_DIR, LOGO_PATH
from database.db_connection import DatabaseConnection

# ═══════════════════════════════════════════════════════════════════════════
# LOGIN SYSTEM CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════
# Set to True to enable login system (Production mode)
# Set to False to bypass login and go directly to main window (Testing mode)
# ═══════════════════════════════════════════════════════════════════════════
LOGIN_ENABLED = os.environ.get("AC_LOGIN_ENABLED", "0").lower() in ("1", "true", "yes")  # off by default (single-owner desktop use)
# ═══════════════════════════════════════════════════════════════════════════

if not LOGIN_ENABLED:
    print("[INFO] Login is disabled (single-owner mode). Set AC_LOGIN_ENABLED=1 to require login.")


class Application:
    """Main application class for PySide6-based AC Service Billing"""

    def __init__(self):
        # Enable high-performance Qt attributes before QApplication creation
        from PySide6.QtCore import Qt
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_CompressHighFrequencyEvents, True)
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

        # Initialize Qt application first (QSharedMemory needs QApplication)
        self.app = QApplication(sys.argv)
        self.app.setApplicationName(APP_NAME)
        self.app.setApplicationVersion(APP_VERSION)

        # Clean shutdown on quit
        self.app.aboutToQuit.connect(self._on_about_to_quit)

        # Acquire single instance lock after QApplication exists
        self._shared_mem = _acquire_single_instance_lock()

        # Set application-wide font and corporate icon
        font = QFont('Segoe UI', 10)
        self.app.setFont(font)

        from PySide6.QtGui import QIcon
        from config import RESOURCE_DIR
        icon_path = RESOURCE_DIR / 'assets' / 'app_icon.ico'
        if not icon_path.exists():
            icon_path = RESOURCE_DIR / 'assets' / 'Logo.png'
        if icon_path.exists():
            self.app.setWindowIcon(QIcon(str(icon_path)))

        # Global auto-capitalize
        from utils.text_capitalizer import install_auto_capitalize
        install_auto_capitalize(self.app)

        # Global mouse wheel & touchpad scroll protection (prevents accidental price/qty changes)
        from utils.scroll_filter import install_scroll_protection
        install_scroll_protection(self.app)

        # Initialize database connection
        self.db = None
        self.main_window = None
        self.login_window = None
        self.user_data = None

        # Setup database
        self._setup_database()

        # Show splash screen
        self._show_splash()

        # Show login window after splash
        QTimer.singleShot(500, self._show_login)

    def _on_about_to_quit(self):
        """Clean shutdown — stop all timers, workers, close DB."""
        try:
            # Clean up all views in main window
            if self.main_window:
                self.main_window.close()
        except Exception:
            pass
        try:
            # Close database connection
            if self.db:
                self.db.close()
        except Exception:
            pass
        try:
            # Run WAL checkpoint on shutdown
            from config import DB_PATH
            if DB_PATH.exists():
                import sqlite3
                try:
                    conn = sqlite3.connect(str(DB_PATH))
                    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                    conn.close()
                except Exception:
                    pass
        except Exception:
            pass

    def _setup_database(self):
        """Initialize database connection"""
        try:
            self.db = DatabaseConnection()
            print("[OK] Database connected successfully")
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                None,
                "Database Error",
                f"Cannot connect to database:\n{str(e)}\n\nPlease check your database configuration."
            )
            sys.exit(1)

    def _show_splash(self):
        """Show application splash screen"""
        try:
            splash_pix = QPixmap(str(LOGO_PATH))
            if splash_pix.isNull():
                splash_pix = QPixmap(400, 300)
                splash_pix.fill(Qt.GlobalColor.white)

            self.splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint)
            self.splash.showMessage(
                f"\n\n{APP_NAME}\nVersion {APP_VERSION}\n\nStarting...",
                Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
                Qt.GlobalColor.darkBlue
            )
            self.splash.show()
            self.app.processEvents()
        except Exception as e:
            print(f"Splash screen error: {e}")
            self.splash = None

    def _show_login(self):
        """Show login window or bypass based on LOGIN_ENABLED setting"""
        if LOGIN_ENABLED:
            print("[INFO] Login system ENABLED")
            if self.splash:
                self.splash.finish(self.app.activeWindow() if self.app.activeWindow() else None)

            from views.login_view import LoginWindow
            self.login_window = LoginWindow(on_login_success=self._on_login_success)
            self.login_window.show()
        else:
            print("[INFO] Login system BYPASSED (Development mode)")
            if self.splash:
                self.splash.finish(self.app.activeWindow() if self.app.activeWindow() else None)

            self._show_main_window_direct()

    def _on_login_success(self, user_data):
        """Handle successful login"""
        self.user_data = user_data

        if self.login_window:
            self.login_window.close()
            self.login_window = None

        self._show_main_window()

    def _show_main_window(self):
        """Show main application window with authenticated user data"""
        from views.main_window import MainWindow

        self.main_window = MainWindow(
            user_data=self.user_data,
            on_logout=self._on_logout
        )
        self.main_window.show()

    def _show_main_window_direct(self):
        """Show main window directly without login"""
        from views.main_window import MainWindow
        from utils.session_manager import get_session

        admin_user = self._load_admin_user()
        session = get_session()
        session.login(admin_user)

        if self.splash:
            self.splash.finish(self.app.activeWindow() if self.app.activeWindow() else None)

        self.main_window = MainWindow(
            user_data=admin_user,
            on_logout=self._on_logout
        )
        self.main_window.show()

    def _load_admin_user(self):
        """Load admin user from users table so profile edits persist after restart"""
        try:
            user = self.db.execute_query(
                "SELECT id, username, full_name, email, phone, is_active FROM users WHERE id = %s",
                (1,), fetch_one=True
            )
            if user:
                return user
        except Exception as e:
            print(f"[WARN] Could not load admin user from DB: {e}")

        return {
            'id': 1,
            'username': 'admin',
            'full_name': 'Administrator',
            'email': 'admin@anshaircool.com',
            'phone': '',
            'is_active': True,
        }

    def _on_logout(self):
        """Handle logout"""
        if self.main_window:
            self.main_window.close()
            self.main_window = None

        self._show_login()

    def run(self):
        """Start the application"""
        sys.exit(self.app.exec())


def main():
    """Main entry point"""

    # Run startup validation before anything else
    if not _validate_startup():
        sys.exit(1)

    # Create and run application
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
