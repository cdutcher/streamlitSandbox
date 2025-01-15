import streamlit as st
import numpy as np
import pandas as pd
import streamlit_authenticator as stauth
from database import UserDB
import json
import re

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
    authenticator.logout('Logout', 'sidebar')
    st.write(f'Welcome *{name}*')
    
    st.title("Flashcard Creator")
    
    # Add debug toggle in sidebar
    debug_mode = st.sidebar.checkbox("Debug Mode", value=True)
    
    from claude_service import ClaudeService
    claude = ClaudeService()
    
    def clean_and_parse_json(response_text, debug_mode=False):
        try:
            # Try direct JSON parsing first
            if debug_mode:
                st.write("Attempting direct JSON parse...")
            return json.loads(str(response_text))
        except:
            if debug_mode:
                st.write("Direct parse failed, trying to extract JSON...")
            
            # Remove TextBlock wrapper if present
            text = re.sub(r'TextBlock\(text=\'(.*?)\'.*?\)', r'\1', str(response_text))
            
            # Find anything that looks like a JSON array
            match = re.search(r'\[(.*?)\]', text, re.DOTALL)
            if match:
                try:
                    # Clean up the extracted JSON
                    json_str = match.group(0)
                    # Remove extra brackets and clean whitespace
                    json_str = json_str.strip('[]').strip()
                    json_str = f"[{json_str}]"  # Wrap in single set of brackets
                    json_str = json_str.replace('\n', ' ').replace('\\n', ' ')
                    json_str = re.sub(r'\s+', ' ', json_str)
                    
                    if debug_mode:
                        st.write("Cleaned JSON:", json_str)
                    
                    return json.loads(json_str)
                except Exception as e:
                    if debug_mode:
                        st.error(f"JSON cleaning failed: {str(e)}")
                    raise
            raise ValueError("No JSON array found in response")
    
    with st.form(key='flashcard_form'):
        topic = st.text_input("Enter a topic for flashcards:", 
                            value="Amino acids",  # Add default value
                            key="topic_input")
        submit = st.form_submit_button("Generate Flashcards")
        
        if submit and topic:
            with st.spinner("Creating flashcards..."):
                response = claude.create_flashcards(topic)
                
                if debug_mode:
                    st.write("Raw response:", response)
                
                try:
                    flashcards = clean_and_parse_json(response, debug_mode)
                    
                    if flashcards:
                        # Create tabs for each flashcard
                        tabs = st.tabs([f"Flashcard {i+1}" for i in range(len(flashcards))])
                        
                        for i, (tab, card) in enumerate(zip(tabs, flashcards)):
                            with tab:
                                st.markdown(f"**Q: {card['question']}**")
                                
                                # Use checkbox instead of button
                                if st.checkbox("Show Answer", key=f"show_{i}"):
                                    st.markdown(f"**A:** {card['answer']}")
                    else:
                        st.error("No flashcards generated")
                        
                except Exception as e:
                    if debug_mode:
                        st.error(f"Error processing response: {str(e)}")
                    st.error("Failed to generate flashcards. Please try again.")
        elif submit:
            st.warning("Please enter a topic") 