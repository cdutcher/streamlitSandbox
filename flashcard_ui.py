import streamlit as st

def show_progress(current_index, total_cards):
    progress = current_index / total_cards
    st.progress(progress)
    st.caption(f"Card {current_index + 1} of {total_cards}")

def show_question(question):
    st.markdown(f"""
    <div class='question-card'>
        <h3>Q: {question}</h3>
    </div>
    """, unsafe_allow_html=True)

def show_answer_input():
    st.markdown("##### Your Answer")
    return st.text_area("", placeholder="Type your answer here...", key="answer_input", height=100)

def show_feedback(correct_answer, user_answer, feedback):
    # Create a container for the entire feedback section
    with st.container():
        if isinstance(feedback, list):
            feedback = feedback[0]
        
        is_correct = feedback.get('correct', False)
        
        # Apply styling based on correctness
        if is_correct:
            st.markdown("""
                <style>
                    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
                        background-color: #f0faf4;
                        padding: 1rem;
                        border-radius: 8px;
                        border: 1px solid #dcfce7;
                    }
                </style>
            """, unsafe_allow_html=True)
        
        st.markdown(f"**Correct Answer:** {correct_answer}")
        st.markdown("**Your Answer:**")
        st.write(user_answer)
        
        if is_correct:
            st.success(feedback.get('explanation', 'Correct!'))
        else:
            st.error(feedback.get('explanation', 'Incorrect. Try again.'))
        return is_correct

def show_difficulty_buttons(disabled=False):
    st.markdown("##### How well did you know this?")
    col1, col2, col3 = st.columns(3)
    return {
        'easy': col1.button("😊 Easy", disabled=disabled, use_container_width=True, key="easy_btn"),
        'medium': col2.button("😐 Medium", disabled=disabled, use_container_width=True, key="medium_btn"),
        'hard': col3.button("😓 Hard", disabled=disabled, use_container_width=True, key="hard_btn")
    }

def show_next_button(text="Next Card", disabled=False):
    return st.button(text, disabled=disabled, use_container_width=True)

def show_error(error_message, show_state=False):
    """Display error message and optionally show session state for debugging"""
    st.error(f"🐛 Error: {error_message}")
    
    if show_state:
        with st.expander("Debug Information"):
            st.write("Session State:")
            # Filter out sensitive information
            debug_state = {k: v for k, v in st.session_state.items() 
                         if k not in ['config', 'authentication_status', 'password']}
            st.json(debug_state)

def clear_session_state():
    """Clear all flashcard-related session state and UI elements"""
    try:
        # First, clear all session state
        keys_to_preserve = {'config', 'initialized', 'username', 'name', 'authentication_status'}
        preserved_values = {k: st.session_state[k] for k in keys_to_preserve if k in st.session_state}
        
        # Clear everything else
        for key in list(st.session_state.keys()):
            if key not in keys_to_preserve:
                del st.session_state[key]
        
        # Restore preserved values
        st.session_state.update(preserved_values)
        
        # Set clean initial state
        st.session_state.update({
            'show_form_only': True,
            'current_cards': None,
            'current_index': 0,
            'show_answer': False,
            'user_answer': "",
            'feedback': None,
            'difficulty': None,
            'session_results': [],
            'form_disabled': False,
            'session_complete': False,
            'clearing_session': True,
            'error': None  # Add error tracking
        })
        
        # Force rerun to clear the UI
        st.rerun()
    except Exception as e:
        show_error(f"Error clearing session state: {str(e)}", show_state=True)

def initialize_session():
    """Initialize or reset session state"""
    try:
        if not st.session_state.get('initialized', False):
            st.session_state.update({
                'initialized': True,
                'show_form_only': True,
                'session_complete': False,
                'clearing_session': False,
                'error': None
            })
    except Exception as e:
        show_error(f"Error initializing session: {str(e)}", show_state=True)

def show_study_session_summary(results):
    try:
        if not results or st.session_state.get('clearing_session'):
            return
            
        st.markdown("## 🎉 Session Complete!")
        
        # Stats in a nice card
        total_cards = len(results)
        correct_answers = sum(1 for r in results if r['correct'])
        accuracy = (correct_answers / total_cards) * 100
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Cards Reviewed", total_cards)
        with col2:
            st.metric("Correct Answers", correct_answers)
        with col3:
            st.metric("Accuracy", f"{accuracy:.1f}%")
        
        # Difficulty breakdown with emojis
        st.markdown("### 📊 Performance Breakdown")
        difficulties = {'easy': 0, 'medium': 0, 'hard': 0}
        for r in results:
            difficulties[r['difficulty']] += 1
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("😊 Easy", difficulties['easy'])
        with col2:
            st.metric("😐 Medium", difficulties['medium'])
        with col3:
            st.metric("😓 Hard", difficulties['hard'])
        
        # Detailed results in expandable sections
        st.markdown("### 📝 Detailed Review")
        for i, result in enumerate(results, 1):
            with st.expander(f"Card {i}: {result['question']}", expanded=False):
                cols = st.columns([3, 1])
                with cols[0]:
                    st.markdown(f"**Your Answer:**\n{result['user_answer']}")
                    st.markdown(f"**Correct Answer:**\n{result['correct_answer']}")
                with cols[1]:
                    st.markdown(f"**Result:** {'✅' if result['correct'] else '❌'}")
                    st.markdown(f"**Difficulty:** {result['difficulty'].title()} {'😊' if result['difficulty']=='easy' else '😐' if result['difficulty']=='medium' else '😓'}")
        
        # Always show the restart button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Start New Session", use_container_width=True):
                st.write("DEBUG: Start New Session clicked")
                st.session_state.update({
                    'show_form_only': True,
                    'clearing_session': True,
                    'current_cards': None,
                    'current_index': 0,
                    'session_complete': False,  # Changed to False
                    'session_results': []  # Clear results
                })
                st.rerun()
    except Exception as e:
        show_error(f"Error showing session summary: {str(e)}", show_state=True) 