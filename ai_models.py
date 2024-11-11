import torch
from transformers import pipeline


device = "cuda" if torch.cuda.is_available() else "cpu"
ai_models = {
    "lesson1": pipeline("audio-classification", model="haris-waqar/qaida-lesson1-classification", device=device),
    "lesson2": pipeline("audio-classification", model="haris-waqar/qaida-lesson2-classification", device=device),
    "lesson3": pipeline("audio-classification", model="haris-waqar/qaida-lesson3-classification", device=device),
    "lesson4": pipeline("audio-classification", model="haris-waqar/qaida-lesson4-classification", device=device),
    "lesson5": pipeline("audio-classification", model="haris-waqar/qaida-lesson5-classification", device=device),
    "lesson6": pipeline("audio-classification", model="haris-waqar/qaida-Lesson6-classification", device=device),
    "lesson7": pipeline("audio-classification", model="haris-waqar/qaida-Lesson7-classification", device=device),
    "lesson8_9": pipeline("audio-classification", model="haris-waqar/New-Lesson8-9results", device=device),
    "lesson10": pipeline("audio-classification", model="haris-waqar/qaida-lesson10-classification", device=device),
    "quran": pipeline("automatic-speech-recognition", model="haris-waqar/quran-asr-30-sec", device=device)
}