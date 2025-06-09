import os
import uuid
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from inference import Wav2LipInference
from fastapi.responses import StreamingResponse

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE = os.getcwd()                  
INPUT_DIR    = os.path.join(BASE, "input")
OUTPUT_DIR   = os.path.join(BASE, "output")
PROFILES_DIR = os.path.join(BASE, "profiles")
TRANSFER_DIR = os.path.join(BASE, "transfer")
FALLBACK_VIDEO = os.path.join(BASE, "fallback.mp4")

for d in (INPUT_DIR, OUTPUT_DIR, PROFILES_DIR):
    os.makedirs(d, exist_ok=True)

# Preload wav2lip into VRAM
model = Wav2LipInference("./checkpoints/wav2lip_gan.pth")


@app.post("/register/")
async def register_profile(
    professor: str = Form(...),
    default_video: UploadFile = File(...)
):
    if not professor.strip():
        raise HTTPException(status_code=400, detail="`professor` field must not be empty")

    user_dir = os.path.join(PROFILES_DIR, professor)
    os.makedirs(user_dir, exist_ok=True)

    ext        = default_video.filename.rsplit(".", 1)[-1]
    video_name = f"{professor}_default.{ext}"
    video_path = os.path.join(user_dir, video_name)
    with open(video_path, "wb") as f:
        f.write(await default_video.read())

    return {
        "message": "Profile registered",
        "profile": professor,
        "default_video": video_name
    }


class VideoGenerationRequest(BaseModel):
    audio_name: str
    professor_id: str

@app.post("/")
async def run_inference(request: VideoGenerationRequest):
    user_dir = os.path.join(PROFILES_DIR, request.professor_id)
    face_path = ""
    if os.path.isdir(user_dir):
        default_files = [f for f in os.listdir(user_dir) if f.startswith('wav2lip.')]
        if not default_files:
            print("Avatar not found. Using fallback video")
            face_path = FALLBACK_VIDEO
        face_path = os.path.join(user_dir, default_files[0])
    else:
        print("Avatar not found. Using fallback video")
        face_path = FALLBACK_VIDEO



    audio_path = os.path.join(TRANSFER_DIR, request.audio_name)

    try:
        stream = model.infer(
            face_path=face_path,
            audio_path=audio_path,
            professor=request.professor_id
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")

    return StreamingResponse(
        stream,
        media_type="video/mp4",
        headers={"Content-Disposition": "attachment; filename=result.mp4"}
    )
