"""Strands BidiAgent with pywebrtc-audio echo cancellation and noise suppression.

Speaks to a Nova Sonic agent through speakers + mic without the agent
hearing its own output. The AudioProcessor removes the speaker signal
and background noise from the mic capture before it reaches the model.

Usage:
    pip install 'strands-agents[bidi]' pywebrtc-audio
    python examples/strands_agents_bidi.py

Requires: Python 3.12+, AWS credentials configured for us-east-1
(e.g. via `aws configure` or environment variables).
"""

import asyncio
import base64
import datetime
import queue
from typing import TYPE_CHECKING, Any

import numpy as np
import pyaudio

from pywebrtc_audio import AudioProcessor

from strands.experimental.bidi import BidiAgent
from strands.experimental.bidi.io.audio import _BidiAudioBuffer
from strands.experimental.bidi.io.text import BidiTextIO
from strands.experimental.bidi.models import BidiNovaSonicModel
from strands import tool
from strands.experimental.bidi.tools import stop_conversation
from strands.experimental.bidi.types.events import (
    BidiAudioInputEvent,
    BidiAudioStreamEvent,
    BidiInterruptionEvent,
    BidiOutputEvent,
)
from strands.experimental.bidi.types.io import BidiInput, BidiOutput

if TYPE_CHECKING:
    from strands.experimental.bidi.agent.agent import BidiAgent as BidiAgentType

SAMPLE_RATE = 16000
FRAME_SIZE = 160  # 10ms at 16kHz
PYAUDIO_FRAMES_PER_BUFFER = 160  # align with 10ms frame size


class _ProcessedAudioInput(BidiInput):
    """Mic input that applies echo cancellation + noise suppression using a shared reference buffer."""

    def __init__(self, ap: AudioProcessor | None, ref_buf: queue.Queue):
        self._ap = ap
        self._ref_buf = ref_buf
        self._buffer = _BidiAudioBuffer()

    async def start(self, agent: "BidiAgentType") -> None:
        self._channels = agent.model.config["audio"]["channels"]
        self._format = agent.model.config["audio"]["format"]
        self._rate = agent.model.config["audio"]["input_rate"]

        self._buffer.start()
        self._audio = pyaudio.PyAudio()
        self._stream = self._audio.open(
            channels=self._channels,
            format=pyaudio.paInt16,
            frames_per_buffer=PYAUDIO_FRAMES_PER_BUFFER,
            input=True,
            rate=self._rate,
            stream_callback=self._callback,
        )

    async def stop(self) -> None:
        if hasattr(self, "_stream"):
            self._stream.close()
        if hasattr(self, "_audio"):
            self._audio.terminate()
        self._buffer.stop()

    async def __call__(self) -> BidiAudioInputEvent:
        data = await asyncio.to_thread(self._buffer.get)
        return BidiAudioInputEvent(
            audio=base64.b64encode(data).decode("utf-8"),
            channels=self._channels,
            format=self._format,
            sample_rate=self._rate,
        )

    def _callback(self, in_data: bytes, frame_count: int, *_: Any) -> tuple[None, Any]:
        if self._ap:
            near = np.frombuffer(in_data, dtype=np.int16)
            try:
                far_frame = self._ref_buf.get_nowait()
            except queue.Empty:
                far_frame = np.zeros(FRAME_SIZE, dtype=np.int16)
            self._buffer.put(self._ap.process(near, far_frame).tobytes())
        else:
            self._buffer.put(in_data)

        return (None, pyaudio.paContinue)


class _ProcessedAudioOutput(BidiOutput):
    """Speaker output that feeds reference frames for echo cancellation."""

    def __init__(self, ref_buf: queue.Queue, feed_ref: bool = True):
        self._ref_buf = ref_buf
        self._feed_ref = feed_ref
        self._buffer = _BidiAudioBuffer()

    async def start(self, agent: "BidiAgentType") -> None:
        self._channels = agent.model.config["audio"]["channels"]
        self._rate = agent.model.config["audio"]["output_rate"]

        self._buffer.start()
        self._audio = pyaudio.PyAudio()
        self._stream = self._audio.open(
            channels=self._channels,
            format=pyaudio.paInt16,
            frames_per_buffer=PYAUDIO_FRAMES_PER_BUFFER,
            output=True,
            rate=self._rate,
            stream_callback=self._callback,
        )

    async def stop(self) -> None:
        if hasattr(self, "_stream"):
            self._stream.close()
        if hasattr(self, "_audio"):
            self._audio.terminate()
        self._buffer.stop()

    async def __call__(self, event: BidiOutputEvent) -> None:
        if isinstance(event, BidiAudioStreamEvent):
            self._buffer.put(base64.b64decode(event["audio"]))
        elif isinstance(event, BidiInterruptionEvent):
            self._buffer.clear()
            while not self._ref_buf.empty():
                try:
                    self._ref_buf.get_nowait()
                except queue.Empty:
                    break

    def _callback(self, _in_data: None, frame_count: int, *_: Any) -> tuple[bytes, Any]:
        byte_count = frame_count * pyaudio.get_sample_size(pyaudio.paInt16)
        data = self._buffer.get(byte_count)

        # Feed reference frame for echo cancellation
        if self._feed_ref:
            samples = np.frombuffer(data, dtype=np.int16)
            if len(samples) == FRAME_SIZE:
                self._ref_buf.put(samples.copy())

        return (data, pyaudio.paContinue)


class BidiProcessedAudioIO:
    """Audio IO with optional echo cancellation + noise suppression."""

    def __init__(self, audio_processing: bool = True) -> None:
        self._audio_processing = audio_processing
        self._ref_buf: queue.Queue[np.ndarray] = queue.Queue()
        self._ap = (
            AudioProcessor(
                sample_rate=SAMPLE_RATE,
                echo_cancellation=audio_processing,
                noise_suppression=audio_processing,
                auto_gain_control=audio_processing,
                stream_delay_ms=int(PYAUDIO_FRAMES_PER_BUFFER / SAMPLE_RATE * 1000),
            )
            if audio_processing
            else None
        )

    def input(self) -> _ProcessedAudioInput:
        return _ProcessedAudioInput(self._ap, self._ref_buf)

    def output(self) -> _ProcessedAudioOutput:
        return _ProcessedAudioOutput(self._ref_buf, self._audio_processing)


@tool
def current_datetime() -> str:
    """Return the current date and time."""
    return datetime.datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")


async def main(audio_processing: bool = True) -> None:
    model = BidiNovaSonicModel(
        provider_config={"audio": {"voice": "tiffany"}},
        client_config={"region": "us-east-1"},
    )
    agent = BidiAgent(model=model, tools=[stop_conversation, current_datetime])

    audio_io = BidiProcessedAudioIO(audio_processing=audio_processing)
    text_io = BidiTextIO()

    print(f"Audio processing: {'enabled' if audio_processing else 'disabled'}")
    print("Speak into your mic. Say 'stop conversation' to end.")
    await agent.run(
        inputs=[audio_io.input()],
        outputs=[audio_io.output(), text_io.output()],
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no-processing",
        action="store_true",
        help="Disable audio processing (echo cancellation + noise suppression)",
    )
    args = parser.parse_args()
    asyncio.run(main(audio_processing=not args.no_processing))
