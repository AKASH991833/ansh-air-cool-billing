"""
Global Event Bus for Real-time Updates
Centralized pub-sub system for cross-component communication
"""
from PySide6.QtCore import QObject, Signal, QTimer


class EventBus(QObject):
    """
    Global event bus for real-time updates across all views.
    Uses Qt signals for thread-safe communication.
    """
    
    # Signals for different events
    settings_updated = Signal(dict)  # Emitted when settings are saved
    master_data_updated = Signal(str)  # Emitted when master data changes (Services/Parts/Brands)
    shop_details_updated = Signal(dict)  # Emitted when shop details change
    user_profile_updated = Signal(dict)  # Emitted when user profile changes
    invoice_created = Signal(dict)  # Emitted when new invoice is created
    customer_updated = Signal(dict)  # Emitted when customer data changes
    privacy_mode_toggled = Signal(bool)  # Emitted when privacy/masking mode is toggled
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            super().__init__()
            self._initialized = True
            self._pending_updates = []
            
            # Debounce timer for batch updates
            self._debounce_timer = QTimer()
            self._debounce_timer.setSingleShot(True)
            self._debounce_timer.timeout.connect(self._emit_pending_updates)
    
    def emit_settings_updated(self, settings_data):
        """Emit settings updated event with debounce"""
        self._pending_updates.append(('settings', settings_data))
        self._debounce_timer.start(100)  # 100ms debounce
    
    def emit_master_data_updated(self, data_type):
        """Emit master data updated event (debounced, no double-emit)"""
        self._pending_updates.append(('master_data', data_type))
        self._debounce_timer.start(100)
    
    def emit_shop_details_updated(self, shop_data):
        """Emit shop details updated event (debounced, no double-emit)"""
        self._pending_updates.append(('shop', shop_data))
        self._debounce_timer.start(100)
    
    def emit_user_profile_updated(self, user_data):
        """Emit user profile updated event (debounced, no double-emit)"""
        self._pending_updates.append(('profile', user_data))
        self._debounce_timer.start(100)
    
    def emit_invoice_created(self, invoice_data):
        """Emit invoice created event"""
        self.invoice_created.emit(invoice_data)
    
    def emit_customer_updated(self, customer_data):
        """Emit customer updated event"""
        self.customer_updated.emit(customer_data)

    def emit_privacy_mode_toggled(self, enabled: bool):
        """Emit privacy mode toggled event immediately without debounce"""
        self.privacy_mode_toggled.emit(enabled)
    
    def _emit_pending_updates(self):
        """Emit all pending updates (deduplicated - only last of each type)"""
        seen = {}
        for update_type, data in self._pending_updates:
            seen[update_type] = data
        for update_type, data in seen.items():
            if update_type == 'settings':
                self.settings_updated.emit(data)
            elif update_type == 'master_data':
                self.master_data_updated.emit(data)
            elif update_type == 'shop':
                self.shop_details_updated.emit(data)
            elif update_type == 'profile':
                self.user_profile_updated.emit(data)
        self._pending_updates.clear()


# Global accessor
def get_event_bus():
    """Get global event bus instance"""
    return EventBus()
