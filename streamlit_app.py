import streamlit as st
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Connect to MongoDB
uri = st.secrets["uri"]
client = MongoClient(uri, server_api=ServerApi('1'), tls=True)
db = client[st.secrets["questions"]]
rerun = False

try:
    client.server_info()
except Exception as e:
    st.error(f"Error connecting to MongoDB: {e}")

def get_current_pin():
    try:
        pin_doc = db['pincode'].find_one({}, {'pin': 1})
        if pin_doc:
            return pin_doc['pin']
        else:
            st.error("No document found in the collection.")
            return None
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

if 'authorized' not in st.session_state:
    st.session_state.authorized = False
    st.session_state.cached_pin = get_current_pin()

def verify_pin(user_input):
    return user_input == st.session_state.cached_pin

if not st.session_state.authorized:
    pin_input = st.text_input('Enter the PIN:', type='password')
    if pin_input:
        if verify_pin(pin_input):
            st.session_state.authorized = True
            st.success("Access Granted")
            st.rerun()
        else:
            st.error("Invalid PIN")

if st.session_state.authorized:
    current_pin = get_current_pin()
    if current_pin and current_pin != st.session_state.cached_pin:
        st.session_state.authorized = False
        st.warning("PIN has changed. Session closed.")
        st.stop()

if st.session_state.authorized:
    questions = list(db['questions'].find())
    
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
        st.session_state.answers = [None] * len(questions)

    def select_option(index, key):
        st.session_state.answers[index] = key
        st.session_state[f"answer{index}"] = (key == questions[index]['correct_answer'])
        st.rerun()


    def display_question(index):
        global rerun
        question = questions[index]
        st.write(question['question'])

        options = question['options']
        
        # Display feedback message after the question
        if f"answer{index}" in st.session_state:
            if st.session_state[f"answer{index}"]:
                st.success(f"Correct: {questions[index]['correct_answer']}: {options[questions[index]['correct_answer']]}")
            else:
                st.error("Incorrect!")
                
        st.divider()
        options = question['options']

        for key, value in options.items():
            col1, col2 = st.columns([1,8], vertical_alignment = "center")
            with col1:
                st.write(f"{key}")
            with col2:
                if st.button(f"{value}", key=f"option_{index}_{key}", use_container_width=True):
                    select_option(index, key)


    current_index = st.session_state.current_question
    
    st.header(f"Question {current_index+1}")

    st.divider()
    
    display_question(current_index)

    st.divider()

    col3, col4 = st.columns(2)
    with col3:
        if st.button("Previous", use_container_width=True) and current_index > 0:
            st.session_state.current_question -= 1
            st.rerun()

    with col4:
        if st.button("Next", use_container_width=True) and current_index < len(questions) - 1:
            st.session_state.current_question += 1
            st.rerun()

    # Sidebar for question status
    st.sidebar.title("Questions")
    for i, answer in enumerate(st.session_state.answers):
        status = "Not Attempted" if answer is None else ("Correct" if answer == questions[i]['correct_answer'] else "Incorrect")
        if st.sidebar.button(f"Question {i+1}: {status}", key=f"link_{i}"):
            st.session_state.current_question = i
            st.rerun()