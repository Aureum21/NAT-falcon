import streamlit as st
from ai71 import AI71
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import traceback
import json
from io import BytesIO
import time 
import imageio_ffmpeg as ffmpeg
import sqlite3
from streamlit_webrtc import webrtc_streamer, WebRtcMode

st.set_page_config(layout="wide")

AudioSegment.ffmpeg = ffmpeg.get_ffmpeg_exe()

def get_db_connection():
    try:
        conn = sqlite3.connect('ai_conversation.db')
        conn.row_factory = sqlite3.Row  # Ensure rows are returned as dictionaries
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


def save_to_database(user_message, assistant_response):
    conn = get_db_connection()
    if conn is None:
        return
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO conversations (user_message, assistance_response) VALUES (?, ?)",
            (user_message, assistant_response)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# Page configuration
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'signup_step' not in st.session_state:
    st.session_state.signup_step = 0
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'username' not in st.session_state:
    st.session_state.username = None
    
lesson_plans = {
    "Beginner": {
        "General": {
            "language": ["English", "Spanish", "French", "Arabic", "German", "Italian", "Chinese", "Japanese", "Korean", "Portuguese", "Russian", "Hindi"],  
            "lesson": "Lesson plan for Beginner learners focusing on general language skills."
        },
        "Travel": {
            "language": ["English", "Spanish", "French", "Arabic", "German", "Italian", "Chinese", "Japanese", "Korean", "Portuguese", "Russian", "Hindi"],
            "lesson": "Lesson plan for Beginner learners focusing on travel-related language skills."
        },
        "Business": {
            "language": ["English", "Spanish", "French", "Arabic", "German", "Italian", "Chinese", "Japanese", "Korean", "Portuguese", "Russian", "Hindi"],
            "lesson": "Lesson plan for Beginner learners focusing on business-related language skills."
        },
        "Academic": {
            "language": ["English", "Spanish", "French", "Arabic", "German", "Italian", "Chinese", "Japanese", "Korean", "Portuguese", "Russian", "Hindi"],
            "lesson": "Lesson plan for Beginner learners focusing on academic-related language skills."
        }
    },
    "Intermediate": {
         "General": {
            "language": ["English", "Spanish", "French", "Arabic", "German", "Italian", "Chinese", "Japanese", "Korean", "Portuguese", "Russian", "Hindi"],  
            "lesson": "Lesson plan for Intermediate learners focusing on general language skills."
        },
        "Travel": {
            "language": ["English", "Spanish", "French", "Arabic", "German", "Italian", "Chinese", "Japanese", "Korean", "Portuguese", "Russian", "Hindi"],
            "lesson": "Lesson plan for Intermediate learners focusing on travel-related language skills."
        },
        "Business": {
            "language": ["English", "Spanish", "French", "Arabic", "German", "Italian", "Chinese", "Japanese", "Korean", "Portuguese", "Russian", "Hindi"],
            "lesson": "Lesson plan for intermediate learners focusing on business-related language skills."
        },
        "Academic": {
            "language": ["English", "Spanish", "French", "Arabic", "German", "Italian", "Chinese", "Japanese", "Korean", "Portuguese", "Russian", "Hindi"],
            "lesson": "Lesson plan for Intermediate learners focusing on academic-related language skills."
        }
    },
    "Advanced": {
         "General": {
            "language": ["English", "Spanish", "French", "Arabic", "German", "Italian", "Chinese", "Japanese", "Korean", "Portuguese", "Russian", "Hindi"],  
            "lesson": "Lesson plan for Advanced learners focusing on general language skills."
        },
        "Travel": {
            "language": ["English", "Spanish", "French", "Arabic", "German", "Italian", "Chinese", "Japanese", "Korean", "Portuguese", "Russian", "Hindi"],
            "lesson": "Lesson plan for Advanced learners focusing on travel-related language skills."
        },
        "Business": {
            "language": ["English", "Spanish", "French", "Arabic", "German", "Italian", "Chinese", "Japanese", "Korean", "Portuguese", "Russian", "Hindi"],
            "lesson": "Lesson plan for Advanced learners focusing on business-related language skills."
        },
        "Academic": {
            "language": ["English", "Spanish", "French", "Arabic", "German", "Italian", "Chinese", "Japanese", "Korean", "Portuguese", "Russian", "Hindi"],
            "lesson": "Lesson plan for Advanced learners focusing on academic-related language skills."
        }
    }
}

if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()
if 'total_time' not in st.session_state:
    st.session_state.total_time = 0.0

@st.dialog("API Key Entry", width="large")
def api_key_dialog():
    api_key = st.text_input("Provide your AI71 API key to proceed", type="password")

    if st.button("Submit"):
        if api_key:
            st.session_state.api_key = api_key
            st.success("API Key has been set successfully!")
            st.rerun()

        else:
            st.error("Please enter an API Key.")

if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
    
AI71_API_KEY = st.session_state.api_key
client = AI71(AI71_API_KEY)

def capture_voice():
    
    webrtc_ctx = webrtc_streamer(
        key="audio",
        mode=WebRtcMode.SENDONLY,
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
    )

    if webrtc_ctx.audio_receiver:
        audio_frames = webrtc_ctx.audio_receiver.get_frames()
        audio_data = b"".join(audio_frames)

        r = sr.Recognizer()
        with sr.AudioFile(BytesIO(audio_data)) as source:
            audio = r.record(source)
            try:
                text = r.recognize_google(audio)
                st.success(f"You said: {text}")
                return text
            except sr.UnknownValueError:
                st.error("Sorry, I did not understand that.")
                return None
            except sr.RequestError:
                st.error("Sorry, there was an error with the speech recognition service.")
                return None

    else:
        st.error("No audio input detected.")
        return None


def get_response(messages):
    if not st.session_state.api_key:
        st.error("API key is not set. Please provide a valid API key.")
        return None

    try:
        response = client.chat.completions.create(
            model="tiiuae/falcon-180B-chat",
            messages=messages,
            max_tokens=200,
            temperature=0.7
        )
        if response and response.choices:
            response_text = response.choices[0].message.content
            return response_text
        else:
            st.error("Unexpected response format.")
            return None
    except Exception as e:
        st.error("An error occurred while getting the response.")
        traceback.print_exc()
        return None

language_map = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Chinese": "zh",
    "Japanese": "ja",
    "Korean": "ko",
    "Portuguese": "pt",
    "Russian": "ru",
    "Arabic": "ar",
    "Hindi": "hi"
}

def speak_text(text, lang='en'):
    if lang in language_map:
        tts = gTTS(text=text, lang=language_map[lang])
        tts.save("response.mp3")
        sound = AudioSegment.from_mp3("response.mp3")
        play(sound)
    else:
        st.error(f"Language not supported: {lang}")

def chat_with_falcon(user_input):
    if not st.session_state.api_key:
        st.error("API key is not set. Please provide a valid API key.")
        return "API key is missing."
    profile_language = st.session_state.get('profile_language', 'English')
    profile_level = st.session_state.get('profile_level', 'Beginner')
    profile_purpose = st.session_state.get('profile_purpose', 'General')

    lesson = ""
    if profile_level in lesson_plans:
        if profile_purpose in lesson_plans[profile_level]:
            lesson = lesson_plans[profile_level][profile_purpose]

    system_prompt = (
        f"You are an assistant helping a user learn {profile_language} at {profile_level} level. "
        f"The user's purpose is {profile_purpose}. "
        f"Here is the current lesson plan: {lesson}"
    )

    response = client.chat.completions.create(
        model="tiiuae/falcon-180B-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        max_tokens=200,  
        temperature=0.7  
    )

    if response and response.choices:
        return response.choices[0].message.content.strip()
    else:
        return "Sorry, I didn't understand that."


def main():

    if 'api_key' not in st.session_state:
        st.session_state.api_key = None
        api_key_dialog()
    
    sidebar = st.sidebar
    sidebar.title("Menu")
    profile_button = sidebar.button("Profile", use_container_width=True)
    progress_button = sidebar.button("Progress", use_container_width=True)
    pricing_button = sidebar.button("Pricing", use_container_width=True)
    about_us_button = sidebar.button("About Us", use_container_width=True)
    contact_us_button = sidebar.button("Contact Us", use_container_width=True)
    api_button = sidebar.button("API-key", use_container_width=True)
    sidebar.caption("All rights reserved \u00A9 2024 Voicepal")

    if 'profile_step' not in st.session_state:
        st.session_state.profile_step = 0

    # Define dialogs for each profile step
    @st.dialog("Language Selection", width="large")
    def profile_step_1():
        language = st.selectbox("What language?", ["English", "Spanish", "French", "Arabic", "German", "Italian", "Chinese", "Japanese", "Korean", "Portuguese", "Russian", "Hindi"])
        if st.button("Next"):
            st.session_state.profile_language = language
            st.session_state.profile_step = 1
            st.rerun()

    @st.dialog("Proficiency Level selection", width="large")
    def profile_step_2():
        level = st.selectbox("What level?", ["Beginner", "Intermediate", "Advanced"])
        if st.button("Next"):
            st.session_state.profile_level = level
            st.session_state.profile_step = 2
            st.rerun()

    @st.dialog("Purpose", width="large")
    def profile_step_3():
        purpose = st.selectbox("Why are you taking this course?", ["General", "Academic", "Business", "Travel"])
        if st.button("Next"):
            st.session_state.profile_purpose = purpose
            st.session_state.profile_step = 3
            st.rerun()

    @st.dialog("Minutes per day", width="large")
    def profile_step_4():
        minutes_per_day = st.number_input("How many minutes a day would be preferable?", min_value=0)
        if st.button("Submit"):
            st.session_state.profile_minutes_per_day = minutes_per_day
            st.session_state.profile_step = 4
            st.write("Profile saved successfully!")
            time.sleep(2)
            st.rerun()

    @st.dialog("User Profile", width="large")
    def profile_dialog():

        st.write(f"**Language Preference:** {st.session_state.profile_language}")
        st.write(f"**Proficiency Level:** {st.session_state.profile_level}")
        st.write(f"**Purpose of Learning:** {st.session_state.profile_purpose}")
        st.write(f"**Minutes Per Day:** {st.session_state.profile_minutes_per_day} minutes")

    if profile_button or st.session_state.profile_step >= 0:
        if st.session_state.profile_step == 0:
            profile_step_1()
        elif st.session_state.profile_step == 1:
            profile_step_2()
        elif st.session_state.profile_step == 2:
            profile_step_3()
        elif st.session_state.profile_step == 3:
            profile_step_4()
    if profile_button and st.session_state.profile_step == 4:
        profile_dialog()
    if api_button:
        api_key_dialog()

    @st.dialog("Progress")
    def progress_dialog():
        progress_bar = st.progress(0.0)
        current_time = time.time()
        required_minutes_per_day = st.session_state.profile_minutes_per_day
        elapsed_time = current_time - st.session_state.start_time
        st.session_state.total_time += elapsed_time
        st.session_state.start_time = current_time

        total_time_minutes = st.session_state.total_time / 60
        
        progress_percentage = min(total_time_minutes / required_minutes_per_day, 1.0)
        progress_bar.progress(progress_percentage)
        
        st.write(f'Elapsed time: {int(total_time_minutes)} minutes')
        st.write(f'Total required time per day: {required_minutes_per_day} minutes')

        if total_time_minutes >= required_minutes_per_day:
            st.success('You have met the required time for today!')
        else:
            st.info(f'You need to stay {required_minutes_per_day - int(total_time_minutes)} more minutes to meet the daily requirement.')
              

    if progress_button:     
        progress_dialog()

    @st.dialog("Pricing", width="large")
    def pricing_dialog():
        st.title("Pricing Plans")
        
        colu1, colu2, colu3 = st.columns(3)

        with colu1:
            st.header("Free Plan")
            st.write("Features:")
            st.write("- Access to basic lessons")
            st.write("- Limited chat interactions")
            st.write("- Basic quizzes")
            st.write("- Community support")
            if st.button("Select Free Plan"):
                st.session_state.current_plan = "Free Plan"
                st.toast(f"Your current plan is: Free Plan")

        with colu2:
            st.header("Monthly Premium \n 19.99 AED/month")
            st.write("Features:")
            st.write("- All Free Plan features")
            st.write("- Access to advanced lessons")
            st.write("- Unlimited chat interactions")
            st.write("- Detailed progress tracking")
            st.write("- Priority customer support")
            if st.button("Select Monthly Premium"):
                st.session_state.current_plan = "Monthly Premium"
                st.toast(f"Your current plan is: Monthly Premium")

        with colu3:
            st.header("Annual Premium \n 12.99 AED/month")
            st.write("Features:")
            st.write("- All Monthly Premium features")
            st.write("- Yearly discount")
            st.write("- Exclusive content and webinars")
            st.write("- Personalized learning plans")
            st.write("- Access to beta features")
            if st.button("Select Annual Premium"):
                st.session_state.current_plan = "Annual Premium"
                st.toast(f"Your current plan is: Annual Premium")

        if st.button("Close"):

            st.session_state.current_plan = None
            st.write("Dialog closed")

    if pricing_button:
        pricing_dialog()

    @st.dialog("About Us")
    def about_us_dialog():
        
        st.write("VoicePal is dedicated to provide the best language learning experience. Our innovative platform offers personalized and interactive learning opportunities. "
            "Our mission is to make language learning engaging and effective through conversational practice with our AI assistant.")
        
        st.write("With VoicePal, you can practice speaking with a friendly AI assistant, receive real-time feedback, and engage in full conversations that adapt to your level. Our approach is designed to make learning feel natural and enjoyable.")
        st.write("We're committed to continuously improving our platform and providing the best possible experience for our users. Join us and start mastering a new language today!")

    if about_us_button:
        about_us_dialog()

    @st.dialog("Contact Us")
    def contact_us_dialog():

        st.write("We're here to assist you with any questions, feedback, or support you need.")
        st.write("- Email: support@voicepal.com")
        st.write("- Phone: 1-800-VOICEPAL")
        st.write("- Social Media: @VoicePalApp")
        st.write("Feel free to reach out to us anytime. Our team is dedicated to helping you make the most of your language learning journey. We look forward to hearing from you.")

    if contact_us_button:
        contact_us_dialog()

    col1, col2 = st.columns([4, 1])
    user_input = st.chat_input("Say something...")
    with col1:
        st.title("Learn with Conversation")

        if 'messages' not in st.session_state:
            st.session_state.messages = []

        for msg in st.session_state.messages:
            if msg['role'] == 'user':
                st.chat_message("user").markdown(msg['content'])
            else:
                st.chat_message("assistant").markdown(msg['content'])

        if user_input:

            st.session_state.messages.append({"role": "user", "content": user_input})

            response_text = chat_with_falcon(user_input)

            st.session_state.messages.append({"role": "assistant", "content": response_text})

            st.chat_message("assistant").markdown(response_text)

            #save_to_database(user_input, response_text)

            st.rerun()

    with col2:
        st.header("Learning approaches")

        selected_page = st.radio("Select a page:", ["Learn with Conversation", "Quiz", "Podcast"])
        
        if selected_page == "Learn with Conversation":
            st.subheader("Learn with Conversation")
            st.write("This is the chat app where you can practice language skills through conversation.")
            
        elif selected_page == "Quiz":
            st.subheader("Quiz")

            if 'quiz_questions' not in st.session_state:
                st.session_state.quiz_questions = []
                st.session_state.current_question_index = 0
                st.session_state.correct_answers = 0

                profile_language = st.session_state.get('profile_language', 'English')
                profile_level = st.session_state.get('profile_level', 'Beginner')
                profile_purpose = st.session_state.get('profile_purpose', 'General')

                system_prompt = (
                    f"Generate a list of 5 quiz questions for a {profile_level} level learner of {profile_language}. "
                    f"The purpose of the learning is {profile_purpose}. Each question should include a 'question' text, "
                    f"a list of 'choices' 'answer can be either one of them' (3 options), and the correct 'answer'. Format as a list of dictionaries."
                )

                response = client.chat.completions.create(
                    model="tiiuae/falcon-180B-chat",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": ""}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )

                if response and response.choices:
                    quiz_questions_json = response.choices[0].message.content.strip()
                    try:
                        quiz_questions = json.loads(quiz_questions_json)
                        for question in quiz_questions:
                            if "question" in question and "choices" in question and "answer" in question:
                                st.session_state.quiz_questions.append(question)
                            else:
                                st.write("Error: Question format is incorrect. Skipping...")
                    except json.JSONDecodeError:
                        st.write("Error: Invalid JSON response.")

            with col1:

                if st.session_state.quiz_questions:
                    current_question = st.session_state.quiz_questions[st.session_state.current_question_index]
                    if "question" in current_question and "choices" in current_question and "answer" in current_question:
                        st.write(current_question["question"])
                        answer = st.radio("Choose an answer:", current_question["choices"])

                        if st.button("Submit Answer"):
                            if answer == current_question["answer"]:
                                st.write("Correct!")
                                st.session_state.correct_answers += 1
                            else:
                                st.write(f"Incorrect. The correct answer is {current_question['answer']}.")

                            if st.session_state.current_question_index < len(st.session_state.quiz_questions) - 1:
                                st.session_state.current_question_index += 1
                                st.rerun()
                            else:
                                st.write(f"Quiz completed! You scored {st.session_state.correct_answers} out of {len(st.session_state.quiz_questions)}.")
                                if st.session_state.correct_answers > 3:
                                    st.balloons()
                                st.session_state.quiz_questions = []
                                st.session_state.current_question_index = 0
                                st.session_state.correct_answers = 0
                    else:
                        st.write("The question format is incorrect. Please try again later.")

        elif selected_page == "Podcast":
            st.subheader("Podcast")

            profile_language = st.session_state.get('profile_language', 'English')
            profile_level = st.session_state.get('profile_level', 'Beginner')
            st.write(f"Generating a podcast story in {profile_language}...")

            system_prompt = (
                f"Generate a podcast story in {profile_language} for a {profile_level} level learner. "
                f"Ensure the story is engaging and appropriate for the learner's level."
            )

            response = client.chat.completions.create(
                model="tiiuae/falcon-180B-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": ""}
                ],
                max_tokens=500,
                temperature=0.7
            )

            if response and response.choices:
                story = response.choices[0].message.content.strip()
            else:
                story = "Sorry, I couldn't generate a story at this time."

            with col1:
                st.write(story)

                if profile_language in language_map:
                    tts = gTTS(text=story, lang=language_map[profile_language])
                    audio_file = BytesIO()
                    tts.write_to_fp(audio_file)
                    audio_file.seek(0)

                    if st.button("Play Story"):
                        st.audio(audio_file, format="audio/mp3")
                else:
                    st.error(f"Language not supported: {profile_language}")
  
    if st.button("Speak", help="Say whats on your mind we got YOU."):
        
        user_voice_input = capture_voice()
        if user_voice_input:

            profile_language = st.session_state.get('profile_language', 'en')
            speak_text(user_voice_input, lang=profile_language)

            st.chat_message("user").markdown(user_voice_input)

            st.session_state.messages.append({"role": "user", "content": user_voice_input})

            response_text = chat_with_falcon(user_voice_input)

            st.session_state.messages.append({"role": "assistant", "content": response_text})

            st.audio("response.mp3", format="audio/mpeg", autoplay=True)

            st.chat_message("assistant").markdown(response_text)

            speak_text(response_text, lang=profile_language)

            #save_to_database(user_voice_input, response_text)

if __name__ == "__main__":
    main()
