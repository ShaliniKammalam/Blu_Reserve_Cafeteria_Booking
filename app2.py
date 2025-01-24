from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafeteria_seats.db'
db = SQLAlchemy(app)


class Seat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seat_number = db.Column(db.String(10), nullable=False)
    slot = db.Column(db.String(20), nullable=False)  # Time slot field
    is_booked = db.Column(db.Boolean, default=False)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    balance = db.Column(db.Float, default=30.0)  # Default balance is $30


@app.route('/seats', methods=['GET'])
def get_seats():
    """Get seat availability for a specific time slot."""
    slot = request.args.get('slot')
    if not slot:
        return jsonify({"message": "Slot parameter is required!"}), 400

    seats = Seat.query.filter_by(slot=slot).all()
    if not seats:
        return jsonify({"message": "No seats available for the selected slot!"}), 404

    seat_matrix = []
    for i in range(0, 100, 10):
        row = []
        for j in range(i, i + 10):
            seat = seats[j]
            row.append({"seat_number": seat.seat_number, "is_booked": seat.is_booked})
        seat_matrix.append(row)

    return jsonify(seat_matrix)


@app.route('/book_seat', methods=['POST'])
def book_seat():
    """Book a seat for a specific time slot."""
    data = request.get_json()
    username = data.get('username')
    seat_number = data.get('seat_number')
    slot = data.get('slot')

    if not username or not seat_number or not slot:
        return jsonify({"message": "Username, seat number, and slot are required!"}), 400

    # Check if the user exists
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"message": "User not found!"}), 400

    # Check if the user has enough balance
    if user.balance < 1:
        return jsonify({"message": "Insufficient balance!"}), 400

    # Check if the seat is available for the selected slot
    seat = Seat.query.filter_by(seat_number=seat_number, slot=slot).first()
    if seat and not seat.is_booked:
        seat.is_booked = True
        user.balance -= 1  # Deduct $1
        db.session.commit()
        return jsonify({"message": f"Seat {seat_number} booked successfully for slot {slot}!", "balance": user.balance}), 200
    else:
        return jsonify({"message": f"Seat {seat_number} is already booked or invalid!"}), 400


@app.route('/cancel_seat', methods=['POST'])
def cancel_seat():
    """Cancel a seat for a specific time slot."""
    data = request.get_json()
    username = data.get('username')
    seat_number = data.get('seat_number')
    slot = data.get('slot')

    if not username or not seat_number or not slot:
        return jsonify({"message": "Username, seat number, and slot are required!"}), 400

    # Check if the user exists
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"message": "User not found!"}), 400

    # Check if the seat is booked for the selected slot
    seat = Seat.query.filter_by(seat_number=seat_number, slot=slot).first()
    if seat and seat.is_booked:
        seat.is_booked = False
        user.balance += 1  # Refund $1
        db.session.commit()
        return jsonify({"message": f"Seat {seat_number} booking cancelled for slot {slot}!", "balance": user.balance}), 200
    else:
        return jsonify({"message": f"Seat {seat_number} is not booked or invalid!"}), 400


if __name__ == '__main__':
    # Create tables within the application context
    with app.app_context():
        db.create_all()  # Create tables

        # Prepopulate with 100 seats per time slot if not already populated
        if Seat.query.count() == 0:
            time_slots = ["12:30-1:00", "1:00-1:30"]
            for slot in time_slots:
                for i in range(1, 101):
                    seat = Seat(seat_number=f"Seat {i}", slot=slot)
                    db.session.add(seat)
            db.session.commit()

        # Prepopulate users if no users exist
        if User.query.count() == 0:
            user = User(username="User1")  # Default user
            db.session.add(user)
            db.session.commit()

    app.run(debug=True)
