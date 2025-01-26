import streamlit as st
from database import sign_up, login

# Function to display the Sign-Up page
def show_signup_page():
    # Check if already logged in, redirect to the dashboard
    if st.session_state.get('logged_in'):
        redirect_to_dashboard()
        return

    # Display the sign-up form
    st.subheader("Create Riveria Account")
    email = st.text_input("Email", key="signup_email")
    username = st.text_input("Username", key="signup_username")
    password = st.text_input("Password", type="password", key="signup_password")
    confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")
    role = st.selectbox("Select Role", ["Employee", "Manager"], key="signup_role")

    manager_email = None
    if role == "Employee":
        manager_email = st.text_input("Manager Email ID", key="signup_manager_email")

    if st.button("Sign Up"):
        if password != confirm_password:
            st.error("Passwords do not match!")
        else:
            result = sign_up(email, username, password, role, manager_email=manager_email)
            if result:  # If sign_up() returns an error message
                st.error(result)
            else:
                st.success("Account created successfully! Please log in.")
                st.experimental_rerun()  # Refresh to clear the form


# Function to display the Login page
def show_login_page():
    # Check if already logged in, redirect to the dashboard
    if st.session_state.get('logged_in'):
        redirect_to_dashboard()
        return

    # Display the login form
    st.subheader("Login to Your Riveria Account")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")
    role = st.selectbox("Select Role", ["Employee", "Manager"], key="login_role")

    if st.button("Login"):
        user = login(email, password, role)
        if user:
            # Set session state variables on successful login
            st.session_state.logged_in = True
            st.session_state.username = user[0]
            st.session_state.role = role
            st.session_state.user_id = user[1]
            st.session_state.email = email  # Store email in session state


            st.success(f"Welcome back, {st.session_state.username} ({st.session_state.role})!")
            redirect_to_dashboard()
        else:
            st.error("Invalid email, password, or role.")


# Redirect to appropriate dashboard based on user role
def redirect_to_dashboard():
    if st.session_state.get("role") == "Manager":
        st.experimental_set_query_params(page="manager_dashboard")
    elif st.session_state.get("role") == "Employee":
        st.experimental_set_query_params(page="employee_dashboard")
    st.experimental_rerun()


# Function to display the main Login/Signup page
def display_page():
    query_params = st.experimental_get_query_params()
    current_page = query_params.get("page", ["login"])[0]  # Default to "login"

    if current_page == "manager_dashboard":
        import manager_dashboard
        manager_dashboard.show_manager_dashboard()
    elif current_page == "employee_dashboard":
        import employee_dashboard
        employee_dashboard.show_employee_dashboard()
    else:
        # If not logged in, show login/signup options
        if not st.session_state.get("logged_in"):
            login_or_signup = st.radio("Select Login or Sign-Up", ["Login", "Sign Up"])
            if login_or_signup == "Login":
                show_login_page()
            else:
                show_signup_page()
        else:
            redirect_to_dashboard()


# Initialize session state variables
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None

# Call the function to display the appropriate page
if __name__ == "__main__":
    display_page()
