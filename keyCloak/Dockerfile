FROM python:3.11-slim

COPY ai-avatar-realm.json /app/ai-avatar-realm.json
COPY setup-keycloak-realm.py /app/setup-keycloak-realm.py

RUN pip install --no-cache-dir requests

ENTRYPOINT ["python", "/app/setup-keycloak-realm.py"]
