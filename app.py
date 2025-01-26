import streamlit as st
from components.login_signup import show_login_page, show_signup_page
import employee_dashboard
import manager_dashboard
import book_time  # Import the book_time page for seat booking functionality

# Backend API URL (Flask app2)
API_URL = "http://127.0.0.1:5000"  # Ensure Flask API is running on this port

# Main function to handle the app logic
def main():
    # Initialize session state variables
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "role" not in st.session_state:
        st.session_state.role = None
    if "balance" not in st.session_state:
        st.session_state.balance = 0  # Default balance is 0
    if "user_id" not in st.session_state:  # Add missing initialization
        st.session_state.user_id = None

    # Check if the user is logged in
    if st.session_state.logged_in:
        st.subheader(f"Welcome, {st.session_state.username} ({st.session_state.role})!")

        # Show appropriate dashboard based on role
        query_params = st.experimental_get_query_params()
        
        # Handle navigation based on query parameters
        if query_params.get("page") == ["book_time"]:
            book_time.show_booking_page()  # Show seat booking page
        elif st.session_state.role == "Manager":
            manager_dashboard.show_manager_dashboard()  # Show manager dashboard
        elif st.session_state.role == "Employee":
            employee_dashboard.show_employee_dashboard()  # Show employee dashboard
        else:
            st.error("Invalid role. Please contact support.")

        # Logout button
        if st.button("Logout"):
            logout()

    else:
        # Show login or signup option
        login_or_signup = st.sidebar.radio("Select Login or Sign-Up", ["Login", "Sign Up"])
        if login_or_signup == "Login":
            show_login_page()
        elif login_or_signup == "Sign Up":
            show_signup_page()

# Logout function
def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.user_id = None
    st.session_state.balance = 0  # Reset balance or remove if unnecessary
    st.experimental_rerun()  # Refresh the app UI

# Entry point
if __name__ == "__main__":
    main()
