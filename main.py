from flask import Flask, render_template, request, Response
import openai
import requests
import io

app = Flask(__name__)

# Replace with your OpenAI API key
openai.api_key = "sk-proj-6PuG10ra5RdkXVoO4SltT3BlbkFJfNaociDXS1ybfEmQzQd5"

# Replace with your ElevenLabs API key
ELEVENLABS_API_KEY = "sk_4ac025acfe13a4b650d918f22a4c20939cc4c280ca229f08"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    audio_data = request.get_data()
    audio_file = io.BytesIO(audio_data)

    # Transcribe audio using OpenAI API
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    text = transcript["text"]

    # Get ChatGPT response
    response = openai.Completion.create(
        engine="gpt-3.5-turbo",
        prompt=text,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.7,
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
