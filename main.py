import os
import io
from datetime import timedelta
import random
import string
import numpy as np
import torch
from transformers import pipeline
from huggingface_hub import login
from flask_cors import CORS
from flask import Flask, jsonify, request
from config import HUGGINGFACE_TOKEN
from routes.audio_prediction import router as audio_prediction_router
from routes.lesson_data import router as lesson_data_router
from utils.extensions import ACCESS_TOKEN_EXPIRE_MINUTES, verify_api_key
from utils.file_utils import ensure_audio_directory
from utils.jwt_utils import create_access_token
from utils.database import create_table  # Import the create_table function
import json
import threading
import asyncio
import wave
import websockets

# Initialize HuggingFace login
login(HUGGINGFACE_TOKEN)

# Initialize ASR pipeline
device = "cuda" if torch.cuda.is_available() else "cpu"
asr_pipeline = pipeline("automatic-speech-recognition", model="haseeb-9d/Quran-ASR-Full", device=device)

app = Flask(__name__)
CORS(app)

# Startup event
ensure_audio_directory()
# Ensure the table is created on startup
create_table()

# Include routers
app.register_blueprint(audio_prediction_router)
app.register_blueprint(lesson_data_router)


# def generate_random_name(length=10):
#     letters = string.ascii_lowercase
#     return ''.join(random.choice(letters) for i in range(length))

@app.route("/quran", methods=["POST"])
def save_data_for_quran():
    surah_no = request.form.get('surah_no')
    ayah_no = request.form.get('ayah_no')
    audio_file = request.files['audio_file']

    if not surah_no or not ayah_no or not audio_file:
        return "Missing form data", 400

    # Create the directory structure
    base_dir = 'quran_audio'
    surah_dir = os.path.join(base_dir, f'surah_no_{surah_no}')
    ayah_dir = os.path.join(surah_dir, f'ayah_no_{ayah_no}')

    os.makedirs(ayah_dir, exist_ok=True)

    # Generate a random name for the audio file
    # random_name = generate_random_name()
    file_path = os.path.join(ayah_dir, f'{surah_no + ayah_no}.wav')

    # Save the audio file
    audio_file.save(file_path)
    transcript = asr_pipeline(file_path)

    return jsonify({
        "file_path": file_path,
        "transcript": transcript
    }), 200

@app.route("/token", methods=["POST"])
def login_for_access_token():
    print("Request received for /token")
    # Verify API key
    if not verify_api_key():
        return jsonify({"detail": "Invalid API key"}), 401

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": "qaida"}, expires_delta=access_token_expires
    )
    token_data = {
        "token": access_token,
        "token_duration" : (ACCESS_TOKEN_EXPIRE_MINUTES * 60 * 1000)
    }
    return jsonify(token_data)

# Initialize connected clients set
connected_clients = set()

# Create resampled audio folder if it doesn't exist


def convert_pcm_to_wav(pcm_data, sample_rate=32000, num_channels=1, sample_width=2):
    with io.BytesIO() as wav_file:
        with wave.open(wav_file, 'wb') as wav_writer:
            wav_writer.setnchannels(num_channels)
            wav_writer.setsampwidth(sample_width)
            wav_writer.setframerate(sample_rate)
            wav_writer.writeframes(pcm_data)
        wav_file.seek(0)
        return wav_file.read()

def read_wav_from_bytes(audio_bytes):
    with wave.open(io.BytesIO(audio_bytes), 'rb') as wav_file:
        sample_rate = wav_file.getframerate()
        num_channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        num_frames = wav_file.getnframes()

        audio_data = wav_file.readframes(num_frames)
        audio_array = np.frombuffer(audio_data, dtype=np.int16)

        if num_channels == 2:
            audio_array = audio_array.reshape(-1, 2).mean(axis=1)

        return audio_array, sample_rate


def pad_audio(audio_data, target_length):
    current_length = len(audio_data)
    if current_length < target_length:
        padding_length = target_length - current_length
        padding = np.zeros(padding_length, dtype=audio_data.dtype)
        audio_data = np.concatenate((audio_data, padding))
    return audio_data

chunk_counter = 0

def save_as_wav(audio_chunk, filename="output.wav", sample_rate=32000, num_channels=1, sample_width=2):
    with wave.open(filename, "wb") as wav_file:
        wav_file.setnchannels(num_channels)    # Mono channel
        wav_file.setsampwidth(sample_width)    # 2 bytes per sample for 16-bit PCM
        wav_file.setframerate(sample_rate)     # 16 kHz sample rate
        wav_file.writeframes(audio_chunk)

# WebSocket handler
async def handle_client(websocket, path):
    # Register the client
    chunk_counter = 0
    resampled_audio_folder = 'resampled_audio_chunks'
    if not os.path.exists(resampled_audio_folder):
        os.makedirs(resampled_audio_folder)
    connected_clients.add(websocket)
    print(f"Client connected: {websocket.remote_address}")

    try:
        async for message in websocket:
            # print(f"Received message from {websocket.remote_address}: {message}")

            if isinstance(message, bytes):
                print(f"Received audio chunk of size: {len(message)} bytes")

                # Convert raw PCM data to WAV format
                wav_data = convert_pcm_to_wav(message)
                
                audio_path = os.path.join(resampled_audio_folder, f"chunk_{chunk_counter}.wav")
                with open(audio_path, "wb") as f:
                    f.write(wav_data)
                
                # Read WAV data into a NumPy array
                audio_data, sample_rate = read_wav_from_bytes(wav_data)

                # Process the audio data with the ASR pipeline
                response = asr_pipeline(audio_data)

                print(response)

                # Convert the response to a JSON string
                response_json = json.dumps(response)
                
                chunk_counter += 1
                
                await websocket.send(response_json)
            else:
                await websocket.send("Received non-binary message")

    except websockets.exceptions.ConnectionClosed as e:
        print(f"Client {websocket.remote_address} disconnected: {e}")
    finally:
        # Unregister the client
        connected_clients.remove(websocket)
        print(f"Client disconnected: {websocket.remote_address}")

async def server():
    # WebSocket server setup
    server = await websockets.serve(handle_client, "69.197.145.4", 5000)

    # Run the server forever
    print("WebSocket server started on ws://69.197.145.4:5000")
    await server.wait_closed()

if __name__ == "__main__":
    # Set the environment variable to use only GPU 2
    os.environ['CUDA_VISIBLE_DEVICES'] = '2'
    
    # asyncio.run(server())

    # Start the WebSocket server in a separate thread
    websocket_thread = threading.Thread(target=lambda: asyncio.run(server()))
    websocket_thread.start()

    # # Start the Flask server
    app.run(host="69.197.145.4", port=8000, debug=True, use_reloader=False)
    