import smtplib
from dotenv import load_dotenv
import os

load_dotenv()

email = os.getenv('EMAIL_ADDRESS')
password = os.getenv('EMAIL_PASSWORD')

print("Testing email configuration...")
print(f"Email: {email}")
print(f"Password: {'*' * len(password) if password else 'NOT SET'}")

if not email or not password:
    print("❌ ERROR: Email or password not set in .env file")
else:
    try:
        # Test Gmail
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email, password)
        print("✅ SUCCESS: Gmail login works!")
        server.quit()
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("\nTry using Outlook:")
        try:
            server = smtplib.SMTP('smtp-mail.outlook.com', 587)
            server.starttls()
            server.login(email, password)
            print("✅ SUCCESS: Outlook login works!")
            server.quit()
        except Exception as e2:
            print(f"❌ Outlook also failed: {e2}")