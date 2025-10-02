# test_textbelt.py - Test TextBelt API directly
import requests

def test_textbelt_directly():
    phone = "+254797971425"  # Your number in international format
    message = "Direct test from TextBelt API"
    
    print(f"Testing TextBelt API directly...")
    print(f"To: {phone}")
    print(f"Message: {message}")
    
    try:
        resp = requests.post('https://textbelt.com/text', {
            'phone': phone,
            'message': message,
            'key': 'textbelt',
        })
        
        result = resp.json()
        print(f"\nTextBelt Response: {result}")
        
        if result.get('success'):
            print("✅ SMS sent successfully via TextBelt!")
            print(f"Quota remaining: {result.get('quotaRemaining', 'Unknown')}")
        else:
            print("❌ Failed to send SMS via TextBelt")
            print(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == '__main__':
    test_textbelt_directly()