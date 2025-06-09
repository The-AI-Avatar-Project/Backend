# Wav2Lip API Setup

Diese Anleitung beschreibt, wie du das Wav2Lip-Projekt klonst, die benötigten Modellgewichte herunterlädst und die API mittels Docker Compose startest.

## 1. Repository klonen

Wechsle in das Verzeichnis, in dem du das Projekt ablegen möchtest, und führe folgenden Befehl aus:

```bash
git clone https://github.com/Rudrabha/Wav2Lip.git
```

## 2. Modellgewichte herunterladen

### 2.1 Wav2Lip GAN-Gewichte

Lade die Datei `wav2lip_gan.pth` von Hugging Face herunter:

- URL: https://huggingface.co/Nekochu/Wav2Lip/tree/main

Speichere die Datei anschließend im Ordner `Wav2Lip/checkpoints`:


### 2.2 S3FD Face Detection Modell

Lade das S3FD-Gewicht für die Gesichtserkennung herunter:

- URL: https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth

Speichere die Datei als `s3fd.pth` im Verzeichnis `Wav2Lip/face_detection/detection/sfd`:


## 3. API mit Docker Compose starten

Baue das Docker-Image und starte die Container:

```bash
docker-compose up --build
```

> Hinweis: Der erste Build kann einige Minuten dauern, da alle Abhängigkeiten installiert werden.

## 4. Endpunkte nutzen

Nach erfolgreichem Start sind folgende Endpunkte verfügbar unter `http://localhost:8000`:

- **POST** `/register`
  - Beschreibung: Upload einer neuen Default-Datei (Video oder Bild) für einen Profilnamen.
  - Felder:
    - `professor` (Form-Field): Profilname als Text.
    - `default_video` (File-Upload): Video- oder Bilddatei.
  - Beispiel mit `curl`:

    ```bash
    curl -X POST http://localhost:8000/register \
         -F "professor=mustermann" \
         -F "default_video=@/pfad/zur/datei.mp4"
    ```

- **POST** `/inference`
  - Beschreibung: Führt Wav2Lip-Inferenz für einen hinterlegten Avatar und eine übermittelte Audiodatei durch.
  - Felder:
    - `professor` (Form-Field): Profilname (muss zuvor mit `/register` angelegt worden sein).
    - `audio` (File-Upload): Audiodatei (z. B. `.wav` oder `.mp3`).
  - Beispiel mit `curl`:

    ```bash
    curl -X POST http://localhost:8000/inference \
         -F "professor=mustermann" \
         -F "audio=@/pfad/zur/audio.wav" \
         --output result.mp4
    ```