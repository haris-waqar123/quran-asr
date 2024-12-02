import io
import os
import random
import string
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from huggingface_hub import login
from utils.ai_models import ai_models
from utils.background_tasks import move_audio_files, quran_audio_file
from config import HUGGINGFACE_TOKEN
from routes.audio_prediction import router as audio_prediction_router
from routes.lesson_data import router as lesson_data_router
from utils.database import insert_lesson_data
from utils.extensions import verify_token
import librosa
import firebase_admin
from firebase_admin import credentials
from utils.special_verse_dict import special_verses
from utils.app_logger import logger

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

logger.info('Main App startup')

# Get the current working directory
current_directory = os.getcwd()
logger.info(f"Current Working Directory: {current_directory}")

def generate_random_name(length=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

@app.post("/quran")
async def quran(
    surah_no: str = Form(...),
    ayah_no: str = Form(...),
    audio_file: UploadFile = File(...),
    authorization: str = Header(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    logger.info("Quran API Called")

    if not authorization:
        logger.warning('Authorization header is missing')
        raise HTTPException(status_code=401, detail='Authorization header is missing')

    logger.info(f'Authorization header: {authorization}')

    try:
        token = authorization.split(" ")[1]
        user_info = verify_token(token)
    except Exception as e:
        logger.error(f"Failed to Authorize: {e}")
        raise HTTPException(status_code=401, detail="Failed to Authorize")

    if user_info is None:
        logger.warning('Invalid token')
        raise HTTPException(status_code=403, detail='Invalid token')

    if not surah_no or not ayah_no or not audio_file:
        logger.warning('Missing form data')
        raise HTTPException(status_code=400, detail='Missing form data')

    user_id = user_info.get('uid', 'unknown_user')

    try:
        audio_bytes = await audio_file.read()
        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=32000)
        logger.info(f'Audio sampling rate is {sr}')

        base_dir = 'quran_saved_audio'
        user_dir = os.path.join(base_dir, user_id)
        surah_dir = os.path.join(user_dir, f'surah_no_{surah_no}')
        ayah_dir = os.path.join(surah_dir, f'ayah_no_{ayah_no}')
        os.makedirs(ayah_dir, exist_ok=True)

        random_name = generate_random_name()
        file_path = os.path.join(ayah_dir, f'{random_name}.wav')

        transcript = ai_models["quran"](audio_bytes)
        logger.info('Transcription successful')

        surah_no = int(surah_no)
        ayah_no = int(ayah_no)
        is_special_verse = (surah_no, ayah_no) in special_verses

        if is_special_verse:
            logger.info(f"is Special Verse {is_special_verse}")
            classification_result = ai_models["lesson10"](audio)
            classification_text = classification_result[0]['label']
            logger.warning(f'Classification successful: {classification_text}')

            return JSONResponse(content={
                "transcript": classification_text,
                "classification": classification_result,
            }, status_code=200)

        background_tasks.add_task(quran_audio_file, file_path, audio_bytes, surah_no, ayah_no)
        background_tasks.add_task(insert_lesson_data, surah_no, ayah_no, file_path, 0, False)

        return JSONResponse(content={
            "transcript": transcript['text'],
        }, status_code=200)

    except Exception as e:
        logger.error(f'Error during ASR processing: {e}')
        raise HTTPException(status_code=500, detail='Failed to transcribe audio')

@app.post("/delete_data")
async def delete_data(
    authorization: str = Header(None)):
    
    logger.info("Request Received for Delete Data")

    if not authorization:
        logger.warning('Authorization header is missing')
        raise HTTPException(status_code=401, detail='Authorization header is missing')

    logger.info(f'Authorization header: {authorization}')

    try:
        token = authorization.split(" ")[1]
        user_info = verify_token(token)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=401, detail="Failed to Authorize")

    if user_info is None:
        logger.warning('Invalid token')
        raise HTTPException(status_code=403, detail='Invalid token')

    saved_audio_files = 'qaida_saved_audio'
    user_id = user_info.get('uid', 'unknown_user')
    if user_id:
        source_folder = os.path.join(saved_audio_files, user_id)
        destination_folder = "moved_audio_files"
        move_audio_files(source_folder, destination_folder)
        logger.info("Data Was moved Successfully")

        return JSONResponse(content={"status": "Data Deletion Scheduled", "status_code": 200})
    else:
        return JSONResponse(content={"status": "User ID not provided", "status_code": 400})

# Include routers
app.include_router(audio_prediction_router)
app.include_router(lesson_data_router)

if __name__ == "__main__":
    pass
