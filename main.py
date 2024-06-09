from flask import Flask, request, render_template, send_file
import io
import openai
import requests

app = Flask(__name__)

# Set your API keys here
OPENAI_API_KEY = 'sk-proj-ijdoTZeLeauBlHVCiIMvT3BlbkFJmN4pZ1QUH8BUewXh29Ut'
ELEVEN_LABS_API_KEY = 'sk_4ac025acfe13a4b650d918f22a4c20939cc4c280ca229f08'

openai.api_key = OPENAI_API_KEY

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_audio', methods=['POST'])
def process_audio():
    audio = request.files['audio']
    audio_data = audio.read()

    # Transcribe audio using OpenAI's Whisper model
    response = openai.Audio.transcribe("whisper-1", audio_data)
    transcription = response['text']

    # Get ChatGPT response
    chat_response = openai.Completion.create(
        model="gpt-3.5-turbo",
        prompt=transcription,
        max_tokens=150
    )
    chat_text = chat_response.choices[0].text.strip()

    # Convert ChatGPT response to speech using Eleven Labs API
    tts_response = requests.post(
        'https://api.elevenlabs.io/v1/speech',
        headers={
            'Authorization': f'Bearer {ELEVEN_LABS_API_KEY}',
            'Content-Type': 'application/json'
        },
        json={
            'text': chat_text,
            'voice_settings': {
                'voice': '21m00Tcm4TlvDq8ikWAM'
            }
        }
    )

    audio_content = io.BytesIO(tts_response.content)

    return send_file(audio_content, mimetype='audio/mpeg')

if __name__ == '__main__':
    app.run(debug=True)
