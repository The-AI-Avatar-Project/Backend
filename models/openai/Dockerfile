FROM python:3.13.3-slim

RUN pip install --no-cache-dir fastapi openai uvicorn
COPY entrypoint.py /

CMD ["uvicorn", "entrypoint:app", "--host", "0.0.0.0", "--port", "8080"]