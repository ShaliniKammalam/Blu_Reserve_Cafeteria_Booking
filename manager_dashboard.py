import streamlit as st
from database import get_db_connection

# Add custom CSS for the Manager Dashboard
def add_custom_css():
    st.markdown(
        """
        <style>
            /* General page styling */
            .stApp {
                background-color: #f5f5f5;
                font-family: 'Arial', sans-serif;
            }

            /* Header Styling */
            h1, h2 {
                color: #4CAF60;
                font-weight: 600;
            }

            h3 {
                color: #333;
                font-weight: 400;
            }

            /* Button Styling */
            .stButton>button {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 16px;
                transition: background-color 0.3s ease, transform 0.3s ease;
            }

            .stButton>button:hover {
                background-color: #45a049;
                transform: scale(1.05);
            }

            /* Number Input Field Styling without border */
            .stNumberInput input {
                font-size: 16px;
                padding: 12px;
                border-radius: 6px;
                border: none;
                width: 260px;
                background-color: #f0f4f1;
                box-shadow: 0 3px 6px rgba(0, 0, 0, 0.1);
            }

            /* General Text Styling */
            .stText {
                font-size: 18px;
            }

            /* Manager Info Box */
            .manager-info {
                padding: 25px;
                background-color: #ffffff;
                border-radius: 10px;
                margin-bottom: 25px;
                box-shadow: 0px 6px 8px rgba(0, 0, 0, 0.1);
            }

            /* Balance Box Styling */
            .balance-box {
                background-color: #f0f4f1;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 3px 6px rgba(0, 0, 0, 0.1);
            }

            /* Success and Warning Text */
            .warning {
                color: #ff6600;
                font-size: 16px;
                margin-top: 15px;
            }

            .success {
                color: #4CAF50;
                font-size: 16px;
                margin-top: 15px;
            }

            /* Positioning Logout Button to the Right */
            .logout-button {
                display: flex;
                justify-content: flex-end;
                margin-top: 20px;
            }

        </style>
        """, unsafe_allow_html=True
    )

# Function to fetch manager's data based on the logged-in user's ID
def get_manager_data(manager_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT username, email, manager_balance FROM users WHERE id=?", (manager_id,))
    manager = c.fetchone()
    conn.close()
    return manager

# Function to update the manager's balance
def update_manager_balance(manager_id, amount):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET manager_balance = manager_balance + ? WHERE id=?", (amount, manager_id))
    conn.commit()
    conn.close()

# Logout function
def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.user_id = None
    st.experimental_set_query_params(page="login")  # Redirect to the login page
    st.experimental_rerun()

# Manager Dashboard
def show_manager_dashboard():
    # Add the custom CSS for styling
    add_custom_css()

    # Ensure the user is logged in and has the Manager role
    if 'logged_in' in st.session_state and st.session_state.get('role') == 'Manager' and st.session_state.get('logged_in'):
        
        # Fetch manager data
        manager_id = st.session_state.get('user_id')  # Get manager ID from session
        manager_data = get_manager_data(manager_id)

        if manager_data:
            username, email, manager_balance = manager_data
            st.title(f"Manager Dashboard: {username}")

            # Display manager's information
            st.markdown(f"<div class='manager-info'><h3>Manager Information</h3></div>", unsafe_allow_html=True)
            st.markdown(f"**Username:** {username}")
            st.markdown(f"**Email:** {email}")
            st.markdown(f"**Current Balance:** <span class='balance-box'>${manager_balance:.2f}</span>", unsafe_allow_html=True)

            # Add amount to the manager's balance
            st.markdown("<div class='manager-info'><h3>Add Amount to Balance</h3></div>", unsafe_allow_html=True)
            amount = st.number_input("Enter Amount to Add", min_value=0.0, step=10.0, format="%.2f")
            
            if st.button("Add Amount", key="add_amount_button"):
                if amount > 0:
                    update_manager_balance(manager_id, amount)
                    st.markdown(f"<div class='success'>Successfully added ${amount:.2f} to your balance.</div>", unsafe_allow_html=True)
                    st.experimental_rerun()  # Refresh the page to show updated balance
                else:
                    st.markdown("<div class='warning'>Please enter an amount greater than 0.</div>", unsafe_allow_html=True)

            # Logout button positioned to the right
            st.markdown("<div class='logout-button'>", unsafe_allow_html=True)
            
  
        else:
            st.error("Manager data not found.")
    else:
        st.warning("You need to be logged in as a Manager to access this page.")
        st.stop()

# Main function to check login and show appropriate page
def main():
    # Initialize session state if it's not already initialized
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'role' not in st.session_state:
        st.session_state.role = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None

    # Check the page query parameter
    query_params = st.experimental_get_query_params()
    if query_params.get("page") == ["manager_dashboard"]:
        show_manager_dashboard()
    else:
        st.error("Unauthorized access! Please log in as a Manager.")

# Run the main function when the script is executed
if __name__ == "__main__":
    main()
