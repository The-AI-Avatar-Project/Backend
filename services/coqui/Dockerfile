FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

RUN apt-get update &&  \
    apt-get install -y python3 python3-pip && \
    apt-get clean &&  \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir torch  \
        torchvision  \
        torchaudio  \
        --index-url https://download.pytorch.org/whl/cu121 && \
    pip install --no-cache-dir aiofiles \
        fastapi \
        numpy \
        python-multipart  \
        soundfile  \
        transformers==4.36.2  \
        TTS==0.22.0  \
        uvicorn


WORKDIR /app
COPY entrypoint.py .
COPY audio.mp3 /app/fallback.mp3

CMD ["uvicorn", "entrypoint:app", "--host", "0.0.0.0", "--port", "8080"]
