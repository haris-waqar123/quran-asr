from flask import Blueprint, request, jsonify
from pydantic import BaseModel
from models.audio_model import LessonType
# from utils.extensions import receive_rtmp_stream
from utils.model_utils import get_model_state
from utils.file_utils import save_audio_file
from utils.jwt_utils import get_current_user
import librosa
import io

router = Blueprint('audio_prediction', __name__)

class AudioData(BaseModel):
    label: str = None

@router.route("/qaida/<model_type>", methods=["POST"])
def predict_lesson_audio(model_type):
    # Verify API key

    state = get_model_state()
    current_user = get_current_user()

    print(f"current_user {current_user}")

    if not current_user:
        return jsonify({"detail": "Invalid API key"}), 401

    if state.current_model_name != model_type:
        try:
            state.load_specific_model(model_type)
        except Exception as e:
            return jsonify({"detail": f"Model {model_type} is not loaded. Please load the model first."}), 400

    # Check if the file is included in the request
    if 'file' not in request.files:
        return jsonify({"detail": "No file part"}), 400

    audio_data = AudioData(label=request.form.get('label'))
    audio_file = request.files['file']

    # Check if the file is empty
    if audio_file.filename == '':
        return jsonify({"detail": "No selected file"}), 400

    audio_bytes = audio_file.read()
    audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)
    audio = librosa.to_mono(audio)

    if model_type in LessonType.__members__.values():
        base_dir = f"saved_audio_files/{model_type}"
        save_dir = f"{base_dir}/{audio_data.label}" if audio_data.label else base_dir
        unique_name = f"{request.form.get('new_name')}.wav"
        save_audio_file(save_dir, unique_name, audio_bytes)

        predictions = state.current_pipe(audio)
        formatted_predictions = state.formatPrediction(predictions)
        
        return jsonify(formatted_predictions)
    else:
        return jsonify({"detail": "Invalid model type"}), 400
