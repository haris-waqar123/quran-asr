# audio_prediction.py

import os
from flask import Blueprint, request, jsonify
import torch
from pydantic import BaseModel
from ai_models import ai_models
from models.audio_model import LessonType
from utils.extensions import verify_token
from utils.model_utils import get_model_state
from utils.file_utils import save_audio_file
from utils.database import insert_lesson_data
import librosa
import io
import logging

router = Blueprint('audio_prediction', __name__)

class AudioData(BaseModel):
    label: str = None

@router.route("/qaida/<model_type>", methods=["POST"])
def predict_lesson_audio(model_type):
    # Verify API key
    logging.info('Received prediction request')
    state = get_model_state()

    auth_header = request.headers.get('Authorization')

    if not auth_header:
        logging.info(auth_header)
        return jsonify({'label': 'Authorization header is missing',"probability": 0.0}), 401
    
    token = auth_header.split(" ")[1]

    logging.error(f'Authorization header for Qaida: {token}')

    if token == 's2yHZSwIfhm1jUo01We00c9APLAndXgX':
        logging.info('Special token detected, bypassing token verification')
        user_info = {'uid': 'bypass_user'}  # Assign a dummy user_info for bypass
    else:
        user_info = verify_token(token)

    if user_info is None:
        logging.info(f"User {user_info}")
        return jsonify({'label': 'Invalid token', "probability": 0.0}), 401

    # Check if the file is included in the request
    if 'file' not in request.files:
        return jsonify({"label": "No file part", "probability": 0.0}), 400

    audio_data = AudioData(label=request.form.get('label'))
    audio_file = request.files['file']
    # Check if the file is empty
    if audio_file.filename == '':
        return jsonify({"label": "No selected file", "probability": 0.0}), 400

    audio_bytes = audio_file.read()
    audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)
    audio = librosa.to_mono(audio)

    user_id = user_info.get('uid', 'unknown_user')

    if model_type in LessonType.__members__.values():
        base_dir = f"saved_audio_files/{user_id}/{model_type}"
        save_dir = f"{base_dir}/{audio_data.label}" if audio_data.label else base_dir
        unique_name = f"{request.form.get('new_name')}.wav"
        save_audio_file(save_dir, unique_name, audio_bytes)

        logging.info(f"Path to audio {save_dir}, {unique_name}")

        if all(-0.001 <= amp <= 0.001 for amp in audio):
            logging.warning({"label": "Audio is not recorded properly", "probability": "400"})
            return jsonify({"label": "Audio is not recorded properly", "probability": 0.0}), 400

        # Get the model from the models dictionary
        model = ai_models.get(model_type)
        if model is None:
            return jsonify({"label": "Model not found", "probability": 0.0}), 400

        predictions = model(audio)
        formatted_predictions = state.formatPrediction(predictions)

        # Find the probability of the label that matches audio_data.label
        probability = None
        for prediction in formatted_predictions:
            if prediction['label'] == audio_data.label:
                probability = prediction['probability']
                break

        if probability is None:
            probability = 0.0

        file_path = os.path.join(save_dir, unique_name)

        force_fully = False

        # Connect to the database and insert the data
        # conn = connect_db()
        # cursor = conn.cursor()

        # cursor.execute('''
        #     INSERT INTO lessons_data (lesson_no, alphabet, file_name, probability, force_fully)
        #     VALUES (?, ?, ?, ?, ?)
        # ''', (model_type, audio_data.label, file_path, probability, force_fully))

        # conn.commit()
        # conn.close()

        #postgre SQL 
        insert_lesson_data(model_type, audio_data.label, file_path, probability, force_fully) 

        logging.info(f"Predictions: {formatted_predictions}")
        return jsonify(formatted_predictions), 200
    else:
        return jsonify({"label": "Invalid model type", "probability": 0.0}), 400
