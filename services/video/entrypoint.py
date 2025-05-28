from fastapi import FastAPI, File, UploadFile, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import io
import time
from pydub import AudioSegment
from pydub.utils import make_chunks
from PIL import Image
import numpy as np
import os
from concurrent.futures import ThreadPoolExecutor
import subprocess
from typing import Iterator
import threading

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
SHARE_FOLDER = "/root/share/"
TMP_FOLDER = "/tmp/"

def analyze_audio_chunks(audio, chunk_length_ms=100, threshold_dbfs=-35):
    chunks = make_chunks(audio, chunk_length_ms)
    result = []
    for chunk in chunks:
        loud = chunk.dBFS > threshold_dbfs
        result.append(loud)
    return result

def image_sequence_generator(image_open_path, image_closed_path, activity_flags):
    img_open = np.array(Image.open(image_open_path))
    img_closed = np.array(Image.open(image_closed_path))
    
    for flag in activity_flags:
        image = img_open if flag else img_closed
        yield image

def stream_video_generator(activity_flags, audio_path, image_open_path, image_closed_path):
    # Start FFmpeg with stdin (pipe) for images and audio file
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-f", "image2pipe",
        "-r", str(FRAME_RATE),
        "-i", "-",  # input from stdin
        "-i", audio_path,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-c:a", "aac",
        "-f", "mp4",
        "-movflags", "frag_keyframe+empty_moov+default_base_moof",
        "-hide_banner", "-loglevel", "panic",
        "pipe:1"
    ]

    process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def feed_frames():
        for image in image_sequence_generator(image_open_path, image_closed_path, activity_flags):
            img_bytes = Image.fromarray(image).convert("RGB")
            buffer = io.BytesIO()
            img_bytes.save(buffer, format="JPEG")
            process.stdin.write(buffer.getvalue())
        process.stdin.close()

    threading.Thread(target=feed_frames).start()

    def generate_output():
        while True:
            chunk = process.stdout.read(1024)
            if not chunk:
                break
            yield chunk

    return generate_output()

class VideoGenerationRequest(BaseModel):
    file_name: str

@app.post("/", response_class=StreamingResponse)
def respond(request: VideoGenerationRequest = Body(...)):
    audio = AudioSegment.from_file(SHARE_FOLDER + request.file_name).set_channels(1)
    activity = analyze_audio_chunks(audio, chunk_length_ms=1000 // FRAME_RATE, threshold_dbfs=THRESHOLD_DBFS)
    return StreamingResponse(
        stream_video_generator(
            activity,
            SHARE_FOLDER + request.file_name,
            "mouth_open.png",
            "mouth_closed.png"
        ),
        media_type="video/mp4",
        headers={"Content-Disposition": f"attachment; filename={request.file_name}.mp4"},
    )