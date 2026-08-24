import json
import os
import queue
import sys
import time

import fcntl

import numpy as np
import requests
import robertutils
import sounddevice as sd
import soxr
from openwakeword.model import Model as OWWModel
from vosk import KaldiRecognizer, Model as VoskModel


############################################################
# Configuration
############################################################

MIC_SAMPLE_RATE = 48000
PROCESS_SAMPLE_RATE = 16000
BLOCK_SIZE = 2048

WAKEWORD_THRESHOLD = 0.5

VOSK_MODEL_PATH = "/home/asherevan/robert/venv/lib/python3.11/site-packages/speech_recognition/models/vosk"
OWW_MODEL_PATH = "/home/asherevan/robert/Hey_Robert.tflite"

WAKEWORD_COOLDOWN = 2
LAST_RESULT_COOLDOWN = 5.0
VOICE_LOCK_PATH = "/tmp/robert_voice_command.lock"

############################################################
# Globals
############################################################

wakeword = None
vosk_model = None
recognizer = None


def acquire_instance_lock():
    lock_fd = os.open(VOICE_LOCK_PATH, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_fd
    except BlockingIOError:
        os.close(lock_fd)
        print("Voice command instance already running; refusing duplicate start.")
        raise SystemExit(0)


# Keep the lock open for the life of the process so duplicates cannot start.
voice_lock_fd = acquire_instance_lock()

audio_queue = queue.Queue(maxsize=16)
state = "sleeping"
last_voice_time = 0
TIMEOUT = 5
last_sleep_time = 0
last_transcript = ""
last_transcript_at = 0.0


def initialize_models():
    global wakeword, vosk_model
    if wakeword is None:
        wakeword = OWWModel(wakeword_models=[OWW_MODEL_PATH])
    if vosk_model is None:
        vosk_model = VoskModel(VOSK_MODEL_PATH)
    return wakeword, vosk_model


def should_emit_result(result_text: str, last_result_text: str, last_result_time: float) -> bool:
    cleaned = (result_text or "").strip()
    if not cleaned:
        return False
    if last_result_text and cleaned.lower() == last_result_text.lower():
        if time.monotonic() - last_result_time < LAST_RESULT_COOLDOWN:
            return False
    return True


############################################################
# Audio callback
############################################################

def audio_callback(indata, frames, time_info, status):
    if status:
        print(status)

    try:
        audio_queue.put_nowait(indata.copy())
    except queue.Full:
        pass


############################################################
# Main
############################################################

def main():
    global state, last_sleep_time, last_voice_time, last_transcript, last_transcript_at
    initialize_models()

    print("Loading microphone...")

    stream = sd.InputStream(
        samplerate=MIC_SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        channels=1,
        dtype=np.int16,
        callback=audio_callback,
    )

    stream.start()
    print("Listening...")

    while True:
        audio = audio_queue.get()
        pcm48 = audio.flatten()
        pcm = soxr.resample(pcm48, MIC_SAMPLE_RATE, PROCESS_SAMPLE_RATE)

        if state == "sleeping":
            if time.monotonic() - last_sleep_time < WAKEWORD_COOLDOWN:
                continue

            wakeword.predict(pcm)

            for mdl in wakeword.prediction_buffer:
                scores = wakeword.prediction_buffer[mdl]
                if scores and scores[-1] > WAKEWORD_THRESHOLD:
                    print("Wake word!")

                    for scores in wakeword.prediction_buffer.values():
                        scores.clear()

                    recognizer = KaldiRecognizer(vosk_model, PROCESS_SAMPLE_RATE)
                    last_voice_time = time.monotonic()
                    state = "listening"
                    break

        elif state == "listening":
            if recognizer is None:
                state = "sleeping"
                last_sleep_time = time.monotonic()
                continue

            try:
                is_done = recognizer.AcceptWaveform(pcm.tobytes())
                partial = json.loads(recognizer.PartialResult() or '{}')
            except (TypeError, ValueError):
                is_done = False
                partial = {}

            if partial.get("partial"):
                print(partial["partial"], end="\r", flush=True)

            if is_done:
                try:
                    result = json.loads(recognizer.Result() or '{}').get('text', '')
                except (TypeError, ValueError):
                    result = ''

                result_text = (result or '').strip()
                if should_emit_result(result_text, last_transcript, last_transcript_at):
                    print(result_text)
                    try:
                        robertutils.send_event('voice', 'voice_command', {'text': result_text}, priority='high')
                    except requests.RequestException as exc:
                        print(f"Voice event failed: {exc}")
                    last_transcript = result_text
                    last_transcript_at = time.monotonic()
                else:
                    print(f"Skipping duplicate command: {result_text}")

                recognizer = None
                state = "sleeping"
                last_voice_time = time.monotonic()
                last_sleep_time = time.monotonic()

        if time.monotonic() - last_voice_time > TIMEOUT:
            if state != 'sleeping':
                print("Sleeping...\n")
                recognizer = None
                state = "sleeping"
                last_sleep_time = time.monotonic()


if __name__ == "__main__":
    main()