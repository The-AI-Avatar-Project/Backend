FROM python:3.9-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir openai-whisper fastapi uvicorn python-multipart torch triton

COPY entrypoint.py /

CMD ["uvicorn", "entrypoint:app", "--host", "0.0.0.0", "--port", "8080"]