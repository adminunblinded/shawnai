from flask import Flask, request, jsonify
import openai
import requests
import wave
import numpy as np
from io import BytesIO
import os

app = Flask(__name__)

# Set your API keys here
openai.api_key = os.getenv('OPENAI_API_KEY')
eleven_labs_api_key = os.getenv('ELEVEN_LABS_API_KEY')

def convert_audio_to_wav(audio_file):
    # Read the audio data from the file
    audio_bytes = audio_file.read()
    
    # Convert WebM to WAV using wave and numpy
    with wave.open(BytesIO(audio_bytes), 'rb') as webm_audio:
        params = webm_audio.getparams()
        frames = webm_audio.readframes(params.nframes)
        
        # Create a new WAV file in-memory
        with BytesIO() as wav_buffer:
            with wave.open(wav_buffer, 'wb') as wav_audio:
                wav_audio.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
                wav_audio.writeframes(frames)
            return wav_buffer.getvalue()

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Audio Recording</title>
    </head>
    <body>
        <h1>Audio Recording Interface</h1>
        <button id="recordButton">Record</button>
        <button id="stopButton" disabled>Stop</button>
        <audio id="audioPlayback" controls></audio>

        <script>
            let mediaRecorder;
            let audioChunks = [];

            const recordButton = document.getElementById('recordButton');
            const stopButton = document.getElementById('stopButton');
            const audioPlayback = document.getElementById('audioPlayback');

            recordButton.addEventListener('click', async () => {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                
                mediaRecorder.ondataavailable = event => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    audioPlayback.src = audioUrl;

                    const formData = new FormData();
                    formData.append('audio', audioBlob, 'recording.webm');

                    const response = await fetch('/process_audio', {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();
                    const audio = new Audio(result.audio_url);
                    audio.play();
                };

                mediaRecorder.start();
                recordButton.disabled = true;
                stopButton.disabled = false;
            });

            stopButton.addEventListener('click', () => {
                mediaRecorder.stop();
                recordButton.disabled = false;
                stopButton.disabled = true;
            });
        </script>
    </body>
    </html>
    '''

@app.route('/process_audio', methods=['POST'])
def process_audio():
    # Get the audio file from the request
    audio_file = request.files['audio']

    # Convert the audio file to WAV format
    wav_audio = convert_audio_to_wav(audio_file)

    # Transcribe the audio using OpenAI's Whisper
    transcript = openai.Audio.transcribe("whisper-1", wav_audio)

    # Send the transcription to ChatGPT
    prompt = transcript['text']
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=150
    )

    chat_response = response.choices[0].text.strip()

    # Use Eleven Labs API to synthesize speech from ChatGPT's response
    eleven_labs_response = requests.post(
        "https://api.elevenlabs.io/v1/text-to-speech",
        headers={
            "Authorization": f"Bearer {eleven_labs_api_key}",
            "Content-Type": "application/json"
        },
        json={
            "text": chat_response,
            "voice": "Joanna"  # Replace with the desired voice name
        }
    )

    if eleven_labs_response.status_code == 200:
        audio_content = eleven_labs_response.content
        audio_url = f"data:audio/wav;base64,{audio_content.encode('base64').decode()}"
        return jsonify({"audio_url": audio_url})
    else:
        return jsonify({"error": "Failed to synthesize speech"}), 500

if __name__ == '__main__':
    app.run(debug=True)
