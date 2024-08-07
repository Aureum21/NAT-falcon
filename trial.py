import streamlit as st
import io
import base64
from PIL import Image

def record_audio_html():
    return '''
    <script>
        let mediaRecorder;
        let audioChunks = [];

        function startRecording() {
            navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
                mediaRecorder = new MediaRecorder(stream);
                
                mediaRecorder.ondataavailable = event => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const audioUrl = URL.createObjectURL(audioBlob);

                    // Create a FormData object to send the audio file
                    const formData = new FormData();
                    formData.append('audio', audioBlob, 'audio.wav');

                    fetch('/upload_audio', {
                        method: 'POST',
                        body: formData
                    }).then(response => response.text())
                      .then(data => console.log(data));
                };

                mediaRecorder.start();
                document.getElementById('stop').disabled = false;
            });
        }

        function stopRecording() {
            mediaRecorder.stop();
            document.getElementById('stop').disabled = true;
        }

        window.addEventListener('load', () => {
            document.getElementById('start').addEventListener('click', startRecording);
            document.getElementById('stop').addEventListener('click', stopRecording);
        });
    </script>
    <button id="start">Start Recording</button>
    <button id="stop" disabled>Stop Recording</button>
    <audio controls></audio>
    '''

st.title("Audio Recorder")

# Render HTML for audio recording
st.components.v1.html(record_audio_html(), height=200)

# Handling the audio file upload
uploaded_file = st.file_uploader("Upload an audio file", type="wav")

if uploaded_file is not None:
    # Process the audio file as needed
    st.audio(uploaded_file)