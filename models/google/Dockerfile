FROM python:3.9-slim

RUN pip install --no-cache-dir fastapi gTTS uvicorn[standard]

COPY entrypoint.py /

CMD ["uvicorn", "entrypoint:app", "--host", "0.0.0.0", "--port", "8080"]