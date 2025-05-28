from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from gtts import gTTS
import os
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TTSRequest(BaseModel):
    text: str

@app.post("/")
def respond(request: TTSRequest):
    tts = gTTS(request.text, lang="de")
    tts.save("text.mp3")
    with open("text.mp3", "rb") as f:
        file_bytes = f.read()

    return StreamingResponse(io.BytesIO(file_bytes), media_type="audio/mpeg3")