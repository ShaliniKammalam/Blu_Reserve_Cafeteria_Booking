import streamlit as st
import requests

# Backend API URL
API_URL = "http://127.0.0.1:5000"

# Initialize session state
if "username" not in st.session_state:
    st.session_state.username = "User1"
if "balance" not in st.session_state:
    st.session_state.balance = 30.0
if "selected_slot" not in st.session_state:
    st.session_state.selected_slot = "12:30-1:00"

# Helper Functions
def get_seats(slot):
    """Fetch the seat matrix for the selected time slot from the backend."""
    response = requests.get(f"{API_URL}/seats?slot={slot}")
    return response.json()

def book_seat(seat_number, slot):
    """Send a request to book a seat for the selected time slot."""
    data = {"username": st.session_state.username, "seat_number": seat_number, "slot": slot}
    response = requests.post(f"{API_URL}/book_seat", json=data)
    return response.json()

def cancel_seat(seat_number, slot):
    """Send a request to cancel a seat for the selected time slot."""
    data = {"username": st.session_state.username, "seat_number": seat_number, "slot": slot}
    response = requests.post(f"{API_URL}/cancel_seat", json=data)
    return response.json()

def update_balance():
    """Update the user's balance from the backend."""
    response = requests.get(f"{API_URL}/user/{st.session_state.username}")
    if response.status_code == 200:
        st.session_state.balance = response.json().get("balance", 30.0)

def display_seat_matrix(mode="book"):
    """
    Display the seat matrix for the selected time slot.
    `mode` can be 'book' or 'cancel'.
    """
    slot = st.session_state.selected_slot
    seat_matrix = get_seats(slot)

    for row in seat_matrix:
        cols = st.columns(len(row))
        for i, seat in enumerate(row):
            seat_number = seat['seat_number']
            is_booked = seat['is_booked']
            seat_button = f"{seat_number}"

            if mode == "book":
                if is_booked:
                    cols[i].markdown(
                        f'<button style="background-color: #ff4d4d; color: white; width: 100%; border-radius: 5px; border: none; padding: 10px; cursor: not-allowed;" disabled>{seat_button}</button>',
                        unsafe_allow_html=True
                    )
                else:
                    if cols[i].button(seat_button, key=f"book_{slot}_{seat_number}"):
                        booking_response = book_seat(seat_number, slot)
                        if "message" in booking_response:
                            st.success(booking_response["message"])
                            st.session_state.balance = booking_response["balance"]
                        else:
                            st.error("Booking failed!")
                        st.experimental_rerun()
            elif mode == "cancel":
                if is_booked:
                    if cols[i].button(seat_button, key=f"cancel_{slot}_{seat_number}"):
                        cancel_response = cancel_seat(seat_number, slot)
                        if "message" in cancel_response:
                            st.success(cancel_response["message"])
                            st.session_state.balance = cancel_response["balance"]
                        else:
                            st.error("Cancellation failed!")
                        st.experimental_rerun()
                else:
                    cols[i].markdown(
                        f'<button style="background-color: #d3d3d3; color: black; width: 100%; border-radius: 5px; border: none; padding: 10px; cursor: not-allowed;" disabled>{seat_button}</button>',
                        unsafe_allow_html=True
                    )

# Main App
def main():
    st.title("Blu - Reserve")

    # Sidebar for navigation
    st.sidebar.title("Menu")
    action = st.sidebar.radio("Choose an action:", ["Book Seat", "Cancel Seat"])

    # Select Time Slot
    time_slots = ["12:30-1:00", "1:00-1:30"]
    st.sidebar.subheader("Select Time Slot")
    st.session_state.selected_slot = st.sidebar.selectbox("Time Slot:", time_slots)

    # Display user balance
    st.sidebar.write(f"**Blu Balance: ${st.session_state.balance:.2f}**")

    # Actions
    if action == "Book Seat":
        st.header(f"Book a Seat ({st.session_state.selected_slot})")
        display_seat_matrix(mode="book")
    elif action == "Cancel Seat":
        st.header(f"Cancel a Seat ({st.session_state.selected_slot})")
        display_seat_matrix(mode="cancel")

if __name__ == "__main__":
    main()
