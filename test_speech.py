import wave, json
from vosk import Model, KaldiRecognizer

model = Model("vosk-model-small-en-us-0.15")
wf = wave.open("audio.wav", "rb")
rec = KaldiRecognizer(model, wf.getframerate())

print('Starting transcription!')
while True:
    data = wf.readframes(4000)
    if not data: break
    if rec.AcceptWaveform(data):
        print(json.loads(rec.Result())["text"])
print(json.loads(rec.FinalResult())["text"])