"""
WhatsApp Helper Utility
Free WhatsApp Click-to-Chat integration
"""
import webbrowser
from urllib.parse import quote
import re


class WhatsAppHelper:
    """
    Free WhatsApp Click-to-Chat Helper
    WhatsApp number is loaded from DB settings; falls back to config.py
    """
    
    BASE_URL = "https://wa.me"
    DEFAULT_COUNTRY_CODE = "91"  # India

    @staticmethod
    def get_company_number():
        from config import WHATSAPP_NUMBER as FALLBACK
        try:
            from utils.app_settings import get_setting
            return get_setting('whatsapp_number', FALLBACK)
        except Exception:
            return FALLBACK
    
    @staticmethod
    def clean_phone_number(phone):
        """
        Clean phone number - remove spaces, special chars
        Returns: Phone number with country code (e.g., 919876543210)
        """
        if not phone:
            return None
        
        # Remove all non-digit characters
        clean_phone = re.sub(r'\D', '', str(phone))
        
        # Remove leading zeros
        clean_phone = clean_phone.lstrip('0')
        
        # Add country code if not present
        if not clean_phone.startswith(WhatsAppHelper.DEFAULT_COUNTRY_CODE):
            clean_phone = WhatsAppHelper.DEFAULT_COUNTRY_CODE + clean_phone
        
        return clean_phone
    
    @staticmethod
    def send_message(phone, message):
        """
        Open WhatsApp with pre-filled message

        Args:
            phone (str): Phone number (with or without country code)
            message (str): Message to send

        Returns:
            bool: True if WhatsApp opened successfully, False otherwise
        """
        try:
            # Clean phone number
            clean_phone = WhatsAppHelper.clean_phone_number(phone)

            if not clean_phone:
                print("Error: Invalid phone number")
                return False

            if not message:
                print("Error: Message is empty")
                return False

            # Encode message for URL
            encoded_message = quote(message.strip())

            # Create WhatsApp URL
            url = f"{WhatsAppHelper.BASE_URL}/{clean_phone}?text={encoded_message}"

            # Open in default browser
            webbrowser.open(url)

            print(f"✅ WhatsApp opened for {clean_phone}")
            return True

        except Exception as e:
            print(f"❌ Error sending WhatsApp message: {str(e)}")
            return False

    @staticmethod
    def send_message_with_attachment(phone, message, file_path=None):
        """
        Open WhatsApp with message and attachment (PDF/Image)
        NOTE: WhatsApp Web API doesn't support direct file upload
        This opens WhatsApp with message, user needs to attach file manually
        
        Args:
            phone (str): Phone number
            message (str): Message to send
            file_path (str): Path to file to attach (optional)

        Returns:
            bool: True if WhatsApp opened successfully
        """
        try:
            # First open WhatsApp with message
            success = WhatsAppHelper.send_message(phone, message)
            
            if success and file_path:
                # Show instructions for manual attachment
                print(f"\n📎 File to attach: {file_path}")
                print("👉 WhatsApp Web mein jaakar manually file attach karein:")
                print(f"   1. 📎 (Attach) icon par click karein")
                print(f"   2. 📄 Document select karein")
                print(f"   3. {file_path} file choose karein")
                print(f"   4. Send button dabayein")
            
            return success
            
        except Exception as e:
            print(f"❌ Error sending WhatsApp with attachment: {str(e)}")
            return False
    
    @staticmethod
    def send_template(template_name, **kwargs):
        """
        Send pre-defined template message
        
        Args:
            template_name (str): Name of the template (from whatsapp_messages.py)
            **kwargs: Variables to fill in the template
        
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        try:
            from utils.whatsapp_messages import format_message
            
            # Get phone number from kwargs
            phone = kwargs.get('phone', '')
            
            if not phone:
                print("Error: Phone number is required")
                return False
            
            # Format message with variables
            message = format_message(template_name, **kwargs)
            
            if not message:
                print(f"Error: Template '{template_name}' not found")
                return False
            
            # Send message
            return WhatsAppHelper.send_message(phone, message)
            
        except Exception as e:
            print(f"❌ Error sending template: {str(e)}")
            return False
    
    @staticmethod
    def send_multiple_messages(phone_list, message):
        """
        Send same message to multiple phone numbers
        
        Args:
            phone_list (list): List of phone numbers
            message (str): Message to send
        
        Returns:
            dict: {'success': count, 'failed': count}
        """
        success_count = 0
        failed_count = 0
        
        for phone in phone_list:
            if WhatsAppHelper.send_message(phone, message):
                success_count += 1
            else:
                failed_count += 1
        
        return {
            'success': success_count,
            'failed': failed_count
        }
    
    @staticmethod
    def create_shareable_link(phone, message):
        """
        Create a shareable WhatsApp link
        
        Args:
            phone (str): Phone number
            message (str): Pre-filled message
        
        Returns:
            str: WhatsApp URL
        """
        clean_phone = WhatsAppHelper.clean_phone_number(phone)
        encoded_message = quote(message.strip())
        
        return f"{WhatsAppHelper.BASE_URL}/{clean_phone}?text={encoded_message}"
    
    @staticmethod
    def open_chat(phone):
        """
        Just open WhatsApp chat (no pre-filled message)
        
        Args:
            phone (str): Phone number
        
        Returns:
            bool: True if opened successfully
        """
        clean_phone = WhatsAppHelper.clean_phone_number(phone)
        
        if not clean_phone:
            return False
        
        url = f"{WhatsAppHelper.BASE_URL}/{clean_phone}"
        webbrowser.open(url)
        
        return True


# Convenience functions for direct import
def send_whatsapp(phone, message):
    """Quick function to send WhatsApp message"""
    return WhatsAppHelper.send_message(phone, message)


def send_whatsapp_template(template_name, **kwargs):
    """Quick function to send template message"""
    return WhatsAppHelper.send_template(template_name, **kwargs)


def create_whatsapp_link(phone, message):
    """Quick function to create WhatsApp link"""
    return WhatsAppHelper.create_shareable_link(phone, message)
