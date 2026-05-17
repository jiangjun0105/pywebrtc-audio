import numpy as np
import pytest

from pywebrtc_audio import GainController, AudioProcessor


def test_create_default():
    assert GainController() is not None


@pytest.mark.parametrize("rate", [16000, 32000, 48000])
def test_create_with_sample_rate(rate):
    assert GainController(sample_rate=rate) is not None


def test_invalid_sample_rate():
    with pytest.raises(ValueError):
        GainController(sample_rate=8000)


def test_process_silence():
    gc = GainController()
    result = gc.process(np.zeros(160, dtype=np.int16))
    assert result.shape == (160,)
    assert result.dtype == np.int16


def test_quiet_signal_amplified():
    gc = GainController(sample_rate=16000, adaptive_digital=True)
    rng = np.random.default_rng(42)
    quiet = (rng.standard_normal(16000) * 100).astype(np.int16)
    loud = gc.process(quiet)
    assert np.abs(loud).mean() > np.abs(quiet).mean()
    assert gc.gain_db > 0.0


def test_loud_signal_no_clipping():
    gc = GainController(sample_rate=16000)
    rng = np.random.default_rng(42)
    loud = (rng.standard_normal(16000) * 30000).astype(np.int16)
    result = gc.process(loud)
    assert np.all(np.abs(result) <= 32767)


def test_float32_dtype_preserved():
    gc = GainController(sample_rate=16000)
    audio = (np.random.default_rng(42).standard_normal(16000) * 0.003).astype(np.float32)
    result = gc.process(audio)
    assert result.dtype == np.float32


def test_external_speech_probability():
    gc = GainController(sample_rate=16000)
    audio = (np.random.default_rng(42).standard_normal(16000) * 500).astype(np.int16)
    result = gc.process(audio, speech_probability=0.99)
    assert result.shape == audio.shape


def test_fixed_gain_only():
    gc = GainController(sample_rate=16000, adaptive_digital=False, fixed_gain_db=6.0)
    rng = np.random.default_rng(42)
    audio = (rng.standard_normal(16000) * 1000).astype(np.int16)
    result = gc.process(audio)
    # Fixed 6dB gain ~= 2x amplitude, limiter may reduce peaks
    assert np.abs(result).mean() > np.abs(audio).mean()


def test_gain_db_property():
    gc = GainController(sample_rate=16000)
    assert gc.gain_db == 0.0
    audio = (np.random.default_rng(42).standard_normal(16000) * 100).astype(np.int16)
    gc.process(audio)
    # After processing quiet audio, gain should have changed
    assert isinstance(gc.gain_db, float)


def test_reset_clears_state():
    gc = GainController(sample_rate=16000)
    audio = (np.random.default_rng(42).standard_normal(16000) * 100).astype(np.int16)
    gc.process(audio)
    gc.reset()
    assert gc.gain_db == 0.0


def test_arbitrary_length():
    gc = GainController(sample_rate=16000)
    result = gc.process(np.zeros(100, dtype=np.int16))
    assert result.shape == (100,)


@pytest.mark.parametrize("rate", [16000, 32000, 48000])
def test_all_sample_rates_process(rate):
    gc = GainController(sample_rate=rate)
    frame_size = rate // 100
    result = gc.process(np.zeros(frame_size, dtype=np.int16))
    assert result.shape == (frame_size,)


def test_empty_input_raises():
    gc = GainController()
    with pytest.raises(ValueError):
        gc.process(np.array([], dtype=np.int16))


def test_audio_processor_agc_only():
    ap = AudioProcessor(sample_rate=16000, auto_gain_control=True)
    rng = np.random.default_rng(42)
    quiet = (rng.standard_normal(16000) * 100).astype(np.int16)
    result = ap.process(quiet)
    assert result.shape == quiet.shape
    assert np.abs(result).mean() > np.abs(quiet).mean()


def test_audio_processor_agc_plus_ns():
    ap = AudioProcessor(
        sample_rate=16000, auto_gain_control=True, noise_suppression=True
    )
    rng = np.random.default_rng(42)
    audio = (rng.standard_normal(16000) * 100).astype(np.int16)
    result = ap.process(audio)
    assert result.shape == audio.shape
    assert 0.0 <= ap.speech_probability <= 1.0


def test_audio_processor_agc_reset():
    ap = AudioProcessor(sample_rate=16000, auto_gain_control=True)
    audio = (np.random.default_rng(42).standard_normal(16000) * 100).astype(np.int16)
    ap.process(audio)
    ap.reset()
    # Should not crash after reset
    result = ap.process(audio)
    assert result.shape == audio.shape


def test_audio_processor_gain_db_with_agc():
    ap = AudioProcessor(sample_rate=16000, auto_gain_control=True)
    audio = (np.random.default_rng(42).standard_normal(16000) * 100).astype(np.int16)
    ap.process(audio)
    assert isinstance(ap.gain_db, float)


def test_audio_processor_gain_db_without_agc_raises():
    ap = AudioProcessor(sample_rate=16000)
    with pytest.raises(RuntimeError, match="auto_gain_control"):
        ap.gain_db


def test_speech_probability_out_of_range_raises():
    gc = GainController()
    audio = np.zeros(160, dtype=np.int16)
    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        gc.process(audio, speech_probability=1.5)
    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        gc.process(audio, speech_probability=-0.1)


def test_speech_probability_default():
    gc = GainController()
    assert gc.speech_probability == 0.0


def test_speech_probability_after_process():
    gc = GainController()
    audio = (np.random.default_rng(42).standard_normal(16000) * 500).astype(np.int16)
    gc.process(audio)
    assert isinstance(gc.speech_probability, float)
    assert 0.0 <= gc.speech_probability <= 1.0


def test_speech_probability_uses_external():
    gc = GainController()
    audio = np.zeros(160, dtype=np.int16)
    gc.process(audio, speech_probability=0.75)
    assert gc.speech_probability == pytest.approx(0.75)


def test_speech_probability_reset():
    gc = GainController()
    audio = (np.random.default_rng(42).standard_normal(16000) * 500).astype(np.int16)
    gc.process(audio)
    gc.reset()
    assert gc.speech_probability == 0.0
