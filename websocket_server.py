import asyncio
import io
import json
import logging
from logging.handlers import RotatingFileHandler
import os
import wave
import numpy as np
import websockets
from huggingface_hub import login
from utils.ai_models import ai_models
from datetime import datetime
import pytz

login("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")

# Configure logging
if not os.path.exists('logs'):
    os.mkdir('logs')

# Define a custom formatter that includes Pakistan Standard Time
class PKTFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, pytz.timezone('Asia/Karachi'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')

# Create a RotatingFileHandler
file_handler = RotatingFileHandler('logs/websocket_logs.log', maxBytes=10240)
file_handler.setFormatter(PKTFormatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
file_handler.setLevel(logging.INFO)

# Configure the root logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(file_handler)

logger.info('Websocket startup')

connected_clients = set()

def convert_pcm_to_wav(pcm_data, sample_rate=16000, num_channels=1, sample_width=2):
    with io.BytesIO() as wav_file:
        with wave.open(wav_file, 'wb') as wav_writer:
            wav_writer.setnchannels(num_channels)
            wav_writer.setsampwidth(sample_width)
            wav_writer.setframerate(sample_rate)
            wav_writer.writeframes(pcm_data)
        wav_file.seek(0)
        return wav_file.read()
    

def read_wav_from_bytes(audio_bytes):
    with wave.open(io.BytesIO(audio_bytes), 'rb') as wav_file:
        num_channels = wav_file.getnchannels()
        num_frames = wav_file.getnframes()

        audio_data = wav_file.readframes(num_frames)
        audio_array = np.frombuffer(audio_data, dtype=np.int16)

        if num_channels == 2:
            audio_array = audio_array.reshape(-1, 2).mean(axis=1)

        return audio_array
    

async def handle_client(websocket, path):
    if path != "/ws":
        await websocket.close()
        return

    connected_clients.add(websocket)
    logger.info(f"Client connected: {websocket.remote_address}")

    try:
        async for message in websocket:
            logger.info(f"Received message from {websocket.remote_address}")

            if isinstance(message, bytes):
                logger.info(f"Received audio chunk of size: {len(message)} bytes")

                # Convert raw PCM data to WAV format
                wav_data = convert_pcm_to_wav(message)

                # Read WAV data into a NumPy array
                audio_data = read_wav_from_bytes(wav_data)

                # Process the audio data with the ASR pipeline
                response = ai_models["quran"](audio_data)

                logger.warning(f"Transcription response {response}")

                # Convert the response to a JSON string
                response_json = json.dumps(response)

                await websocket.send(response_json)
            else:
                await websocket.send("Received non-binary message")

    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Client {websocket.remote_address} disconnected: {e}")
    finally:
        # Unregister the client
        connected_clients.remove(websocket)
        logger.info(f"Client disconnected: {websocket.remote_address}")

async def server():
    server = await websockets.serve(handle_client, "69.197.145.4", 5000, max_size=2**24)
    logger.info("WebSocket server started on ws://69.197.145.4:5000")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(server())
