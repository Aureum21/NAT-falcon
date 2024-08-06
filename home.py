import streamlit as st
import os
import sqlite3
import subprocess
import sys

url = 'https://nat-falcon-main.streamlit.app/'

st.set_page_config(layout="wide")

script_dir = os.path.dirname(__file__)

logo_path = "logo.png" 

def get_db_connection():
    try:
        conn = sqlite3.connect('ai_conversation.db')
        conn.row_factory = sqlite3.Row 
        return conn
    except sqlite3.Error as err:
        print(f"Error: {err}")
        return None

def insert_user(name, username, email, password, language, level, purpose, minperday):
    conn = get_db_connection()
    if conn is None:
        return
    cursor = conn.cursor()
    try:
        cursor.execute('''INSERT INTO users 
                          (fullname, username, email, password, profile_language, profile_level, profile_purpose, profile_minutes_per_day) 
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                       (name, username, email, password, language, level, purpose, minperday))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def check_user(username_or_email, password):
    conn = get_db_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM users WHERE (username = ? OR email = ?) AND password = ?', 
                       (username_or_email, username_or_email, password))
        user = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    return user

def get_user_data(username_or_email):
    conn = get_db_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', 
                       (username_or_email, username_or_email))
        user_data = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    return user_data

def get_user_profile(username):
    conn = get_db_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user_profile = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    return user_profile
    
def run_main():
    if sys.platform == 'win32':
        subprocess.run(['start', url], shell=True)
    elif sys.platform == 'darwin':
        subprocess.run(['open', url])
    else:
        subprocess.run(['xdg-open', url])


# Page configuration
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'signup_step' not in st.session_state:
    st.session_state.signup_step = 0
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'username' not in st.session_state:
    st.session_state.username = None

def home_page():
      
    col1, col2 = st.columns([2.5,3])
    with col1:
         st.image(logo_path, width=110)
    with col2:
        st.title("VoicePal")
    colu1, colu2, colu3 = st.columns([2.5,6,2])
    with colu2:
        st.header("Speak Like a Native, Learn Like a Friend")
        st.subheader("Building Connections Through Authentic Conversations")
        cole1, cole2, col3 = st.columns([2,2,2])
        with cole2:
            if st.button("Get Started", use_container_width=True):
                st.session_state.page = 'signup'
            if st.button("Already have an account? Login", use_container_width=True):
                st.session_state.page = 'login'

    st.markdown("### About Us")
    st.write(
        "VoicePal is an innovative language learning app that harnesses the power of interactive conversations. "
        "Our mission is to make learning languages fun, engaging, and accessible to everyone.")

    st.markdown(
        "Through our voice chat feature, learners can practice speaking with a friendly AI assistant at their own pace and skill level. "
        "Whether you're a beginner, intermediate, or advanced student, VoicePal adapts to your needs.")

    st.markdown("#### Here's how it works:")
    st.write(
        "1. **Repeat After AI:** Start by listening to the AI pronounce words and phrases in your target language. Repeat after the AI to improve your pronunciation and get comfortable with the sounds.")
    st.write(
        "2. **Practice with Corrections:** As you progress, the AI will provide real-time feedback and corrections to help you speak more accurately. Engage in interactive exercises and receive praise for your efforts.")
    st.write(
        "3. **Converse with AI:** Once you've mastered the basics, it's time to put your skills to the test. Engage in full conversations with the AI, discussing a variety of topics. The AI will adapt to your level, providing support when needed.")

    st.write(
        "Our goal is to make language learning feel like a natural conversation, not a chore. With VoicePal, you'll build confidence, expand your vocabulary, and gain practical communication skills.")

    st.markdown("### Contact Us")
    st.write(
        "We're here to help! If you have any questions, feedback, or suggestions, please don't hesitate to reach out.")
    st.write("- Email: support@voicepal.com")
    st.write("- Phone: 1-800-VOICEPAL")
    st.write("- Social Media: @VoicePalApp")

    st.write(
        "Our team of language experts and AI engineers is dedicated to continuously improving VoicePal to better serve our users. We welcome all inquiries and look forward to hearing from you.")
    st.write("Start your language learning journey today!")

def signup_page():
    st.title('Signup')
    name = st.text_input('Name', placeholder='Enter your name')
    global username
    username = st.text_input('Username', placeholder='Enter your username')
    email = st.text_input('Email', placeholder='Enter your email')
    password = st.text_input('Password', placeholder='Enter your password', type='password')
    confirm_password = st.text_input('Confirm Password', placeholder='Confirm your password', type='password')
    if st.button('Signup'):
        if name and username and email and password and confirm_password:
            if password == confirm_password:
                st.session_state.name = name
                st.session_state.username = username
                st.session_state.email = email
                st.session_state.password = password
                st.session_state.page = 'profile_setup'
            else:
                st.error('Passwords do not match')
        else:
            st.error('All fields are required')
            
def login_page():
    st.title('Login')
    username_or_email = st.text_input('Username/Email', placeholder='Enter your username or email')
    password = st.text_input('Password', placeholder='Enter your password', type='password')
    if st.button('Login'):
        user = check_user(username_or_email, password)
        if user:
            st.session_state.username = user[3]
            run_main()
        else:
            st.error('Invalid username or password')

def profile_setup_page():
    step = st.session_state.signup_step

    if step == 0:
        @st.dialog("Language selection", width="large")
        def profile_step_1():
            
            language = st.text_input("What language?")
            if st.button("Next"):
                st.session_state.profile_language = language
                st.session_state.signup_step += 1
                st.rerun()

        profile_step_1()

    elif step == 1:
        @st.dialog("Language proficiency", width="large")
        def profile_step_2():
            
            level = st.selectbox("What level?", ["Beginner", "Intermediate", "Advanced"])
            if st.button("Next"):
                st.session_state.profile_level = level
                st.session_state.signup_step += 1
                st.rerun()

        profile_step_2()

    elif step == 2:
        @st.dialog("Learning Purpose", width="large")
        def profile_step_3():

            purpose = st.text_input("What is your purpose?")
            if st.button("Next"):
                st.session_state.profile_purpose = purpose
                st.session_state.signup_step += 1
                st.rerun()

        profile_step_3()

    elif step == 3:
        @st.dialog("Minutes per day", width="large")
        def profile_step_4():
            
            minutes_per_day = st.number_input("How many minutes a day would be preferable?", min_value=0)
            if st.button("Submit"):
                st.session_state.profile_minutes_per_day = minutes_per_day
                st.session_state.signup_step = 0
                st.toast("Profile saved successfully!")
                insert_user(st.session_state.name, st.session_state.username, st.session_state.email, st.session_state.password, 
                            st.session_state.profile_language, st.session_state.profile_level, st.session_state.profile_purpose, st.session_state.profile_minutes_per_day)
                run_main()
                st.rerun()
        profile_step_4()

def main():
    page_mapping = {
        'home': home_page,
        'signup': signup_page,
        'login': login_page,
        'profile_setup': profile_setup_page,
    }
    page_mapping.get(st.session_state.page, home_page)()

main()
