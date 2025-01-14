import streamlit as st
import numpy as np
import pandas as pd
import streamlit_authenticator as stauth
from database import UserDB

# Initialize database
db = UserDB()

# Get credentials from database
config = {
    'credentials': db.get_user_credentials(),
    'cookie': {
        'expiry_days': 30,
        'key': st.secrets["cookie_key"],
        'name': 'streamlit_auth'
    }
}

# Create authentication object
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Add login widget
name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')
    
    # Move registration form here, outside of error case
    with st.expander("Don't have an account? Sign Up"):
        with st.form("registration_form"):
            new_username = st.text_input("Username*")
            new_email = st.text_input("Email*")
            new_name = st.text_input("Full Name*")
            new_password = st.text_input("Password*", type="password")
            new_password_repeat = st.text_input("Repeat Password*", type="password")
            
            if st.form_submit_button("Sign Up"):
                if new_password != new_password_repeat:
                    st.error("Passwords do not match")
                else:
                    try:
                        db.validate_signup(new_username, new_email, new_password)
                        db.add_user(new_username, new_email, new_name, new_password)
                        st.success("Registration successful! Please log in.")
                    except ValueError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error("Registration failed. Please try again.")

elif authentication_status:
    # Show the app content
    authenticator.logout('Logout', 'sidebar')
    st.write(f'Welcome *{name}*')
    
    # Your existing app code here
    st.title("My First Streamlit App")
    
    # Add a text input
    user_input = st.text_input("Enter your name:", "")
    
    # Add a button
    if st.button("Say hello"):
        if user_input:
            st.write(f"Hello {user_input}!")
        else:
            st.write("Please enter your name!")
    
    # Add a slider
    number = st.slider("Select a number", 0, 100, 50)
    st.write(f"Selected number: {number}")
    
    # Add a selectbox
    option = st.selectbox(
        'What is your favorite color?',
        ['Red', 'Green', 'Blue', 'Yellow']
    )
    st.write(f'Your favorite color is {option}')
    
    # Display a chart
    chart_data = pd.DataFrame(
        np.random.randn(20, 3),
        columns=['Column 1', 'Column 2', 'Column 3']
    )
    st.line_chart(chart_data) 