import io
import os
import shutil
import librosa
import soundfile as sf
from utils.database import insert_lesson_data
from utils.app_logger import logger


async def save_audio_file(save_dir, unique_name, audio_bytes, move=False, original_path=None):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    file_path = os.path.join(save_dir, unique_name)

    with open(file_path, "wb") as f:
        f.write(audio_bytes)

    if move and original_path:
        os.rename(original_path, file_path)

    return file_path

async def quran_audio_file(file_path: str, audio_bytes, surah_no: int, ayah_no: int):
    try:
        # Load the audio file with librosa to resample at 32000 Hz
        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=32000)

        # Save the resampled audio using soundfile
        sf.write(file_path, audio, sr)

        # Insert lesson data into the database
        await insert_lesson_data(surah_no, ayah_no, file_path, 0, False)
    except Exception as e:
        logger.error(f'Error processing the audio file: {e}')

def move_audio_files(source_folder: str, destination_folder: str):
    try:
        # Ensure the destination directory exists
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)

        # Check if the source folder exists
        if os.path.exists(source_folder):
            # Move the folder
            shutil.move(source_folder, os.path.join(destination_folder, os.path.basename(source_folder)))
    except Exception as e:
        logger.error(f'Error moving audio files: {e}')