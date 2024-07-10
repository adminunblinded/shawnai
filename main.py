from flask import Flask, request, render_template, jsonify
import openai
import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Set your API key here
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize OpenAI
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

# Function to preprocess and save chunks from multiple files
def preprocess_files(filenames, chunks_file='chunks.pkl'):
    if not os.path.exists(chunks_file):
        all_chunks = []
        for filename in filenames:
            with open(filename, 'r', encoding='utf-8') as file:
                text = file.read()
            chunks = split_text(text)
            all_chunks.extend(chunks)
        save_chunks_to_file(all_chunks, chunks_file)
    else:
        all_chunks = load_chunks_from_file(chunks_file)
    return all_chunks

# List of primary and secondary text files to be processed
primary_files = ['Sean-Speaking.txt']
secondary_files = ['MSPM.txt', 'Influence.txt', 'Group-Influence-Grand-Cayman.txt']

# Preprocess and save chunks if not already done
primary_chunks = preprocess_files(primary_files, 'primary_chunks.pkl')
secondary_chunks = preprocess_files(secondary_files, 'secondary_chunks.pkl')

# Function to find the most relevant chunk based on the user's prompt
def find_most_relevant_chunk(prompt, primary_chunks, secondary_chunks):
    all_chunks = primary_chunks + secondary_chunks
    vectorizer = TfidfVectorizer().fit_transform(all_chunks + [prompt])
    vectors = vectorizer.toarray()
    prompt_vector = vectors[-1].reshape(1, -1)  # Reshape prompt vector for cosine similarity
    chunk_vectors = vectors[:-1]
    cosine_similarities = cosine_similarity(prompt_vector, chunk_vectors)
    most_relevant_index = cosine_similarities.argmax()
    return all_chunks[most_relevant_index]

# Function to generate a response using the most relevant chunk
def generate_relevant_response(prompt, chunk):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert on the books and materials by Sean Callagy, including 'Unblinded Mastery', 'Self Mastery', 'MSPM', 'Influence Mastery', and 'Group Influence Grand Cayman'. Answer questions based on these texts. Avoid mentioning any sources, including the names of the books, and speak in the first person as if you were Sean Callagy. Keep your responses concise; each response should be 500 characters max. Use the speech patterns and sayings found in 'Sean-Speaking.txt'."},
            {"role": "user", "content": chunk},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150
    )
    return response['choices'][0]['message']['content']

# Function to generate a response from OpenAI
def generate_response(prompt):
    # Find the most relevant chunk
    relevant_chunk = find_most_relevant_chunk(prompt, primary_chunks, secondary_chunks)
    return generate_relevant_response(prompt, relevant_chunk)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form['user_input']
    bot_response = generate_response(user_input)
    return jsonify({"response": bot_response})

if __name__ == '__main__':
    app.run(debug=True)
