from flask import Flask, request, render_template, send_file
import openai
import requests
import os

app = Flask(__name__)

# Set your API keys here
OPENAI_API_KEY = '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'
ELEVEN_LABS_API_KEY = 'sk_4ac025acfe13a4b650d918f22a4c20939cc4c280ca229f08'

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY

# Function to generate a response from OpenAI
def generate_response(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form['user_input']
    bot_response = generate_response(user_input)
    
    output_file = 'response.mp3'
    text_to_speech(bot_response, output_file)
    
    return send_file(output_file, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
