import streamlit as st
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId

st.session_state.update(st.session_state)

# Connect to MongoDB
uri = st.secrets["uri"]
client = MongoClient(uri, server_api=ServerApi('1'), tls=True)  # 5000
db = client.db[st.secrets["questions"]]

try:
    # Attempt to get the server information to verify the connection
    client.server_info()
    st.success("Connected to MongoDB successfully!")
    pin_doc = db['pincode'].find_one({'_id': ObjectId('66b417525f97a65f18cf2b08')}, {'pin': 1})
    st.write(pin_doc)
except Exception as e:
    st.error(f"Error connecting to MongoDB: {e}")

# Function to get the current PIN from the database
def get_current_pin():
    # Retrieve the pin from the pincode collection using the ObjectId
    pin_doc = db['pincode'].find_one({'_id': ObjectId('66b417525f97a65f18cf2b08')}, {'pin': 1})

    # Extract the pin if the document is found
    pin = pin_doc['pin'] if pin_doc else None

    # Output the pin
    st.write(pin_doc)

# Initialize session state for authorization and PIN
if 'authorized' not in st.session_state:
    st.session_state.authorized = False
    st.session_state.cached_pin = get_current_pin()

# Function to verify pin
def verify_pin(user_input):
    return user_input == st.session_state.cached_pin

# PIN input and verification
pin_input = st.text_input('Enter the PIN:', type='password')
if pin_input and not st.session_state.authorized:
    if verify_pin(pin_input):
        st.session_state.authorized = True
        st.success("Access Granted")
    else:
        st.error("Invalid PIN")

# Check PIN on every user event
if st.session_state.authorized:
    current_pin = get_current_pin()
    if current_pin != st.session_state.cached_pin:
        st.session_state.authorized = False
        st.warning("PIN has changed. Session closed.")
        st.stop()

# Main application logic
if st.session_state.authorized:
    # Fetch questions from the database
    questions = list(db['questions'].find())

    # Initialize session state for questions
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