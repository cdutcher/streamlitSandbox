import streamlit as st

def show_progress(current_index, total_cards):
    st.progress(current_index / total_cards)
    st.write(f"Card {current_index + 1} of {total_cards}")

def show_question(question):
    st.markdown(f"**Q: {question}**")

def show_answer_input():
    return st.text_area("Your answer:", key="answer_input")

def show_feedback(correct_answer, user_answer, feedback):
    st.markdown(f"**Correct Answer:** {correct_answer}")
    st.markdown("**Your Answer:**")
    st.write(user_answer)
    
    if isinstance(feedback, list):
        feedback = feedback[0]
    
    is_correct = feedback.get('correct', False)
    if is_correct:
        st.success(feedback.get('explanation', 'Correct!'))
    else:
        st.error(feedback.get('explanation', 'Incorrect. Try again.'))
    return is_correct

def show_difficulty_buttons(disabled=False):
    st.write("How difficult was this to recall?")
    col1, col2, col3 = st.columns(3)
    return {
        'easy': col1.button("Easy 😊", disabled=disabled),
        'medium': col2.button("Medium 😐", disabled=disabled),
        'hard': col3.button("Hard 😓", disabled=disabled)
    }

def show_next_button(text="Next Card", disabled=False):
    return st.button(text, disabled=disabled)

def clear_session_state():
    """Clear all flashcard-related session state"""
    keys_to_clear = [
        'current_cards',
        'current_index',
        'show_answer',
        'user_answer',
        'feedback',
        'difficulty',
        'session_results',
        'form_disabled'
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

def show_study_session_summary(results):
    st.markdown("## Study Session Summary")
    
    # Calculate statistics
    total_cards = len(results)
    correct_answers = sum(1 for r in results if r['correct'])
    accuracy = (correct_answers / total_cards) * 100 if total_cards > 0 else 0
    
    # Display overall stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Cards", total_cards)
    with col2:
        st.metric("Correct Answers", correct_answers)
    with col3:
        st.metric("Accuracy", f"{accuracy:.1f}%")
    
    # Display difficulty breakdown
    difficulties = {'easy': 0, 'medium': 0, 'hard': 0}
    for r in results:
        difficulties[r['difficulty']] += 1
    
    st.markdown("### Difficulty Breakdown")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Easy 😊", difficulties['easy'])
    with col2:
        st.metric("Medium 😐", difficulties['medium'])
    with col3:
        st.metric("Hard 😓", difficulties['hard'])
    
    # Show detailed results
    st.markdown("### Detailed Results")
    for i, result in enumerate(results, 1):
        with st.expander(f"Card {i}: {result['question']}"):
            st.markdown(f"**Your Answer:** {result['user_answer']}")
            st.markdown(f"**Correct Answer:** {result['correct_answer']}")
            st.markdown(f"**Result:** {'✅ Correct' if result['correct'] else '❌ Incorrect'}")
            st.markdown(f"**Difficulty:** {result['difficulty'].title()}")
    
    # Disable the form while showing summary
    st.session_state['form_disabled'] = True
    
    # Add restart button
    if st.button("Start New Session"):
        clear_session_state()
        st.rerun() 