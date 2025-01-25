from flask import Flask, jsonify, request
import sqlite3
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

DATABASE = 'cafeteria_seats.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  
    return conn

def init_db():
    """Initialize the database with tables if they do not exist."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS seats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        seat_number TEXT NOT NULL,
                        slot TEXT NOT NULL,
                        is_booked INTEGER DEFAULT 0)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        balance REAL DEFAULT 30.0)''')

    conn.commit()

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

    if cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username) VALUES ('User1')")
        conn.commit()

    conn.close()

@app.route('/seats', methods=['GET'])
def get_seats():
    slot = request.args.get('slot')
    if not slot:
        return jsonify({"message": "Slot parameter is required!"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM seats WHERE slot = ? ORDER BY seat_number", (slot,))
    seats = cursor.fetchall()
    conn.close()

    if not seats:
        return jsonify({"message": "No seats available for the selected slot!"}), 404

    seat_matrix = [
        [
            {"seat_number": seats[j]["seat_number"], "is_booked": seats[j]["is_booked"]}
            for j in range(i, min(i + 10, len(seats)))
        ]
        for i in range(0, len(seats), 10)
    ]

    return jsonify(seat_matrix)

# CREATE A .env file having the sender email and password.(Eg: EMAIL=sender@example.com, PASSWORD=.....). The gitignore file ensures that it isnt pushed to github.

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

@app.route('/book_seat', methods=['POST'])
def book_seat():
    data = request.get_json()
    username = data.get('username')
    seat_number = data.get('seat_number')
    slot = data.get('slot')

    if not username or not seat_number or not slot:
        return jsonify({"message": "Username, seat number, and slot are required!"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if not user or user["balance"] < 1:
        return jsonify({"message": "User not found or insufficient balance!"}), 400

    cursor.execute("SELECT * FROM seats WHERE seat_number = ? AND slot = ?", (seat_number, slot))
    seat = cursor.fetchone()

    if seat and not seat["is_booked"]:
        cursor.execute("UPDATE seats SET is_booked = 1 WHERE seat_number = ? AND slot = ?", (seat_number, slot))
        cursor.execute("UPDATE users SET balance = balance - 1 WHERE username = ?", (username,))
        conn.commit()
        updated_balance = user["balance"] - 1
        conn.close()

        # Booking confirmation email
        send_reservation_email(
            receiver_email, seat_number, slot)
        return jsonify({"message": f"Seat {seat_number} booked for {slot}!", "balance": updated_balance}), 200
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

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if not user:
        return jsonify({"message": "User not found!"}), 400

    cursor.execute("SELECT * FROM seats WHERE seat_number = ? AND slot = ?", (seat_number, slot))
    seat = cursor.fetchone()

    if seat and seat["is_booked"]:
        cursor.execute("UPDATE seats SET is_booked = 0 WHERE seat_number = ? AND slot = ?", (seat_number, slot))
        cursor.execute("UPDATE users SET balance = balance + 1 WHERE username = ?", (username,))
        conn.commit()
        conn.close()

        # Cancellation email
        send_cancellation_email(receiver_email, seat_number, slot)

        return jsonify({"message": f"Seat {seat_number} booking cancelled for slot {slot}!", "balance": user["balance"] + 1}), 200
    else:
        conn.close()
        return jsonify({"message": f"Seat {seat_number} is not booked or invalid!"}), 400



if __name__ == '__main__':
    init_db()
    receiver_email = "example@example.com"   # hard coded for now, the logged in email should be used as receiver when we integrate the modules.
    app.run(debug=True)
