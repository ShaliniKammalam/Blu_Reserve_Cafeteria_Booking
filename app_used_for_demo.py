
from flask import Flask, jsonify, request
import sqlite3
import hashlib
from flask_restx import Api
from flasgger import Swagger
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from pathlib import Path
from dotenv import load_dotenv  # pip install python-dotenv
from io import BytesIO 
import qrcode # pip install "qrcode[pil]"

app = Flask(__name__)
api = Api(app)  # Swagger UI will be available at /swagger
swagger = Swagger(app)

# Database file paths
CAFE_DB = 'cafeteria_seats.db'
BLU_DB = 'blu_reserve.db'

def get_db(db_name):
    """
    Connect to the specified database and return the connection.
    """
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initialize the appropriate database based on available schema.
    """
    # Initialize both databases
    init_cafe_db()
    init_blu_db()

def init_cafe_db():
    """
    Initialize the cafeteria_seats.db schema if it doesn't exist.
    """
    conn = get_db(CAFE_DB)
    cursor = conn.cursor()

    # Create tables if they don't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS seats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        seat_number TEXT NOT NULL,
                        slot TEXT NOT NULL,
                        is_booked INTEGER DEFAULT 0,
                        booked_by TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS managers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        user_type TEXT NOT NULL,
                        balance INTEGER DEFAULT 0)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        user_type TEXT NOT NULL,
                        manager_email TEXT,
                        balance INTEGER DEFAULT 30,
                        FOREIGN KEY (manager_email) REFERENCES managers(email) ON DELETE SET NULL)''')

    # Populate seats if empty
    if cursor.execute("SELECT COUNT(*) FROM seats").fetchone()[0] == 0:
        time_slots = [
            "9:00 AM - 9:30 AM", "9:30 AM - 10:00 AM", "10:00 AM - 10:30 AM",
            "10:30 AM - 11:00 AM", "11:00 AM - 11:30 AM", "11:30 AM - 12:00 PM",
            "12:00 PM - 12:30 PM", "12:30 PM - 1:00 PM", "1:00 PM - 1:30 PM",
            "1:30 PM - 2:00 PM", "2:00 PM - 2:30 PM", "2:30 PM - 3:00 PM",
            "3:00 PM - 3:30 PM", "3:30 PM - 4:00 PM", "4:00 PM - 4:30 PM",
            "4:30 PM - 5:00 PM", "5:00 PM - 5:30 PM", "5:30 PM - 6:00 PM"
        ]
        for slot in time_slots:
            for i in range(1, 101):
                cursor.execute("INSERT INTO seats (seat_number, slot) VALUES (?, ?)", (f"Seat {i}", slot))
        conn.commit()

    conn.close()

def init_blu_db():
    """
    Initialize the blu_reserve.db schema if it doesn't exist.
    """
    conn = get_db(BLU_DB)
    cursor = conn.cursor()

    # Drop and recreate tables to match the schema
    #cursor.execute('DROP TABLE IF EXISTS employees;')

    cursor.execute('''CREATE TABLE IF NOT EXISTS employees (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        balance REAL NOT NULL,
                        manager_email TEXT,
                        email TEXT,
                        FOREIGN KEY (manager_email) REFERENCES managers(email)
                    );''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS managers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        balance INTEGER DEFAULT 30,
                        email TEXT NOT NULL UNIQUE
                    );''')

    # Insert hardcoded data if not already present
    cursor.execute('''INSERT OR IGNORE INTO managers (name, email) VALUES
                      ('John Doe', 'john.doe@example.com'),
                      ('Jane Smith', 'jane.smith@example.com');''')

    cursor.execute('''INSERT OR IGNORE INTO employees (name, balance, manager_email) VALUES
                      ('Alice', 50.0, 'john.doe@example.com'),
                      ('Bob', 30.0, 'jane.smith@example.com'),
                      ('Charlie', 40.0, 'jane.smith@example.com'),
                      ('David', 20.0, 'john.doe@example.com');''')

    conn.commit()
    conn.close()

# Choose the database to interact with dynamically
def query_db(query, args=(), one=False, db=CAFE_DB):
    """
    Execute a query on the specified database.
    """
    conn = get_db(db)
    cursor = conn.cursor()
    cursor.execute(query, args)
    rv = cursor.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

# Email Configuration
EMAIL_SERVER = "smtp.gmail.com"
PORT = 587
current_dir = Path(__file__).resolve().parent if "__file__" in locals() else Path.cwd()
load_dotenv(current_dir / ".env")  
sender_email = os.getenv("EMAIL")
password_email = os.getenv("PASSWORD")

def send_reservation_email(receiver_email, seat, slot):
    # Generate QR code 
    booking_details = f"Seat: {seat}, Slot: {slot}"
    qr_image = generate_qr_code(booking_details)
    # Create email
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = "Seat Reservation Confirmation"

    email_body = f"""
    <html>
    <body>
        <h2>Booking Confirmation</h2>
        <p>Your seat <b>{seat}</b> for slot <b>{slot}</b> has been reserved successfully.</p>
        <p>Please scan the QR code below when you enter the cafetaria</p>
        <img src="cid:qr_code" alt="QR Code" />
    </body>
    </html>
    """
    msg.attach(MIMEText(email_body, "html"))

    # Attach QR code with mail
    qr_attachment = MIMEImage(qr_image.read(), name="qr_code.png")
    qr_attachment.add_header("Content-ID", "<qr_code>")
    qr_attachment.add_header("Content-Disposition", "inline", filename="qr_code.png")
    msg.attach(qr_attachment)

    try:
        with smtplib.SMTP(EMAIL_SERVER, PORT) as server:
            server.starttls()
            server.login(sender_email, password_email)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print(f"Email sent to {receiver_email} successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

def generate_qr_code(data):
    """Generate a QR code and return it as a BytesIO object."""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    qr_image = BytesIO()
    qr.make_image(fill="black", back_color="white").save(qr_image, format="PNG")
    qr_image.seek(0)
    return qr_image


def send_cancellation_email(receiver_email, seat, slot):
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = "Seat Cancellation Confirmation"
    msg.attach(MIMEText(f"Your reservation for {seat} at {slot} has been cancelled successfully!", "plain"))

    try:
        with smtplib.SMTP(EMAIL_SERVER, PORT) as server:
            server.starttls()
            server.login(sender_email, password_email)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print(f"Email sent to {receiver_email} successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")


# Route to get manager details by email
@app.route('/manager/<manager_email>', methods=['GET'])
def get_manager(manager_email):
    conn = get_db(BLU_DB)
    manager = conn.execute('SELECT * FROM managers WHERE email = ?', (manager_email,)).fetchone()
    conn.close()
    if manager:
        return jsonify({
            'id': manager['id'],
            'name': manager['name'],
            'email': manager['email']
        })
    else:
        return jsonify({"error": "Manager not found"}), 404

# Route to get employee details by ID
@app.route('/employee/<int:employee_id>', methods=['GET'])
def get_employee(employee_id):
    conn = get_db(BLU_DB)
    employee = conn.execute('SELECT * FROM employees WHERE id = ?', (employee_id,)).fetchone()
    conn.close()
    if employee:
        return jsonify({
            'id': employee['id'],
            'name': employee['name'],
            'balance': employee['balance'],
            'manager_email': employee['manager_email']
        })
    else:
        return jsonify({"error": "Employee not found"}), 404

# Route to update employee balance
@app.route('/employee/<int:employee_id>', methods=['PUT'])
def update_employee_balance(employee_id):
    new_balance = request.json.get('balance')
    if new_balance is None:
        return jsonify({"error": "Missing balance value"}), 400
    conn = get_db(BLU_DB)
    conn.execute('UPDATE employees SET balance = ? WHERE id = ?', (new_balance, employee_id))
    conn.commit()
    conn.close()
    return jsonify({"message": f"Employee {employee_id} balance updated to {new_balance}."})

# Route to get all employees under a manager
@app.route('/manager/<manager_email>/employees', methods=['GET'])
def get_all_employees(manager_email):
    conn = get_db(BLU_DB)
    employees = conn.execute('SELECT * FROM employees WHERE manager_email = ?', (manager_email,)).fetchall()
    conn.close()
    if employees:
        return jsonify([{
            'id': employee['id'],
            'name': employee['name'],
            'balance': employee['balance'],
            'manager_email': employee['manager_email']
        } for employee in employees])
    else:
        return jsonify({"error": "No employees found for this manager"}), 404


# Existing routes (register, login, etc.)
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    username = data.get("username")  # Added to get the username
    user_type = data.get("user_type")
    manager_email = data.get("manager_email", None)
    balance = 30
    if not username:
        return jsonify({"message": "Username is required!"}), 400  # Check if username is provided

    # Check if email already exists
    conn = get_db(CAFE_DB)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if user:
        return jsonify({"message": "Email already registered"}), 400

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    if user_type == "employee":
        if not manager_email:
            return jsonify({"message": "Manager's email is required for employees"}), 400
        cursor.execute("INSERT INTO users (username, email, password, user_type, manager_email) VALUES (?, ?, ?, ?, ?)",
                       (username, email, hashed_password, user_type, manager_email))
    else:
        cursor.execute("INSERT INTO users (username, email, password, user_type) VALUES (?, ?, ?, ?)",
                       (username, email, hashed_password, user_type))

    conn.commit()
    conn.close()
    conn2 = get_db(BLU_DB)
    cursor2 = conn2.cursor()

    if user_type == "employee":
        cursor2.execute("INSERT INTO employees (name, balance, manager_email, email) VALUES (?, ?, ?, ?)",
                       (username, balance, manager_email, email))
    else:
        cursor2.execute("INSERT INTO managers (name, balance, email) VALUES (?, ?, ?)",
                       (username, balance, email))
    conn2.commit()
    conn2.close()
    return jsonify({"message": "User registered successfully"}), 200


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "Email and password are required!"}), 400

    conn = get_db(CAFE_DB)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if not user:
        return jsonify({"message": "User not found!"}), 400

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    if hashed_password != user["password"]:
        return jsonify({"message": "Invalid password!"}), 400

    # If the user is an employee, fetch the manager's name
    manager_name = None
    if user["user_type"] == "employee" and user["manager_email"]:
        cursor.execute("SELECT username FROM users WHERE email = ?", (user["manager_email"],))
        manager = cursor.fetchone()
        if manager:
            manager_name = manager["username"]

    conn.close()

    return jsonify({
        "message": "Login successful!",
        "user_type": user["user_type"],
        "email": user["email"],
        "manager_email": user["manager_email"] if user["user_type"] == "employee" else None,
        "username": user["username"],  # Include the username
        "manager_name": manager_name  # Include the manager's name if employee
    }), 200


# Seats booking-related routes
@app.route('/seats', methods=['GET'])
def get_seats():
    slot = request.args.get('slot')
    if not slot:
        return jsonify({"message": "Slot parameter is required!"}), 400

    conn = get_db(CAFE_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM seats WHERE slot = ? ORDER BY seat_number", (slot,))
    seats = cursor.fetchall()
    conn.close()

    if not seats:
        return jsonify({"message": "No seats available for the selected slot!"}), 404

    seat_matrix = []
    for i in range(0, len(seats), 10):  
        row = []
        for j in range(i, i + 10):
            if j < len(seats):  
                seat = seats[j]
                row.append({"seat_number": seat["seat_number"], "is_booked": seat["is_booked"]})
        seat_matrix.append(row)

    return jsonify(seat_matrix)

@app.route('/book_seat', methods=['POST'])
def book_seat():
    data = request.get_json()
    username = data.get('username')
    seat_number = data.get('seat_number')
    slot = data.get('slot')

    if not username or not seat_number or not slot:
        return jsonify({"message": "Username, seat number, and slot are required!"}), 400

    conn = get_db(CAFE_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    receiver_email = user["email"] 
    if not user:
        return jsonify({"message": "User not found!"}), 400

    cursor.execute("SELECT * FROM seats WHERE seat_number = ? AND slot = ?", (seat_number, slot))
    seat = cursor.fetchone()

    if seat and not seat["is_booked"]:
        cursor.execute("UPDATE seats SET is_booked = 1, booked_by = ? WHERE seat_number = ? AND slot = ?", 
                       (username, seat_number, slot))

        # Deduct 1 from the manager's balance (same logic as before)
        if user["user_type"] == 'employee' and not user["manager_email"]:
            cursor.execute("UPDATE users SET balance = balance - 1 WHERE id = ?", (user["id"],))
        elif user["user_type"] == 'manager':
            cursor.execute("UPDATE managers SET balance = balance - 1 WHERE email = ?", (user["email"],))

        conn.commit()
        conn.close()
        send_reservation_email(receiver_email,seat_number,slot)
        return jsonify({"message": f"Seat {seat_number} booked successfully for slot {slot}!"}), 200
    else:
        conn.close()
        return jsonify({"message": f"Seat {seat_number} is already booked or invalid!"}), 400


@app.route('/cancel_seat', methods=['POST'])
def cancel_seat():
    data = request.get_json()
    username = data.get('username')
    seat_number = data.get('seat_number')
    slot = data.get('slot')

    if not username or not seat_number or not slot:
        return jsonify({"message": "Username, seat number, and slot are required!"}), 400

    conn = get_db(CAFE_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    cancellation_email = user['email']
    if not user:
        return jsonify({"message": "User not found!"}), 400

    cursor.execute("SELECT * FROM seats WHERE seat_number = ? AND slot = ?", (seat_number, slot))
    seat = cursor.fetchone()

    if seat and seat["is_booked"]:
        # Check if the seat was booked by the current user
        if seat["booked_by"] != username:
            conn.close()
            return jsonify({"message": "You can only cancel a seat you have booked!"}), 400

        cursor.execute("UPDATE seats SET is_booked = 0, booked_by = NULL WHERE seat_number = ? AND slot = ?", 
                       (seat_number, slot))

        
        if user["user_type"] == 'employee' and user["manager_email"]:
            cursor.execute("UPDATE users SET balance = balance + 1 WHERE id = ?", (user["id"],))
        elif user["user_type"] == 'manager':
            cursor.execute("UPDATE managers SET balance = balance + 1 WHERE email = ?", (user["email"],))

        conn.commit()
        conn.close()
        send_cancellation_email(cancellation_email,seat_number,slot)
        return jsonify({"message": f"Seat {seat_number} booking canceled for slot {slot}!"}), 200
    else:
        conn.close()
        return jsonify({"message": f"Seat {seat_number} is not booked or invalid!"}), 400


@app.route('/send_money_request_email', methods=['POST'])
def send_money_request_email():
    data = request.json
    employee_mail = data.get('employee_mail')
    manager_email = data.get('manager_email')
    amount = data.get('amount')

    # Create email
    msg = MIMEMultipart()
    msg["From"] = employee_mail
    msg["To"] = manager_email
    msg["Subject"] = "Request for Blu Dollars"

    email_body = f"""
    <html>
    <body>
        <p>Hey can you add <b>{amount}</b> to my Blu Reserve wallet please?</p>
    </body>
    </html>
    """
    msg.attach(MIMEText(email_body, "html"))

    try:
        with smtplib.SMTP(EMAIL_SERVER, PORT) as server:
            server.starttls()
            server.login(sender_email, password_email)
            server.sendmail(sender_email, manager_email, msg.as_string())
            print(f"Email sent to {manager_email} successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == '__main__':
    init_db()  
    app.run(debug=True)