import sqlite3

# Function to get the database connection for users.db
def get_db_connection():
    conn = sqlite3.connect("users.db", timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")  # Enable WAL mode for concurrency
    return conn

# Function to create the users table if it doesn't exist
def create_users_table():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(''' 
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            username TEXT,
            password TEXT,
            role TEXT,
            manager_email TEXT,
            manager_balance REAL DEFAULT 0.0  -- Add manager_balance column
        )
    ''')
    conn.commit()
    conn.close()

# Function to sign up a user
def sign_up(email, username, password, role, manager_email=None):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        if not email or not username or not password:
            return "All fields are required."
        
        # Insert user data into the table
        if role == "Employee" and manager_email:
            c.execute("INSERT INTO users (email, username, password, role, manager_email) VALUES (?, ?, ?, ?, ?)", 
                      (email, username, password, role, manager_email))
        else:
            c.execute("INSERT INTO users (email, username, password, role) VALUES (?, ?, ?, ?)", 
                      (email, username, password, role))
        conn.commit()
        return None  # Success
    except sqlite3.IntegrityError:
        return "Email already registered."
    except sqlite3.Error as e:
        return f"Database error: {e}"
    finally:
        conn.close()  # Ensure the connection is closed

# Function to log in a user
def login(email, password, role):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT username, id FROM users WHERE email=? AND password=? AND role=?", 
              (email, password, role))
    user = c.fetchone()
    conn.close()
    return user  # Returns username and user_id (as a tuple)

# Ensure the table is created when the script is run
if __name__ == "__main__":
    create_users_table()
