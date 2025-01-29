
import streamlit as st
import sqlite3
import requests
from datetime import datetime

API_URL = "http://127.0.0.1:5000"  # Ensure your Flask API is running here

current_date = datetime.now().strftime("%A, %d %B %Y")

# Initialize session state if not already set
if "username" not in st.session_state:
    st.session_state.username = None
if "user_type" not in st.session_state:
    st.session_state.user_type = None
if "balance" not in st.session_state:
    st.session_state.balance = 30.0  
if "manager_balance" not in st.session_state:
    st.session_state.manager_balance = 30.0  
if "selected_slot" not in st.session_state:
    st.session_state.selected_slot = None
if "bookings" not in st.session_state:
    st.session_state.bookings = {}

# Modify the database setup function to accept a parameter for selecting the database
def get_db_connection(db_name="blu_reserve.db"):
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row  # This allows column names to be accessed as keys
    return conn


# Initialize session state for employees and manager (fetch data from DB)
if "employees" not in st.session_state:
    try:
        # Connect to the database and fetch employee data
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM employees')
        employees = cursor.fetchall()
        st.session_state.employees = [{"id": emp["id"], "name": emp["name"], "balance": emp["balance"], "manager_email": emp["manager_email"]} for emp in employees]
        conn.close()
    except Exception as e:
        st.error(f"Error fetching employees: {e}")

if "manager_name" not in st.session_state or "manager_email" not in st.session_state:
    try:
        # Fetch manager data (assuming manager_email is unique)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM managers WHERE email = ?', ('manager@gmail.com',))  # Replace with actual manager's email if dynamic
        manager = cursor.fetchone()
        st.session_state.manager_name = manager["name"]
        st.session_state.manager_email = manager["email"]
        conn.close()
    except Exception as e:
        st.error(f"Error fetching manager: {e}")

# Initialize user balance (you might fetch this dynamically for real use)
if "balance" not in st.session_state:
    st.session_state.balance = 30.0  # Initial balance for user (you can adjust this)


# Example function to insert data into both blu_reserve.db and cafe.db
def add_money_to_employee(employee_id, amount):
    # Connect to blu_reserve.db
    conn_blu = get_db_connection('blu_reserve.db')
    cursor_blu = conn_blu.cursor()
    cursor_blu.execute('SELECT * FROM employees WHERE id = ?', (employee_id,))
    employee = cursor_blu.fetchone()
    if employee:
        new_balance_blu = employee["balance"] + amount
        cursor_blu.execute('UPDATE employees SET balance = ? WHERE id = ?', (new_balance_blu, employee_id))
        conn_blu.commit()
        conn_blu.close()
        
        # Now, update cafe_db as well
        conn_cafe = get_db_connection('cafe.db')
        cursor_cafe = conn_cafe.cursor()
        cursor_cafe.execute('SELECT * FROM employees WHERE id = ?', (employee_id,))
        employee_cafe = cursor_cafe.fetchone()
        if employee_cafe:
            new_balance_cafe = employee_cafe["balance"] + amount
            cursor_cafe.execute('UPDATE employees SET balance = ? WHERE id = ?', (new_balance_cafe, employee_id))
            conn_cafe.commit()
        else:
            # Handle case where employee doesn't exist in cafe_db (optional)
            cursor_cafe.execute('INSERT INTO employees (id, balance) VALUES (?, ?)', (employee_id, amount))
            conn_cafe.commit()

        conn_cafe.close()
        
        # Update session state
        for emp in st.session_state.employees:
            if emp["id"] == employee_id:
                emp["balance"] = new_balance_blu
        return f"Added ${amount} to {employee['name']}'s balance in both databases."
    
    conn_blu.close()
    return "Employee not found."


# User balance page
def employee_dashboard():
    st.title("Blu Reserve Payment Page")
    # Display user's balance
    st.subheader("Your Blu Dollar Balance")
    st.write(f"**Balance**: ${st.session_state.balance:.2f}")
    # Display manager's details
    st.subheader("Manager's Information")
    st.write(f"**Manager Name**: {st.session_state.manager_name}")
    st.write(f"**Manager Email**: {st.session_state.manager_email}")
    # Section for requesting the user to add money
    if st.session_state.user_type == "employee":
        st.subheader("Add Money to Your Balance")
        add_amount = st.number_input("Enter the amount to add (in Blu Dollars)", min_value=1.0, step=1.0)
        # Button to trigger balance update
        if st.button("Request to add Money"):
            if add_amount > 0:
                st.session_state.balance += add_amount
                st.success(f"${add_amount} has been requested")
            else:
                st.error("Please enter a valid amount to add.")


# Manager Dashboard for Employee Balance Management
def manager_dashboard():
    #st.write(f"Session State: {st.session_state}")

    st.title(f"Manager Dashboard: {st.session_state.manager_name}")
    st.write(f"Manager Email: {st.session_state.manager_email}")
    # Filter employees who are managed by the current manager
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM employees')
    employees = cursor.fetchall()
    st.session_state.employees = [{"id": emp["id"], "name": emp["name"], "balance": emp["balance"], "manager_email": emp["manager_email"]} for emp in employees]
     # Filter employees who are managed by the current manager
    employees_under_manager = [
        emp for emp in st.session_state.employees if emp["manager_email"] == st.session_state.manager_email
    ]
    conn.close()
    # Show the employees under the manager
    st.subheader("Employees under your management")
    if not employees_under_manager:
        st.write("Pratheek, Shubham")
    
    total_balance = 90.0  # To keep track of the total balance
    for employee in employees_under_manager:
        col1, col2, col3, col4 = st.columns([2, 3, 2, 2])
        with col1:
            st.write("pratheek")
            st.write("Alice")
        with col2:
            st.write("1")
            st.write("2")
        with col3:
            st.write("25.0")
            st.write("30.0")
        with col4:
            # Input box to add money to employee's balance
            add_money = st.number_input(f"Add Money to {employee['name']}", min_value=0.0, step=1.0, key=f"add_money_{employee['id']}")
            if st.button(f"Add Money to {employee['name']}", key=f"add_button_{employee['id']}"):
                if add_money > 0:
                    result = add_money_to_employee(employee["id"], add_money)
                    st.success(result)
                else:
                    st.warning("Please enter a valid amount.")
        total_balance += employee["balance"]
    
    # Total balance of all employees
    st.subheader(f"Total Balance of All Employees: ${total_balance:.2f}")
    # Button to update the database (simulation)
    if st.button("Update Employee Balances"):
        st.success("Employee balances have been updated in the database.")

def first_page():
    st.title("Seat Reservation System")
    btn1 = st.button("Go to Seat Booking")
    btn2 = st.button("Check Wallet")
    if btn1:
        st.session_state.runpage = select_time_slot
        st.session_state.runpage()
        st.rerun()

    if btn2:
        if st.session_state.user_type == "employee":
            st.session_state.runpage = employee_dashboard # Redirect to employee dashboard
        elif st.session_state.user_type == "manager":
            st.session_state.runpage = manager_dashboard # Redirect to manager dashboard
        else:
            st.error("🚫 Invalid user type.")
        st.session_state.runpage()
        st.rerun()
def login_user():
    st.title("Login to Blu-Reserve Booking")
    
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("Login"):
        if email and password:
            data = {"email": email, "password": password}
            response = requests.post(f"{API_URL}/login", json=data)
            
            if response.status_code == 200:
                try:
                    res_data = response.json()
                    st.session_state.username = res_data["username"]
                    st.session_state.user_type = res_data["user_type"]
                    st.session_state.email = res_data["email"]
                    st.session_state.manager_email = res_data.get("manager_email")  
                    st.session_state.manager_name = res_data.get("manager_name", "Unknown Manager")  
                    st.session_state.balance = res_data.get("balance", 30.0)  
                    
                except ValueError:
                    st.error("🚫 Invalid response from server (not JSON).")
            else:
                if response.text:
                    try:
                        error_data = response.json()
                        st.error(f"Login failed: {error_data.get('message', 'Unknown error')}")
                    except ValueError:
                        st.error(f"Login failed: {response.text}")
                else:
                    st.error("🚫 No response received from server.")
        else:
            st.warning("Please enter both email and password.")





def register_user():
    st.title("Register for Blu-Reserve Booking")
    
    email = st.text_input("Email", key="register_email")
    password = st.text_input("Password", type="password", key="register_password")
    username = st.text_input("Username", key="register_username")  
    
    user_type = st.selectbox("Select user type", ["employee", "manager"], key="user_type")
    manager_email = None
    if user_type == "employee":
        manager_email = st.text_input("Manager's Email", key="register_manager_email")
        
    if st.button("Register"):
        if not username:
            st.warning("Please provide a username!")
            return
        
        if email and password and (user_type != "employee" or manager_email):
            data = {
                "email": email,
                "password": password,
                "username": username,  # Include username
                "user_type": user_type,
                "manager_email": manager_email
            }
            
            response = requests.post(f"{API_URL}/register", json=data)
            
            if response.status_code == 200:
                try:
                    res_data = response.json()  
                    st.success("Registration successful!")
                except ValueError:
                    st.error("🚫 Invalid response from server (not JSON).")
            else:
                if response.text:  
                    try:
                        error_data = response.json()  
                        st.error(f"Registration failed: {error_data.get('message', 'Unknown error')}")
                    except ValueError:
                        st.error(f"Registration failed: {response.text}")  
                else:
                    st.error("🚫 No response received from server.")
        else:
            st.warning("Please fill all fields.")


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
        res_data = response.json()
        if res_data.get("status") == "success":
            if "balance" in res_data:
                st.session_state.balance = st.session_state.balance - 5
            if st.session_state.user_type == "manager" and 'manager_balance' in res_data:
                st.session_state.manager_balance = st.session_state.manager_balance - 5
            st.session_state.bookings[slot] = st.session_state.bookings.get(slot, 0) + 1
            st.success(f"👍 {res_data['message']}")
        else:
            st.error(f"❌ {res_data.get('message', 'Booking failed.')}")
        return res_data
    except ValueError:
        return {"message": "🚫 Invalid response from the server."}


def cancel_seat(seat_number, slot):
    data = {"username": st.session_state.username, "seat_number": seat_number, "slot": slot}
    response = requests.post(f"{API_URL}/cancel_seat", json=data)
    try:
        res_data = response.json()
        if res_data.get("status") == "success":
            if st.session_state.user_type == "manager" and 'manager_balance' in res_data:
                st.session_state.manager_balance = st.session_state.manager_balance + 5
            st.session_state.bookings[slot] -= 1
            if st.session_state.bookings[slot] == 0:
                del st.session_state.bookings[slot]
            st.success(f"👍 {res_data['message']}")
            st.session_state.balance = st.session_state.balance + 5
        else:
            st.error(f"❌ {res_data.get('message', 'Booking cancellation failed.')}")

    except ValueError:
        st.error("🚫 Invalid response from the server.")

def display_seat_matrix(mode="book"):
    slot = st.session_state.selected_slot
    if not slot:
        st.warning("Please select a time slot first.")
        return

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
                        if cols[col_idx].button("🪑", key=f"book_{seat_id}") :
                            res = book_seat(seat_id, slot)
                            st.success(f"👍 {res['message']}")
                            st.session_state.balance = res.get("balance", st.session_state.balance)
                            st.session_state.bookings[slot] = st.session_state.bookings.get(slot, 0) + 1
                            st.rerun()
                elif mode == "cancel":
                    if is_booked:
                        if cols[col_idx].button("❌", key=f"cancel_{seat_id}") :
                            cancel_seat(seat_id, slot)
                            st.session_state.bookings[slot] -= 1
                            if st.session_state.bookings[slot] == 0:
                                del st.session_state.bookings[slot]
                            st.rerun()
                    else:
                        cols[col_idx].button("⬜", disabled=True, key=f"cancel_unbooked_{seat_id}")

def select_time_slot():
    st.title("🍽️ Blu-Reserve Booking System")
    st.header("Reserve your seat hassle-free! 🪑")
    st.subheader(f"{current_date}")
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
        if cols[i % 3].button(button_label, key=f"slot_{slot}") :
            st.session_state.selected_slot = slot
            st.rerun()

def logout_user():
    st.session_state.username = None
    st.session_state.user_type = None
    st.session_state.balance = 30.0  # Reset balance
    st.session_state.selected_slot = None
    st.session_state.bookings = {}

def my_bookings():
    st.title("📅 My Bookings")
    if not st.session_state.bookings:
        st.write("❌ No bookings yet.")
    else:
        for slot, booked_seats in st.session_state.bookings.items():
            with st.container():
                st.markdown(f"### Booking for {slot}")
                st.write(f"**Seats Booked:** {booked_seats}")
                cancel_button = st.button(f"❌ Cancel Booking for {slot}", key=f"cancel_booking_{slot}")
                if cancel_button:
                    # Cancel the booked seats
                    cancel_seat_for_slot(slot)
                    del st.session_state.bookings[slot]  
                    st.session_state.selected_slot = None
                    st.rerun()

def cancel_seat_for_slot(slot):
   
    seat_matrix = get_seats(slot)
    if seat_matrix:
        for row in seat_matrix:
            for seat in row:
                if isinstance(seat, dict) and seat["is_booked"]:
                    cancel_seat(seat["seat_number"], slot)

import requests

def send_email_to_manager(employee_mail, manager_email, amount):
    api_url = "http://127.0.0.1:5000/send_money_request_email"  # URL to the backend API
    data = {
        "employee_name": employee_mail,
        "manager_email": manager_email,
        "amount": amount
    }
    response = requests.post(api_url, json=data)
    if response.status_code == 200:
        return response.json().get("message")
    else:
        return f"Error: {response.json().get('message')}"


def main():
    if st.session_state.username is None:
        page = st.sidebar.radio("Select Page", ["Login", "Register"])
        if page == "Login":
            login_user()
        elif page == "Register":
            register_user()
    else:
        st.sidebar.title("💼 User Dashboard")
        st.sidebar.write(f"**Logged in as:** {st.session_state.username}")
        if st.session_state.user_type == "employee":
            st.sidebar.write(f"**Balance:** ${st.session_state.balance}")
        elif st.session_state.user_type == "manager":
            st.sidebar.write(f"**Balance:** ${st.session_state.balance}")
        else:
            st.sidebar.write("User type is not recognized.")
        if st.session_state.user_type == "employee":
            if st.session_state.manager_name:
                st.sidebar.write(f"**Manager:** {st.session_state.manager_name}")  
        if st.session_state.user_type == "employee":
            sidebar_options = ["Select Slot", "My Bookings","Check Wallet"]
            sidebar_selection = st.sidebar.radio("Choose Option", sidebar_options)
        elif st.session_state.user_type == "manager":
            sidebar_options = ["Select Slot", "My Bookings","Check Wallet", "Manage Team Funds"]
            sidebar_selection = st.sidebar.radio("Choose Option", sidebar_options)

       
        if st.sidebar.button("Logout"):
            logout_user()
            st.session_state.clear()
            st.rerun()  
            
        if st.session_state.user_type == "employee":
            if sidebar_selection == "Select Slot":
                if st.session_state.selected_slot is None:
                    select_time_slot()
                else:
                    st.sidebar.write(f"**Selected Slot:** {st.session_state.selected_slot}")
                    action = st.sidebar.radio("Choose Action", ["Book Seat", "Cancel Booking"])

                    if action == "Book Seat":
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
            elif sidebar_selection == "My Bookings":
                my_bookings()
            elif sidebar_selection == "Check Wallet":
                    employee_dashboard()

        elif st.session_state.user_type == "manager":
            if sidebar_selection == "Select Slot":
                if st.session_state.selected_slot is None:
                    select_time_slot()
                else:
                    st.sidebar.write(f"**Selected Slot:** {st.session_state.selected_slot}")
                    action = st.sidebar.radio("Choose Action", ["Book Seat", "Cancel Booking"])

                    if action == "Book Seat":
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
            elif sidebar_selection == "My Bookings":
                my_bookings()
            elif sidebar_selection == "Check Wallet":
                employee_dashboard()
            elif sidebar_selection == "Manage Team Funds":
                manager_dashboard()

            


if __name__ == "__main__":
    main()