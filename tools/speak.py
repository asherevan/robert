import numpy as np
import sounddevice as sd
from piper import PiperVoice

# Load your voice model
voice = PiperVoice.load("/home/asherevan/robert/en_US-ryan-low.onnx")
sample_rate = voice.config.sample_rate

def speak_text(text: str):
    # Stream directly to the default speaker
    with sd.RawOutputStream(
        samplerate=sample_rate, channels=1, dtype="int16"
    ) as stream:
        for audio_bytes in voice.synthesize(text):
            stream.write(audio_bytes.audio_int16_array)

main = speak_text # Tool definition files include a main variable pointing to the function to be run
function_schema = { # and the tool schema definition.
        "type": "function",
        "function": {
            "name": "speak",
            "description": "Speak text through Robert's TTS system.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The string to speak"},
                },
                "required": ["text"],
            },
        },
    }