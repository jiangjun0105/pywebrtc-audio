import numpy as np
import pytest

from pywebrtc_audio import NoiseSuppressor


def test_create_default():
    assert NoiseSuppressor() is not None


@pytest.mark.parametrize("rate", [16000, 32000, 48000])
def test_create_with_sample_rate(rate):
    assert NoiseSuppressor(sample_rate=rate) is not None


@pytest.mark.parametrize("level", [0, 1, 2, 3])
def test_create_with_level(level):
    assert NoiseSuppressor(level=level) is not None


def test_invalid_sample_rate():
    with pytest.raises(ValueError):
        NoiseSuppressor(sample_rate=8000)


def test_invalid_level():
    with pytest.raises(ValueError):
        NoiseSuppressor(level=5)


def test_process_silence():
    ns = NoiseSuppressor()
    result = ns.process(np.zeros(160, dtype=np.int16))
    assert result.shape == (160,)
    assert result.dtype == np.int16


def test_noise_reduction():
    ns = NoiseSuppressor(level=2)
    rng = np.random.default_rng(42)

    for _ in range(200):
        noise = (rng.standard_normal(160) * 1000).astype(np.int16)
        result = ns.process(noise)

    assert np.sum(result.astype(float) ** 2) < np.sum(noise.astype(float) ** 2)


def test_arbitrary_length():
    ns = NoiseSuppressor()
    result = ns.process(np.zeros(100, dtype=np.int16))
    assert result.shape == (100,)
    assert result.dtype == np.int16


@pytest.mark.parametrize("rate,frame_size", [(16000, 160), (32000, 320), (48000, 480)])
def test_all_sample_rates_process(rate, frame_size):
    ns = NoiseSuppressor(sample_rate=rate)
    result = ns.process(np.zeros(frame_size, dtype=np.int16))
    assert result.shape == (frame_size,)
    assert result.dtype == np.int16


def test_reset_clears_state():
    """After reset, output should match a freshly constructed instance."""
    rng = np.random.default_rng(42)
    noise = (rng.standard_normal(160) * 1000).astype(np.int16)

    ns = NoiseSuppressor(level=2)
    for _ in range(200):
        ns.process(noise)
    ns.reset()

    fresh = NoiseSuppressor(level=2)
    assert np.array_equal(ns.process(noise), fresh.process(noise))


def test_speech_probability_range():
    ns = NoiseSuppressor()
    rng = np.random.default_rng(42)
    for _ in range(10):
        ns.process((rng.standard_normal(160) * 1000).astype(np.int16))
    prob = ns.speech_probability
    assert isinstance(prob, float)
    assert 0.0 <= prob <= 1.0
