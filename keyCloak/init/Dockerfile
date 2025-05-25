FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY ai-avatar-realm.json /app/ai-avatar-realm.json
COPY setup-keycloak-realm.py /app/setup-keycloak-realm.py
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

ENTRYPOINT ["python", "/app/setup-keycloak-realm.py"]
