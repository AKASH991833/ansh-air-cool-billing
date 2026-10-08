
"""
WhatsApp Message Templates - Dynamic from DB
"""
from database.db_connection import DatabaseContext
from utils.app_settings import get_setting

def get_message_template(template_key):
    """Get a message template by key from DB with robust encoding"""
    try:
        with DatabaseContext() as db:
            query = "SELECT template_body FROM whatsapp_templates WHERE template_key = %s"
            result = db.execute_query(query, (template_key,), fetch_one=True)
            if result and result['template_body']:
                return result['template_body']
    except Exception as e:
        print(f"[ERROR] DB Template load failed: {e}")
    
    # Fallback to hardcoded defaults
    return _get_fallback_template(template_key)

def format_message(template_key, **kwargs):
    """Format a message template with variables and clean emojis"""
    from config import WHATSAPP_NUMBER
    if 'company_phone' not in kwargs:
        kwargs['company_phone'] = WHATSAPP_NUMBER
    if 'company_name' not in kwargs:
        kwargs['company_name'] = get_setting('company_name', 'Your Company Name')
    
    template = get_message_template(template_key)
    if not template:
        return None
    
    try:
        # Standardize data types for formatting
        for k, v in kwargs.items():
            if v is None: kwargs[k] = ""
            
        return template.format(**kwargs)
    except KeyError as e:
        print(f"Missing variable in template {template_key}: {e}")
        return template

def _get_fallback_template(key):
    # Using Unicode escape sequences for emojis to ensure cross-platform compatibility
    fallbacks = {
        'service_confirm': "\u2705 *Service Request Confirmed*\n\nNamaste {name}!\n\n\ud83d\udd27 Service: {service_type}\n\ud83d\udccd Location: {location}\n\n*{company_name}*",
        'payment_reminder': "\ud83d\udcb3 *Payment Reminder*\n\nNamaste {name},\n\n\ud83d\udcc4 Invoice: {invoice_number}\n\ud83d\udcb0 Amount: {amount}\n\n*{company_name}*",
        'thank_you': "\ud83c\udf1f *Thank You!*\n\nNamaste {name},\n\n*{company_name}*",
        'invoice_share': "\ud83d\udcc4 *New Invoice*\n\nNamaste {customer_name},\n\nAapka bill ready hai.\n\n\ud83d\udd22 Invoice: {invoice_number}\n\ud83d\udcb0 Total: {total_amount}\n\ud83d\udcc5 Date: {invoice_date}\n\n*{company_name}*"
    }
    return fallbacks.get(key, "Namaste {name}!")
