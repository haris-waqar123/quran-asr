# app.py

import os
import random
import shutil
import string
import librosa
import logging
from logging.handlers import RotatingFileHandler
from huggingface_hub import login
from flask_cors import CORS
from flask import Flask, jsonify, request
from ai_models import ai_models
from config import HUGGINGFACE_TOKEN
from routes.audio_prediction import router as audio_prediction_router
from routes.lesson_data import router as lesson_data_router
from utils.extensions import verify_token
from utils.file_utils import ensure_audio_directory
from utils.database import create_table  # Import the create_table function
import flask_monitoringdashboard as dashboard
import firebase_admin
from firebase_admin import credentials
import soundfile as sf


app = Flask(__name__)
dashboard.bind(app)

cred = credentials.Certificate('/sdb-disk/9D-Muslim-Ai/asr_live/firebase/al-quran-imai-firebase-adminsdk-bh3zo-9309f678af.json')

firebase_admin.initialize_app(cred)

CORS(app)

# Initialize HuggingFace login
login(HUGGINGFACE_TOKEN)

# Configure logging
if not os.path.exists('logs'):
    os.mkdir('logs')

file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)

app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

app.logger.info('Main App startup')

# Get the current working directory
current_directory = os.getcwd()

# Print the current working directory
app.logger.info(f"Current Working Directory: {current_directory}")

def generate_random_name(length=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

# Initialize models

@app.route("/quran", methods=["POST"])
def quran():
    auth_header = request.headers.get('Authorization')
    surah_no = request.form.get('surah_no')
    ayah_no = request.form.get('ayah_no')
    audio_file = request.files['audio_file']

    special_verses = {
        (2, 1),
        (3, 1),
        (7, 1),
        (19, 1),
        (20, 1),
        (26, 1),
        (28, 1),
        (29, 1),
        (30, 1),
        (31, 1),
        (32, 1),
        (36, 1),
        (40, 1),
        (41, 1),
        (42, 1),
        (43, 1),
        (44, 1),
        (45, 1),
        (46, 1),
    }

    # Check for Authorization header
    if not auth_header:
        app.logger.warning('Authorization header is missing')
        return jsonify({'error': 'Authorization header is missing'}), 401

    app.logger.info(f'Authorization header: {auth_header}')

    # Verify token
    token = auth_header.split(" ")[1]
    if token == 's2yHZSwIfhm1jUo01We00c9APLAndXgX':
        logging.info('Special token detected, bypassing token verification')
        user_info = {'uid': 'bypass_user'}  # Assign a dummy user_info for bypass
    else:
        user_info = verify_token(token)
        print(f"User Info {user_info}")

    if user_info is None:
        app.logger.warning('Invalid token')
        return jsonify({'error': 'Invalid token'}), 403

    # Validate form data
    if not surah_no or not ayah_no or not audio_file:
        app.logger.warning('Missing form data')
        return jsonify({'error': 'Missing form data'}), 400

    user_id = user_info.get('uid', 'unknown_user')
    # Create the directory structure for saving audio files
    base_dir = 'quran_audio'
    user = os.path.join(base_dir, f"{user_id}")
    surah_dir = os.path.join(user, f'surah_no_{surah_no}')
    ayah_dir = os.path.join(surah_dir, f'ayah_no_{ayah_no}')
    os.makedirs(ayah_dir, exist_ok=True)

    # Generate a random name for the audio file
    random_name = generate_random_name()
    file_path = os.path.join(ayah_dir, f'{random_name}.wav')

    try:
        # Load the audio file with librosa to resample at 32000 Hz
        y, sr = librosa.load(audio_file)

        app.logger.info(f"Quran API Audio Sampling rate is {sr}")

        # Save the resampled audio using soundfile
        sf.write(file_path, y, sr)
        app.logger.info(user_id, f'Audio file saved and resampled to {file_path}')

    except Exception as e:
        app.logger.error(f'Error processing the audio file: {e}')
        return jsonify({'error': 'Failed to process the audio file'}), 500

    try:
        # Perform ASR on the saved audio file
        transcript = ai_models["quran"](file_path)
        app.logger.info(f'Transcription successful for {file_path}')

        surah_no = int(surah_no)
        ayah_no = int(ayah_no)
        is_special_verse = (surah_no, ayah_no) in special_verses

        # If the surah and ayah numbers are in the special verses list, call the classification pipeline
        if is_special_verse:
            print(f"is Special Verse {is_special_verse}")
            classification_result = ai_models["lesson10"](file_path)

            classification_text = classification_result[0]['label']
            app.logger.info(f'Classification successful for {file_path}: {classification_text} ')

            return jsonify({
                "file_path": file_path,
                "transcript": classification_text,
                "classification": classification_result,
            }), 200

        return jsonify({
            "file_path": file_path,
            "transcript": transcript['text'],
        }), 200

    except Exception as e:
        app.logger.error(f'Error during ASR processing: {e}')
        return jsonify({'error': 'Failed to transcribe audio'}), 500

@app.route("/delete_data", methods=["POST"])
def delete_data():
    app.logger.info("Request Received for Delete Data")
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        app.logger.warning('Authorization header is missing')
        return jsonify({'error': 'Authorization header is missing'}), 401

    app.logger.info(f'Authorization header: {auth_header}')

    # Verify token
    token = auth_header.split(" ")[1]
    if token == 's2yHZSwIfhm1jUo01We00c9APLAndXgX':
        logging.info('Special token detected, bypassing token verification')
        user_info = {'uid': 'bypass_user'}  # Assign a dummy user_info for bypass
    else:
        user_info = verify_token(token)
        print(f"User Info {user_info}")

    if user_info is None:
        app.logger.warning('Invalid token')
        return jsonify({'error': 'Invalid token'}), 403

    saved_audio_files = '/sdb-disk/9D-Muslim-Ai/asr_live/saved_audio_files'

    user_id = user_info.get('uid', 'unknown_user')
    if user_id:
        source_folder = os.path.join(saved_audio_files, user_id)
        destination_folder = '/sdb-disk/9D-Muslim-Ai/asr_live/moved_audio_files'  # Define the new path

        # Ensure the destination directory exists
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)

        # Check if the source folder exists
        if os.path.exists(source_folder):
            # Move the folder
            shutil.move(source_folder, os.path.join(destination_folder, user_id))
            return jsonify({"status": "Data Deleted Successfully", "status_code": 200})
        else:
            return jsonify({"status": "User folder not found OR Data Already Deleted", "status_code": 404})
    else:
        return jsonify({"status": "User ID not provided", "status_code": 400})

# Startup event
ensure_audio_directory()
# Ensure the table is created on startup
create_table()

# Include routers
app.register_blueprint(audio_prediction_router)
app.register_blueprint(lesson_data_router)

if __name__ == "__main__":
    app.run()
    # app.run(host='69.197.145.4', port=8000, debug=True, use_reloader=True)
