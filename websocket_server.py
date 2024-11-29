import asyncio
import io
import json
import logging
from logging.handlers import RotatingFileHandler
import os
import wave
import numpy as np
import torch
import websockets
from transformers import pipeline

from huggingface_hub import login

login("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")

# Configure logging
if not os.path.exists('logs'):
    os.mkdir('logs')

file_handler = RotatingFileHandler('logs/websocket_logs.log', maxBytes=10240)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(file_handler)

logger.info('Websocket startup')

connected_clients = set()

device = "cuda" if torch.cuda.is_available() else "cpu"
asr_pipeline = pipeline("automatic-speech-recognition", model="haris-waqar/quran-asr-30-sec", device=device)


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
        sample_rate = wav_file.getframerate()
        num_channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        num_frames = wav_file.getnframes()

        audio_data = wav_file.readframes(num_frames)
        audio_array = np.frombuffer(audio_data, dtype=np.int16)

        if num_channels == 2:
            audio_array = audio_array.reshape(-1, 2).mean(axis=1)

        return audio_array, sample_rate
    

async def handle_client(websocket, path):
    if path != "/ws":
        await websocket.close()
        return

    # Register the client
    # chunk_counter = 0
    # resampled_audio_folder = 'websocket_resampled_audio_chunks'
    # if not os.path.exists(resampled_audio_folder):
    #     os.makedirs(resampled_audio_folder)

    connected_clients.add(websocket)
    logger.info(f"Client connected: {websocket.remote_address}")

    try:
        async for message in websocket:
            # logger.info(f"Received message from {websocket.remote_address}: {message}")

            if isinstance(message, bytes):
                logger.info(f"Received audio chunk of size: {len(message)} bytes")

                # Convert raw PCM data to WAV format
                wav_data = convert_pcm_to_wav(message)

                # audio_path = os.path.join(resampled_audio_folder, f"chunk_{chunk_counter}.wav")
                # with open(audio_path, "wb") as f:
                #     f.write(wav_data)

                # Read WAV data into a NumPy array
                audio_data, sample_rate = read_wav_from_bytes(wav_data)

                # Process the audio data with the ASR pipeline
                response = asr_pipeline(audio_data)

                logger.warning(f"Transcription response {response}")

                # Convert the response to a JSON string
                response_json = json.dumps(response)

                # chunk_counter += 1

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
