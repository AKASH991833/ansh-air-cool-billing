"""
Multi-language Support System
Hindi and English translations for the entire application
"""
from config import APP_NAME

# Translations dictionary
TRANSLATIONS = {
    'en': {
        # App
        'app_name': APP_NAME,
        'welcome': 'Welcome',
        'loading': 'Loading...',
        'ready': 'Ready',
        'error': 'Error',
        'success': 'Success',
        'warning': 'Warning',
        'confirm': 'Confirm',
        'cancel': 'Cancel',
        'save': 'Save',
        'delete': 'Delete',
        'edit': 'Edit',
        'search': 'Search',
        'print': 'Print',
        'export': 'Export',
        'refresh': 'Refresh',
        'no_data': 'No data available',
        'yes': 'Yes',
        'no': 'No',
        'ok': 'OK',

        # Navigation
        'dashboard': 'Dashboard',
        'invoice': 'New Invoice',
        'invoice_management': 'Manage Invoices',
        'amc': 'AMC Contracts',
        'customers': 'Customers',
        'technicians': 'Technicians',
        'daily_logs': 'Daily Work & Cost Logs',
        'online_requests': 'Online Requests',
        'settings': 'Settings',

        # Dashboard
        'total_customers': 'Total Customers',
        'total_invoices': 'Total Invoices',
        'total_revenue': 'Total Revenue',
        'pending_payments': 'Pending Payments',
        'today_summary': "Today's Summary",
        'services_done': 'Services Done',
        'payment_received': 'Payment Received',
        'new_customers': 'New Customers',
        'revenue_trend': 'Revenue Trend',
        'top_services': 'Top Services',
        'expired_amc': 'Expired AMC',
        'active_amc': 'Active AMC',

        # Invoice
        'invoice_number': 'Invoice Number',
        'customer_name': 'Customer Name',
        'customer_mobile': 'Mobile Number',
        'customer_address': 'Address',
        'ac_details': 'AC Details',
        'ac_brand': 'AC Brand',
        'ac_type': 'AC Type',
        'ton_capacity': 'Ton Capacity',
        'star_rating': 'Star Rating',
        'inverter_type': 'Inverter Type',
        'technician': 'Technician',
        'items': 'Items',
        'service': 'Service',
        'part': 'Part',
        'quantity': 'Qty',
        'rate': 'Rate',
        'amount': 'Amount',
        'subtotal': 'Subtotal',
        'gst': 'GST',
        'total': 'Total',
        'advance': 'Advance',
        'balance': 'Balance',
        'payment_mode': 'Payment Mode',
        'payment_status': 'Payment Status',
        'notes': 'Notes',

        # Customer
        'customer_history': 'Customer History',
        'total_services': 'Total Services',
        'last_visit': 'Last Visit',
        'add_customer': 'Add Customer',
        'edit_customer': 'Edit Customer',

        # Technician
        'commission': 'Commission',
        'performance': 'Performance',
        'assign': 'Assign',

        # Settings
        'language': 'Language',
        'shortcuts': 'Keyboard Shortcuts',
        'customize_shortcuts': 'Customize Shortcuts',
        'backup': 'Backup & Restore',
        'shop_details': 'Shop Details',
        'profile': 'Profile',
        'change_password': 'Change Password',

        # Common
        'search_placeholder': 'Search customer by name or phone...',
        'no_results': 'No customers found',
        'are_you_sure': 'Are you sure?',
        'operation_successful': 'Operation completed successfully',
        'operation_failed': 'Operation failed',
    },
    'hi': {
        # App
        'app_name': 'अंश एयर कूल - बिलिंग सिस्टम',
        'welcome': 'स्वागत है',
        'loading': 'लोड हो रहा है...',
        'ready': 'तैयार',
        'error': 'त्रुटि',
        'success': 'सफल',
        'warning': 'चेतावनी',
        'confirm': 'पुष्टि करें',
        'cancel': 'रद्द करें',
        'save': 'सहेजें',
        'delete': 'हटाएं',
        'edit': 'संपादित करें',
        'search': 'खोजें',
        'print': 'प्रिंट करें',
        'export': 'निर्यात करें',
        'refresh': 'रिफ्रेश करें',
        'no_data': 'कोई डेटा उपलब्ध नहीं',
        'yes': 'हाँ',
        'no': 'नहीं',
        'ok': 'ठीक है',

        # Navigation
        'dashboard': 'डैशबोर्ड',
        'invoice': 'नया इनवॉइस',
        'invoice_management': 'इनवॉइस प्रबंधन',
        'amc': 'एएमसी अनुबंध',
        'customers': 'ग्राहक',
        'technicians': 'तकनीशियन',
        'daily_logs': 'दैनिक कार्य व खर्च रजिस्टर',
        'online_requests': 'ऑनलाइन अनुरोध',
        'settings': 'सेटिंग्स',

        # Dashboard
        'total_customers': 'कुल ग्राहक',
        'total_invoices': 'कुल इनवॉइस',
        'total_revenue': 'कुल आय',
        'pending_payments': 'लंबित भुगतान',
        'today_summary': 'आज का सारांश',
        'services_done': 'सेवाएं की गईं',
        'payment_received': 'भुगतान प्राप्त',
        'new_customers': 'नए ग्राहक',
        'revenue_trend': 'आय का रुझान',
        'top_services': 'शीर्ष सेवाएं',
        'expired_amc': 'समाप्त एएमसी',
        'active_amc': 'सक्रिय एएमसी',

        # Invoice
        'invoice_number': 'इनवॉइस नंबर',
        'customer_name': 'ग्राहक का नाम',
        'customer_mobile': 'मोबाइल नंबर',
        'customer_address': 'पता',
        'ac_details': 'एसी विवरण',
        'ac_brand': 'एसी ब्रांड',
        'ac_type': 'एसी प्रकार',
        'ton_capacity': 'टन क्षमता',
        'star_rating': 'स्टार रेटिंग',
        'inverter_type': 'इन्वर्टर प्रकार',
        'technician': 'तकनीशियन',
        'items': 'आइटम',
        'service': 'सेवा',
        'part': 'पार्ट',
        'quantity': 'मात्रा',
        'rate': 'दर',
        'amount': 'राशि',
        'subtotal': 'उप-योग',
        'gst': 'जीएसटी',
        'total': 'कुल',
        'advance': 'अग्रिम',
        'balance': 'शेष',
        'payment_mode': 'भुगतान मोड',
        'payment_status': 'भुगतान स्थिति',
        'notes': 'नोट्स',

        # Customer
        'customer_history': 'ग्राहक इतिहास',
        'total_services': 'कुल सेवाएं',
        'last_visit': 'पिछली विज़िट',
        'add_customer': 'ग्राहक जोड़ें',
        'edit_customer': 'ग्राहक संपादित करें',

        # Technician
        'commission': 'कमीशन',
        'performance': 'प्रदर्शन',
        'assign': 'असाइन करें',

        # Settings
        'language': 'भाषा',
        'shortcuts': 'कीबोर्ड शॉर्टकट',
        'customize_shortcuts': 'शॉर्टकट कस्टमाइज़ करें',
        'backup': 'बैकअप और रिस्टोर',
        'shop_details': 'दुकान विवरण',
        'profile': 'प्रोफ़ाइल',
        'change_password': 'पासवर्ड बदलें',

        # Common
        'search_placeholder': 'नाम या मोबाइल से ग्राहक खोजें...',
        'no_results': 'कोई ग्राहक नहीं मिला',
        'are_you_sure': 'क्या आपको यकीन है?',
        'operation_successful': 'कार्य सफलतापूर्वक पूरा हुआ',
        'operation_failed': 'कार्य विफल रहा',
    }
}


class LanguageManager:
    """Singleton language manager"""

    _instance = None
    _current_lang = 'en'

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def set_language(self, lang_code):
        """Set current language (en/hi)"""
        if lang_code in TRANSLATIONS:
            self._current_lang = lang_code
            # Save to DB
            try:
                from database.db_connection import DatabaseConnection
                db = DatabaseConnection()
                db.execute_query(
                    "INSERT INTO app_settings (setting_key, setting_value, updated_at) "
                    "VALUES (%s, %s, NOW()) ON DUPLICATE KEY UPDATE setting_value = %s, updated_at = NOW()",
                    ('app_language', lang_code, lang_code)
                )
            except Exception:
                pass
            return True
        return False

    def get_language(self):
        """Get current language code"""
        return self._current_lang

    def load_saved_language(self):
        """Load language from database"""
        try:
            from database.db_connection import DatabaseConnection
            db = DatabaseConnection()
            result = db.execute_query(
                "SELECT setting_value FROM app_settings WHERE setting_key = 'app_language'",
                fetch_one=True
            )
            if result and result.get('setting_value') in TRANSLATIONS:
                self._current_lang = result['setting_value']
        except Exception:
            pass
        return self._current_lang

    def get_text(self, key):
        """Get translated text for a key"""
        lang = TRANSLATIONS.get(self._current_lang, TRANSLATIONS['en'])
        return lang.get(key, TRANSLATIONS['en'].get(key, key))

    def get_all_keys(self):
        """Get all translation keys"""
        return list(TRANSLATIONS['en'].keys())

    def is_hindi(self):
        return self._current_lang == 'hi'


# Shortcut functions
_lang_manager = None


def get_language_manager():
    global _lang_manager
    if _lang_manager is None:
        _lang_manager = LanguageManager()
        _lang_manager.load_saved_language()
    return _lang_manager


def _(key):
    """Translate a key - shorthand function"""
    return get_language_manager().get_text(key)


def set_language(lang_code):
    return get_language_manager().set_language(lang_code)


def current_language():
    return get_language_manager().get_language()
