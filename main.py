from flask import Flask, request, render_template, send_file, jsonify
import openai
import requests
import os
import io

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
    voice_id = "2EiwWnXFnvU5JabPnv8n"  # Replace with the actual voice ID you want to use
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
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        return io.BytesIO(response.content)
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form['user_input']
    bot_response = generate_response(user_input)
    
    audio_data = text_to_speech(bot_response)
    
    if audio_data:
        return send_file(audio_data, mimetype='audio/mpeg', as_attachment=False, attachment_filename='response.mp3')
    else:
        return jsonify({"error": "TTS conversion failed"}), 500

if __name__ == '__main__':
    app.run(debug=True)
