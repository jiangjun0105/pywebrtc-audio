import numpy as np
import pytest

from pywebrtc_audio import VoiceDetector


def test_create_default():
    assert VoiceDetector() is not None


@pytest.mark.parametrize("rate", [16000, 32000, 48000])
def test_create_with_sample_rate(rate):
    assert VoiceDetector(sample_rate=rate) is not None


def test_invalid_sample_rate():
    with pytest.raises(ValueError):
        VoiceDetector(sample_rate=8000)


def test_process_silence():
    vd = VoiceDetector()
    prob = vd.process(np.zeros(160, dtype=np.int16))
    assert isinstance(prob, float)
    assert 0.0 <= prob <= 1.0


def test_silence_low_probability():
    vd = VoiceDetector()
    for _ in range(200):
        prob = vd.process(np.zeros(160, dtype=np.int16))
    assert prob <= 0.5


def test_noise_low_probability():
    vd = VoiceDetector()
    rng = np.random.default_rng(42)
    for _ in range(200):
        noise = (rng.standard_normal(160) * 1000).astype(np.int16)
        prob = vd.process(noise)
    assert prob < 0.5


def test_speech_higher_than_noise():
    """Speech-like signal should produce higher probability than stationary noise."""
    rng = np.random.default_rng(42)
    t = np.arange(160) / 16000

    vd_noise = VoiceDetector()
    for _ in range(200):
        noise = (rng.standard_normal(160) * 1000).astype(np.int16)
        noise_prob = vd_noise.process(noise)

    # Multi-harmonic signal resembling voiced speech
    vd_speech = VoiceDetector()
    for _ in range(200):
        speech = np.zeros(160, dtype=np.float64)
        for harmonic in [150, 300, 450, 600]:
            speech += np.sin(2 * np.pi * harmonic * t) * 10000
        speech = (speech + rng.standard_normal(160) * 500).astype(np.int16)
        speech_prob = vd_speech.process(speech)

    assert speech_prob > noise_prob


def test_arbitrary_length():
    vd = VoiceDetector()
    prob = vd.process(np.zeros(100, dtype=np.int16))
    assert isinstance(prob, float)
    assert 0.0 <= prob <= 1.0


@pytest.mark.parametrize("rate,frame_size", [(16000, 160), (32000, 320), (48000, 480)])
def test_all_sample_rates_process(rate, frame_size):
    vd = VoiceDetector(sample_rate=rate)
    prob = vd.process(np.zeros(frame_size, dtype=np.int16))
    assert isinstance(prob, float)
    assert 0.0 <= prob <= 1.0


def test_float32_input():
    vd = VoiceDetector()
    prob = vd.process(np.zeros(160, dtype=np.float32))
    assert isinstance(prob, float)
    assert 0.0 <= prob <= 1.0


def test_reset_clears_state():
    rng = np.random.default_rng(42)
    t = np.arange(160) / 16000
    speech = (np.sin(2 * np.pi * 200 * t) * 15000 + rng.standard_normal(160) * 500).astype(np.int16)

    vd = VoiceDetector()
    for _ in range(200):
        vd.process(speech)
    vd.reset()

    fresh = VoiceDetector()
    assert vd.process(speech) == fresh.process(speech)


def test_speech_probability_default():
    vd = VoiceDetector()
    assert vd.speech_probability == 0.0


def test_speech_probability_matches_process():
    vd = VoiceDetector()
    audio = (np.random.default_rng(42).standard_normal(160) * 1000).astype(np.int16)
    result = vd.process(audio)
    assert vd.speech_probability == result


def test_speech_probability_reset():
    vd = VoiceDetector()
    audio = (np.random.default_rng(42).standard_normal(160) * 1000).astype(np.int16)
    vd.process(audio)
    vd.reset()
    assert vd.speech_probability == 0.0
