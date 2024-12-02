import os
from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Header, BackgroundTasks
from pydantic import BaseModel
from utils.ai_models import ai_models
from utils.extensions import verify_token
from utils.model_utils import formatPrediction
from utils.background_tasks import save_audio_file
from utils.database import insert_lesson_data
import librosa
import io
from utils.app_logger import logger

router = APIRouter()

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
    logger.info('Received prediction request')

    if not authorization:
        logger.info(authorization)
        raise HTTPException(status_code=401, detail='Authorization header is missing')

    try:
        token = authorization.split("Bearer ")[1]
        logger.info(f'Authorization header for Qaida: {token}')
        user_info = verify_token(token)
    
    except Exception as e:
        logger.error(f"Failed to Authorize: {e}")
        raise HTTPException(status_code=401, detail='Failed to Authorize')

    if user_info is None:
        logger.error(f"Invalid token: User {user_info}")
        raise HTTPException(status_code=401, detail='Invalid token')

    audio_data = AudioData(label=label)
    audio_bytes = await audio_file.read()
    audio, _ = librosa.load(io.BytesIO(audio_bytes), sr=16000)
    audio = librosa.to_mono(audio)

    user_id = user_info.get('uid', 'unknown_user')

    if model_type in ai_models:
        base_dir = f"qaida_saved_audio/{user_id}/{model_type}"
        save_dir = f"{base_dir}/{audio_data.label}" if audio_data.label else base_dir
        unique_name = f"{new_name}.wav"

        logger.info(f"Path to audio {save_dir}, {unique_name}")

        model = ai_models.get(model_type)
        if model is None:
            logger.error('Model not found')
            raise HTTPException(status_code=400, detail='Model not found')

        predictions = model(audio)
        formatted_predictions = formatPrediction(predictions)

        probability = next((pred['probability'] for pred in formatted_predictions if pred['label'] == audio_data.label), 0.0)

        file_path = os.path.join(save_dir, unique_name)
        force_fully = False

        background_tasks.add_task(insert_lesson_data, model_type, audio_data.label, file_path, probability, force_fully)
        background_tasks.add_task(save_audio_file, save_dir, unique_name, audio_bytes)

        logger.warning(f"Predictions: {formatted_predictions}")
        return formatted_predictions
    else:
        raise HTTPException(status_code=400, detail='Invalid model type')
