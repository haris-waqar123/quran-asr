import os
import torch
from transformers import pipeline
from config import HUGGINGFACE_TOKEN
import logging
import random
import gc

# device = "cuda" if torch.cuda.is_available() else "cpu"
    
# pipe1 = pipeline("audio-classification", model="haris-waqar/qaida-lesson1-classification", device=device)
# pipe2 = pipeline("audio-classification", model="haris-waqar/qaida-lesson2-classification", device=device)
# pipe3 = pipeline("audio-classification", model="haris-waqar/qaida-lesson3-classification", device=device)
# pipe4 = pipeline("audio-classification", model="haris-waqar/qaida-lesson4-classification", device=device)
# pipe5 = pipeline("audio-classification", model="haris-waqar/qaida-lesson5-classification", device=device)
# pipe6 = pipeline("audio-classification", model="haris-waqar/qaida-Lesson6-classification", device=device)
# pipe7 = pipeline("audio-classification", model="haris-waqar/qaida-Lesson7-classification", device=device)
# pipe8_9 = pipeline("audio-classification", model="haris-waqar/New-Lesson8-9results", device=device)
# pipe10 = pipeline("audio-classification", model="haris-waqar/qaida-lesson10-classification", device=device)
# pipeQ = pipeline("automatic-speech-recognition", model="haris-waqar/quran-asr-30-sec", device=device)

class ModelState:
    def __init__(self):
        self.current_pipe = None
        self.current_model_name = None

    def formatPrediction(self, predictions):
        # Ensure predictions are sorted in descending order of score
        sorted_predictions = sorted(predictions, key=lambda x: x['score'], reverse=True)

        # Adjust probabilities
        adjusted_predictions = self.adjust_probabilities(sorted_predictions)

        # Select the top 3 predictions
        top_predictions = adjusted_predictions[:3]

        # Format the top predictions
        formatted_predictions = [{"label": pred["label"], "probability": pred["probability"]} for pred in top_predictions]

        return formatted_predictions

    def adjust_probabilities(self, predictions):
        """
        Adjusts probabilities so that the highest probability remains as it is,
        and the rest are randomly scaled between 0.30 and 0.50.
        """
        # Ensure predictions are sorted in descending order of score
        sorted_predictions = sorted(predictions, key=lambda x: x['score'], reverse=True)

        # Keep the first probability as it is
        top_probability = sorted_predictions[0]['score']

        # Create adjusted predictions list with top probability unchanged
        adjusted_predictions = [{"label": sorted_predictions[0]["label"], "probability": top_probability}]

        # Set the probabilities for the second and third predictions randomly within the range [0.30, 0.50]
        for pred in sorted_predictions[1:3]:  # Only adjust the next two predictions
            adjusted_probability = random.uniform(0.30, 0.50)
            adjusted_predictions.append({"label": pred["label"], "probability": adjusted_probability})

        # Add remaining predictions with probabilities unchanged if any are left
        for pred in sorted_predictions[3:]:
            adjusted_predictions.append({"label": pred["label"], "probability": pred["score"]})

        return adjusted_predictions

    # def load_specific_model(self, model_name):
    #     os.environ["HUGGINGFACE_HUB_TOKEN"] = HUGGINGFACE_TOKEN
    #     token = os.getenv("HUGGINGFACE_HUB_TOKEN")
    #     if not token:
    #         logging.error("HuggingFace Hub token is not set")
    #         raise EnvironmentError("HuggingFace Hub token is not set")

    #     logging.info(f"Using HuggingFace Hub token: {token}")

    #     device = "cuda" if torch.cuda.is_available() else "cpu"
    #     logging.info(f"Device for Computing audio {device}")

    #     try:
    #         if model_name == "lesson1":
    #             self.current_pipe = pipeline("audio-classification", model="haris-waqar/qaida-lesson1-classification", device=device)
    #         elif model_name == "lesson2":
    #             self.current_pipe = pipeline("audio-classification", model="haris-waqar/qaida-lesson2-classification", device=device)
    #         elif model_name == "lesson3":
    #             self.current_pipe = pipeline("audio-classification", model="haris-waqar/qaida-lesson3-classification", device=device)
    #         elif model_name == "lesson4":
    #             self.current_pipe = pipeline("audio-classification", model="haris-waqar/qaida-lesson4-classification", device=device)
    #         elif model_name == "lesson5":
    #             self.current_pipe = pipeline("audio-classification", model="haris-waqar/qaida-lesson5-classification", device=device)
    #         elif model_name == "lesson6":
    #             self.current_pipe = pipeline("audio-classification", model="haris-waqar/qaida-Lesson6-classification", device=device)
    #         elif model_name == "lesson7":
    #             self.current_pipe = pipeline("audio-classification", model="haris-waqar/qaida-Lesson7-classification", device=device)
    #         elif model_name == "lesson8_9":
    #             self.current_pipe = pipeline("audio-classification", model="haris-waqar/New-Lesson8-9results", device=device)
    #         elif model_name == "lesson10":
    #             self.current_pipe = pipeline("audio-classification", model="haris-waqar/qaida-lesson10-classification", device=device)
    #         elif model_name == "quran":
    #             self.current_pipe = pipeline("automatic-speech-recognition", model="haris-waqar/quran-asr-30-sec", device=device)
    #         else:
    #             raise ValueError(f"Unknown model name: {model_name}")

    #         self.current_model_name = model_name
    #         logging.info(f"Model {model_name} loaded successfully")
    #         return {"message": f"Model {model_name} loaded successfully"}
    #     except Exception as e:
    #         logging.error(f"Failed to load model {model_name}: {e}")
    #         raise EnvironmentError(f"Failed to load model {model_name}: {e}")

model_state = ModelState()

def get_model_state():
    return model_state