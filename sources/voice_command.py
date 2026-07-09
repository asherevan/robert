import json
import queue
import time
import requests

import numpy as np
import sounddevice as sd

from vosk import Model as VoskModel
from vosk import KaldiRecognizer

from openwakeword.model import Model as OWWModel
import soxr
import uuid


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

############################################################
# Models
############################################################

wakeword = OWWModel(
    wakeword_models=[OWW_MODEL_PATH]
)

vosk_model = VoskModel(VOSK_MODEL_PATH)


############################################################
# Globals
############################################################

audio_queue = queue.Queue(maxsize=8)

state = "sleeping"

last_voice_time = 0

TIMEOUT = 10

last_sleep_time = 0

############################################################
# Helpers
############################################################

def submit_event(text):

    event = {
        "source": 'voice',
        "type": "voice_command",
        "timestamp": str(time.time()),
        "data": {
            "text": text
        }
    }

    try:
        requests.post(
            "http://127.0.0.1/submit",
            json=event,
            timeout=0.5
        )
    except Exception as e:
        print(e)

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


recognizer = None

while True:

    audio = audio_queue.get()

    pcm48 = audio.flatten()

    pcm = soxr.resample(pcm48, MIC_SAMPLE_RATE, PROCESS_SAMPLE_RATE)

    ########################################################
    # Sleeping
    ########################################################

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

                recognizer = KaldiRecognizer(
                    vosk_model,
                    PROCESS_SAMPLE_RATE
                )

                last_voice_time = time.monotonic()

                state = "listening"

                break

    ########################################################
    # Listening
    ########################################################

    elif state == "listening":

        isDone = recognizer.AcceptWaveform(pcm.tobytes())

        partial = json.loads(
            recognizer.PartialResult()
        )

        if partial["partial"]:

            print(
                partial["partial"],
                end="\r",
                flush=True
            )
        
        if isDone:
            result = json.loads(
                recognizer.Result()
            )['text']
            if result != '':
                print(result)
                submit_event(result)

                last_voice_time = time.monotonic()

    if time.monotonic() - last_voice_time > TIMEOUT:
        if not state == 'sleeping':
            print("Sleeping...\n")

            state = "sleeping"
            last_sleep_time = time.monotonic()