import streamlit as st
import nltk
import os

nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)

# Define the authentication function
def authenticate(username, password):
    return (username == st.secrets["auth_username"] and 
            password == st.secrets["auth_password"])

# Main application
def main():
    st.set_page_config(page_title="Skybox Assistant", page_icon="🏠")

    # Initialize session state for authentication
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # Sidebar for login/logout
    with st.sidebar:
        if not st.session_state.authenticated:
            st.title("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                if authenticate(username, password):
                    st.session_state.authenticated = True
                    st.success("Logged in successfully!")
                else:
                    st.error("Invalid username or password")
        else:
            st.title("Navigation")
            if st.button("Logout"):
                st.session_state.authenticated = False
                st.success("Logged out successfully!")
    # Main content
    if st.session_state.authenticated:
        st.title("Welcome to Skybox Assistant")


        # Display available pages
        st.sidebar.page_link("pages/1_upload_pdf.py", label="Skybox PDF Upload")
        st.sidebar.page_link("pages/2_Skybox_Assistant.py", label="Skybox Assistant")

        st.sidebar.success("Select a page above.")
    else:
        st.title("Welcome to Skybox Assistant")
        st.write("Please log in to access the application.")

# Disable pages if not authenticated
def check_authentication():
    if not st.session_state.get('authenticated', False):
        st.error("Please log in to access this page.")
        st.stop()

if __name__ == "__main__":
    main()