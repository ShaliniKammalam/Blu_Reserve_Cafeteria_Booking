import streamlit as st
from database import get_db_connection

# Add custom CSS for styling
def add_custom_css():
    st.markdown(
        """
        <style>
            /* General styling */
            .stApp {
                background-color: #f4f7f6;
                font-family: 'Arial', sans-serif;
                padding: 20px;
            }

            /* Header styling */
            h1, h2 {
                color: #4CAF50;
                font-weight: bold;
                text-align: center;
            }

            h3 {
                color: #333;
                font-weight: bold;
                margin-bottom: 10px;
            }

            /* Employee and Manager Info Boxes */
            .info-box {
                background-color: #ffffff;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0px 6px 12px rgba(0, 0, 0, 0.1);
                margin-bottom: 20px;
            }

            /* Manager and Employee details alignment */
            .details {
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
            }

            .details div {
                font-size: 16px;
            }

            .details span {
                font-weight: bold;
            }

            /* Button Styling */
            .stButton>button {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-size: 16px;
                cursor: pointer;
                transition: background-color 0.3s ease, transform 0.3s ease;
            }

            .stButton>button:hover {
                background-color: #45a049;
                transform: scale(1.05);
            }

            /* Success and warning messages */
            .success {
                color: #4CAF50;
                font-size: 16px;
                font-weight: bold;
                text-align: center;
                margin-top: 10px;
            }

            .warning {
                color: #ff6600;
                font-size: 16px;
                font-weight: bold;
                text-align: center;
                margin-top: 10px;
            }
        </style>
        """, unsafe_allow_html=True
    )

# Function to fetch employee's manager data and the manager's balance using employee_email
def get_manager_data(employee_email):
    conn = get_db_connection()
    c = conn.cursor()

    # Fetch the manager_email for the logged-in employee
    c.execute("SELECT manager_email FROM users WHERE email = ? AND role = 'Employee'", (employee_email,))
    manager_email = c.fetchone()

    if manager_email:
        manager_email = manager_email[0]
        # Now fetch the manager's balance using the manager_email
        c.execute("SELECT manager_balance, email FROM users WHERE email = ?", (manager_email,))
        manager_data = c.fetchone()
        conn.close()
        return manager_data
    else:
        conn.close()
        return None

# Employee Dashboard
def show_employee_dashboard():
    add_custom_css()

    # Ensure the user is logged in and is an Employee
    if 'logged_in' in st.session_state and st.session_state.get('role') == 'Employee' and st.session_state.get('logged_in'):

        employee_email = st.session_state.get('email')  # Get employee email from session
        manager_data = get_manager_data(employee_email)

        if manager_data:
            manager_balance, manager_email = manager_data
            # Manager Info Box
            st.markdown(""" 
                <div class="info-box">
                    <h3>Manager Information</h3>
                    <div class="details">
                        <div><span>Email:</span> {}</div>
                        <div><span>Balance:</span> ${:.2f}</div>
                    </div>
                </div>
            """.format(manager_email, manager_balance), unsafe_allow_html=True)

            # Seat Booking Section
            if st.button("Go to Seat Booking"):
                # Set session state and redirect to book_time page for booking
                st.session_state.manager_balance = manager_balance
                st.session_state.manager_email = manager_email
                # Set query params to navigate to the book_time page
                st.experimental_set_query_params(page="book_time")  # Redirect to the booking page
                st.experimental_rerun()  # Refresh the page

        else:
            st.error("Manager data not found.")
    else:
        st.warning("You need to be logged in as an Employee to access this page.")
        st.stop()

# Main function
def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'role' not in st.session_state:
        st.session_state.role = None

    query_params = st.experimental_get_query_params()
    if query_params.get("page") == ["employee_dashboard"]:
        show_employee_dashboard()
    else:
        st.error("Unauthorized access! Please log in as an Employee.")

if __name__ == "__main__":
    main()
