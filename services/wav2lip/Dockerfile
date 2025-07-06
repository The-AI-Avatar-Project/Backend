FROM nvidia/cuda:11.1.1-cudnn8-runtime-ubuntu20.04


ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/opt/conda/bin:$PATH" \
    LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu:/opt/conda/lib:$LD_LIBRARY_PATH"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      wget curl git ffmpeg \
      libglib2.0-0 libxrender1 libsm6 libxext6 \
      bzip2 ca-certificates build-essential && \
    rm -rf /var/lib/apt/lists/* && \
    wget https://repo.anaconda.com/miniconda/Miniconda3-4.7.12.1-Linux-x86_64.sh -O miniconda.sh && \
    bash miniconda.sh -b -p /opt/conda && \
    rm miniconda.sh && \
    conda install -y python=3.6 && \
    conda clean -ya

RUN git clone https://github.com/Rudrabha/Wav2Lip.git /app/Wav2Lip
ADD https://huggingface.co/Nekochu/Wav2Lip/resolve/main/wav2lip_gan.pth /app/Wav2Lip/checkpoints/wav2lip_gan.pth
ADD https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth /app/Wav2Lip/face_detection/detection/sfd/s3fd.pth

WORKDIR /app/Wav2Lip
COPY requirements.txt /app/requirements.txt


RUN conda install -y -c conda-forge opencv=4.5.1 && \
    conda clean -ya

RUN sed -i '/^torch/d;/^torchvision/d;/^torchaudio/d;/^opencv/d' /app/requirements.txt && \
    pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
      torch==1.8.2 torchvision==0.9.2 torchaudio==0.8.2 \
      --extra-index-url https://download.pytorch.org/whl/lts/1.8/cu111 && \
    pip install --no-cache-dir \
      fastapi uvicorn python-multipart && \
    pip install --no-cache-dir -r /app/requirements.txt



RUN apt-get update && \
    apt-get install -y locales && \
    locale-gen de_DE.UTF-8 && \
    update-locale LANG=de_DE.UTF-8

ENV LANG=de_DE.UTF-8 \
    LANGUAGE=de_DE:de \
    LC_ALL=de_DE.UTF-8

COPY inference.py /app/Wav2Lip 
COPY api.py /app/Wav2Lip
COPY fallback.mp4 /app/Wav2Lip

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]