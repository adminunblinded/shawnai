from flask import Flask, request, render_template, send_file, jsonify
import openai
import requests
import os
import tempfile

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
def text_to_speech(text, output_file):
    url = 'https://api.elevenlabs.io/v1/text-to-speech'
    headers = {
        'xi-api-key': ELEVEN_LABS_API_KEY,
        'Content-Type': 'application/json'
    }
    data = {
        "text": text,
        "voice_settings": {
            "voice_id": "en_us_male",
            "stability": 0.75,
            "similarity_boost": 0.75
        }
    }
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        with open(output_file, 'wb') as f:
            f.write(response.content)
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return False
    return True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form['user_input']
    bot_response = generate_response(user_input)
    
    # Use a temporary file to save the TTS response
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
        output_file = temp_file.name
    
    success = text_to_speech(bot_response, output_file)
    
    if success:
        return send_file(output_file, as_attachment=True)
    else:
        return jsonify({"error": "TTS conversion failed"}), 500

if __name__ == '__main__':
    app.run(debug=True)
