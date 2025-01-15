import streamlit as st
import numpy as np
import pandas as pd
import streamlit_authenticator as stauth
from database import UserDB
import json
import re
from claude_service import ClaudeService
from flashcard_ui import (
    show_error, show_progress, show_question, show_answer_input, 
    show_feedback, show_difficulty_buttons, show_next_button, 
    initialize_session, show_study_session_summary
)

# After imports
st.set_page_config(
    page_title="MemApp",
    page_icon="🧠",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
    /* Color variables */
    :root {
        --primary-blue: #3b71ca;
        --primary-blue-hover: #4f8df5;
        --success-green: #257953;
        --success-bg: #f0faf4;
        --success-border: #dcfce7;
        --error-red: #cc0f35;
        --error-bg: #fff3f5;
        --error-border: #fecdd3;
        --neutral-gray: #e5e7eb;
        --text-dark: #1f2937;
    }

    /* Override any red borders/text except for errors */
    *:not([data-baseweb="notification"][class*="error"]) {
        border-color: var(--neutral-gray) !important;
        color: inherit !important;
    }

    /* Remove hover border color changes */
    *:not([data-baseweb="notification"][class*="error"]):focus,
    *:not([data-baseweb="notification"][class*="error"]):hover {
        border-color: var(--neutral-gray) !important;
    }

    /* Preserve specific text colors */
    .stButton button {
        color: white !important;
    }

    [data-testid="stFormSubmitButton"] button {
        color: var(--primary-blue) !important;
    }

    /* Base card styling */
    .stMarkdown div.stMarkdown {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }

    /* Button styling - prevent any red flashes */
    .stButton button,
    .stButton button:hover,
    .stButton button:active,
    .stButton button:focus,
    .stButton button:visited {
        border-radius: 20px;
        padding: 0.5rem 1.5rem;
        transition: all 0.3s ease;
        font-weight: 500;
        box-shadow: 0 2px 4px rgba(59, 113, 202, 0.1);
        border-color: transparent !important;
        outline: none !important;
    }

    /* Regular buttons - all states */
    .stButton button:not([data-testid="stFormSubmitButton"]),
    .stButton button:not([data-testid="stFormSubmitButton"]):hover,
    .stButton button:not([data-testid="stFormSubmitButton"]):active,
    .stButton button:not([data-testid="stFormSubmitButton"]):focus {
        background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-blue-hover) 100%);
        color: white !important;
        border: none !important;
    }

    /* Form submit button - all states */
    [data-testid="stFormSubmitButton"] button,
    [data-testid="stFormSubmitButton"] button:hover,
    [data-testid="stFormSubmitButton"] button:active,
    [data-testid="stFormSubmitButton"] button:focus {
        background: white;
        color: var(--primary-blue) !important;
        border: 2px solid var(--primary-blue) !important;
    }

    /* Button specific hover states */
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 113, 202, 0.2);
        color: white !important;
    }

    [data-testid="stFormSubmitButton"] button:hover {
        color: var(--primary-blue) !important;
    }

    /* Input fields */
    .stTextArea textarea {
        border-radius: 10px;
        border: 2px solid var(--neutral-gray) !important;
        padding: 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }

    .stTextArea textarea:focus {
        border-color: var(--primary-blue) !important;
        box-shadow: 0 0 0 3px rgba(59, 113, 202, 0.1);
    }

    /* Success and error messages */
    div[data-baseweb="notification"][class*="success"] {
        background-color: var(--success-bg) !important;
        color: var(--success-green) !important;
        border-left: 4px solid var(--success-green);
        border-radius: 8px;
        padding: 1rem;
    }

    div[data-baseweb="notification"][class*="error"] {
        background-color: var(--error-bg) !important;
        color: var(--error-red) !important;
        border-left: 4px solid var(--error-red);
        border-radius: 8px;
        padding: 1rem;
    }

    /* Progress bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--primary-blue) 0%, var(--primary-blue-hover) 100%);
        height: 8px;
        border-radius: 4px;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        color: var(--text-dark);
        font-weight: 600;
    }

    /* Question card */
    .question-card {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin: 1.5rem 0;
        border: 1px solid var(--neutral-gray);
    }

    .question-card h3 {
        color: var(--text-dark);
        margin: 0;
        font-weight: 600;
    }

    /* Remove link icons */
    .stMarkdown a::after,
    .stMarkdown a::before,
    a.external-link::after,
    a.internal-link::after {
        content: none !important;
        display: none !important;
    }

    /* Hide any other auto-generated icons */
    .stMarkdown svg.icon {
        display: none !important;
    }

    /* Preset topic buttons */
    [data-testid="stFormSubmitButton"]:not(:last-child) button {
        min-height: 0;
        padding: 0.3rem;
        white-space: pre-line;
        line-height: 1.2;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

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
    debug_mode = st.sidebar.checkbox("Debug Mode", value=False)
    st.session_state['debug_mode'] = debug_mode
    
    def load_config():
        try:
            config = st.config.get_option('app')
            if st.session_state.get('debug_mode', False):
                st.sidebar.write("Config loaded:", config)
        except:
            config = {'flashcards_per_session': 2}  # Default if not in config
            if st.session_state.get('debug_mode', False):
                st.sidebar.write("Using default config:", config)
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
            
            # Only append and save if this card hasn't been reviewed yet
            if len(st.session_state.session_results) < len(st.session_state.current_cards):
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
            
            # Show summary if all cards are reviewed
            if len(st.session_state.session_results) >= len(st.session_state.current_cards):
                st.session_state.update({
                    'session_complete': True,
                    'clearing_session': False,  # Don't clear yet
                    'show_form_only': False     # Keep showing the current UI
                })
            else:
                self.next_card()
            st.rerun()
        
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
            try:
                if st.session_state.get('debug_mode', False):
                    st.write("DEBUG: Current session state at start of run:", {
                        'show_form_only': st.session_state.get('show_form_only'),
                        'clearing_session': st.session_state.get('clearing_session'),
                        'session_complete': st.session_state.get('session_complete'),
                        'current_cards': bool(st.session_state.get('current_cards')),
                        'current_index': st.session_state.get('current_index')
                    })

                # Show summary if session is complete
                if st.session_state.get('session_complete'):
                    show_study_session_summary(st.session_state.get('session_results', []))
                    return

                # Only show form if in reset state or session complete
                if st.session_state.get('show_form_only', False):
                    # Clear any existing UI
                    st.empty()
                    
                    # Show only the form
                    with st.form(key='flashcard_form'):
                        topic = st.text_input(
                            "",  # Remove label
                            value="",
                            placeholder="Enter any topic you want to learn about...",
                        )
                        
                        # Add suggestion text and buttons in columns
                        st.markdown("##### Try one of these:")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            amino_clicked = st.form_submit_button("🧬 Amino\nAcids", use_container_width=True)
                        with col2:
                            provinces_clicked = st.form_submit_button("🍁 Canadian\nProvinces", use_container_width=True)
                        with col3:
                            amendments_clicked = st.form_submit_button("📜 US\nAmendments", use_container_width=True)
                        
                        # Add spacing before main button
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        # Main generate button
                        generate_clicked = st.form_submit_button("✨ Generate Flashcards", use_container_width=True)
                        
                        # Handle form submission
                        if amino_clicked:
                            topic = "Amino acids"
                        elif provinces_clicked:
                            topic = "Provinces of Canada"
                        elif amendments_clicked:
                            topic = "Constitutional amendments"
                        
                        # Generate flashcards if we have a topic
                        if (amino_clicked or provinces_clicked or amendments_clicked or 
                            (generate_clicked and topic)):
                            self.generate_flashcards(topic)
                            st.session_state['show_form_only'] = False
                            st.session_state['session_complete'] = False
                            st.rerun()
                    return

                # Normal flow
                if st.session_state.get('current_cards'):
                    self.show_current_card()
                else:
                    # Show the form if no cards are present
                    with st.form(key='flashcard_form'):
                        st.markdown("##### Create New Flashcards")
                        topic = st.text_input(
                            "Enter a topic:",
                            value="Amino acids",
                            placeholder="e.g., Photosynthesis, French Revolution, Python Programming"
                        )
                        if st.form_submit_button("✨ Generate Flashcards", use_container_width=True):
                            self.generate_flashcards(topic)
                            st.rerun()
            except Exception as e:
                show_error(f"Application error: {str(e)}", show_state=True)
        
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
            try:
                with st.spinner("Creating flashcards..."):
                    # Only show debug info if debug mode is enabled
                    if st.session_state.get('debug_mode', False):
                        st.write("DEBUG: Attempting to create flashcards for topic:", topic)
                    
                    response = self.claude.create_flashcards(topic)
                    if st.session_state.get('debug_mode', False):
                        st.write("DEBUG: Raw response from Claude:", response)
                    
                    try:
                        flashcards = self.clean_and_parse_json(response)
                        if st.session_state.get('debug_mode', False):
                            st.write("DEBUG: Parsed flashcards:", flashcards)
                        
                        if flashcards and isinstance(flashcards, list) and len(flashcards) > 0:
                            st.session_state.update({
                                'current_cards': flashcards,
                                'current_index': 0,
                                'show_answer': False,
                                'user_answer': "",
                                'feedback': None,
                                'difficulty': None
                            })
                            st.write("DEBUG: Successfully updated session state with flashcards")
                        else:
                            show_error("No valid flashcards were generated. Response was empty or invalid.", show_state=True)
                    except Exception as parse_error:
                        st.write("DEBUG: Failed to parse response:", str(parse_error))
                        show_error(f"Failed to process flashcards: {str(parse_error)}", show_state=True)
                        if st.session_state.get('debug_mode', False):
                            st.write("Raw response that failed parsing:", response)
            except Exception as e:
                st.write("DEBUG: Top-level error in generate_flashcards:", str(e))
                show_error(f"Failed to generate flashcards: {str(e)}", show_state=True)
                if st.session_state.get('debug_mode', False):
                    st.write("Full error details:", e)
                    import traceback
                    st.code(traceback.format_exc())

        def clean_and_parse_json(self, response_text):
            try:
                # Handle Anthropic API response structure
                if hasattr(response_text, 'content') and hasattr(response_text.content[0], 'text'):
                    response_text = response_text.content[0].text
                
                # Try direct JSON parsing first
                if st.session_state.get('debug_mode', False):
                    st.write("DEBUG: Attempting direct JSON parse")
                return json.loads(str(response_text).strip())
            except json.JSONDecodeError as e:
                if st.session_state.get('debug_mode', False):
                    st.write(f"DEBUG: Direct JSON parse failed: {str(e)}")
                try:
                    # Try to find JSON object or array
                    text = str(response_text).strip()
                    if text.strip().startswith('{'):
                        # Handle single JSON object
                        return json.loads(text)
                    else:
                        # Handle JSON array
                        match = re.search(r'\[(.*?)\]', text, re.DOTALL)
                        if match:
                            try:
                                # Clean up the extracted JSON
                                json_str = match.group(0)
                                json_str = json_str.replace('\n', ' ').replace('\\n', ' ')
                                json_str = re.sub(r'\s+', ' ', json_str)
                                
                                if st.session_state.get('debug_mode', False):
                                    st.write("DEBUG: Attempting to parse cleaned JSON:", json_str)
                                return json.loads(json_str)
                            except Exception as e:
                                if st.session_state.get('debug_mode', False):
                                    st.write(f"DEBUG: Failed to parse cleaned JSON: {str(e)}")
                                raise
                    
                    if st.session_state.get('debug_mode', False):
                        st.write("DEBUG: No valid JSON found in response")
                    raise ValueError("No valid JSON found in response")
                except Exception as e:
                    if st.session_state.get('debug_mode', False):
                        st.write(f"DEBUG: Error in cleanup process: {str(e)}")
                    raise

        def handle_answer_input(self):
            user_answer = show_answer_input()
            if st.button("Check Answer"):
                if st.session_state.get('debug_mode', False):
                    st.write("DEBUG: Starting answer check")
                    st.write("DEBUG: User answer:", user_answer)
                
                feedback_prompt = {
                    "question": st.session_state.current_cards[st.session_state.current_index]['question'],
                    "answer": st.session_state.current_cards[st.session_state.current_index]['answer'],
                    "user_answer": user_answer
                }
                
                # Ensure prompt is properly formatted JSON
                feedback_prompt_json = json.dumps(feedback_prompt)
                
                if st.session_state.get('debug_mode', False):
                    st.write("DEBUG: Feedback prompt:", feedback_prompt_json)
                
                feedback_response = self.claude.create_feedback(json.loads(feedback_prompt_json))
                
                if st.session_state.get('debug_mode', False):
                    st.write("DEBUG: Raw feedback response:", feedback_response)
                
                try:
                    cleaned_response = self.clean_and_parse_json(feedback_response)
                    if st.session_state.get('debug_mode', False):
                        st.write("DEBUG: Cleaned feedback response:", cleaned_response)
                    
                    # Validate feedback format
                    if isinstance(cleaned_response, list):
                        cleaned_response = cleaned_response[0]
                    
                    if not isinstance(cleaned_response, dict) or 'correct' not in cleaned_response or 'explanation' not in cleaned_response:
                        raise ValueError("Invalid feedback format")
                    
                    st.session_state.update({
                        'user_answer': user_answer,
                        'show_answer': True,
                        'feedback': cleaned_response
                    })
                except Exception as e:
                    if st.session_state.get('debug_mode', False):
                        st.write("DEBUG: Error processing feedback:", str(e))
                        st.write("DEBUG: Response type:", type(feedback_response))
                        st.write("DEBUG: Full error:", e)
                        import traceback
                        st.code(traceback.format_exc())
                    
                    st.error(f"Failed to process feedback: {str(e)}")
                    st.session_state.update({
                        'user_answer': user_answer,
                        'show_answer': True,
                        'feedback': {
                            "correct": False,
                            "explanation": f"Error evaluating answer: {str(e)}"
                        }
                    })
                st.rerun()

        def show_answer_and_feedback(self, current_card):
            is_correct = show_feedback(current_card['answer'], 
                                     st.session_state.user_answer, 
                                     st.session_state.feedback)
            
            is_last_card = len(st.session_state.session_results) >= len(st.session_state.current_cards) - 1
            
            if is_correct:
                clicked = show_difficulty_buttons(disabled=False)
                if any(clicked.values()):
                    difficulty = next(k for k, v in clicked.items() if v)
                    st.write("DEBUG: Difficulty button clicked:", difficulty)
                    self.handle_card_completion(difficulty, is_correct)
            else:
                button_text = "Show Summary" if is_last_card else "Next Card"
                if show_next_button(text=button_text, disabled=False):
                    st.write("DEBUG: Next/Summary button clicked")
                    self.handle_card_completion("hard", is_correct)

    # Initialize and run app
    if authentication_status:
        # Initialize session state
        initialize_session()
        
        app = FlashcardApp()
        app.run()