from flask import Flask, request, render_template, send_file, jsonify
import openai
import requests
import os
import io
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Set your API keys here
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ELEVEN_LABS_API_KEY = os.getenv('ELEVEN_LABS_API_KEY')

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY

# Load your OpenAI API key
openai.api_key = OPENAI_API_KEY

# Function to split the text into chunks
def split_text(text, max_tokens=2000):
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        current_length += len(word) + 1  # +1 for the space
        if current_length > max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = len(word) + 1
        else:
            current_chunk.append(word)
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

# Function to save chunks to a file
def save_chunks_to_file(chunks, filename='chunks.pkl'):
    with open(filename, 'wb') as file:
        pickle.dump(chunks, file)

# Function to load chunks from a file
def load_chunks_from_file(filename='chunks.pkl'):
    with open(filename, 'rb') as file:
        return pickle.load(file)

# Preprocess and save chunks if not already done
chunks_file = 'chunks.pkl'
if not os.path.exists(chunks_file):
    with open('influence.txt', 'r', encoding='utf-8') as file:
        text = file.read()
    chunks = split_text(text)
    save_chunks_to_file(chunks)
else:
    chunks = load_chunks_from_file(chunks_file)

# Function to find the most relevant chunk based on the user's prompt
def find_most_relevant_chunk(prompt, chunks):
    vectorizer = TfidfVectorizer().fit_transform(chunks + [prompt])
    vectors = vectorizer.toarray()
    prompt_vector = vectors[-1].reshape(1, -1)  # Reshape prompt vector for cosine similarity
    chunk_vectors = vectors[:-1]
    cosine_similarities = cosine_similarity(prompt_vector, chunk_vectors)
    most_relevant_index = cosine_similarities.argmax()
    return chunks[most_relevant_index]

# Function to generate a response using the most relevant chunk
def generate_relevant_response(prompt, chunk):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert on the book 'Influence Group Influence and MSPM Super book' by Sean Callagy. Answer questions based on this book."},
            {"role": "user", "content": chunk},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150
    )
    return response['choices'][0]['message']['content']


# Function to generate a response from OpenAI
def generate_response(prompt):
    # Find the most relevant chunk
    relevant_chunk = find_most_relevant_chunk(prompt, chunks)
    return generate_relevant_response(prompt, relevant_chunk)

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
