# app.py (UPDATED WITH AUTOMATION, LOGIN, STAFF MANAGEMENT, SIGN-UP, PASSWORD RESET, AND WINDOWS COMPATIBILITY)
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import datetime
import threading
import time
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
import shutil
from reminder import reminder_system

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'medical-reminder-system-secret-key')

# Load environment variables
load_dotenv()

# Automation: Daily reminder check at 8:00 AM
def automated_reminder_check():
    while True:
        now = datetime.datetime.now()
        target_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if now > target_time:
            target_time += datetime.timedelta(days=1)
        sleep_seconds = (target_time - now).total_seconds()
        time.sleep(sleep_seconds)
        print("🚀 Running automated daily reminder check...")
        reminder_system.check_reminders()

# Start the automation thread
threading.Thread(target=automated_reminder_check, daemon=True).start()

def send_reset_email(email, token):
    """Send password reset email"""
    try:
        msg = MIMEText(f"""
        To reset your MedReminder password, click the link below:
        http://localhost:5000/reset-password/{token}

        This link will expire in 1 hour. If you didn't request a reset, ignore this email.
        """)
        msg['Subject'] = 'MedReminder Password Reset'
        msg['From'] = os.getenv('EMAIL_ADDRESS')
        msg['To'] = email

        with smtplib.SMTP(os.getenv('SMTP_SERVER'), os.getenv('SMTP_PORT')) as server:
            server.starttls()
            server.login(os.getenv('EMAIL_ADDRESS'), os.getenv('EMAIL_PASSWORD'))
            server.send_message(msg)
        print(f"✅ Password reset email sent to {email}")
        return True
    except Exception as e:
        print(f"❌ Error sending reset email: {str(e)}")
        return False

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if session.get('logged_in'):
        return redirect(url_for('index'))
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'login':
            username = request.form['username']
            password = request.form['password']
            if reminder_system.validate_staff(username, password):
                session['logged_in'] = True
                session['username'] = username
                flash('Logged in successfully!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid credentials', 'error')
        elif action == 'signup':
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            if reminder_system.add_staff(username, password, email):
                flash(f'Account created for {username}! Please log in.', 'success')
            else:
                flash(f'Failed to create account. Username or email may already exist.', 'error')
    return render_template('auth.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('Logged out successfully!', 'info')
    return redirect(url_for('auth'))

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    if session.get('logged_in'):
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form['email']
        staff = reminder_system.get_staff_by_email(email)
        if staff:
            token = reminder_system.generate_reset_token(email)
            if send_reset_email(email, token):
                flash('Password reset link sent to your email!', 'success')
            else:
                flash('Failed to send reset email. Please try again.', 'error')
        else:
            flash('Email not found.', 'error')
    return render_template('reset_password_request.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if session.get('logged_in'):
        return redirect(url_for('index'))
    email = reminder_system.validate_reset_token(token)
    if not email:
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('reset_password_request'))
    if request.method == 'POST':
        username = request.form['username']
        new_password = request.form['password']
        if reminder_system.validate_staff(username, None):  # Check if username exists
            if reminder_system.reset_password(username, new_password):
                flash('Password reset successfully! Please log in.', 'success')
                return redirect(url_for('auth'))
            else:
                flash('Failed to reset password.', 'error')
        else:
            flash('Invalid username.', 'error')
    return render_template('reset_password.html', token=token)

@app.route('/manage-staff', methods=['GET', 'POST'])
def manage_staff():
    if not session.get('logged_in'):
        return redirect(url_for('auth'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        if reminder_system.add_staff(username, password, email):
            flash(f'Staff {username} added successfully!', 'success')
        else:
            flash(f'Failed to add staff {username}. Username or email may already exist.', 'error')
        return redirect(url_for('manage_staff'))
    staff = reminder_system.get_all_staff()
    return render_template('manage_staff.html', staff=staff)

@app.route('/delete-staff/<int:staff_id>')
def delete_staff(staff_id):
    if not session.get('logged_in'):
        return redirect(url_for('auth'))
    try:
        reminder_system.delete_staff(staff_id)
        flash('Staff deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting staff: {str(e)}', 'error')
    return redirect(url_for('manage_staff'))

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('auth'))
    """Dashboard - Show upcoming appointments"""
    appointments = reminder_system.get_all_appointments()
    
    # Filter today's and tomorrow's appointments
    today = datetime.datetime.now().date().isoformat()
    tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).date().isoformat()
    
    today_appointments = [apt for apt in appointments if apt[5] == today]
    tomorrow_appointments = [apt for apt in appointments if apt[5] == tomorrow]
    
    return render_template('index.html', 
                         today_appointments=today_appointments,
                         tomorrow_appointments=tomorrow_appointments,
                         total_appointments=len(appointments))

@app.route('/add-appointment', methods=['GET', 'POST'])
def add_appointment():
    if not session.get('logged_in'):
        return redirect(url_for('auth'))
    """Add a new appointment"""
    if request.method == 'POST':
        try:
            patient_name = request.form['patient_name']
            patient_phone = request.form['patient_phone']
            doctor_name = request.form['doctor_name']
            doctor_phone = request.form['doctor_phone']
            appointment_date = request.form['appointment_date']
            appointment_time = request.form['appointment_time']
            
            reminder_system.add_appointment(
                patient_name, patient_phone, doctor_name, 
                doctor_phone, appointment_date, appointment_time
            )
            
            flash('Appointment added successfully!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            flash(f'Error adding appointment: {str(e)}', 'error')
    
    return render_template('add_appointment.html')

@app.route('/appointments')
def view_appointments():
    if not session.get('logged_in'):
        return redirect(url_for('auth'))
    """View all appointments"""
    appointments = reminder_system.get_all_appointments()
    return render_template('appointments.html', appointments=appointments)

@app.route('/delete-appointment/<int:appointment_id>')
def delete_appointment(appointment_id):
    if not session.get('logged_in'):
        return redirect(url_for('auth'))
    """Delete an appointment"""
    try:
        reminder_system.delete_appointment(appointment_id)
        flash('Appointment deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting appointment: {str(e)}', 'error')
    
    return redirect(url_for('view_appointments'))

@app.route('/send-reminders')
def send_reminders():
    if not session.get('logged_in'):
        return redirect(url_for('auth'))
    """Manually send reminders"""
    try:
        results = reminder_system.check_reminders()
        
        if results:
            successful = sum(1 for r in results if r['reminder_sent'])
            message = f"Reminders processed: {successful} successful out of {len(results)} appointments"
            flash(message, 'success' if successful > 0 else 'warning')
        else:
            flash('No reminders to send at this time.', 'info')
            
        return render_template('send_reminders.html', results=results)
        
    except Exception as e:
        flash(f'Error sending reminders: {str(e)}', 'error')
        return render_template('send_reminders.html', results=[])

@app.route('/test-sms', methods=['GET', 'POST'])
def test_sms():
    if not session.get('logged_in'):
        return redirect(url_for('auth'))
    """Test SMS functionality"""
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        test_message = request.form['test_message']
        
        success, message = reminder_system.test_sms(phone_number, test_message)
        
        if success:
            flash(f'Test SMS sent successfully: {message}', 'success')
        else:
            flash(f'Failed to send test SMS: {message}', 'error')
    
    return render_template('test_sms.html')

@app.route('/api/appointments')
def api_appointments():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    """API endpoint to get appointments"""
    appointments = reminder_system.get_all_appointments()
    appointments_list = []
    
    for apt in appointments:
        appointments_list.append({
            'id': apt[0],
            'patient_name': apt[1],
            'patient_phone': apt[2],
            'doctor_name': apt[3],
            'doctor_phone': apt[4],
            'appointment_date': apt[5],
            'appointment_time': apt[6],
            'reminder_sent': bool(apt[7])
        })
    
    return jsonify(appointments_list)

@app.route('/test-whatsapp', methods=['GET', 'POST'])
def test_whatsapp():
    if not session.get('logged_in'):
        return redirect(url_for('auth'))
    """Test WhatsApp functionality"""
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        test_message = request.form['test_message']
        
        success, message = reminder_system.test_whatsapp(phone_number, test_message)
        
        if success:
            flash(f'WhatsApp test sent successfully: {message}', 'success')
        else:
            flash(f'Failed to send WhatsApp: {message}', 'error')
    
    return render_template('test_whatsapp.html')

@app.route('/send-test-reminder', methods=['GET', 'POST'])
def send_test_reminder():
    if not session.get('logged_in'):
        return redirect(url_for('auth'))
    """Send a test reminder immediately (bypass date check)"""
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        test_message = request.form['test_message']
        
        success, message = reminder_system.send_test_reminder(phone_number, test_message)
        
        if success:
            flash(f'Test reminder sent successfully: {message}', 'success')
        else:
            flash(f'Failed to send test reminder: {message}', 'error')
    
    return render_template('test_reminder.html')

if __name__ == '__main__':
    print("Starting Medical Reminder System...")
    print("Access your application at: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    app.run(debug=True, host='0.0.0.0', port=5000)