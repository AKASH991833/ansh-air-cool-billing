"""
Privacy Manager - Enterprise Privacy Shield for Sensitive Financial Data
Allows toggling masking of income, revenues, card metrics, and payment records.
"""
from utils.app_settings import get_setting, save_setting
from utils.event_bus import EventBus
import threading


class PrivacyManager:
    """Central manager for application-wide privacy / financial masking state."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_state()
        return cls._instance

    def _init_state(self):
        # By default, software always opens with Privacy Shield ACTIVE for enterprise privacy
        # Checks 'privacy_start_on_launch' (default True)
        pref_val = get_setting('privacy_start_on_launch', 'true')
        if isinstance(pref_val, bool):
            saved_pref = pref_val
        else:
            saved_pref = str(pref_val).lower() in ('true', '1', 'yes')
        self._is_enabled = saved_pref

    def is_privacy_enabled(self) -> bool:
        """Return True if privacy mode is active (financial data should be masked)."""
        return self._is_enabled

    def set_privacy_enabled(self, enabled: bool, persist: bool = False) -> None:
        """Enable or disable privacy mode and notify all listening components."""
        if self._is_enabled == enabled:
            return
        self._is_enabled = enabled
        if persist:
            try:
                save_setting('privacy_mode_enabled', 'true' if enabled else 'false')
            except Exception as e:
                print(f"[PRIVACY] Warning: could not persist setting: {e}")

        # Notify UI components through global EventBus
        EventBus().emit_privacy_mode_toggled(enabled)

    def toggle_privacy(self, persist: bool = False) -> bool:
        """Toggle privacy mode on/off and return the new state."""
        new_state = not self._is_enabled
        self.set_privacy_enabled(new_state, persist=persist)
        return new_state

    @staticmethod
    def mask_value(value_str: str, symbol: str = "₹", mask_pattern: str = "••••••") -> str:
        """
        Mask a string value cleanly.
        If symbol is present, preserves symbol: e.g. '₹ 1,50,000' -> '₹ ••••••'
        """
        if not value_str:
            return mask_pattern
        value_str = str(value_str).strip()
        for sym in [symbol, '₹', '$', '€', '£', 'Rs.', 'Rs ']:
            if sym and value_str.startswith(sym):
                return f"{sym} {mask_pattern}"
        return mask_pattern


_global_privacy_manager = None

def get_privacy_manager() -> PrivacyManager:
    """Helper to get the singleton PrivacyManager."""
    global _global_privacy_manager
    if _global_privacy_manager is None:
        _global_privacy_manager = PrivacyManager()
    return _global_privacy_manager
