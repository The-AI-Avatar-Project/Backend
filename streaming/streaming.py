import os
import time
import asyncio
from fastapi import FastAPI, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi import Response
from fastapi.middleware.cors import CORSMiddleware
import aiohttp

TTS_URL = "http://xtts:8000/tts_stream_to_file"
WAV2LIP_URL = "http://wav2lip:8000/inference"
CHUNKS_BASE = "/app/output/chunks"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_connections = {}

@app.post("/speak/")
async def speak(
    professor: str = Form(...),
    language: str = Form(...),
    text: str = Form(...)
):
    # Step 1: Request audio chunks via TTS
    async with aiohttp.ClientSession() as session:
        async with session.post(TTS_URL, json={
            "speaker_name": professor,
            "language": language,
            "text": text
        }) as tts_resp:
            if tts_resp.status != 200:
                detail = await tts_resp.text()
                raise HTTPException(status_code=tts_resp.status, detail=f"TTS failed: {detail}")
            tts_data = await tts_resp.json()
            uuid_ = tts_data["uuid"]

    chunk_dir = os.path.join(CHUNKS_BASE, uuid_)
    chunk_path = os.path.join(chunk_dir, "0001p.wav")

    # Step 2: Wait for first audio chunk
    timeout = 15
    start_time = time.time()
    while not os.path.exists(chunk_path):
        await asyncio.sleep(0.5)
        if time.time() - start_time > timeout:
            raise HTTPException(status_code=504, detail="Timeout waiting for first audio chunk.")

    # Step 3: Trigger Wav2Lip processing
    async with aiohttp.ClientSession() as session:
        form_data = aiohttp.FormData()
        form_data.add_field("professor", professor)
        form_data.add_field("uuid", uuid_)
        async with session.post(WAV2LIP_URL, data=form_data) as resp:
            if resp.status != 200:
                detail = await resp.text()
                raise HTTPException(status_code=resp.status, detail=f"Wav2Lip failed: {detail}")

    return JSONResponse({"uuid": uuid_})


@app.websocket("/ws/{uuid}")
async def websocket_playlist_updates(websocket: WebSocket, uuid: str):
    await websocket.accept()
    print(f"[ws] WebSocket connected for UUID: {uuid}", flush=True)

    if uuid not in active_connections:
        active_connections[uuid] = []
    active_connections[uuid].append(websocket)

    m3u8_path = os.path.join(CHUNKS_BASE, uuid, "hls", "playlist.m3u8")
    last_mtime = 0

    try:
        while True:
            if os.path.exists(m3u8_path):
                mtime = os.path.getmtime(m3u8_path)
                if mtime > last_mtime:
                    last_mtime = mtime
                    print(f"[ws] Playlist updated, sending 'update' to clients ({uuid})", flush=True)
                    await websocket.send_text("update")
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        print(f"[ws] WebSocket disconnected for UUID: {uuid}", flush=True)
        active_connections[uuid].remove(websocket)
    except Exception as e:
        print(f"[ws] WebSocket error for UUID {uuid}: {e}", flush=True)
        if websocket in active_connections.get(uuid, []):
            active_connections[uuid].remove(websocket)


@app.head("/stream/{uuid}/playlist.m3u8")
async def head_playlist(uuid: str):
    path = os.path.join(CHUNKS_BASE, uuid, "video", "playlist.m3u8")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Playlist not found")
    # Nur Header zurückgeben, kein Body
    file_stat = os.stat(path)
    headers = {
        "Content-Length": str(file_stat.st_size),
        "Content-Type": "application/vnd.apple.mpegurl",
    }
    return Response(status_code=200, headers=headers)

@app.get("/stream/{uuid}/playlist.m3u8")
async def get_playlist(uuid: str):
    path = os.path.join(CHUNKS_BASE, uuid, "video", "playlist.m3u8")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Playlist not found")
    return FileResponse(path, media_type="application/vnd.apple.mpegurl")

@app.get("/stream/{uuid}/{filename}")
async def get_segment(uuid: str, filename: str):
    path = os.path.join(CHUNKS_BASE, uuid, "video", filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Segment not found")
    return FileResponse(path, media_type="video/MP2T")

