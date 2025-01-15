import streamlit as st
import numpy as np
import pandas as pd
import streamlit_authenticator as stauth
from database import UserDB
import json
import re
from claude_service import ClaudeService
from flashcard_ui import *

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
    
    st.title("MemApp")
    
    # Add debug toggle in sidebar
    debug_mode = st.sidebar.checkbox("Debug Mode", value=True)
    
    def load_config():
        try:
            config = st.config.get_option('app')
        except:
            config = {'flashcards_per_session': 3}  # Default if not in config
        st.session_state['config'] = config
    
    load_config()
    
    class FlashcardApp:
        def __init__(self):
            self.db = UserDB()
            self.claude = ClaudeService()
            self.init_session_state()
        
        def init_session_state(self):
            if 'current_cards' not in st.session_state:
                st.session_state.update({
                    'current_cards': None,
                    'current_index': 0,
                    'show_answer': False,
                    'user_answer': "",
                    'feedback': None,
                    'difficulty': None,
                    'session_results': []
                })
        
        def handle_card_completion(self, difficulty, is_correct):
            current_card = st.session_state.current_cards[st.session_state.current_index]
            
            # Save result to session
            st.session_state.session_results.append({
                'question': current_card['question'],
                'correct_answer': current_card['answer'],
                'user_answer': st.session_state.user_answer,
                'correct': is_correct,
                'difficulty': difficulty
            })
            
            # Save to database
            self.db.save_flashcard_result(
                username=username,
                question=current_card['question'],
                answer=current_card['answer'],
                is_correct=is_correct,
                difficulty=difficulty
            )
            
            # Check if session is complete
            if len(st.session_state.session_results) >= len(st.session_state.current_cards):
                show_study_session_summary(st.session_state.session_results)
            else:
                self.next_card()
        
        def next_card(self):
            st.session_state.current_index += 1
            if st.session_state.current_index >= len(st.session_state.current_cards):
                st.session_state.current_index = 0
            st.session_state.update({
                'show_answer': False,
                'user_answer': "",
                'feedback': None,
                'difficulty': None
            })
            st.rerun()
        
        def run(self):
            with st.form(key='flashcard_form'):
                topic = st.text_input("Enter a topic:", 
                                    value="Amino acids",
                                    disabled=st.session_state.get('form_disabled', False))
                submit_disabled = st.session_state.get('form_disabled', False)
                if st.form_submit_button("Generate Flashcards", disabled=submit_disabled):
                    self.generate_flashcards(topic)
            
            if st.session_state.current_cards:
                self.show_current_card()
        
        def show_current_card(self):
            current_card = st.session_state.current_cards[st.session_state.current_index]
            total_cards = len(st.session_state.current_cards)
            
            show_progress(st.session_state.current_index, total_cards)
            show_question(current_card['question'])
            
            if not st.session_state.show_answer:
                self.handle_answer_input()
            else:
                self.show_answer_and_feedback(current_card)

        def generate_flashcards(self, topic):
            with st.spinner("Creating flashcards..."):
                response = self.claude.create_flashcards(topic)
                try:
                    flashcards = self.clean_and_parse_json(response)
                    if flashcards:
                        st.session_state.update({
                            'current_cards': flashcards,
                            'current_index': 0,
                            'show_answer': False,
                            'user_answer': "",
                            'feedback': None,
                            'difficulty': None
                        })
                except Exception as e:
                    if st.session_state.get('debug_mode', False):
                        st.error(f"Error processing response: {str(e)}")
                    st.error("Failed to generate flashcards. Please try again.")

        def clean_and_parse_json(self, response_text):
            try:
                # Try direct JSON parsing first
                return json.loads(str(response_text))
            except:
                # Remove TextBlock wrapper if present
                text = re.sub(r'TextBlock\(text=\'(.*?)\'.*?\)', r'\1', str(response_text))
                
                # Find anything that looks like a JSON array
                match = re.search(r'\[(.*?)\]', text, re.DOTALL)
                if match:
                    try:
                        # Clean up the extracted JSON
                        json_str = match.group(0)
                        json_str = json_str.strip('[]').strip()
                        json_str = f"[{json_str}]"
                        json_str = json_str.replace('\n', ' ').replace('\\n', ' ')
                        json_str = re.sub(r'\s+', ' ', json_str)
                        
                        return json.loads(json_str)
                    except Exception as e:
                        if st.session_state.get('debug_mode', False):
                            st.write("Raw response:", response_text)
                            st.write("Cleaned JSON:", json_str)
                        raise
                raise ValueError("No JSON array found in response")

        def handle_answer_input(self):
            user_answer = show_answer_input()
            if st.button("Check Answer"):
                feedback_prompt = {
                    "question": st.session_state.current_cards[st.session_state.current_index]['question'],
                    "answer": st.session_state.current_cards[st.session_state.current_index]['answer'],
                    "user_answer": user_answer
                }
                feedback_response = self.claude.create_feedback(feedback_prompt)
                try:
                    cleaned_response = self.clean_and_parse_json(feedback_response)
                    st.session_state.update({
                        'user_answer': user_answer,
                        'show_answer': True,
                        'feedback': cleaned_response
                    })
                except Exception as e:
                    st.error(f"Failed to parse feedback: {str(e)}")
                    st.error("Raw response:")
                    st.code(feedback_response)
                    st.session_state.update({
                        'user_answer': user_answer,
                        'show_answer': True,
                        'feedback': {
                            "correct": False,
                            "explanation": "Unable to evaluate answer. Please try again."
                        }
                    })
                st.rerun()

        def show_answer_and_feedback(self, current_card):
            is_correct = show_feedback(current_card['answer'], 
                                     st.session_state.user_answer, 
                                     st.session_state.feedback)
            
            is_last_card = len(st.session_state.session_results) >= len(st.session_state.current_cards) - 1
            
            if is_correct:
                clicked = show_difficulty_buttons(disabled=False)  # Never disable difficulty buttons
                if any(clicked.values()):
                    difficulty = next(k for k, v in clicked.items() if v)
                    self.handle_card_completion(difficulty, is_correct)
            else:
                # Show "Summary" button for last card, otherwise "Next Card"
                button_text = "Show Summary" if is_last_card else "Next Card"
                if show_next_button(text=button_text, disabled=False):
                    self.handle_card_completion("hard", is_correct)

    # Initialize and run app
    if authentication_status:
        app = FlashcardApp()
        app.run()