from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from TTS.api import TTS
import os
import uuid
import shutil
import torch

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = "profiles"
FALLBACK_VOICE = "/app/fallback.mp3"
TRANSFER_DIR = "transfer"
os.makedirs(BASE_DIR, exist_ok=True)


device = "cuda" if torch.cuda.is_available() else "cpu"
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

class AudioGenerationRequest(BaseModel):
    id: str
    language: str
    text: str

@app.post("/")
async def speak(request: AudioGenerationRequest = Body(...)):
    user_dir = os.path.join(BASE_DIR, request.id)
    voice_path = os.path.join(user_dir, "voice.mp3")

    if not os.path.isfile(voice_path):
        print("Voice " + request.id + " does not exist. Using fallback voice")
        os.makedirs(user_dir, exist_ok=True)
        voice_path = FALLBACK_VOICE

    output_file_name = f"spoken_{uuid.uuid4().hex}.wav"
    output_path = os.path.join(TRANSFER_DIR, output_file_name)

    try:
        tts.tts_to_file(
            text=request.text,
            file_path=output_path,
            speaker_wav=voice_path,
            language=request.language
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {e}")

    return output_file_name
