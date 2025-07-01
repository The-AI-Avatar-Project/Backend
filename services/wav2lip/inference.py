from os import listdir, path
import numpy as np
import scipy, cv2, os, sys, argparse, audio
import json, subprocess, random, string
from tqdm import tqdm
from glob import glob
import torch, face_detection
from models import Wav2Lip
import platform
import threading
from fastapi.responses import StreamingResponse
import multiprocessing
import time
import uuid
import os
import cv2
import numpy as np
import time
import torch
import threading
from queue import Queue
from audio import load_wav, melspectrogram
import soundfile as sf
import subprocess
import tempfile
import shutil
import librosa


class Wav2LipInference:
    def __init__(self, checkpoint_path, img_size=96):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.img_size = img_size
        self.model = self._load_model(checkpoint_path)
        print("cuda available?", torch.cuda.is_available())
        print("current device:", self.device)
        print("GPU name:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "n/a")
        print(f'Model preloaded and ready on {self.device}')

    def _load_model(self, path):
        model = Wav2Lip()
        checkpoint = torch.load(path, map_location=self.device)
        state_dict = checkpoint["state_dict"]
        model.load_state_dict({k.replace("module.", ""): v for k, v in state_dict.items()})
        return model.to(self.device).eval()

    def _get_smoothened_boxes(self, boxes, T=5):
        for i in range(len(boxes)):
            window = boxes[max(0, i - T + 1):i + 1]
            boxes[i] = np.mean(window, axis=0)
        return boxes

    def _face_detect(self, images, pads, nosmooth):
        detector = face_detection.FaceAlignment(face_detection.LandmarksType._2D, flip_input=False, device='cpu')
        predictions = [None] * len(images)
        DETECT_EVERY = 10

        for i in tqdm(range(0, len(images), DETECT_EVERY)):
            pred = detector.get_detections_for_batch(np.array([images[i]]))[0]
            if pred is None:
                raise ValueError(f'Face not detected at frame {i}!')
            predictions[i] = pred

        last_known = None
        for i in range(len(images)):
            if predictions[i] is not None:
                last_known = predictions[i]
            else:
                predictions[i] = last_known

        pady1, pady2, padx1, padx2 = pads
        boxes = []
        for rect, image in zip(predictions, images):
            y1 = max(0, rect[1] - pady1)
            y2 = min(image.shape[0], rect[3] + pady2)
            x1 = max(0, rect[0] - padx1)
            x2 = min(image.shape[1], rect[2] + padx2)
            boxes.append([x1, y1, x2, y2])

        boxes = np.array(boxes)
        if not nosmooth:
            boxes = self._get_smoothened_boxes(boxes)

        results = [[image[y1:y2, x1:x2], (y1, y2, x1, x2)] for image, (x1, y1, x2, y2) in zip(images, boxes)]
        del detector
        return results

    def _prepare_batches(self, img_batch, mel_batch, frame_batch, coords_batch):
        img_batch = np.asarray(img_batch)
        mel_batch = np.asarray(mel_batch)

        img_masked = img_batch.copy()
        img_masked[:, self.img_size // 2:] = 0

        img_batch = np.concatenate((img_masked, img_batch), axis=3) / 255.
        mel_batch = np.reshape(mel_batch, [len(mel_batch), mel_batch.shape[1], mel_batch.shape[2], 1])

        return img_batch, mel_batch, frame_batch, coords_batch

    def _live_datagen(self, frames, mel_stream, args, face_det_results):
        for filename, mels in mel_stream:
            img_batch, mel_batch, frame_batch, coords_batch = [], [], [], []
            for i, mel in enumerate(mels):
                idx = 0 if args["static"] else i % len(frames)
                frame = frames[idx].copy()
                face, coords = face_det_results[idx]
                face = cv2.resize(face, (self.img_size, self.img_size))

                img_batch.append(face)
                mel_batch.append(mel)
                frame_batch.append(frame)
                coords_batch.append(coords)

                if len(img_batch) >= args["wav2lip_batch_size"]:
                    yield self._prepare_batches(img_batch, mel_batch, frame_batch, coords_batch)
                    img_batch, mel_batch, frame_batch, coords_batch = [], [], [], []

            if len(img_batch) > 0:
                yield self._prepare_batches(img_batch, mel_batch, frame_batch, coords_batch)

    

    def infer(self, face_path, chunk_dir, professor='default', **kwargs):
        args = {
            "static": False,
            "fps": 25.0,
            "pads": [0, 10, 0, 0],
            "crop": [0, -1, 0, -1],
            "box": [-1, -1, -1, -1],
            "rotate": False,
            "nosmooth": False,
            "resize_factor": 1,
            "face_det_batch_size": 16,
            "wav2lip_batch_size": 32,
        }
        args.update(kwargs)

        if not os.path.isfile(face_path):
            raise ValueError("Invalid face path")

        full_frame = cv2.imread(face_path)
        profile_dir = os.path.join("/app/profiles", professor)
        os.makedirs(profile_dir, exist_ok=True)
        cache_fp = os.path.join(profile_dir, "lipdetections.npy")

        if os.path.isfile(cache_fp):
            coords_arr = np.load(cache_fp)
            coords = tuple(coords_arr[0])
        else:
            det_results = self._face_detect([full_frame], args["pads"], args["nosmooth"])
            coords = det_results[0][1]
            np.save(cache_fp, np.array([coords]))

        y1, y2, x1, x2 = coords
        face = full_frame[y1:y2, x1:x2]
        face = cv2.resize(face, (self.img_size, self.img_size))

        # === Neuen Ordner mit UUID anlegen 
        session = Session(chunk_dir)

        def audio_watcher():
            seen = set()

            while not session.done_flag["done"]:
                files = sorted(f for f in os.listdir(chunk_dir) if f.endswith(".wav"))
                new_files = [f for f in files if f not in seen]

                for fname in new_files:
                    seen.add(fname)
                    path = os.path.join(chunk_dir, fname)

                    try:
                        wav_24khz = load_wav(path, 24000)
                        wav_16khz = librosa.resample(wav_24khz, orig_sr=24000, target_sr=16000)
                        mel = melspectrogram(wav_16khz)

                        if mel.shape[1] < 16:
                            print(f"⚠️ {fname} zu kurz – übersprungen.")
                            continue

                        mel_chunks = []
                        i = 0
                        mel_idx_multiplier = 80.0 / args["fps"]
                        while True:
                            start_idx = int(i * mel_idx_multiplier)
                            if start_idx + 16 > mel.shape[1]:
                                mel_chunks.append(mel[:, -16:])
                                break
                            mel_chunks.append(mel[:, start_idx:start_idx + 16])
                            i += 1

                        #print(f"🎧 {fname} → {len(mel_chunks)} Mel-Chunks")

                        frames = []
                        for mel in mel_chunks:
                            img_masked = face.copy()
                            img_masked[self.img_size // 2:] = 0
                            img_input = np.concatenate((img_masked, face), axis=2) / 255.
                            mel_input = mel.reshape(1, mel.shape[0], mel.shape[1], 1)

                            img_tensor = torch.FloatTensor(img_input.transpose(2, 0, 1)).unsqueeze(0).to(self.device)
                            mel_tensor = torch.FloatTensor(mel_input.transpose(0, 3, 1, 2)).to(self.device)

                            with torch.no_grad():
                                pred = self.model(mel_tensor, img_tensor).cpu().numpy()[0]
                                pred = (pred.transpose(1, 2, 0) * 255).astype(np.uint8)

                            pred_resized = cv2.resize(pred, (x2 - x1, y2 - y1))
                            frame = full_frame.copy()
                            frame[y1:y2, x1:x2] = pred_resized
                            frames.append(frame)

                        self.generate_video_chunk(fname, frames, wav_16khz, session.session_dir, args["fps"])

                    except Exception as e:
                        print(f"⚠️ Fehler bei {fname}: {e}")
                    
                    if fname.endswith("f.wav"):
                        session.done_flag["done"] = True
                        print(f"🛑 Endsignal erkannt durch Datei: {fname}")
                        continue

                time.sleep(0.1)

        threading.Thread(target=audio_watcher, daemon=True).start()

        return session.session_id
    
    
    def generate_video_chunk(self, fname, frames, wav_16khz, session_dir, fps):
        index = fname.replace(".wav", "")
        temp_dir = tempfile.mkdtemp()

        try:
            audio_duration_sec = librosa.get_duration(y=wav_16khz, sr=16000)
            expected_frame_count = int(audio_duration_sec * fps)

            if len(frames) < expected_frame_count:
                last_frame = frames[-1]
                frames.extend([last_frame] * (expected_frame_count - len(frames)))

            for i, frame in enumerate(frames):
                cv2.imwrite(os.path.join(temp_dir, f"{i:05d}.jpg"), frame)

            audio_path = os.path.join(temp_dir, "audio.wav")
            sf.write(audio_path, wav_16khz, 16000)

            out_path = os.path.join(session_dir, f"chunk_{index}.mp4")
            hls_flags = "append_list+program_date_time" if fname.endswith("f.wav") else "append_list+omit_endlist+program_date_time"

            cmd = [
                "ffmpeg", "-y",
                "-r", str(fps),
                "-i", os.path.join(temp_dir, "%05d.jpg"),
                "-i", audio_path,
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "veryfast",
                "-force_key_frames", f"expr:gte(t,n_forced*2)",
                "-c:a", "aac",
                "-f", "hls",
                "-hls_time", "2",
                "-hls_list_size", "0",
                "-hls_flags", hls_flags,
                "-hls_segment_filename", os.path.join(session_dir, "chunk_%04d.ts"),
                os.path.join(session_dir, "playlist.m3u8")
            ]

            subprocess.run(cmd, check=True)
            #print(f"🎞 {fname} → {os.path.basename(out_path)} gespeichert.")

        finally:
            shutil.rmtree(temp_dir)
            
class Session:
    def __init__(self, chunk_dir: str):
        self.session_id = str(uuid.uuid4())
        self.session_dir = os.path.join(chunk_dir, "video")
        os.makedirs(self.session_dir, exist_ok=True)
        self.done_flag = {"done": False}

def watch_chunks(chunk_dir, fps=25.0):
    already_seen = set()
    mel_step_size = 16

    while True:
        chunk_files = sorted(f for f in os.listdir(chunk_dir) if f.endswith("p.wav"))
        new_files = [f for f in chunk_files if f not in already_seen]

        if not new_files:
            time.sleep(1)
            continue

        for filename in new_files:
            filepath = os.path.join(chunk_dir, filename)
            wav = audio.load_wav(filepath, 16000)
            mel = audio.melspectrogram(wav)

            mel_chunks = []
            mel_idx_multiplier = 80.0 / fps
            i = 0
            while True:
                start_idx = int(i * mel_idx_multiplier)
                if start_idx + mel_step_size > mel.shape[1]:
                    mel_chunks.append(mel[:, -mel_step_size:])
                    break
                mel_chunks.append(mel[:, start_idx:start_idx + mel_step_size])
                i += 1

            already_seen.add(filename)
            yield filename, mel_chunks