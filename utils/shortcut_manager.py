"""
Customizable Keyboard Shortcuts Manager
Users can create and customize their own shortcuts
"""
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtCore import QObject
from database.db_connection import DatabaseConnection

# Default shortcuts (Standardized to Office/Excel style where possible)
DEFAULT_SHORTCUTS = {
    'new_invoice': {'key': 'Ctrl+N', 'action': 'New Invoice', 'view': 'invoice'},
    'save': {'key': 'Ctrl+S', 'action': 'Save / Submit', 'view': 'save'},
    'search': {'key': 'Ctrl+F', 'action': 'Search / Find', 'view': 'search'},
    'refresh': {'key': 'F5', 'action': 'Refresh Data', 'view': 'refresh'},
    'print': {'key': 'Ctrl+P', 'action': 'Print Document', 'view': 'print'},
    'close': {'key': 'Esc', 'action': 'Close / Back', 'view': 'close'},
    'inventory': {'key': 'Ctrl+I', 'action': 'Inventory (Stock)', 'view': 'inventory'},
    'reports': {'key': 'Ctrl+R', 'action': 'Reports / Analytics', 'view': 'reports'},
    'dashboard': {'key': 'Ctrl+D', 'action': 'Dashboard', 'view': 'dashboard'},
    'customers': {'key': 'Ctrl+Shift+C', 'action': 'Customers List', 'view': 'customers'},
    'technicians': {'key': 'Ctrl+T', 'action': 'Technicians List', 'view': 'technicians'},
    'daily_logs': {'key': 'Ctrl+L', 'action': 'Daily Work & Cost Logs', 'view': 'daily logs'},
    'settings': {'key': 'Ctrl+,', 'action': 'Settings', 'view': 'settings'},
    'whatsapp': {'key': 'Ctrl+W', 'action': 'Send WhatsApp', 'view': 'whatsapp'},
}


class ShortcutManager(QObject):
    """Manages customizable keyboard shortcuts"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._shortcuts = {}
        self._shortcuts_refs = []
        self._loaded = False
        self._initialized = True

    def load_shortcuts(self):
        """Load shortcuts from database, fallback to defaults"""
        self._shortcuts = dict(DEFAULT_SHORTCUTS)
        try:
            db = DatabaseConnection()
            rows = db.execute_query(
                "SELECT setting_key, setting_value FROM app_settings WHERE setting_key LIKE 'shortcut_%'",
                fetch_all=True
            )
            if rows:
                for row in rows:
                    key_name = row['setting_key'].replace('shortcut_', '')
                    if key_name in self._shortcuts:
                        self._shortcuts[key_name]['key'] = row['setting_value']
        except Exception:
            pass
        self._loaded = True
        return self._shortcuts

    def save_shortcut(self, name, key_sequence):
        """Save a custom shortcut to database"""
        self._shortcuts[name]['key'] = key_sequence
        try:
            db = DatabaseConnection()
            db.execute_query(
                "INSERT INTO app_settings (setting_key, setting_value, updated_at) "
                "VALUES (%s, %s, NOW()) ON DUPLICATE KEY UPDATE setting_value = %s, updated_at = NOW()",
                (f'shortcut_{name}', key_sequence, key_sequence)
            )
            return True
        except Exception as e:
            print(f"[SHORTCUT] Save failed: {e}")
            return False

    def reset_to_defaults(self):
        """Reset all shortcuts to defaults"""
        self._shortcuts = dict(DEFAULT_SHORTCUTS)
        try:
            db = DatabaseConnection()
            db.execute_query(
                "DELETE FROM app_settings WHERE setting_key LIKE 'shortcut_%'"
            )
            return True
        except Exception:
            return False

    def get_shortcut(self, name):
        """Get key sequence for a shortcut"""
        if not self._loaded:
            self.load_shortcuts()
        return self._shortcuts.get(name, {}).get('key', '')

    def get_all_shortcuts(self):
        """Get all shortcuts with metadata"""
        if not self._loaded:
            self.load_shortcuts()
        return dict(self._shortcuts)

    def apply_shortcuts_to_window(self, main_window, callback=None):
        """Apply all shortcuts to a main window instance"""
        self.load_shortcuts()
        # Clear existing
        for sc in self._shortcuts_refs:
            try:
                sc.deleteLater()
            except Exception:
                pass
        self._shortcuts_refs = []

        if callback:
            for name, sc_data in self._shortcuts.items():
                key = sc_data.get('key')
                if key:
                    action = sc_data.get('action', '')
                    shortcut = QShortcut(QKeySequence(key), main_window)
                    shortcut.activated.connect(lambda n=name, a=action: callback(n, a))
                    self._shortcuts_refs.append(shortcut)
        else:
            view_map = {
                'new_invoice': lambda: main_window._switch_to_view('invoice') if hasattr(main_window, '_switch_to_view') else None,
                'dashboard': lambda: main_window._switch_to_view('dashboard') if hasattr(main_window, '_switch_to_view') else None,
                'customers': lambda: main_window._switch_to_view('customers') if hasattr(main_window, '_switch_to_view') else None,
                'settings': lambda: main_window._switch_to_view('settings') if hasattr(main_window, '_switch_to_view') else None,
                'daily_logs': lambda: main_window._switch_to_view('daily logs') if hasattr(main_window, '_switch_to_view') else None,
                'technicians': lambda: main_window._switch_to_view('technicians') if hasattr(main_window, '_switch_to_view') else None,
                'inventory': lambda: main_window._switch_to_view('inventory') if hasattr(main_window, '_switch_to_view') else None,
                'reports': lambda: main_window._switch_to_view('reports') if hasattr(main_window, '_switch_to_view') else None,
                'save': lambda: self._trigger_current_view_action(main_window, '_save_data'),
                'refresh': lambda: self._trigger_current_view_action(main_window, 'refresh_data'),
                'close': lambda: self._trigger_current_view_action(main_window, 'close'),
            }

            for name, sc_data in self._shortcuts.items():
                key = sc_data.get('key')
                if key and name in view_map:
                    cb = view_map[name]
                    if cb:
                        shortcut = QShortcut(QKeySequence(key), main_window)
                        shortcut.activated.connect(cb)
                        self._shortcuts_refs.append(shortcut)

    def _trigger_current_view_action(self, main_window, method_name):
        """Helper to trigger a method on the currently active stacked widget"""
        if hasattr(main_window, 'stacked_widget'):
            current_widget = main_window.stacked_widget.currentWidget()
            if current_widget and hasattr(current_widget, method_name):
                getattr(current_widget, method_name)()
            elif method_name == 'close' and hasattr(main_window, 'close'):
                main_window.close()


# Global accessor
def get_shortcut_manager():
    return ShortcutManager()
