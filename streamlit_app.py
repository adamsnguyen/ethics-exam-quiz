import streamlit as st
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId

# Connect to MongoDB
uri = st.secrets["uri"]
client = MongoClient(uri, server_api=ServerApi('1'), tls=True)
db = client[st.secrets["questions"]]

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
            del pin_input
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

    def display_question(index):
        question = questions[index]
        st.write(question['question'])
        options = question['options']

        # Custom CSS for button styling
        st.markdown("""
            <style>
            .option-button {
                display: flex;
                align-items: center;
                justify-content: flex-start;
                width: 100%;
                height: 50px;
                margin-bottom: 10px;
            }
            .option-label {
                width: 30px;
                height: 100%;
                display: inline-block;
                text-align: center;
                color: white;
                font-weight: bold;
            }
            .A { background-color: blue; }
            .B { background-color: green; }
            .C { background-color: red; }
            .D { background-color: orange; }
            </style>
        """, unsafe_allow_html=True)

        # Create a 2x2 grid for the options with equal size buttons
        cols = st.columns(2)
        colors = ['A', 'B', 'C', 'D']
        for idx, (key, value) in enumerate(options.items()):
            with cols[idx % 2]:
                label = colors[idx]
                button_html = f"""
                <div class="option-button">
                    <div class="option-label {label}">{label}</div>
                    <div style="flex: 1;">
                        <button style="width: 100%; height: 100%;" onclick="document.getElementById('{key}').click()">{value}</button>
                    </div>
                </div>
                """
                st.markdown(button_html, unsafe_allow_html=True)
                if st.button("", key=f"option_{index}_{key}", help=value):
                    select_option(index, key)

    current_index = st.session_state.current_question
    display_question(current_index)

    # Submit button that spans across both columns
    submit_col = st.columns([1, 1])
    with submit_col[0]:
        if st.button("Submit", key="submit", use_container_width=True):
            correct_answer = questions[current_index]['correct_answer']
            user_answer = st.session_state.answers[current_index]
            if user_answer == correct_answer:
                st.success("Correct!")
            else:
                st.error("Incorrect!")

    # Navigation buttons with equal width
    nav_cols = st.columns(2)
    with nav_cols[0]:
        if st.button("Previous", key="prev", use_container_width=True) and current_index > 0:
            st.session_state.current_question -= 1
    with nav_cols[1]:
        if st.button("Next", key="next", use_container_width=True) and current_index < len(questions) - 1:
            st.session_state.current_question += 1

    # Sidebar for question status
    st.sidebar.title("Question Status")
    for i, answer in enumerate(st.session_state.answers):
        status = "Not Attempted" if answer is None else ("Correct" if answer == questions[i]['correct_answer'] else "Incorrect")
        link_key = f"link_{i}"
        if st.sidebar.button(f"Question {i+1}: {status}", key=link_key):
            st.session_state.current_question = i