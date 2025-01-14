import streamlit as st
import numpy as np
import pandas as pd

# Set page title
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

# Display a chart - Modified to use pandas DataFrame
chart_data = pd.DataFrame(
    np.random.randn(20, 3),
    columns=['Column 1', 'Column 2', 'Column 3']
)
st.line_chart(chart_data) 