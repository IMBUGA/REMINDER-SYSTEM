import sqlite3
import bcrypt

def add_initial_staff(username, password, email):
    try:
        # Connect to the database
        conn = sqlite3.connect('appointments.db')
        c = conn.cursor()

        # Hash the password
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insert the staff member
        c.execute('INSERT INTO staff (username, password_hash, email) VALUES (?, ?, ?)',
                  (username, hashed, email))
        
        # Commit and close
        conn.commit()
        conn.close()
        print(f"✅ Successfully added staff: {username} with email: {email}")
    except sqlite3.IntegrityError:
        print(f"❌ Failed to add staff: Username {username} or email {email} already exists")
    except Exception as e:
        print(f"❌ Error adding staff: {str(e)}")

if __name__ == "__main__":
    # Define the initial staff details
    username = "admin"
    password = "87654321"
    email = "danmarksande@gmail.com"
    
    # Add the staff member
    add_initial_staff(username, password, email)