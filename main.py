from flask import Flask, render_template, request, Response
import openai
import elevenlabs
import io
import pyaudio

app = Flask(__name__)

# Replace with your OpenAI API key
openai.api_key = "sk-proj-ijdoTZeLeauBlHVCiIMvT3BlbkFJmN4pZ1QUH8BUewXh29UtY"

# Replace with your Elevenlabs API key
elevenlabs_client = elevenlabs.set_key("sk_4ac025acfe13a4b650d918f22a4c20939cc4c280ca229f08")

# Configure PyAudio
audio = pyaudio.PyAudio()
stream = None
audio_frames = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/record', methods=['POST'])
def record():
    global stream
    stream = audio.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=16000,
                        input=True,
                        frames_per_buffer=1024)
    return "Recording started"

@app.route('/stop', methods=['POST'])
def stop():
    global stream, audio_frames
    stream.stop_stream()
    stream.close()
    audio_frames = b''.join(audio_frames)
    audio_data = io.BytesIO(audio_frames)

    # Transcribe audio using OpenAI API
    transcript = openai.Audio.transcribe("whisper-1", audio_data)
    text = transcript["text"]

    # Get ChatGPT response
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=text,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.7,
    )

    # Synthesize audio using Elevenlabs API
    audio_bytes = elevenlabs_client.generate(
        text=response.choices[0].text,
        voice="Rachel",
        model="elevenlabs-neural",
    )

    return Response(audio_bytes, mimetype="audio/mpeg")

if __name__ == '__main__':
    app.run(debug=True)
