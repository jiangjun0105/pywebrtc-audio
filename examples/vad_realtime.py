"""Real-time voice activity detection from the microphone.

Prints a live speech probability meter to the terminal.

Usage:
    python examples/vad_realtime.py

Requires: pip install pyaudio
"""

import numpy as np
import pyaudio

from pywebrtc_audio import VoiceDetector

RATE = 16000
FRAME_SIZE = 160  # 10ms
CHANNELS = 1
BAR_WIDTH = 40

vd = VoiceDetector(sample_rate=RATE)
pa = pyaudio.PyAudio()

stream = pa.open(
    format=pyaudio.paInt16,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=FRAME_SIZE,
)

print("Listening... (Ctrl+C to stop)\n")
print("  Speech Probability\n")

try:
    while True:
        data = stream.read(FRAME_SIZE, exception_on_overflow=False)
        audio = np.frombuffer(data, dtype=np.int16)
        prob = vd.process(audio)

        filled = int(prob * BAR_WIDTH)
        bar = "█" * filled + "░" * (BAR_WIDTH - filled)
        label = "SPEECH" if prob > 0.5 else "      "
        print(f"\r  {bar} {prob:.2f} {label}", end="", flush=True)
except KeyboardInterrupt:
    print("\n")
finally:
    stream.close()
    pa.terminate()
