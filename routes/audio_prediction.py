from logging.handlers import RotatingFileHandler
import os
from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Header, BackgroundTasks
from pydantic import BaseModel
from ai_models import ai_models
from config import API_KEY
from models.audio_model import LessonType
from utils.extensions import verify_token
from utils.model_utils import get_model_state
from utils.background_tasks import save_audio_file
from utils.database import insert_lesson_data
import librosa
import io
import logging

router = APIRouter()

if not os.path.exists('logs'):
    os.mkdir('logs')

file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(file_handler)

logger.info('Audio Prediction App startup')

class AudioData(BaseModel):
    label: str = None

@router.post("/qaida/{model_type}")
async def predict_lesson_audio(
    model_type: str,
    audio_file: UploadFile = File(...),
    label: str = Form(None),
    new_name: str = Form(None),
    authorization: str = Header(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    # Verify API key
    logger.info('Received prediction request')
    state = get_model_state()

    if not authorization:
        logger.info(authorization)
        raise HTTPException(status_code=401, detail='Authorization header is missing')

    try:
        token = authorization.split("Bearer ")[1]

        logger.info(f'Authorization header for Qaida: {token}')

        if token == API_KEY:
            logger.info('Special token detected, bypassing token verification')
            user_info = {'uid': 'bypass_user'}  # Assign a dummy user_info for bypass
        else:
            user_info = verify_token(token)
    except Exception as e:
        raise HTTPException(status_code=401, detail='Failed to Authorize')

    if user_info is None:
        logger.error(f"Invalid token: User {user_info}")
        raise HTTPException(status_code=401, detail='Invalid token')

    audio_data = AudioData(label=label)
    audio_bytes = await audio_file.read()
    audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)
    audio = librosa.to_mono(audio)

    user_id = user_info.get('uid', 'unknown_user')

    if model_type in LessonType.__members__.values():
        base_dir = f"saved_audio_files/{user_id}/{model_type}"
        save_dir = f"{base_dir}/{audio_data.label}" if audio_data.label else base_dir
        unique_name = f"{new_name}.wav"
        background_tasks.add_task(save_audio_file, save_dir, unique_name, audio_bytes)

        logger.info(f"Path to audio {save_dir}, {unique_name}")

        # if all(-0.001 <= amp <= 0.001 for amp in audio):
        #     logger.warning({"label": "Audio is not recorded properly", "probability": "400"})
        #     raise HTTPException(status_code=400, detail='Audio is not recorded properly')

        # Get the model from the models dictionary
        model = ai_models.get(model_type)
        if model is None:
            logger.error('Model not found')
            raise HTTPException(status_code=400, detail='Model not found')

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
        background_tasks.add_task(insert_lesson_data, model_type, audio_data.label, file_path, probability, force_fully)

        logger.warning(f"Predictions: {formatted_predictions}")
        return formatted_predictions
    else:
        raise HTTPException(status_code=400, detail='Invalid model type')
