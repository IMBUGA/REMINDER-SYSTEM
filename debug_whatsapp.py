# debug_whatsapp.py - Comprehensive WhatsApp test
import urllib.request
import urllib.parse

def test_whatsapp_directly():
    print("🧪 COMPREHENSIVE WHATSAPP DEBUG TEST")
    print("=" * 60)
    
    # Your details
    api_key = "7722049"
    test_phone = "254797971425"  # Your number in international format
    test_message = "Debug test from Medical Reminder System"
    
    print(f"🔑 API Key: {api_key}")
    print(f"📞 Test Phone: {test_phone}")
    print(f"💬 Test Message: {test_message}")
    print("=" * 60)
    
    try:
        # URL encode the message
        encoded_message = urllib.parse.quote(test_message)
        
        # Build the URL
        url = f"https://api.callmebot.com/whatsapp.php?phone={test_phone}&text={encoded_message}&apikey={api_key}"
        
        print(f"📡 Request URL:")
        print(f"   {url}")
        print("=" * 60)
        
        # Make the request
        print("🔄 Sending request...")
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as response:
            result = response.read().decode()
        
        print(f"📨 Response from CallMeBot:")
        print(f"   {result}")
        print("=" * 60)
        
        # Analyze the response
        if "message queued" in result.lower():
            print("✅ SUCCESS: Message queued for delivery!")
        elif "message sent" in result.lower():
            print("✅ SUCCESS: Message sent successfully!")
        elif "success" in result.lower():
            print("✅ SUCCESS: API call successful!")
        elif "error" in result.lower():
            print("❌ ERROR: API returned an error")
        elif "invalid" in result.lower():
            print("❌ ERROR: Invalid API key or phone number")
        else:
            print("⚠️ UNKNOWN: Unexpected response")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        print("This could be a network issue or API problem")

if __name__ == '__main__':
    test_whatsapp_directly()