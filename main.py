from flask import Flask, render_template, request, Response
import openai
import requests
import io
import os

app = Flask(__name__)

# Replace with your OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Replace with your ElevenLabs API key
ELEVENLABS_API_KEY = os.getenv('ELEVEN_LABS_API_KEY')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    audio_data = request.get_data()

    # Send audio data to OpenAI API for transcription
    headers = {
        "Authorization": f"Bearer {openai.api_key}",
        "Content-Type": "audio/webm"
    }

    audio_file = {"file": audio_data, "model": "whisper-1"}
    transcribe_response = requests.post("https://api.openai.com/v1/audio/transcriptions", headers=headers, files=audio_file)

    if transcribe_response.status_code == 200:
        text = transcribe_response.json()["transcription"]
    else:
        return f"Error: {transcribe_response.status_code} - {transcribe_response.text}", 500

    # Get ChatGPT response
    response =  openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": text}
        ],
        max_tokens=1048
    )

    # Synthesize audio using ElevenLabs API
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }

    data = {
        "text": response.choices[0].text,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }

    url = "https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL"
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        audio_bytes = response.content
        return Response(audio_bytes, mimetype="audio/mpeg")
    else:
        return f"Error: {response.status_code} - {response.text}", 500

if __name__ == '__main__':
    app.run(debug=True)
