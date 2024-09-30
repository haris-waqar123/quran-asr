import os
from config import AUDIO_FILES_DIRECTORY

def ensure_audio_directory():
    if not os.path.exists(AUDIO_FILES_DIRECTORY):
        os.makedirs(AUDIO_FILES_DIRECTORY)

def save_audio_file(save_dir, unique_name, audio_bytes, move=False, original_path=None):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    file_path = os.path.join(save_dir, unique_name)

    with open(file_path, "wb") as f:
        f.write(audio_bytes)

    if move and original_path:
        os.rename(original_path, file_path)

    return file_path
