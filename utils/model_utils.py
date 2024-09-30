import os
import torch
from transformers import pipeline
from config import HUGGINGFACE_TOKEN
import logging
import gc

class ModelState:
    def __init__(self):
        self.current_pipe = None
        self.current_model_name = None

    def formatPrediction(self, predictions):
        sorted_predictions = sorted(predictions, key=lambda x: x['score'], reverse=True)
        top_predictions = sorted_predictions[:3]
        formatted_predictions = [{"label": pred["label"], "probability": pred["score"]} for pred in top_predictions]
        return formatted_predictions

    def unload_model(self):
        if self.current_pipe is not None:
            del self.current_pipe
            self.current_pipe = None
            self.current_model_name = None
            gc.collect()
            torch.cuda.empty_cache()
            logging.info("Unloaded the current model")

    def load_specific_model(self, model_name):
        if self.current_model_name != model_name:
            self.unload_model()

        os.environ["HUGGINGFACE_HUB_TOKEN"] = HUGGINGFACE_TOKEN
        token = os.getenv("HUGGINGFACE_HUB_TOKEN")
        if not token:
            logging.error("HuggingFace Hub token is not set")
            raise EnvironmentError("HuggingFace Hub token is not set")

        logging.info(f"Using HuggingFace Hub token: {token}")

        device = "cuda" if torch.cuda.is_available() else "cpu"

        try:
            if model_name == "lesson1":
                self.current_pipe = pipeline("audio-classification", model="haseeb-9d/qaida-lesson1-classification", device=device)
            elif model_name == "lesson2":
                self.current_pipe = pipeline("audio-classification", model="haseeb-9d/qaida-lesson2-classification", device=device)
            elif model_name == "lesson3":
                self.current_pipe = pipeline("audio-classification", model="haseeb-9d/qaida-lesson3-classification", device=device)
            elif model_name == "lesson5":
                self.current_pipe = pipeline("audio-classification", model="haseeb-9d/qaida-lesson5-classification", device=device)
            elif model_name == "lesson8_9":
                self.current_pipe = pipeline("audio-classification", model="haseeb-9d/Lesson8-9results", device=device)
            elif model_name == "lesson10":
                self.current_pipe = pipeline("audio-classification", model="haseeb-9d/qaida-lesson10-classification", device=device)
            elif model_name == "quran":
                self.current_pipe = pipeline("automatic-speech-recognition", model="haseeb-9d/Quran-ASR-Full", device=device)
            elif model_name == "parah30":
                self.current_pipe = pipeline("automatic-speech-recognition", model="haseeb-9d/Quran-Parah-30", device=device)
            elif model_name == "parah29":
                self.current_pipe = pipeline("automatic-speech-recognition", model="haseeb-9d/Quran-ASR-Parah-29", device=device)
            elif model_name == "parah01":
                self.current_pipe = pipeline("automatic-speech-recognition", model="haseeb-9d/Quran-ASR-Parah-01", device=device)
            else:
                raise ValueError(f"Unknown model name: {model_name}")

            self.current_model_name = model_name
            logging.info(f"Model {model_name} loaded successfully")
            return {"message": f"Model {model_name} loaded successfully"}
        except Exception as e:
            logging.error(f"Failed to load model {model_name}: {e}")
            raise EnvironmentError(f"Failed to load model {model_name}: {e}")

model_state = ModelState()

def get_model_state():
    return model_state