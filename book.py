import streamlit as st
import requests
from datetime import datetime  # Add this import at the top

API_URL = "http://127.0.0.1:5000"

# Define current_date before you use it in the frontend
current_date = datetime.now().strftime("%A, %d %B %Y")  # Get current date

if "username" not in st.session_state:
    st.session_state.username = "User1"
if "balance" not in st.session_state:
    st.session_state.balance = 30.0
if "selected_slot" not in st.session_state:
    st.session_state.selected_slot = None

def get_seats(slot):
    response = requests.get(f"{API_URL}/seats?slot={slot}")
    if response.status_code == 200:
        try:
            return response.json()
        except ValueError:
            st.error("🚫 Invalid response from the backend.")
            return []
    else:
        st.error(f"❌ Failed to fetch seat data. Status: {response.status_code}")
        return []

def get_free_seats_count(slot):
    seat_matrix = get_seats(slot)
    if not seat_matrix:
        return 0
    free_seats = sum(
        1 for row in seat_matrix for seat in row if isinstance(seat, dict) and not seat["is_booked"]
    )
    return free_seats

def book_seat(seat_number, slot):
    data = {"username": st.session_state.username, "seat_number": seat_number, "slot": slot}
    response = requests.post(f"{API_URL}/book_seat", json=data)
    try:
        return response.json()
    except ValueError:
        return {"message": "\ud83d\udeab Invalid response from the server."}

def cancel_seat(seat_number, slot):
    data = {"username": st.session_state.username, "seat_number": seat_number, "slot": slot}
    response = requests.post(f"{API_URL}/cancel_seat", json=data)
    try:
        return response.json()
    except ValueError:
        return {"message": "\ud83d\udeab Invalid response from the server."}

def display_seat_matrix(mode="book"):
    slot = st.session_state.selected_slot
    seat_matrix = get_seats(slot)
    if not seat_matrix:
        st.error("\ud83d\udeab No seats available.")
        return

    for row in seat_matrix:
        cols = st.columns(len(row))
        for col_idx, seat in enumerate(row):
            if isinstance(seat, dict):
                seat_id = seat['seat_number']
                is_booked = seat['is_booked']

                if mode == "book":
                    if is_booked:
                        cols[col_idx].button("🚫", disabled=True, key=f"booked_{seat_id}")
                    else:
                        if cols[col_idx].button("🪑", key=f"book_{seat_id}"):
                            res = book_seat(seat_id, slot)
                            st.success(f"👍 {res['message']}")
                            st.session_state.balance = res.get("balance", st.session_state.balance)
                            st.rerun()
                elif mode == "cancel":
                    if is_booked:
                        if cols[col_idx].button("❌", key=f"cancel_{seat_id}"):
                            res = cancel_seat(seat_id, slot)
                            st.success(f"👍 {res['message']}")
                            st.session_state.balance = res.get("balance", st.session_state.balance)
                            st.rerun()
                    else:
                        cols[col_idx].button("⬜", disabled=True, key=f"cancel_unbooked_{seat_id}")

def select_time_slot():
    st.title("🍽️ Cafeteria Booking System")
    st.header("Reserve your seat hassle-free! 🪑")
    st.subheader(f"{current_date}")  # Display the current date below the header
    time_slots = [
        "9:00 AM - 9:30 AM", "9:30 AM - 10:00 AM", "10:00 AM - 10:30 AM",
        "10:30 AM - 11:00 AM", "11:00 AM - 11:30 AM", "11:30 AM - 12:00 PM",
        "12:00 PM - 12:30 PM", "12:30 PM - 1:00 PM", "1:00 PM - 1:30 PM",
        "1:30 PM - 2:00 PM", "2:00 PM - 2:30 PM", "2:30 PM - 3:00 PM",
        "3:00 PM - 3:30 PM", "3:30 PM - 4:00 PM", "4:00 PM - 4:30 PM",
        "4:30 PM - 5:00 PM", "5:00 PM - 5:30 PM", "5:30 PM - 6:00 PM"
    ]

    cols = st.columns(3)
    for i, slot in enumerate(time_slots):
        free_seats = get_free_seats_count(slot)
        button_label = f"{slot} ({free_seats} free)"
        if cols[i % 3].button(button_label, key=f"slot_{slot}"):
            st.session_state.selected_slot = slot
            st.rerun()

def main():
    st.sidebar.title("💼 User Dashboard")
    st.sidebar.write(f"**Logged in as:** {st.session_state.username}")
    st.sidebar.write(f"**Balance:** ${st.session_state.balance}")
    

    if st.session_state.selected_slot is None:
        select_time_slot()
    else:
        st.sidebar.write(f"**Selected Slot:** {st.session_state.selected_slot}")
        action = st.sidebar.radio("Choose Action", ["Book Seat", "Cancel Booking", "Change Slot"])

        if action == "Change Slot":
            st.session_state.selected_slot = None
            st.rerun()
        elif action == "Book Seat":
            st.title(f"🪑 Book Seat for Slot: {st.session_state.selected_slot} ({current_date})")
            if st.button("🔙 Back to Time Slots"):
                st.session_state.selected_slot = None
                st.rerun()
            display_seat_matrix(mode="book")
        elif action == "Cancel Booking":
            st.title(f"❌ Cancel Booking for Slot: {st.session_state.selected_slot} ({current_date})")
            if st.button("🔙 Back to Time Slots"):
                st.session_state.selected_slot = None
                st.rerun()
            display_seat_matrix(mode="cancel")

if __name__ == "__main__":
    main()
