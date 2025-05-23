FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir fastapi uvicorn[standard] pydub pillow moviepy==1.0.3 numpy python-multipart

COPY * /
COPY audio.mp3 /root/share/audio.mp3

CMD ["uvicorn", "entrypoint:app", "--host", "0.0.0.0", "--port", "8080"]