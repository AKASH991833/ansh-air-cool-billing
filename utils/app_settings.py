"""
Application Settings - Cached in-process for fast repeated reads.

PERFORMANCE FIX:
  Before: every get_setting() call opened a new DatabaseConnection and ran
          a full SQL query -> 13+ ms per call, 13 calls on startup = ~170ms wasted.
  After:  first call loads all settings once into a module-level dict (_cache).
          Every subsequent call returns instantly from memory.
  Cache is invalidated whenever save_setting() is called so edits propagate.
"""
import threading

_cache: dict = {}          # settings key -> value
_cache_loaded: bool = False
_lock = threading.Lock()


def _load_cache() -> None:
    """Load all settings from DB into the module-level cache (once per process)."""
    global _cache, _cache_loaded
    try:
        from database.db_connection import DatabaseConnection
        from controllers.settings_controller import SettingsController
        db = DatabaseConnection()
        sc = SettingsController(db)
        _cache = sc.get_application_settings() or {}
        _cache_loaded = True
        print(f"[SETTINGS] Loaded {len(_cache)} settings from database")
    except Exception as exc:
        print(f"[SETTINGS] Warning: could not load settings ({exc})")
        _cache = {}
        _cache_loaded = True   # don't retry on every call after failure


def get_all_settings() -> dict:
    """Return all application settings as a dict (cached after first call)."""
    global _cache_loaded
    if not _cache_loaded:
        with _lock:
            if not _cache_loaded:   # double-checked locking
                _load_cache()
    return _cache


def get_setting(key: str, default: str = '') -> str:
    """Return a single setting value by key (O(1) after first call)."""
    return get_all_settings().get(key, default)


def save_setting(key: str, value) -> bool:
    """Persist a setting to the database and invalidate the in-process cache."""
    global _cache, _cache_loaded
    try:
        from database.db_connection import DatabaseConnection
        from controllers.settings_controller import SettingsController
        db = DatabaseConnection()
        sc = SettingsController(db)
        result = sc.save_setting(key, value)
        # Invalidate cache so next get_setting() re-reads fresh values
        with _lock:
            _cache_loaded = False
            _cache = {}
        return result
    except Exception as exc:
        print(f"[SETTINGS] Error saving setting '{key}': {exc}")
        return False


def invalidate_cache() -> None:
    """Force-expire the settings cache (call after bulk settings save)."""
    global _cache, _cache_loaded
    with _lock:
        _cache_loaded = False
        _cache = {}
