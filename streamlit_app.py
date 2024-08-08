import streamlit as st
from pymongo import MongoClient
from streamlit.runtime.secrets import secrets

# Connect to MongoDB
uri = secrets["mongo"]["uri"]
client = MongoClient(uri)
questions = secrets["questions"]
db = client[questions]
collection = db['questions']

# Fetch questions from the database
questions = list(collection.find())

# Initialize session state
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
    st.session_state.answers = [None] * len(questions)

# Function to display a question
def display_question(index):
    question = questions[index]
    st.write(question['question'])
    options = question['options']
    for key, value in options.items():
        if st.button(value, key=key):
            st.session_state.answers[index] = key

# Display the current question
current_index = st.session_state.current_question
display_question(current_index)

# Navigation buttons
if st.button("Previous") and current_index > 0:
    st.session_state.current_question -= 1
if st.button("Next") and current_index < len(questions) - 1:
    st.session_state.current_question += 1

# Submit button
if st.button("Submit"):
    correct_answer = questions[current_index]['correct_answer']
    user_answer = st.session_state.answers[current_index]
    if user_answer == correct_answer:
        st.success("Correct!")
    else:
        st.error("Incorrect!")

# Sidebar for question status
st.sidebar.title("Question Status")
for i, answer in enumerate(st.session_state.answers):
    status = "Not Attempted" if answer is None else ("Correct" if answer == questions[i]['correct_answer'] else "Incorrect")
    st.sidebar.write(f"Question {i+1}: {status}")