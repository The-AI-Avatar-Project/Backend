FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# Basis-Update
RUN apt-get update

# Einzelne Pakete installieren
RUN apt-get install -y --no-install-recommends software-properties-common
RUN apt-get install -y --no-install-recommends ca-certificates
RUN apt-get install -y --no-install-recommends gnupg
RUN apt-get install -y --no-install-recommends apt-transport-https
RUN add-apt-repository -y universe

RUN apt-get update

RUN apt-get install -y --no-install-recommends python3
RUN apt-get install -y --no-install-recommends python3-pip
RUN apt-get install -y --no-install-recommends git
RUN apt-get install -y --no-install-recommends curl
RUN apt-get install -y --no-install-recommends wget
RUN apt-get install -y --no-install-recommends ffmpeg
RUN apt-get install -y --no-install-recommends libsndfile1
RUN apt-get install -y --no-install-recommends portaudio19-dev

# pip Pakete
RUN pip install --upgrade pip
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
RUN pip install --ignore-installed blinker
RUN pip install TTS==0.22.0
RUN pip install transformers==4.36.2
RUN pip install fastapi uvicorn python-multipart aiofiles soundfile tqdm packaging loguru requests
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential python3-dev portaudio19-dev \
 && rm -rf /var/lib/apt/lists/*
RUN pip install pydub pyaudio
RUN pip install stream2sentence

WORKDIR /app

RUN git clone https://github.com/daswer123/xtts-api-server.git /app/xtts_api_server
ENV PYTHONPATH="${PYTHONPATH}:/app/xtts_api_server"

COPY server.py /app/server.py

EXPOSE 8000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
