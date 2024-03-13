import os
from flask import Flask, render_template, request, jsonify
import openai

app = Flask(__name__)

# Retrieve OpenAI API key from environment variable
openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send', methods=['POST'])
def send():
    messages = []
    user_msg = request.json['message']
    messages.append({"role": "user", "content": user_msg})
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages)
    reply = response["choices"][0]["message"]["content"]
    messages.append({"role": "assistant", "content": reply})
    return jsonify({'reply': reply})

if __name__ == '__main__':
    app.run(debug=True)
