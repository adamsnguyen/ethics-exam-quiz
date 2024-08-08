import streamlit as st
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId

# Update session state
st.session_state.update(st.session_state)

# Connect to MongoDB
uri = st.secrets["uri"]
client = MongoClient(uri, server_api=ServerApi('1'), tls=True)
db = client[st.secrets["questions"]]

try:
    # Attempt to get the server information to verify the connection
    client.server_info()
except Exception as e:
    st.error(f"Error connecting to MongoDB: {e}")

# Function to get the current PIN from the database
def get_current_pin():
    try:
        # Retrieve the pin from the pincode collection
        pin_doc = db['pincode'].find_one({}, {'pin': 1})
        if pin_doc:
            return pin_doc['pin']
        else:
            st.error("No document found in the collection.")
            return None
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

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
    if current_pin and current_pin != st.session_state.cached_pin:
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

    # Function to handle option selection
    def select_option(index, key):
        st.session_state.answers[index] = key

    # Function to display a question
    def display_question(index):
        question = questions[index]
        st.write(question['question'])
        options = question['options']
        for key, value in options.items():
            # Ensure unique key for each option button
            button_key = f"option_{index}_{key}"
            if st.button(value, key=button_key, on_click=select_option, args=(index, key)):
                pass

    # Display the current question
    current_index = st.session_state.current_question
    display_question(current_index)

    # Navigation buttons
    if st.button("Previous", key="prev") and current_index > 0:
        st.session_state.current_question -= 1
    if st.button("Next", key="next") and current_index < len(questions) - 1:
        st.session_state.current_question += 1

    # Submit button
    if st.button("Submit", key="submit"):
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
        # Create a button for each question link with a unique key
        link_key = f"link_{i}"
        if st.sidebar.button(f"Question {i+1}: {status}", key=link_key):
            st.session_state.current_question = i