import os
import uuid
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from inference import Wav2LipInference
from fastapi.responses import StreamingResponse
from fastapi.responses import JSONResponse
import logging
from fastapi.routing import APIRoute
import inspect
print("🚀 Wav2Lip API gestartet – api.py wurde erfolgreich geladen")
print(f"📂 Läuft aus Datei: {inspect.getfile(inspect.currentframe())}")
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

for d in (INPUT_DIR, OUTPUT_DIR, PROFILES_DIR):
    os.makedirs(d, exist_ok=True)

# Preload wav2lip into VRAM
model = Wav2LipInference("./checkpoints/wav2lip_gan.pth")

@app.on_event("startup")
def show_routes():
    logging.info("🔍 Verfügbare API-Routen:")
    for route in app.routes:
        if isinstance(route, APIRoute):
            logging.info(f"🔁 {route.path}  [{', '.join(route.methods)}]")


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


from fastapi.responses import StreamingResponse

@app.post("/inference")
async def run_inference(professor: str = Form(...), uuid: str = Form(...)):
    profile_dir = f"/app/profiles/{professor}"
    chunk_dir = f"/app/output/chunks/{uuid}"

    if not os.path.isdir(profile_dir):
        raise HTTPException(status_code=500, detail="Profile not found")
    if not os.path.isdir(chunk_dir) or not os.path.isfile(os.path.join(chunk_dir, "0001p.wav")):
        raise HTTPException(status_code=500, detail="Audio chunks not found")

    default_file = next((f for f in os.listdir(profile_dir) if f.startswith(f"face.")), None)
    if not default_file:
        raise HTTPException(status_code=500, detail="No default video or reference image found")

    video_path = os.path.join(profile_dir, default_file)
    static = default_file.lower().endswith((".png", ".jpg", ".jpeg"))

    try:
        # Nur die infer-Methode aufrufen, sie startet asynchron die Verarbeitung im chunk_dir
        session_id = model.infer(face_path=video_path, chunk_dir=chunk_dir,
                         professor=professor, static=static)
        return JSONResponse({"uuid": session_id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {e}")

    