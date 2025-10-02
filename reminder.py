# reminder.py (WHATSAPP AS PRIMARY MESSAGING, UPDATED WITH STAFF TABLE, PASSWORD RESET, AND WINDOWS COMPATIBILITY)
import sqlite3
import datetime
import urllib.request
import urllib.parse
import json
import time
import os
import shutil
import bcrypt
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ReminderSystem:
    def __init__(self):
        self.init_db()
        self.whatsapp_api_key = "7722049"
        self.secret_key = os.getenv('SECRET_KEY', 'medical-reminder-system-secret-key')
        self.serializer = URLSafeTimedSerializer(self.secret_key)
        print(f"🔑 WhatsApp API Key loaded: {self.whatsapp_api_key}")
    
    def init_db(self):
        # Backup database before initialization
        if os.path.exists('appointments.db'):
            backup_path = f"appointments_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy('appointments.db', backup_path)
            print(f"📁 Database backed up to {backup_path}")

        conn = sqlite3.connect('appointments.db')
        c = conn.cursor()
        
        # Create appointments table
        c.execute('''CREATE TABLE IF NOT EXISTS appointments
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      patient_name TEXT,
                      patient_phone TEXT,
                      doctor_name TEXT,
                      doctor_phone TEXT,
                      appointment_date TEXT,
                      appointment_time TEXT,
                      reminder_sent INTEGER DEFAULT 0,
                      whatsapp_sent INTEGER DEFAULT 0,
                      confirmation_sent INTEGER DEFAULT 0)''')
        
        # Create temporary staff table with new schema
        c.execute('''CREATE TABLE IF NOT EXISTS staff_temp
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT UNIQUE,
                      password_hash TEXT,
                      email TEXT UNIQUE)''')
        
        # Check if original staff table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='staff'")
        staff_table_exists = c.fetchone()
        
        if staff_table_exists:
            # Check if email column exists
            c.execute("PRAGMA table_info(staff)")
            columns = [info[1] for info in c.fetchall()]
            if 'email' not in columns:
                print("🔄 Migrating staff table to include email column...")
                # Copy data from old staff table to new one
                c.execute('''INSERT INTO staff_temp (id, username, password_hash)
                            SELECT id, username, password_hash FROM staff''')
                # Drop old staff table and rename new one
                c.execute('DROP TABLE staff')
                c.execute('ALTER TABLE staff_temp RENAME TO staff')
            else:
                # If email column exists, ensure staff_temp is dropped
                c.execute('DROP TABLE IF EXISTS staff_temp')
        else:
            # If no staff table, create it from staff_temp
            c.execute('ALTER TABLE staff_temp RENAME TO staff')
        
        # Check and add missing columns for appointments
        columns_to_check = ['whatsapp_sent', 'confirmation_sent']
        for column in columns_to_check:
            c.execute("PRAGMA table_info(appointments)")
            columns = [info[1] for info in c.fetchall()]
            if column not in columns:
                print(f"🔄 Adding {column} column to appointments table...")
                c.execute(f'ALTER TABLE appointments ADD COLUMN {column} INTEGER DEFAULT 0')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized with appointments and staff tables")

    def add_staff(self, username, password, email):
        """Add a new staff member with hashed password"""
        try:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            conn = sqlite3.connect('appointments.db')
            c = conn.cursor()
            c.execute('INSERT INTO staff (username, password_hash, email) VALUES (?, ?, ?)',
                     (username, hashed, email))
            conn.commit()
            conn.close()
            print(f"✅ Staff added: {username}")
            return True
        except sqlite3.IntegrityError:
            print(f"❌ Username {username} or email {email} already exists")
            return False
        except Exception as e:
            print(f"❌ Error adding staff: {str(e)}")
            return False

    def validate_staff(self, username, password):
        """Validate staff credentials"""
        conn = sqlite3.connect('appointments.db')
        c = conn.cursor()
        c.execute('SELECT password_hash FROM staff WHERE username = ?', (username,))
        result = c.fetchone()
        conn.close()
        if result and bcrypt.checkpw(password.encode('utf-8'), result[0]):
            print(f"✅ Staff login successful: {username}")
            return True
        print(f"❌ Staff login failed: {username}")
        return False

    def get_all_staff(self):
        """Retrieve all staff members"""
        conn = sqlite3.connect('appointments.db')
        c = conn.cursor()
        c.execute('SELECT id, username, email FROM staff')
        staff = c.fetchall()
        conn.close()
        return staff

    def delete_staff(self, staff_id):
        """Delete a staff member"""
        conn = sqlite3.connect('appointments.db')
        c = conn.cursor()
        c.execute('DELETE FROM staff WHERE id = ?', (staff_id,))
        conn.commit()
        conn.close()
        print(f"✅ Staff ID {staff_id} deleted")

    def get_staff_by_email(self, email):
        """Retrieve staff by email for password reset"""
        conn = sqlite3.connect('appointments.db')
        c = conn.cursor()
        c.execute('SELECT id, username FROM staff WHERE email = ?', (email,))
        staff = c.fetchone()
        conn.close()
        return staff

    def generate_reset_token(self, email):
        """Generate a password reset token"""
        return self.serializer.dumps(email, salt='password-reset')

    def validate_reset_token(self, token, max_age=3600):
        """Validate a password reset token (expires after max_age seconds)"""
        try:
            email = self.serializer.loads(token, salt='password-reset', max_age=max_age)
            return email
        except Exception:
            return None

    def reset_password(self, username, new_password):
        """Update staff password"""
        try:
            hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            conn = sqlite3.connect('appointments.db')
            c = conn.cursor()
            c.execute('UPDATE staff SET password_hash = ? WHERE username = ?', (hashed, username))
            conn.commit()
            conn.close()
            print(f"✅ Password reset for {username}")
            return True
        except Exception as e:
            print(f"❌ Error resetting password: {str(e)}")
            return False

    def add_appointment(self, patient_name, patient_phone, doctor_name, doctor_phone, appointment_date, appointment_time):
        conn = sqlite3.connect('appointments.db')
        c = conn.cursor()
        c.execute('''INSERT INTO appointments 
                     (patient_name, patient_phone, doctor_name, doctor_phone, appointment_date, appointment_time)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                     (patient_name, patient_phone, doctor_name, doctor_phone, appointment_date, appointment_time))
        conn.commit()
        conn.close()
        
        print(f"✅ Appointment added: {patient_name} with Dr. {doctor_name} on {appointment_date} at {appointment_time}")
        
        # Send immediate WhatsApp confirmation
        self.send_appointment_confirmation(patient_name, patient_phone, doctor_name, doctor_phone, appointment_date, appointment_time)
        
        return True

    def send_appointment_confirmation(self, patient_name, patient_phone, doctor_name, doctor_phone, appointment_date, appointment_time):
        """Send immediate WhatsApp confirmation when appointment is created"""
        print(f"\n💬 SENDING APPOINTMENT CONFIRMATION VIA WHATSAPP")
        
        # Format date for better readability
        formatted_date = datetime.datetime.strptime(appointment_date, '%Y-%m-%d').strftime('%B %d, %Y')
        
        # Patient confirmation message
        patient_message = f"""✅ *Appointment Confirmed*

Hello {patient_name},

Your appointment has been scheduled:

*Doctor:* Dr. {doctor_name}
*Date:* {formatted_date}
*Time:* {appointment_time}

Please arrive 10 minutes early. 🏥"""

        # Doctor notification message
        doctor_message = f"""✅ *Appointment Confirmed*

Hello Dr. {doctor_name},

You have a new appointment:

*Patient:* {patient_name}
*Date:* {formatted_date}
*Time:* {appointment_time}
*Patient Phone:* {patient_phone}

Please confirm your availability. 🏥"""

        # Send to patient
        print(f"👤 Sending confirmation to patient: {patient_name}")
        patient_success, patient_msg = self.send_whatsapp_message(patient_phone, patient_message)
        
        time.sleep(2)  # Brief delay
        
        # Send to doctor
        print(f"👨‍⚕️ Sending notification to doctor: Dr. {doctor_name}")
        doctor_success, doctor_msg = self.send_whatsapp_message(doctor_phone, doctor_message)
        
        # Update database if confirmations were sent
        if patient_success or doctor_success:
            conn = sqlite3.connect('appointments.db')
            c = conn.cursor()
            # Find the latest appointment for this patient/doctor combination
            c.execute('''SELECT id FROM appointments 
                         WHERE patient_name = ? AND doctor_name = ? AND appointment_date = ? AND appointment_time = ?
                         ORDER BY id DESC LIMIT 1''',
                         (patient_name, doctor_name, appointment_date, appointment_time))
            appointment = c.fetchone()
            if appointment:
                c.execute('UPDATE appointments SET confirmation_sent = 1 WHERE id = ?', (appointment[0],))
                conn.commit()
            conn.close()
        
        return patient_success and doctor_success

    def get_all_appointments(self):
        conn = sqlite3.connect('appointments.db')
        c = conn.cursor()
        c.execute('''SELECT * FROM appointments ORDER BY appointment_date, appointment_time''')
        appointments = c.fetchall()
        conn.close()
        return appointments

    def get_tomorrows_appointments(self):
        """Get appointments for tomorrow specifically"""
        conn = sqlite3.connect('appointments.db')
        c = conn.cursor()
        
        # Calculate tomorrow's date
        tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).date().isoformat()
        
        print(f"📅 Looking for appointments on: {tomorrow}")
        
        c.execute('''SELECT * FROM appointments 
                     WHERE appointment_date = ? AND reminder_sent = 0''', (tomorrow,))
        appointments = c.fetchall()
        conn.close()
        return appointments

    def delete_appointment(self, appointment_id):
        conn = sqlite3.connect('appointments.db')
        c = conn.cursor()
        c.execute('DELETE FROM appointments WHERE id = ?', (appointment_id,))
        conn.commit()
        conn.close()

    def safe_get_appointment_data(self, appointment):
        """Safely extract appointment data with defaults"""
        return {
            'id': appointment[0] if len(appointment) > 0 else None,
            'patient_name': appointment[1] if len(appointment) > 1 else 'Unknown',
            'patient_phone': appointment[2] if len(appointment) > 2 else '',
            'doctor_name': appointment[3] if len(appointment) > 3 else 'Unknown',
            'doctor_phone': appointment[4] if len(appointment) > 4 else '',
            'appointment_date': appointment[5] if len(appointment) > 5 else '',
            'appointment_time': appointment[6] if len(appointment) > 6 else '',
            'reminder_sent': appointment[7] if len(appointment) > 7 else 0,
            'whatsapp_sent': appointment[8] if len(appointment) > 8 else 0,
            'confirmation_sent': appointment[9] if len(appointment) > 9 else 0
        }

    def send_whatsapp_message(self, phone_number, message):
        """Send message via WhatsApp API"""
        try:
            # Clean phone number
            clean_phone = phone_number.replace(' ', '').replace('-', '')
            if not clean_phone.startswith('+'):
                clean_phone = '+' + clean_phone
            
            # URL encode message
            encoded_message = urllib.parse.quote(message)
            
            # Build URL
            url = f"https://api.callmebot.com/whatsapp.php?phone={clean_phone}&text={encoded_message}&apikey={self.whatsapp_api_key}"
            
            print(f"📡 WhatsApp API URL: {url}")
            
            # Send request
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as response:
                result = response.read().decode()
            
            print(f"📨 API Response: {result}")
            
            # Check if successful
            if any(success_word in result.lower() for success_word in ['message queued', 'message sent', 'success']):
                return True, "WhatsApp message sent successfully! ✅"
            else:
                return False, f"WhatsApp API: {result}"
                
        except Exception as e:
            return False, f"WhatsApp error: {str(e)}"

    def send_reminder(self, phone_number, message):
        """Send reminder via WhatsApp"""
        print(f"\n" + "="*50)
        print(f"🚀 SENDING REMINDER TO: {phone_number}")
        print("="*50)
        
        success, result_msg = self.send_whatsapp_message(phone_number, message)
        
        if success:
            print(f"✅ SUCCESS: {result_msg}")
        else:
            print(f"❌ FAILED: {result_msg}")
        print("="*50)
        
        return success, result_msg

    def check_reminders(self):
        """Check and send reminders for appointments tomorrow"""
        print(f"\n🎯 CHECKING REMINDERS - {datetime.datetime.now()}")
        
        appointments = self.get_tomorrows_appointments()
        
        if not appointments:
            print("❌ No appointments found for tomorrow")
            return []
        
        results = []
        conn = sqlite3.connect('appointments.db')
        c = conn.cursor()
        
        for appointment in appointments:
            # Safely extract appointment data
            appt_data = self.safe_get_appointment_data(appointment)
            
            appt_id = appt_data['id']
            patient_name = appt_data['patient_name']
            patient_phone = appt_data['patient_phone']
            doctor_name = appt_data['doctor_name']
            doctor_phone = appt_data['doctor_phone']
            appt_date = appt_data['appointment_date']
            appt_time = appt_data['appointment_time']
            
            print(f"\n📝 Processing Appointment ID: {appt_id}")
            print(f"👤 Patient: {patient_name} ({patient_phone})")
            print(f"👨‍⚕️ Doctor: Dr. {doctor_name} ({doctor_phone})")
            print(f"🕐 Time: {appt_time} on {appt_date}")
            
            # Format date for better readability
            formatted_date = datetime.datetime.strptime(appt_date, '%Y-%m-%d').strftime('%B %d, %Y')
            
            # Patient reminder message
            patient_message = f"""💊 *Appointment Reminder*

Hello {patient_name},

This is a friendly reminder about your appointment tomorrow:

*Doctor:* Dr. {doctor_name}
*Date:* {formatted_date}
*Time:* {appt_time}

Please bring any relevant medical reports or medications. 🏥"""

            print(f"\n👤 SENDING PATIENT REMINDER...")
            whatsapp_patient_success, whatsapp_patient_msg = self.send_reminder(patient_phone, patient_message)
            
            time.sleep(3)  # Wait 3 seconds between messages
            
            # Doctor reminder message
            doctor_message = f"""💊 *Appointment Reminder*

Hello Dr. {doctor_name},

Reminder: You have an appointment tomorrow:

*Patient:* {patient_name}
*Date:* {formatted_date}
*Time:* {appt_time}
*Patient Phone:* {patient_phone}

Please confirm your schedule. 🏥"""

            print(f"\n👨‍⚕️ SENDING DOCTOR REMINDER...")
            whatsapp_doctor_success, whatsapp_doctor_msg = self.send_reminder(doctor_phone, doctor_message)
            
            # Mark reminder as sent only if both WhatsApp were successful
            if whatsapp_patient_success and whatsapp_doctor_success:
                c.execute('UPDATE appointments SET reminder_sent = 1, whatsapp_sent = 1 WHERE id = ?', (appt_id,))
                print(f"✅ Marked appointment {appt_id} as reminded")
            elif whatsapp_patient_success or whatsapp_doctor_success:
                # If only one succeeded, mark as partial
                c.execute('UPDATE appointments SET whatsapp_sent = 1 WHERE id = ?', (appt_id,))
                print(f"⚠️ Marked appointment {appt_id} as partially reminded")
            else:
                print(f"❌ Failed to send reminders for appointment {appt_id}")
            
            results.append({
                'appointment_id': appt_id,
                'patient_name': patient_name,
                'doctor_name': doctor_name,
                'patient_phone': patient_phone,
                'doctor_phone': doctor_phone,
                'whatsapp_patient_success': whatsapp_patient_success,
                'whatsapp_patient_message': whatsapp_patient_msg,
                'whatsapp_doctor_success': whatsapp_doctor_success,
                'whatsapp_doctor_message': whatsapp_doctor_msg,
                'reminder_sent': whatsapp_patient_success and whatsapp_doctor_success
            })
        
        conn.commit()
        conn.close()
        
        print(f"\n📊 REMINDER CHECK COMPLETE")
        print(f"✅ Successful: {sum(1 for r in results if r['reminder_sent'])}")
        print(f"❌ Failed: {sum(1 for r in results if not r['reminder_sent'])}")
        
        return results

    def send_test_reminder(self, phone_number, message):
        """Send a test reminder immediately (bypass date check)"""
        print(f"\n🧪 SENDING TEST REMINDER (IMMEDIATE)")
        return self.send_reminder(phone_number, message)

    def test_whatsapp(self, phone_number, message):
        """Test WhatsApp function"""
        print(f"\n🧪 TESTING WHATSAPP FUNCTION")
        return self.send_reminder(phone_number, message)

    def test_sms(self, phone_number, message):
        """Test SMS function - placeholder since WhatsApp is primary"""
        print(f"\n🧪 TESTING SMS FUNCTION")
        # Implement if needed, but since WhatsApp is primary, return mock
        return True, "SMS test successful (mocked)"

# Create a global instance
reminder_system = ReminderSystem()