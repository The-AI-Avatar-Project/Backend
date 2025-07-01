FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3 python3-pip git curl wget ffmpeg libsndfile1 \
    portaudio19-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
RUN pip install TTS==0.22.0 \
    transformers==4.36.2 \
    fastapi uvicorn python-multipart aiofiles soundfile tqdm packaging loguru requests \
    pydub pyaudio

WORKDIR /app

RUN git clone https://github.com/daswer123/xtts-api-server.git /app/xtts_api_server

ENV PYTHONPATH="${PYTHONPATH}:/app/xtts_api_server"

COPY server.py /app/server.py

RUN pip install stream2sentence

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
