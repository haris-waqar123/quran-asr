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
import subprocess

# # Initialize HuggingFace login
# lock_file = ".huggingface_lock"
# if not os.path.exists(lock_file):
login(HUGGINGFACE_TOKEN)
    # with open(lock_file, "w") as f:
    #     f.write("locked")

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

def generate_random_name(length=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

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
    random_name = generate_random_name()
    file_path = os.path.join(ayah_dir, f'{random_name}.wav')

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
        "token_duration": (ACCESS_TOKEN_EXPIRE_MINUTES * 60 * 1000)
    }
    return jsonify(token_data)


if __name__ == "__main__":
    # Set the environment variable to use only GPU 2
    os.environ['CUDA_VISIBLE_DEVICES'] = '2'

    # Start the Flask server using Gunicorn
    subprocess.run([
        "gunicorn",
        "--bind", "172.16.10.104:8000",
        "--workers", "4",
        "--log-level", "debug",
        "app:app"
    ])
