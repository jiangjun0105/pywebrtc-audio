import wave
from pathlib import Path

import numpy as np
import pytest

from pywebrtc_audio import EchoCanceller

FIXTURES = Path(__file__).parent / "fixtures"


def read_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as w:
        rate = w.getframerate()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    return data, rate


def test_wav_echo_reduction():
    """Processing fixture wav files should reduce echo energy."""
    near_data, rate = read_wav(FIXTURES / "near.wav")
    far_data, _ = read_wav(FIXTURES / "far.wav")

    ec = EchoCanceller(sample_rate=rate)
    frame_size = rate // 100
    num_frames = min(len(near_data), len(far_data)) // frame_size

    output_frames = []
    for i in range(num_frames):
        s = i * frame_size
        e = s + frame_size
        result = ec.process(near_data[s:e], far_data[s:e])
        output_frames.append(result)

    output = np.concatenate(output_frames)

    # Compare energy of last second (after convergence) vs input
    tail = rate  # last 1s of samples
    input_energy = np.sum(near_data[-tail:].astype(np.float64) ** 2)
    output_energy = np.sum(output[-tail:].astype(np.float64) ** 2)
    assert output_energy < input_energy * 0.1  # at least 10dB reduction


def test_streaming_continuous():
    """Simulate continuous streaming - output should remain stable."""
    ec = EchoCanceller(sample_rate=16000)
    frame_size = 160
    rng = np.random.default_rng(99)

    far = (rng.standard_normal(frame_size) * 5000).astype(np.int16)
    near = (far * 0.3 + rng.standard_normal(frame_size) * 80).astype(np.int16)

    energies = []
    for i in range(500):
        result = ec.process(near, far)
        if i >= 400:
            energies.append(np.sum(result.astype(np.float64) ** 2))

    # After convergence, energy should be consistently low
    avg_energy = np.mean(energies)
    input_energy = np.sum(near.astype(np.float64) ** 2)
    assert avg_energy < input_energy * 0.05


@pytest.mark.parametrize("rate,frame_size", [(16000, 160), (32000, 320), (48000, 480)])
def test_all_sample_rates_process(rate, frame_size):
    """All supported sample rates should process without error."""
    ec = EchoCanceller(sample_rate=rate)
    near = np.zeros(frame_size, dtype=np.int16)
    far = np.zeros(frame_size, dtype=np.int16)
    result = ec.process(near, far)
    assert result.shape == (frame_size,)
    assert result.dtype == np.int16
