# test_simple_sms.py - Simple SMS test without external modules
import urllib.request
import urllib.parse
import json

def test_textbelt_simple():
    phone = "+254797971425"  # Your number in international format
    message = "Test from Simple TextBelt API"
    
    print("=" * 50)
    print("Testing TextBelt SMS API")
    print("=" * 50)
    print(f"To: {phone}")
    print(f"Message: {message}")
    print("=" * 50)
    
    try:
        # Prepare the data
        data = urllib.parse.urlencode({
            'phone': phone,
            'message': message,
            'key': 'textbelt'
        }).encode()
        
        # Make the request
        req = urllib.request.Request(
            'https://textbelt.com/text',
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        # Get the response
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            
        print(f"\nTextBelt Response: {json.dumps(result, indent=2)}")
        
        if result.get('success'):
            print("\n✅ SUCCESS: SMS sent via TextBelt!")
            print(f"📱 Quota remaining: {result.get('quotaRemaining', 'Unknown')}")
        else:
            print(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check your internet connection")
        print("2. Make sure the phone number is correct: 254797971425")
        print("3. TextBelt limit: 1 free SMS per day per number")

if __name__ == '__main__':
    test_textbelt_simple()