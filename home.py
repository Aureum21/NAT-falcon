import streamlit as st
import os
import sqlite3


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
            st.markdown(html_code, unsafe_allow_html=True)

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

html_code = """
    <style>
        .button {
            background-color: lightblue; 
            border: none;
            color: black !important;
            padding: 20px 80px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 22px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 12px;
        }
        .button:hover {
            background-color: lightgray;
        }
    </style>
    <a href="https://nat-falcon-main.streamlit.app" target="_blank" class="button">Try It</a>
"""

def main():
    page_mapping = {
        'home': home_page,
    }
    page_mapping.get(st.session_state.page, home_page)()

main()
