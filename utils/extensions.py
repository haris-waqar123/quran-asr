from flask import abort, request
from config import API_KEY

ACCESS_TOKEN_EXPIRE_MINUTES = 30

def to_milli(time: int):
    milli_seconds = time * 1000
    return milli_seconds

def verify_api_key():
    x_api_key = request.headers.get("API-Key")
    if x_api_key != API_KEY:
        abort(403, description="Invalid API Key")
    return x_api_key