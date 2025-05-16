from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import io
from pydub import AudioSegment
from pydub.utils import make_chunks
from PIL import Image
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip
import os
from concurrent.futures import ThreadPoolExecutor

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

FRAME_RATE = 10 
THRESHOLD_DBFS = -35 
OUTPUT_VIDEO = "output_short.mp4"

def analyze_audio_chunks(audio, chunk_length_ms=100, threshold_dbfs=-35):
    chunks = make_chunks(audio, chunk_length_ms)
    result = []
    for chunk in chunks:
        loud = chunk.dBFS > threshold_dbfs
        result.append(loud)
    return result

def generate_image_sequence(image_open_path, image_closed_path, activity_flags):
    img_open = np.array(Image.open(image_open_path))
    img_closed = np.array(Image.open(image_closed_path))

    with ThreadPoolExecutor() as executor:
        image_sequence = list(executor.map(lambda flag: img_open if flag else img_closed, activity_flags))

    return image_sequence

def create_video_from_images(image_sequence, audio_path, frame_rate, output_path):
    audio = AudioFileClip(audio_path)
    clip = ImageSequenceClip(image_sequence, fps=frame_rate)
    clip = clip.set_audio(audio)

    clip.write_videofile(
    output_path,
    codec="libx264",
    audio_codec="aac",
    preset="ultrafast",         
    threads=os.cpu_count(),                  
)

@app.post("/")
def respond(file: UploadFile = File(...)):
    file_path = f"/tmp/{file.filename}"

    # Save the uploaded file
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    audio = AudioSegment.from_file(file_path).set_channels(1)
    activity = analyze_audio_chunks(audio, chunk_length_ms=1000 // FRAME_RATE, threshold_dbfs=THRESHOLD_DBFS)
    image_sequence = generate_image_sequence("mouth_open.png", "mouth_closed.png", activity)
    create_video_from_images(image_sequence, file_path, FRAME_RATE, OUTPUT_VIDEO)
    print(f"Video gespeichert unter: {OUTPUT_VIDEO}")

    with open(OUTPUT_VIDEO, "rb") as f:
        file_bytes = f.read()

    return StreamingResponse(io.BytesIO(file_bytes), media_type="video/mp4")
