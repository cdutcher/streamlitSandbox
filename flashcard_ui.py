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

def show_difficulty_buttons():
    st.write("How difficult was this to recall?")
    col1, col2, col3 = st.columns(3)
    return {
        'easy': col1.button("Easy 😊"),
        'medium': col2.button("Medium 😐"),
        'hard': col3.button("Hard 😓")
    }

def show_next_button():
    return st.button("Next Card") 