"""Stereo audio processing with interleaved layout.

Demonstrates how to process stereo (2-channel) audio. All classes accept
interleaved samples: [L0, R0, L1, R1, ...]. A 10ms stereo frame at 16kHz
is 320 samples (160 per channel x 2 channels).
"""

import numpy as np

from pywebrtc_audio import AudioProcessor, NoiseSuppressor

RATE = 16000
FRAME_SIZE = 160  # samples per channel per 10ms frame
NUM_CHANNELS = 2

t = np.arange(FRAME_SIZE) / RATE

# Create stereo signal: left = 440Hz tone, right = 880Hz tone
left = (np.sin(2 * np.pi * 440 * t) * 10000).astype(np.int16)
right = (np.sin(2 * np.pi * 880 * t) * 10000).astype(np.int16)

# Interleave into [L0, R0, L1, R1, ...]
stereo = np.empty(FRAME_SIZE * NUM_CHANNELS, dtype=np.int16)
stereo[0::2] = left
stereo[1::2] = right

# --- NoiseSuppressor: channels are processed independently ---
ns = NoiseSuppressor(sample_rate=RATE, num_channels=NUM_CHANNELS)

for _ in range(100):
    result = ns.process(stereo)

# De-interleave output
out_left = result[0::2]
out_right = result[1::2]

print("NoiseSuppressor stereo:")
print(f"  Left  RMS: {np.sqrt(np.mean(left.astype(float)**2)):.0f} -> {np.sqrt(np.mean(out_left.astype(float)**2)):.0f}")
print(f"  Right RMS: {np.sqrt(np.mean(right.astype(float)**2)):.0f} -> {np.sqrt(np.mean(out_right.astype(float)**2)):.0f}")

# --- AudioProcessor: full pipeline with stereo AEC ---
rng = np.random.default_rng(42)

far_left = (rng.standard_normal(FRAME_SIZE) * 5000).astype(np.int16)
far_right = (rng.standard_normal(FRAME_SIZE) * 5000).astype(np.int16)
far = np.empty(FRAME_SIZE * NUM_CHANNELS, dtype=np.int16)
far[0::2] = far_left
far[1::2] = far_right

# Mic picks up echo (attenuated far signal) + noise
near = (far * 0.3 + (rng.standard_normal(FRAME_SIZE * NUM_CHANNELS) * 500)).astype(np.int16)

ap = AudioProcessor(
    sample_rate=RATE,
    num_channels=NUM_CHANNELS,
    echo_cancellation=True,
    noise_suppression=True,
    auto_gain_control=True,
)

for _ in range(200):
    result = ap.process(near, far)

input_energy = np.sum(near.astype(float) ** 2)
output_energy = np.sum(result.astype(float) ** 2)

print("\nAudioProcessor stereo (AEC + NS + AGC):")
print(f"  Input energy:  {input_energy:.0f}")
print(f"  Output energy: {output_energy:.0f}")
print(f"  Speech prob:   {ap.speech_probability:.3f}")
print(f"  Gain:          {ap.gain_db:.1f} dB")
