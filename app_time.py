from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)

DATABASE = 'cafeteria_seats.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # To return rows as dictionaries
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

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if not user:
        return jsonify({"message": "User not found!"}), 400

    if user["balance"] < 1:
        return jsonify({"message": "Insufficient balance!"}), 400

    cursor.execute("SELECT * FROM seats WHERE seat_number = ? AND slot = ?", (seat_number, slot))
    seat = cursor.fetchone()

    if seat and not seat["is_booked"]:
        cursor.execute("UPDATE seats SET is_booked = 1 WHERE seat_number = ? AND slot = ?", (seat_number, slot))
        cursor.execute("UPDATE users SET balance = balance - 1 WHERE username = ?", (username,))
        conn.commit()
        updated_balance = user["balance"] - 1
        conn.close()
        return jsonify({"message": f"Seat {seat_number} booked successfully for slot {slot}!", "balance": updated_balance}), 200
    else:
        conn.close()
        return jsonify({"message": f"Seat {seat_number} is already booked or invalid!", "balance": user["balance"]}), 400

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
        return jsonify({"message": f"Seat {seat_number} booking cancelled for slot {slot}!", "balance": user["balance"] + 1}), 200
    else:
        conn.close()
        return jsonify({"message": f"Seat {seat_number} is not booked or invalid!"}), 400

if __name__ == '__main__':
    init_db()  # Initialize the database
    app.run(debug=True)
