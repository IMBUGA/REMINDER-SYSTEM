# sms_apis.py - Free SMS APIs
import requests
import json

class FreeSMSAPI:
    def __init__(self):
        pass
    
    def send_sms_textbelt(self, phone_number, message):
        """TextBelt - Free SMS API (1 free SMS per day)"""
        try:
            # Remove + and spaces
            clean_phone = phone_number.replace('+', '').replace(' ', '')
            
            resp = requests.post('https://textbelt.com/text', {
                'phone': clean_phone,
                'message': message,
                'key': 'textbelt',  # Free key
            })
            
            result = resp.json()
            print(f"TextBelt response: {result}")
            return result.get('success', False), result.get('text', 'Unknown response')
            
        except Exception as e:
            return False, f"TextBelt error: {str(e)}"
    
    def send_sms_callmebot(self, phone_number, message):
        """CallMeBot - Free SMS via WhatsApp API"""
        try:
            # This requires phone in international format without +
            clean_phone = phone_number.replace('+', '').replace(' ', '')
            
            # CallMeBot WhatsApp API (free for testing)
            url = f"https://api.callmebot.com/whatsapp.php?phone={clean_phone}&text={message}&apikey=123456"
            
            resp = requests.get(url)
            if resp.status_code == 200:
                return True, "Message sent via CallMeBot"
            else:
                return False, f"CallMeBot error: {resp.status_code}"
                
        except Exception as e:
            return False, f"CallMeBot error: {str(e)}"

# Test the APIs
if __name__ == '__main__':
    sms_api = FreeSMSAPI()
    
    # Test TextBelt
    success, message = sms_api.send_sms_textbelt('254797971425', 'Test from TextBelt API')
    print(f"TextBelt: {success} - {message}")