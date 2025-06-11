FROM python:3.11-slim

RUN apt-get update &&  \
    apt-get install -y ffmpeg &&  \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir fastapi \
      moviepy==1.0.3 \
      numpy \
      pillow \
      pydub \
      python-multipart \
      uvicorn[standard]

COPY * /

CMD ["uvicorn", "entrypoint:app", "--host", "0.0.0.0", "--port", "8080"]