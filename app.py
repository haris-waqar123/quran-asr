import io
import os
import random
import shutil
import string
from fastapi.responses import JSONResponse
import librosa
import logging
from logging.handlers import RotatingFileHandler
from huggingface_hub import login
from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from ai_models import ai_models
from utils.background_tasks import move_audio_files, quran_audio_file
from config import HUGGINGFACE_TOKEN
from routes.audio_prediction import router as audio_prediction_router
from routes.lesson_data import router as lesson_data_router
from utils.database import insert_lesson_data
from utils.extensions import verify_token
import soundfile as sf
import firebase_admin
from firebase_admin import credentials

app = FastAPI()

cred = credentials.Certificate('firebase/al-quran-imai-firebase-adminsdk-bh3zo-9309f678af.json')

firebase_admin.initialize_app(cred)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(file_handler)

logger.info('Main App startup')

# Get the current working directory
current_directory = os.getcwd()

# Print the current working directory
logger.info(f"Current Working Directory: {current_directory}")

def generate_random_name(length=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))

# Initialize models

@app.post("/quran")
async def quran(
    surah_no: str = Form(...),
    ayah_no: str = Form(...),
    audio_file: UploadFile = File(...),
    authorization: str = Header(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    logger.info("Quran Api Called")

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
    if not authorization:
        logger.warning('Authorization header is missing')
        raise HTTPException(status_code=401, detail='Authorization header is missing')

    logger.info(f'Authorization header: {authorization}')

    # Verify token
    token = authorization.split(" ")[1]
    if token == 's2yHZSwIfhm1jUo01We00c9APLAndXgX':
        logging.info('Special token detected, bypassing token verification')
        user_info = {'uid': 'bypass_user'}  # Assign a dummy user_info for bypass
    else:
        user_info = verify_token(token)
        print(f"User Info {user_info}")

    if user_info is None:
        logger.warning('Invalid token')
        raise HTTPException(status_code=403, detail='Invalid token')

    # Validate form data
    if not surah_no or not ayah_no or not audio_file:
        logger.warning('Missing form data')
        raise HTTPException(status_code=400, detail='Missing form data')

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

    # background_tasks.add_task(
    quran_audio_file(file_path, audio_file, surah_no, ayah_no)

    try:
        # Perform ASR on the saved audio file
        transcript = ai_models["quran"](file_path)
        logger.info(f'Transcription successful for {file_path}')

        surah_no = int(surah_no)
        ayah_no = int(ayah_no)
        is_special_verse = (surah_no, ayah_no) in special_verses

        # If the surah and ayah numbers are in the special verses list, call the classification pipeline
        if is_special_verse:
            print(f"is Special Verse {is_special_verse}")
            classification_result = ai_models["lesson10"](file_path)

            classification_text = classification_result[0]['label']
            logger.info(f'Classification successful for {file_path}: {classification_text} ')

            return {
                "file_path": file_path,
                "transcript": classification_text,
                "classification": classification_result,
            }

        return {
            "file_path": file_path,
            "transcript": transcript['text'],
        }

    except Exception as e:
        logger.error(f'Error during ASR processing: {e}')
        raise HTTPException(status_code=500, detail='Failed to transcribe audio')

@app.post("/delete_data")
async def delete_data(authorization: str = Header(None), background_tasks: BackgroundTasks = BackgroundTasks()):
    logger.info("Request Received for Delete Data")

    if not authorization:
        logger.warning('Authorization header is missing')
        raise HTTPException(status_code=401, detail='Authorization header is missing')

    logger.info(f'Authorization header: {authorization}')

    # Verify token
    token = authorization.split(" ")[1]
    if token == 's2yHZSwIfhm1jUo01We00c9APLAndXgX':
        logging.info('Special token detected, bypassing token verification')
        user_info = {'uid': 'bypass_user'}  # Assign a dummy user_info for bypass
    else:
        user_info = verify_token(token)
        print(f"User Info {user_info}")

    if user_info is None:
        logger.warning('Invalid token')
        raise HTTPException(status_code=403, detail='Invalid token')

    saved_audio_files = '/saved_audio_files'

    user_id = user_info.get('uid', 'unknown_user')
    if user_id:
        source_folder = os.path.join(saved_audio_files, user_id)
        destination_folder = '/moved_audio_files'  # Define the new path

        # Add the background task to move the audio files
        background_tasks.add_task(move_audio_files, source_folder, destination_folder)

        return JSONResponse(content={"status": "Data Deletion Scheduled", "status_code": 200})
    else:
        return JSONResponse(content={"status": "User ID not provided", "status_code": 400})

# Include routers
app.include_router(audio_prediction_router)
app.include_router(lesson_data_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
