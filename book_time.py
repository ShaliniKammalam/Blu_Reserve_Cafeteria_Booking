import streamlit as st
import requests

API_URL = "http://127.0.0.1:5000"

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
            st.error("Invalid response from the backend.")
            return []
    else:
        st.error(f"Failed to fetch seat data. Status: {response.status_code}")
        return []

def book_seat(seat_number, slot):
    data = {"username": st.session_state.username, "seat_number": seat_number, "slot": slot}
    response = requests.post(f"{API_URL}/book_seat", json=data)
    try:
        return response.json()
    except ValueError:
        return {"message": "Invalid response from the server."}

def cancel_seat(seat_number, slot):
    data = {"username": st.session_state.username, "seat_number": seat_number, "slot": slot}
    response = requests.post(f"{API_URL}/cancel_seat", json=data)
    try:
        return response.json()
    except ValueError:
        return {"message": "Invalid response from the server."}

def display_seat_matrix(mode="book"):
    slot = st.session_state.selected_slot
    seat_matrix = get_seats(slot)
    if not seat_matrix:
        st.error("No seats available.")
        return

    for row in seat_matrix:
        cols = st.columns(len(row))
        for col_idx, seat in enumerate(row):
            if isinstance(seat, dict):
                seat_id = seat['seat_number']  # Use seat_number (ID) from the table as the key
                is_booked = seat['is_booked']

                if mode == "book":
                    if is_booked:
                        cols[col_idx].button("🚫", disabled=True, key=f"booked_{seat_id}")
                    else:
                        if cols[col_idx].button("🪑", key=f"book_{seat_id}"):
                            res = book_seat(seat_id, slot)
                            st.success(res["message"])
                            st.session_state.balance = res.get("balance", st.session_state.balance)
                            st.rerun()
                elif mode == "cancel":
                    if is_booked:
                        if cols[col_idx].button("❌", key=f"cancel_{seat_id}"):
                            res = cancel_seat(seat_id, slot)
                            st.success(res["message"])
                            st.session_state.balance = res.get("balance", st.session_state.balance)
                            st.rerun()
                    else:
                        cols[col_idx].button("⬜", disabled=True, key=f"cancel_unbooked_{seat_id}")

def select_time_slot():
    st.title("Select a Time Slot")
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
        if cols[i % 3].button(slot, key=f"slot_{slot}"):
            st.session_state.selected_slot = slot
            st.rerun()

def main():
    if st.session_state.selected_slot is None:
        select_time_slot()
    else:
        st.sidebar.write(f"Logged in as: {st.session_state.username}")
        st.sidebar.write(f"Balance: ${st.session_state.balance}")
        st.sidebar.write(f"Selected Slot: {st.session_state.selected_slot}")
        action = st.sidebar.radio("Choose Action", ["Book Seat", "Cancel Booking", "Change Slot"])

        if action == "Change Slot":
            st.session_state.selected_slot = None
            st.rerun()
        elif action == "Book Seat":
            st.title(f"Book Seat for Slot: {st.session_state.selected_slot}")
            if st.button("🔙 Back to Time Slots"):
                st.session_state.selected_slot = None
                st.rerun()
            display_seat_matrix(mode="book")
        elif action == "Cancel Booking":
            st.title(f"Cancel Booking for Slot: {st.session_state.selected_slot}")
            if st.button("🔙 Back to Time Slots"):
                st.session_state.selected_slot = None
                st.rerun()
            display_seat_matrix(mode="cancel")

if __name__ == "__main__":
    main()
