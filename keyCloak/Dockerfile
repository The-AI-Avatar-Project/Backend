FROM python:3.11-slim

COPY realm-setup.json /app/realm-setup.json
COPY user-setup.json /app/user-setup.json
COPY room-setup.json /app/room-setup.json
COPY setup-keycloak-realm.py /app/setup-keycloak-realm.py

RUN pip install --no-cache-dir requests

ENTRYPOINT ["python", "/app/setup-keycloak-realm.py"]
