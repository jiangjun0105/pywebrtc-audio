"""Automatic gain control example.

Demonstrates the standalone GainController and the AudioProcessor AGC pipeline.
Generates a quiet signal and shows how AGC amplifies it without clipping.
"""

import numpy as np

from pywebrtc_audio import AudioProcessor, GainController

rng = np.random.default_rng(42)
sample_rate = 16000
duration_s = 1

# --- Standalone GainController ---
gc = GainController(sample_rate=sample_rate, adaptive_digital=True)

quiet = (rng.standard_normal(sample_rate * duration_s) * 100).astype(np.int16)
amplified = gc.process(quiet)

print("Standalone GainController:")
print(f"  Input  mean abs: {np.abs(quiet).mean():.0f}")
print(f"  Output mean abs: {np.abs(amplified).mean():.0f}")
print(f"  Gain applied:    {gc.gain_db:.1f} dB")
print(f"  Max output:      {np.abs(amplified).max()} (no clipping)")

# --- Fixed gain only (no adaptive) ---
gc_fixed = GainController(
    sample_rate=sample_rate, adaptive_digital=False, fixed_gain_db=12.0
)
boosted = gc_fixed.process(quiet)

print("\nFixed 12dB gain:")
print(f"  Output mean abs: {np.abs(boosted).mean():.0f}")

# --- Combined pipeline: AEC + NS + AGC ---
ap = AudioProcessor(
    sample_rate=sample_rate,
    noise_suppression=True,
    auto_gain_control=True,
)
cleaned = ap.process(quiet)

print("\nAudioProcessor (NS + AGC):")
print(f"  Output mean abs: {np.abs(cleaned).mean():.0f}")
print(f"  Speech prob:     {ap.speech_probability:.3f}")

# --- External speech probability ---
gc2 = GainController(sample_rate=sample_rate)
out = gc2.process(quiet, speech_probability=0.99)
print("\nWith external speech_probability=0.99:")
print(f"  Gain applied: {gc2.gain_db:.1f} dB")

# --- Reset between conversations ---
gc.reset()
print(f"\nAfter reset: gain_db = {gc.gain_db:.1f} dB")
