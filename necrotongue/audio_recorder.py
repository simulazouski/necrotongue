# audio_recorder.py
import tempfile
import wave
from contextlib import contextmanager

import pyaudio
from loguru import logger


class AudioRecorder:
    def __init__(self, rate=16000, channels=1, chunk=1024, format=pyaudio.paInt16):
        self.rate = rate
        self.channels = channels
        self.chunk = chunk
        self.format = format
        self.audio = pyaudio.PyAudio()

    @contextmanager
    def record_to_tempfile(self, duration=None):
        """
        Record audio and write to a temporary WAV file in /tmp (RAM disk on macOS).
        If duration is None, recording continues until `stop()` is called externally.
        """
        logger.debug("Recording audio to tempfile")
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk,
        )

        frames = []

        try:
            if duration:
                for _ in range(0, int(self.rate / self.chunk * duration)):
                    data = stream.read(self.chunk, exception_on_overflow=False)
                    frames.append(data)
            else:
                # Continuous recording mode
                self._recording = True
                while self._recording:
                    data = stream.read(self.chunk, exception_on_overflow=False)
                    frames.append(data)
        finally:
            stream.stop_stream()
            stream.close()

        # Write to fast RAM disk location
        with tempfile.NamedTemporaryFile(
            suffix=".wav", dir="/tmp", delete=False
        ) as temp_file:
            with wave.open(temp_file.name, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(b"".join(frames))
                logger.debug(f"Audio is recorded to {temp_file.name}")

            yield temp_file.name

    def stop(self):
        """Signal to stop recording in continuous mode"""
        self._recording = False

    def close(self):
        self.audio.terminate()
