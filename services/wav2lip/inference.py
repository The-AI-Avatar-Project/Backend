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

    def _datagen(self, frames, mels, args, face_det_results):
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

    def infer(self, face_path, audio_path, professor='default', **kwargs):
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

        # Load face frames
        video_load_start = time.time()
        if face_path.split(".")[-1].lower() in ["jpg", "jpeg", "png"]:
            args["static"] = True
            full_frames = [cv2.imread(face_path)]
            fps = args["fps"]
        else:
            cap = cv2.VideoCapture(face_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            full_frames = []
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if args["resize_factor"] > 1:
                    frame = cv2.resize(frame, (frame.shape[1] // args["resize_factor"], frame.shape[0] // args["resize_factor"]))
                if args["rotate"]:
                    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
                y1, y2, x1, x2 = args["crop"]
                y2 = y2 if y2 != -1 else frame.shape[0]
                x2 = x2 if x2 != -1 else frame.shape[1]
                full_frames.append(frame[y1:y2, x1:x2])
            cap.release()
        print(f"⏱️ Videoladen + Preprocessing: {time.time() - video_load_start:.2f} s")

        # Load audio and extract mels
        audio_start = time.time()
        if not audio_path.endswith(".wav"):
            subprocess.call(f'ffmpeg -y -i "{audio_path}" -strict -2 temp/temp.wav', shell=True)
            audio_path = "temp/temp.wav"
        print(f"⏱️ Audio laden & Mel-Spektrum: {time.time() - audio_start:.2f} s")

        mel_chunk_start = time.time()
        wav = audio.load_wav(audio_path, 16000)
        mel = audio.melspectrogram(wav)
        mel_step_size = 16
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
        print(f"⏱️ Mel-Chunk-Erzeugung: {time.time() - mel_chunk_start:.2f} s")
        full_frames = full_frames[:len(mel_chunks)]

        # Detect faces
        face_detect_start = time.time()
        detection_dir = os.path.join("temp", professor, "lipdetections")
        os.makedirs(detection_dir, exist_ok=True)

        BASE         = os.getcwd()     
        PROFILES_DIR = os.path.join(BASE, "profiles")
        detection_dir = os.path.join(PROFILES_DIR, professor)
        os.makedirs(detection_dir, exist_ok=True)

        cache_fp = os.path.join(detection_dir, "lipdetections.npy")
        to_detect = full_frames if not args["static"] else [full_frames[0]]
        if args["box"][0] == -1:
            if os.path.isfile(cache_fp):
                print("cached lip detection loaded")
                coords_arr       = np.load(cache_fp)
                face_det_results = []
                for i, (y1, y2, x1, x2) in enumerate(coords_arr):
                    face = to_detect[i][y1:y2, x1:x2]
                    face = cv2.resize(face, (self.img_size, self.img_size))
                    face_det_results.append([face, (y1, y2, x1, x2)])
            else:
                face_det_results = self._face_detect(to_detect, args["pads"], args["nosmooth"])
                coords_arr       = np.array([coords for _, coords in face_det_results])
                np.save(cache_fp, coords_arr)
                print("Saved lip detection")
        else:
            y1, y2, x1, x2 = args["box"]
            face_det_results = [
                [f[y1:y2, x1:x2], (y1, y2, x1, x2)]
                for f in full_frames
            ]
        print(f"⏱️ Lip-Detection + Caching: {time.time() - face_detect_start:.2f} s")
        # Inference and video writing
        available_threads = max(1, multiprocessing.cpu_count() // 2)
        ffmpeg_cmd = [
            "ffmpeg",
            "-threads", str(available_threads),
            "-thread_queue_size", "2024",
            "-y",
            "-f", "image2pipe",
            "-r", str(25),
            "-i", "-",  # input from stdin
            "-i", audio_path,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-f", "mp4",
            "-tune", "zerolatency",
            "-movflags", "frag_keyframe+empty_moov+default_base_moof",
            "pipe:1",
        ]

        self.ffmpeg_ready = threading.Event()

        def start_ffmpeg():
            start_time = time.time()
            self.ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"FFmpeg gestartet in {time.time() - start_time:.2f} Sekunden")
            self.ffmpeg_ready.set()

            def log_ffmpeg_errors():
                for line in self.ffmpeg_process.stderr:
                    print("FFmpeg:", line.decode(errors="ignore").strip())

            threading.Thread(target=log_ffmpeg_errors, daemon=True).start()

        threading.Thread(target=start_ffmpeg, daemon=True).start()

        def feed_frames():
            self.ffmpeg_ready.wait()
            process = self.ffmpeg_process

            gen = self._datagen(full_frames, mel_chunks, args, face_det_results)
            for i, (img_batch, mel_batch, frames, coords) in enumerate(tqdm(gen, total=int(np.ceil(float(len(mel_chunks)) / args["wav2lip_batch_size"])))):
                batch_start = time.time()
                print(f"\n🔁 Verarbeite Batch {i+1}")

                prep_start = time.time()
                img_batch = torch.FloatTensor(np.transpose(img_batch, (0, 3, 1, 2))).to(self.device)
                mel_batch = torch.FloatTensor(np.transpose(mel_batch, (0, 3, 1, 2))).to(self.device)
                print(f"⏱️ Datenvorbereitung: {time.time() - prep_start:.2f} s")

                infer_start = time.time()
                with torch.no_grad():
                    pred = self.model(mel_batch, img_batch)
                print(f"⏱️ Modell-Inferenz: {time.time() - infer_start:.2f} s")

                post_start = time.time()
                pred = pred.cpu().numpy().transpose(0, 2, 3, 1) * 255.

                for p, f, c in zip(pred, frames, coords):
                    y1, y2, x1, x2 = c
                    p = cv2.resize(p.astype(np.uint8), (x2 - x1, y2 - y1))
                    f[y1:y2, x1:x2] = p
                    success, jpeg = cv2.imencode(".jpg", f)
                    if not success:
                        print("⚠️ JPEG Encoding fehlgeschlagen – Frame übersprungen.")
                        continue
                    try:
                        process.stdin.write(jpeg.tobytes())
                        process.stdin.flush()
                    except BrokenPipeError:
                        print("❌ ffmpeg-Pipe geschlossen – Abbruch.")
                        return
                    except Exception as e:
                        print(f"❌ Fehler beim Schreiben an ffmpeg: {e}")
                        return

                print(f"⏱️ Post-Processing + Writing: {time.time() - post_start:.2f} s")
                print(f"⏱️ Gesamtzeit für Batch {i+1}: {time.time() - batch_start:.2f} s")

            try:
                process.stdin.close()
            except Exception as e:
                print(f"⚠️ Fehler beim Schließen von stdin: {e}")

        threading.Thread(target=feed_frames, daemon=True).start()

        def stream_output():
            self.ffmpeg_ready.wait()
            process = self.ffmpeg_process
            try:
                while True:
                    chunk = process.stdout.read(8192)
                    if not chunk:
                        break
                    yield chunk
            finally:
                process.stdout.close()
                process.wait()

        return stream_output()