"""
Data formatters for AC Service Billing Software
"""
from datetime import datetime, date
from decimal import Decimal
from utils.app_settings import get_setting
import logging

# Set up logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def _format_indian(amount):
    """Format number in Indian lakh/crore grouping (e.g., 1,23,456.78)"""
    if amount < 0:
        return '-' + _format_indian(-amount)
    integer_part = int(amount)
    decimal_part = int(round((amount - integer_part) * 100))
    if integer_part < 1000:
        return f"{integer_part}.{decimal_part:02d}" if decimal_part else str(integer_part)
    s = str(integer_part)
    last_3 = s[-3:]
    rest = s[:-3]
    if rest:
        groups = []
        while len(rest) > 2:
            groups.append(rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.append(rest)
        result = ','.join(reversed(groups)) + ',' + last_3
    else:
        result = last_3
    return result + (f".{decimal_part:02d}" if decimal_part else "")


class Formatters:
    """Data formatting utilities"""
    
    @staticmethod
    def format_currency(amount):
        """Format amount as currency with proper symbol"""
        try:
            if isinstance(amount, str):
                amount = Decimal(amount)
            amount_float = float(amount)
            symbol = get_setting("currency_symbol", "₹")
            if amount_float >= 10000000:
                return f"{symbol}{amount_float/10000000:.2f}Cr"
            elif amount_float >= 100000:
                lakh = int(amount_float // 100000)
                remainder = amount_float % 100000
                return f"{symbol}{_format_indian(lakh)}L {_format_indian(remainder)}" if remainder else f"{symbol}{_format_indian(lakh)}L"
            else:
                return f"{symbol}{_format_indian(amount_float)}"
        except (ValueError, TypeError):
            symbol = get_setting("currency_symbol", "₹")
            return f"{symbol}0.00"
    
    @staticmethod
    def format_date(date_obj, format_str='%d-%m-%Y'):
        """Format date object (handles string, date, and datetime)"""
        if not date_obj:
            return ""
        if isinstance(date_obj, (datetime, date)):
            return date_obj.strftime(format_str)
        if isinstance(date_obj, str):
            s = date_obj.strip()
            for fmt in ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%d-%m-%Y', '%d/%m/%Y', '%d %m %Y', '%Y/%m/%d'):
                try:
                    return datetime.strptime(s[:19] if ' ' in s and len(s) > 10 else s[:10], fmt).strftime(format_str)
                except ValueError:
                    continue
            return s.replace(' ', '-')
        return str(date_obj)
    
    @staticmethod
    def format_datetime(datetime_obj, format_str='%d-%m-%Y %I:%M %p'):
        """Format datetime object"""
        if not datetime_obj:
            return ""
        
        if isinstance(datetime_obj, str):
            try:
                # Try to parse the string
                datetime_obj = datetime.fromisoformat(datetime_obj.replace('Z', '+00:00'))
            except ValueError:
                return datetime_obj
        
        if isinstance(datetime_obj, datetime):
            return datetime_obj.strftime(format_str)
        
        return str(datetime_obj)
    
    @staticmethod
    def format_mobile(mobile):
        """Format Indian mobile number"""
        if not mobile:
            return ""
        
        mobile = str(mobile).strip()
        
        # Remove any non-digit characters
        digits = ''.join(filter(str.isdigit, mobile))
        
        if len(digits) == 10:
            return f"{digits[:5]} {digits[5:]}"
        elif len(digits) > 10:
            return f"+{digits[:-10]} {digits[-10:-5]} {digits[-5:]}"
        
        return mobile
    
    @staticmethod
    def format_gst(gst_number):
        """Format GST number with spaces"""
        if not gst_number:
            return ""
        
        gst = str(gst_number).strip().upper()
        
        # Remove any spaces
        gst = gst.replace(' ', '')
        
        if len(gst) == 15:
            return f"{gst[:2]} {gst[2:7]} {gst[7:11]} {gst[11:13]} {gst[13:]}"
        
        return gst
    
    @staticmethod
    def format_percentage(value, decimal_places=2):
        """Format percentage"""
        try:
            if isinstance(value, str):
                value = Decimal(value)
            
            return f"{value:.{decimal_places}f}%"
        except (ValueError, TypeError):
            return "0.00%"
    
    @staticmethod
    def format_quantity(quantity, unit=""):
        """Format quantity with unit"""
        try:
            qty = int(quantity)
            return f"{qty:,} {unit}".strip()
        except (ValueError, TypeError):
            return f"0 {unit}".strip()
    
    @staticmethod
    def format_address(address, max_lines=3, max_length=50):
        """Format address for display"""
        if not address:
            return ""
        
        # Split by newlines or commas
        lines = address.replace('\n', ',').split(',')
        
        # Trim whitespace and filter empty lines
        lines = [line.strip() for line in lines if line.strip()]
        
        # Truncate long lines
        formatted_lines = []
        for line in lines[:max_lines]:
            if len(line) > max_length:
                line = line[:max_length-3] + "..."
            formatted_lines.append(line)
        
        return "\n".join(formatted_lines)
    
    @staticmethod
    def format_title(text):
        """Format text to title case."""
        if not text:
            return ""
        return str(text).title()

    @staticmethod
    def format_upper(text):
        """Convert text to uppercase."""
        if not text:
            return ""
        return str(text).upper()

    @staticmethod
    def format_sentence(text):
        """Convert text to sentence case (first letter of first word capitalized, rest lowercase)."""
        if not text:
            return ""
        text_str = str(text).strip()
        if not text_str:
            return ""
        return text_str[0].upper() + text_str[1:].lower()

    @staticmethod
    def generate_invoice_number(db):
        """Generate next invoice number in format: INV-YYYYMM-XXXX
        
        Real-world format used by professional billing systems.
        Example: INV-202605-0001, INV-202605-0002
        - INV = Invoice prefix
        - 202605 = Year + Month (May 2026)
        - 0001 = Sequential serial number (resets each month)
        
        This format is:
        - Professional and readable
        - Organized by month
        - Easy to search and reference
        - Prevents duplicates
        - Industry standard
        """
        from datetime import datetime
        
        # Load settings
        prefix = 'INV'
        starting_num = 1
        try:
            res = db.execute_query("SELECT setting_key, setting_value FROM app_settings WHERE setting_key IN ('invoice_prefix', 'starting_invoice_number')", fetch_all=True)
            if res:
                for r in res:
                    if r['setting_key'] == 'invoice_prefix': prefix = r['setting_value']
                    if r['setting_key'] == 'starting_invoice_number': starting_num = int(r['setting_value'])
        except Exception:
            pass

        year_month = datetime.now().strftime('%Y%m')
        
        try:
            query = f"""
                SELECT MAX(CAST(SUBSTRING_INDEX(invoice_number, '-', -1) AS UNSIGNED)) as max_num
                FROM invoices
                WHERE invoice_number LIKE %s
            """
            result = db.execute_query(query, (f'{prefix}-{year_month}-%',), fetch_one=True)
            
            if result and result['max_num']:
                next_num = int(result['max_num']) + 1
            else:
                next_num = starting_num
            
            return f"{prefix}-{year_month}-{next_num:04d}"
            
        except Exception as e:
            print(f"[ERROR] Failed to generate invoice number: {e}")
            # Fallback: use timestamp
            return f"{prefix}-{year_month}-{datetime.now().strftime('%H%M%S')}"

    @staticmethod
    def format_invoice_number(invoice_no):
        """Format invoice number for display"""
        if not invoice_no:
            return ""
        
        invoice_no = str(invoice_no).strip().upper()
        
        # Add space after prefix if not present
        if len(invoice_no) > 3 and invoice_no[3].isdigit():
            return f"{invoice_no[:3]} {invoice_no[3:]}"
        
        return invoice_no
    
    @staticmethod
    def format_payment_status(status):
        """Format payment status with color indicators"""
        status = Formatters.format_title(status)
        
        status_map = {
            'Paid': ('✅ Paid', '#10b981'),
            'Partial': ('⏳ Partial', '#f59e0b'),
            'Pending': ('⏰ Pending', '#ef4444'),
            'Overdue': ('⚠️ Overdue', '#dc2626'),
            'Cancelled': ('❌ Cancelled', '#6b7280')
        }
        
        if status in status_map:
            return status_map[status]
        
        return (status, '#6b7280')
    
    @staticmethod
    def format_ac_type(ac_type):
        """Format AC type"""
        ac_type = Formatters.format_title(ac_type)
        
        type_map = {
            'Split': '🔧 Split AC',
            'Window': '🪟 Window AC',
            'Cassette': '💠 Cassette AC',
            'Tower': '🗼 Tower AC',
            'Other': '❓ Other Type'
        }
        
        return type_map.get(ac_type, ac_type)
    
    @staticmethod
    def format_payment_mode(mode):
        """Format payment mode"""
        mode = Formatters.format_title(mode)
        
        mode_map = {
            'Cash': '💵 Cash',
            'UPI': '📱 UPI',
            'Cheque': '🏦 Cheque',
            'Card': '💳 Card',
            'Bank Transfer': '🏛️ Bank Transfer',
            'Pending': '⏳ Pending'
        }
        
        return mode_map.get(mode, mode)
    
    @staticmethod
    def format_yes_no(value):
        """Format boolean as Yes/No"""
        if isinstance(value, bool):
            return "Yes" if value else "No"
        
        if isinstance(value, str):
            value_lower = value.lower().strip()
            if value_lower in ['true', 'yes', '1', 'active']:
                return "Yes"
            elif value_lower in ['false', 'no', '0', 'inactive']:
                return "No"
        
        return str(value)
    
    @staticmethod
    def format_duration(minutes):
        """Format duration in minutes to hours and minutes"""
        try:
            mins = int(minutes)
            hours = mins // 60
            remaining_mins = mins % 60
            
            if hours > 0 and remaining_mins > 0:
                return f"{hours}h {remaining_mins}m"
            elif hours > 0:
                return f"{hours}h"
            else:
                return f"{remaining_mins}m"
        except (ValueError, TypeError):
            return "0m"
    
    @staticmethod
    def format_file_size(bytes_size):
        """Format file size in human readable format"""
        try:
            bytes_size = int(bytes_size)
            
            for unit in ['B', 'KB', 'MB', 'GB']:
                if bytes_size < 1024.0:
                    return f"{bytes_size:.1f} {unit}"
                bytes_size /= 1024.0
            
            return f"{bytes_size:.1f} TB"
        except (ValueError, TypeError):
            return "0 B"
    
    @staticmethod
    def format_list(items, separator=', ', max_items=5):
        """Format list of items"""
        if not items:
            return ""
        
        if isinstance(items, str):
            return items
        
        items = list(items)
        
        if len(items) > max_items:
            displayed = items[:max_items]
            return separator.join(map(str, displayed)) + f" and {len(items) - max_items} more..."
        
        return separator.join(map(str, items))
    
    @staticmethod
    def format_rating(rating, max_stars=5):
        """Format rating with stars"""
        try:
            rating_val = float(rating)
            stars = '★' * int(rating_val) + '☆' * (max_stars - int(rating_val))
            return f"{stars} ({rating_val:.1f})"
        except (ValueError, TypeError):
            return "☆☆☆☆☆ (0.0)"
    
    @staticmethod
    def format_table_row(data, columns, col_widths):
        """Format data as a table row"""
        row_parts = []
        
        for i, col in enumerate(columns):
            value = str(data.get(col, ''))
            width = col_widths[i] if i < len(col_widths) else 20
            
            # Truncate or pad the value
            if len(value) > width:
                value = value[:width-3] + '...'
            else:
                value = value.ljust(width)
            
            row_parts.append(value)
        
        return ' | '.join(row_parts)
    
    @staticmethod
    def format_invoice_summary(invoice_data):
        """Format invoice summary for display"""
        summary_parts = []
        
        if invoice_data.get('invoice_number'):
            summary_parts.append(f"Invoice: {invoice_data['invoice_number']}")
        
        if invoice_data.get('customer_name'):
            # Apply title case to customer name in summary
            summary_parts.append(f"Customer: {Formatters.format_title(invoice_data['customer_name'])}")
        
        if invoice_data.get('total_amount'):
            summary_parts.append(f"Amount: {Formatters.format_currency(invoice_data['total_amount'])}")
        
        if invoice_data.get('created_at'):
            summary_parts.append(f"Date: {Formatters.format_date(invoice_data['created_at'])}")
        
        if invoice_data.get('payment_status'):
            status_text, _ = Formatters.format_payment_status(invoice_data['payment_status'])
            summary_parts.append(f"Status: {status_text}")
        
        return ' | '.join(summary_parts)
    
    @staticmethod
    def format_technician_summary(tech_data):
        """Format technician summary for display"""
        summary_parts = []
        
        if tech_data.get('name'):
            # Apply title case to technician name in summary
            summary_parts.append(Formatters.format_title(tech_data['name']))
        
        if tech_data.get('mobile'):
            summary_parts.append(f"📱 {Formatters.format_mobile(tech_data['mobile'])}")
        
        if tech_data.get('services_done'):
            summary_parts.append(f"🔧 {tech_data['services_done']} services")
        
        if tech_data.get('amount_collected'):
            summary_parts.append(f"💰 {Formatters.format_currency(tech_data['amount_collected'])}")
        
        return ' • '.join(summary_parts)
    
    @staticmethod
    def create_display_text(data, template):
        """Create display text using template"""
        result = template
        
        for key, value in data.items():
            placeholder = f'{{{key}}}'
            
            # Apply general title case formatting for relevant keys
            if 'name' in key.lower() or 'address' in key.lower() or 'city' in key.lower() or 'state' in key.lower():
                formatted_value = Formatters.format_title(value)
            elif 'date' in key.lower():
                formatted_value = Formatters.format_date(value)
            elif 'amount' in key.lower() or 'price' in key.lower() or 'rate' in key.lower():
                formatted_value = Formatters.format_currency(value)
            elif 'mobile' in key.lower() or 'phone' in key.lower():
                formatted_value = Formatters.format_mobile(value)
            elif 'percentage' in key.lower() or 'percent' in key.lower():
                formatted_value = Formatters.format_percentage(value)
            elif 'status' in key.lower():
                status_text, _ = Formatters.format_payment_status(value)
                formatted_value = status_text
            else:
                formatted_value = str(value)
            
            result = result.replace(placeholder, formatted_value)
        
        return result