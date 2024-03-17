import os
from flask import Flask, render_template, request, jsonify
import openai

app = Flask(__name__)

# Retrieve OpenAI API key from environment variable
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Load the text file containing the book
with open("book_text.txt", "r") as file:
    book_text = file.read()

# Split the book text into smaller chunks for context
max_context_size = 1000  # Adjust this value as needed
book_contexts = [book_text[i:i+max_context_size] for i in range(0, len(book_text), max_context_size)]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send', methods=['POST'])
def send():
    user_msg = request.json['message']
    context = ""

    # Use a portion of the book text as context
    for book_context in reversed(book_contexts):
        if user_msg in book_context:
            context = book_context
            break
    
    messages = [
        {"role": "user", "content": user_msg + "\n" + context},  # Include book context as part of user message
        {"role": "assistant", "content": ""}  # Empty assistant message to trigger response
    ]
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages)
    
    reply = response["choices"][0]["message"]["content"]
    
    return jsonify({'reply': reply})

if __name__ == '__main__':
    app.run(debug=True)
