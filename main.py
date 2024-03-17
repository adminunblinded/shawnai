import os
from flask import Flask, render_template, request, jsonify
import openai

app = Flask(__name__)

# Retrieve OpenAI API key from environment variable
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Load the text file containing the context
with open("book_text.txt", "r") as file:
    book_text = file.read()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send', methods=['POST'])
def send():
    messages = []
    user_msg = request.json['message']
    messages.append({"role": "user", "content": user_msg})
    
    # Use the book text as context
    messages.append({"role": "book_context", "content": book_text})
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages)
    
    reply = response["choices"][0]["message"]["content"]
    messages.append({"role": "assistant", "content": reply})
    
    return jsonify({'reply': reply})

if __name__ == '__main__':
    app.run(debug=True)
