"""
Input validators for AC Service Billing Software
"""
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

class Validators:
    """Input validation utilities"""
    
    @staticmethod
    def validate_name(name):
        """Validate person/business name"""
        if not name or not name.strip():
            return False, "Name is required"
        
        name = name.strip()
        if len(name) < 2:
            return False, "Name must be at least 2 characters"
        
        if len(name) > 100:
            return False, "Name must be less than 100 characters"
        
        if not re.match(r'^[\w\s\.\-\'à-üÀ-Üá-éíóúñçÀ-ÿā-žĀ-Žа-яА-ЯёЁα-ωΑ-Ω.,()]+$', name, re.UNICODE):
            if not all(c.isalpha() or c in " .'-()," for c in name.strip()):
                return False, "Name contains invalid characters"
        
        return True, "Valid name"
    
    @staticmethod
    def validate_mobile(mobile):
        """Validate Indian mobile number"""
        if not mobile or not mobile.strip():
            return False, "Mobile number is required"
        
        mobile = mobile.strip()
        
        # Remove any spaces, dashes, or plus signs
        mobile = re.sub(r'[\s\+\-]', '', mobile)
        
        # Remove 91 country code prefix if present (common Indian format: 9199XXXXXXXX)
        if mobile.startswith('91') and len(mobile) == 12:
            mobile = mobile[2:]
        
        # Check if it's a 10-digit number starting with 6-9
        if not re.match(r'^[6-9]\d{9}$', mobile):
            return False, "Invalid Indian mobile number (10 digits starting with 6-9)"
        
        return True, "Valid mobile number"
    
    @staticmethod
    def validate_email(email):
        """Validate email address"""
        if not email or not email.strip():
            return True, ""  # Email is optional
        
        email = email.strip()
        
        # Basic email regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            return False, "Invalid email address"
        
        return True, "Valid email"
    
    @staticmethod
    def validate_amount(amount):
        """Validate monetary amount"""
        if not amount:
            return False, "Amount is required"
        
        try:
            # Convert to Decimal for precise monetary calculations
            amount_dec = Decimal(str(amount))
            
            if amount_dec < 0:
                return False, "Amount cannot be negative"
            
            if amount_dec > Decimal('99999999.99'):
                return False, "Amount is too large"
            
            # Check decimal places
            if abs(amount_dec.as_tuple().exponent) > 2:
                return False, "Amount can have maximum 2 decimal places"
            
            return True, "Valid amount"
        except (InvalidOperation, ValueError):
            return False, "Invalid amount format"
    
    @staticmethod
    def validate_quantity(quantity):
        """Validate quantity (positive integer)"""
        if not quantity:
            return False, "Quantity is required"
        
        try:
            qty = int(quantity)
            
            if qty <= 0:
                return False, "Quantity must be positive"
            
            if qty > 9999:
                return False, "Quantity is too large"
            
            return True, "Valid quantity"
        except ValueError:
            return False, "Quantity must be a whole number"
    
    @staticmethod
    def validate_gst_percentage(gst_percent):
        """Validate GST percentage"""
        if not gst_percent:
            return True, ""  # GST can be 0
        
        try:
            gst = float(gst_percent)
            
            if gst < 0 or gst > 100:
                return False, "GST percentage must be between 0 and 100"
            
            return True, "Valid GST percentage"
        except ValueError:
            return False, "Invalid GST percentage"
    
    @staticmethod
    def validate_date(date_str, date_format='%Y-%m-%d'):
        """Validate date string"""
        if not date_str:
            return False, "Date is required"
        
        try:
            datetime.strptime(date_str, date_format)
            return True, "Valid date"
        except ValueError:
            return False, f"Invalid date format. Use {date_format}"
    
    @staticmethod
    def validate_address(address):
        """Validate address"""
        if not address or not address.strip():
            return True, ""  # Address is optional in some cases
        
        address = address.strip()
        
        if len(address) < 5:
            return False, "Address is too short"
        
        if len(address) > 500:
            return False, "Address is too long (max 500 characters)"
        
        return True, "Valid address"
    
    @staticmethod
    def validate_pan_number(pan):
        """Validate PAN number"""
        if not pan or not pan.strip():
            return True, ""  # PAN is optional
        
        pan = pan.strip().upper()
        
        # PAN format: ABCDE1234F
        pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
        
        if not re.match(pattern, pan):
            return False, "Invalid PAN number format (e.g., ABCDE1234F)"
        
        return True, "Valid PAN"
    
    @staticmethod
    def validate_gst_number(gst):
        """Validate GST number"""
        if not gst or not gst.strip():
            return True, ""  # GST is optional
        
        gst = gst.strip().upper()
        
        # GST format: 27ABCDE1234F1Z5
        pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
        
        if not re.match(pattern, gst):
            return False, "Invalid GST number format (e.g., 27ABCDE1234F1Z5)"
        
        return True, "Valid GST"
    
    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        if not password:
            return False, "Password is required"
        
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"
        
        # Check for special characters
        special_chars = r'[!@#$%^&*(),.?":{}|<>]'
        if not re.search(special_chars, password):
            return False, "Password must contain at least one special character"
        
        return True, "Strong password"
    
    @staticmethod
    def validate_invoice_number(invoice_no):
        """Validate invoice number format"""
        if not invoice_no or not invoice_no.strip():
            return False, "Invoice number is required"
        
        invoice_no = invoice_no.strip().upper()
        
        # Accepted formats:
        # INV-202605-0001 (New professional format - recommended)
        # INV-QA-005 (Legacy short format)
        # INV20260501223045 (Legacy timestamp format)
        import re
        patterns = [
            r'^INV-\d{6}-\d{4}$',      # INV-202605-0001 (New)
            r'^INV-[A-Z]{2,}-\d{3,}$', # INV-QA-005 (Legacy short)
            r'^INV\d{14,}$',           # INV20260501223045 (Legacy timestamp)
        ]
        
        if not any(re.match(p, invoice_no) for p in patterns):
            return False, "Invalid invoice number format. Expected: INV-YYYYMM-XXXX"
        
        return True, "Valid invoice number"
    
    @staticmethod
    def validate_ac_details(ac_type, ton_capacity=None, star_rating=None):
        """Validate AC details"""
        from utils.app_settings import get_setting
        valid_types = get_setting('ac_types', 'Split,Window,Cassette,Tower,Other').split(',')
        
        if ac_type not in valid_types:
            return False, f"Invalid AC type. Must be one of: {', '.join(valid_types)}"
        
        if ton_capacity:
            valid_ton = ['0.75', '1.0', '1.5', '2.0', '2.5', '3.0', '3.5', '4.0', '5.0']
            if ton_capacity not in valid_ton:
                return False, f"Invalid ton capacity. Must be one of: {', '.join(valid_ton)}"
        
        if star_rating:
            valid_stars = get_setting('star_ratings', 'N/A,1,2,3,4,5').split(',')
            if star_rating not in valid_stars:
                return False, f"Invalid star rating. Must be one of: {', '.join(valid_stars)}"
        
        return True, "Valid AC details"
    
    @staticmethod
    def validate_payment_mode(payment_mode):
        """Validate payment mode"""
        valid_modes = ['Cash', 'UPI', 'Cheque', 'Card', 'Bank Transfer', 'Pending']
        
        if payment_mode not in valid_modes:
            return False, f"Invalid payment mode. Must be one of: {', '.join(valid_modes)}"
        
        return True, "Valid payment mode"
    
    @staticmethod
    def validate_percentage(percentage, field_name="Percentage"):
        """Validate percentage value"""
        try:
            pct = float(percentage)
            
            if pct < 0 or pct > 100:
                return False, f"{field_name} must be between 0 and 100"
            
            return True, f"Valid {field_name.lower()}"
        except ValueError:
            return False, f"Invalid {field_name.lower()} value"
    
    @staticmethod
    def validate_commission_rate(rate):
        """Validate technician commission rate"""
        return Validators.validate_percentage(rate, "Commission rate")
    
    @staticmethod
    def validate_stock_quantity(quantity):
        """Validate stock quantity"""
        try:
            qty = int(quantity)
            
            if qty < 0:
                return False, "Stock quantity cannot be negative"
            
            if qty > 99999:
                return False, "Stock quantity is too large"
            
            return True, "Valid stock quantity"
        except ValueError:
            return False, "Stock quantity must be a whole number"
    
    @staticmethod
    def validate_service_rate(rate):
        """Validate service/part rate"""
        return Validators.validate_amount(rate)
    
    @staticmethod
    def validate_customer_data(name, mobile, email=None, address=None):
        """Validate complete customer data"""
        # Validate name
        valid, message = Validators.validate_name(name)
        if not valid:
            return False, message
        
        # Validate mobile
        valid, message = Validators.validate_mobile(mobile)
        if not valid:
            return False, message
        
        # Validate email (optional)
        if email:
            valid, message = Validators.validate_email(email)
            if not valid:
                return False, message
        
        # Validate address (optional)
        if address:
            valid, message = Validators.validate_address(address)
            if not valid:
                return False, message
        
        return True, "Valid customer data"
    
    @staticmethod
    def validate_invoice_data(customer_name, customer_mobile, items):
        """Validate invoice data"""
        # Validate customer
        valid, message = Validators.validate_customer_data(customer_name, customer_mobile)
        if not valid:
            return False, message
        
        # Validate items
        if not items or len(items) == 0:
            return False, "Invoice must have at least one item"
        
        for item in items:
            if 'quantity' not in item or 'rate' not in item:
                return False, "Each item must have quantity and rate"
            
            valid, message = Validators.validate_quantity(item['quantity'])
            if not valid:
                return False, f"Invalid quantity for item: {message}"
            
            valid, message = Validators.validate_amount(item['rate'])
            if not valid:
                return False, f"Invalid rate for item: {message}"
        
        return True, "Valid invoice data"
    
    @staticmethod
    def sanitize_input(input_str):
        """Sanitize input string - uses parameterized queries, no manual stripping needed"""
        if not input_str:
            return ""
        return str(input_str).strip()

    @staticmethod
    def parse_money(money_str):
        """Parse money string to Decimal"""
        try:
            # Remove currency symbol and commas
            clean_str = re.sub(r'[^\d.]', '', money_str)
            return Decimal(clean_str)
        except (InvalidOperation, ValueError):
            return Decimal('0')
