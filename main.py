from flask import Flask, request, render_template, send_file, jsonify
import openai
import requests
import os
import io
import wave
import speech_recognition as sr

app = Flask(__name__)

# Set your API keys here
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ELEVEN_LABS_API_KEY = os.getenv('ELEVEN_LABS_API_KEY')

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY

# Function to generate a response from OpenAI
def generate_response(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150
    )
    return response['choices'][0]['message']['content'].strip()

# Function to convert text to speech using Eleven Labs
def text_to_speech(text):
    voice_id = "21m00Tcm4TlvDq8ikWAM"  # Replace with the actual voice ID you want to use
    url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
    headers = {
        'xi-api-key': ELEVEN_LABS_API_KEY,
        'Content-Type': 'application/json',
        'Accept': 'audio/mpeg'
    }
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.75,
            "similarity_boost": 0.75
        }
    }
    response = requests.post(url, headers=headers, json=data, verify=False)
    
    if response.status_code == 200:
        return io.BytesIO(response.content)
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

# Function to convert speech to text using speech_recognition
def speech_to_text(audio_data):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_data) as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return "Sorry, I could not understand the audio."
        except sr.RequestError as e:
            return f"Could not request results; {e}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    if 'audio_data' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio_data']
    audio_data = io.BytesIO(audio_file.read())
    
    # Ensure the audio data is in WAV format directly (assumes proper client-side conversion)
    user_text = speech_to_text(audio_data)
    
    if "Sorry" in user_text:
        return jsonify({"error": user_text}), 400

    bot_response = generate_response(user_text)
    
    response_audio = text_to_speech(bot_response)
    
    if response_audio:
        return send_file(response_audio, mimetype='audio/mpeg', as_attachment=False, attachment_filename='response.mp3')
    else:
        return jsonify({"error": "TTS conversion failed"}), 500

if __name__ == '__main__':
    app.run(debug=True)
