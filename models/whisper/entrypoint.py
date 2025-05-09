from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import whisper
import os
import torch

MODEL_DIR = "models"
MODEL_NAME = "small"
MODEL_PATH = os.path.join(MODEL_DIR, f"{MODEL_NAME}.pt")  # Save as .pt file

os.makedirs(MODEL_DIR, exist_ok=True)

def download_and_save_model():
    """Download Whisper model and save the weights."""
    print(f"Downloading and saving model to {MODEL_PATH}...")
    model = whisper.load_model(MODEL_NAME)
    torch.save(model.state_dict(), MODEL_PATH)  # Save state_dict instead of full model
    return model

def load_whisper_model():
    """Load Whisper model from local storage or download if not found."""
    if os.path.exists(MODEL_PATH):
        print(f"Loading model from {MODEL_PATH}...")
        model = whisper.load_model(MODEL_NAME)  # Load new model instance
        model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu", weights_only=False))  # Load weights
    else:
        model = download_and_save_model()
    return model

model = load_whisper_model()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/")
async def transcribe_audio(file: UploadFile = File(...)):
    file_path = f"/tmp/{file.filename}"

    # Save the uploaded file
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    # Transcribe the audio
    result = model.transcribe(file_path)

    # Delete file after processing
    os.remove(file_path)

    return {"transcription": result["text"]}