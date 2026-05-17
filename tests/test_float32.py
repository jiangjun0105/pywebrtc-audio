import numpy as np
import pytest

from pywebrtc_audio import AudioProcessor, EchoCanceller, NoiseSuppressor


@pytest.mark.parametrize("cls,kwargs,needs_far", [
    (EchoCanceller, {}, True),
    (NoiseSuppressor, {}, False),
    (AudioProcessor, {"noise_suppression": True}, False),
    (AudioProcessor, {"echo_cancellation": True}, True),
])
def test_dtype_preserved(cls, kwargs, needs_far):
    proc = cls(**kwargs)
    near = np.zeros(160, dtype=np.float32)
    args = (near, np.zeros(160, dtype=np.float32)) if needs_far else (near,)
    result = proc.process(*args)
    assert result.dtype == np.float32
    assert result.shape == (160,)


def test_clipping():
    ap = AudioProcessor(high_pass_filter=True)
    loud = np.full(160, 3.0, dtype=np.float32)
    result = ap.process(loud)
    assert result.max() <= 1.0
    assert result.min() >= -1.0


def test_round_trip_parity():
    ns = NoiseSuppressor(level=2)
    ns2 = NoiseSuppressor(level=2)
    rng = np.random.default_rng(42)

    audio_f32 = rng.standard_normal(160).astype(np.float32) * 0.1
    audio_i16 = np.clip(audio_f32 * 32767, -32768, 32767).astype(np.int16)

    result_f32 = ns.process(audio_f32)
    result_i16_as_f32 = ns2.process(audio_i16).astype(np.float32) / 32767.0

    np.testing.assert_allclose(result_f32, result_i16_as_f32, atol=1e-4)
