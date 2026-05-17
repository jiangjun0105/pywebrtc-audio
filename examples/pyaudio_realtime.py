"""PyAudio callback wiring template for real-time echo cancellation.

This is a structural example showing how to connect PyAudio's callback-based
streams with the AudioProcessor. It plays silence and discards the cleaned
output - replace the TODOs with your actual audio source and sink.

For a working end-to-end demo that plays a tone and saves wav files,
see e2e_verify.py and e2e_speech.py instead.

Requires: pip install pyaudio
"""

import queue

import numpy as np
import pyaudio

from pywebrtc_audio import AudioProcessor

RATE = 16000
FRAME_SIZE = 160  # 10ms
FORMAT = pyaudio.paInt16
CHANNELS = 1

ap = AudioProcessor(
    sample_rate=RATE,
    echo_cancellation=True,
    noise_suppression=True,
    auto_gain_control=True,
    stream_delay_ms=int(FRAME_SIZE / RATE * 1000),
)
reference_queue: queue.Queue[bytes] = queue.Queue()

pa = pyaudio.PyAudio()


def playback_callback(in_data, frame_count, time_info, status):
    # TODO: replace with real audio (TTS, music, etc.)
    far = np.zeros(frame_count, dtype=np.int16)
    reference_queue.put(far.tobytes())
    return (far.tobytes(), pyaudio.paContinue)


def capture_callback(in_data, frame_count, time_info, status):
    near = np.frombuffer(in_data, dtype=np.int16)
    try:
        far_bytes = reference_queue.get_nowait()
        far = np.frombuffer(far_bytes, dtype=np.int16)
        near = ap.process(near, far)
    except queue.Empty:
        pass
    # TODO: do something with the cleaned audio (send to STT, save to file, etc.)
    return (None, pyaudio.paContinue)


output_stream = pa.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    output=True,
    frames_per_buffer=FRAME_SIZE,
    stream_callback=playback_callback,
)

input_stream = pa.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=FRAME_SIZE,
    stream_callback=capture_callback,
)

print("Streams running (silence playback + mic capture with AEC).")
print("This template doesn't produce output - wire in your audio source and sink.")
input("Press Enter to stop...\n")

input_stream.close()
output_stream.close()
pa.terminate()
print("Done.")
