import os
import subprocess
import threading

import pyperclip
import rumps
from audio_recorder import AudioRecorder
from config import Settings
from input_monitor import InputMonitor
from loguru import logger
from prompt import COMMENT_WITH_CODE, FORMAT_EMAIL_PROMPT
from pynput.keyboard import Controller, Key
from transcriber import Transcriber


class NecroTongueApp(rumps.App):
    def __init__(self, settings: Settings):
        super().__init__("🎙️", quit_button=rumps.MenuItem("Quit"))

        self.status_item = rumps.MenuItem("Status: Ready")
        self.menu = [None, self.status_item]  # No clickable recording toggle

        self.is_recording = False
        self.temp_audio_file = None

        self.recorder = AudioRecorder()
        self.transcriber = Transcriber(
            whisper_url=f"http://localhost:{settings.transcribe.port}/inference",
            refine_url=f"http://localhost:{settings.refine.port}/v1/chat/completions",
        )

        self.task_map = {
            Key.alt: FORMAT_EMAIL_PROMPT,
            Key.cmd: COMMENT_WITH_CODE,
        }
        self.monitor = InputMonitor(
            base_keys={Key.ctrl, Key.shift},
            task_keys=set(self.task_map.keys()),
        )
        self.monitor.start(
            on_press=self.handle_hotkey_press,
            on_release=self.handle_hotkey_release,
        )

        logger.debug("RecorderApp started. Look for 🎙️ in menu bar.")

    def handle_hotkey_press(self):
        if not self.is_recording:
            self.start_recording()

    def handle_hotkey_release(self):
        if self.is_recording:
            self.stop_recording()

    def start_recording(self):
        self.is_recording = True
        self._notify(
            subtitle="Rec. started",
            message="Speak now...",
            sound="Pop",
        )

        def record():
            with self.recorder.record_to_tempfile() as audio_path:
                self.temp_audio_file = audio_path

        self.recording_thread = threading.Thread(target=record)
        self.recording_thread.start()

    def stop_recording(self):
        self.is_recording = False
        self.recorder.stop()
        self._notify(
            subtitle="Rec. stopped",
            message="Transcribing...",
            sound="Submarine",
        )

        def process():
            try:
                self.recording_thread.join(timeout=3)
                transcribed = self.transcriber.transcribe(self.temp_audio_file)
                logger.info(f"Transcribed {transcribed=}")

                combo_triggered_key = self.monitor.combo_triggered_key
                prompt = self.task_map[combo_triggered_key]
                refined = self.transcriber.refine(transcribed, prompt=prompt)
                logger.info(f"Refined {refined=}")

                self.insert_text(refined)
                self._notify(
                    subtitle="Transcription Complete",
                    message=refined[:50],
                    sound="Hero",
                )
            except Exception as e:
                logger.debug(f"[ERROR] Transcription failed: {e}")
                self._notify(
                    subtitle="Transcription failed",
                    message=str(e),
                )
                rumps.alert("Transcription failed", str(e))
            finally:
                self.title = "🎙️"
                if self.temp_audio_file and os.path.exists(self.temp_audio_file):
                    os.unlink(self.temp_audio_file)

        threading.Thread(target=process).start()

    def insert_text(self, text: str):
        controller = Controller()
        # logger.debug("Typing text at cursor...")
        # controller.type(text)

        logger.debug("Copying text to the clipboard")
        pyperclip.copy(text)

    def _play_sound(self, sound_name: str):
        sound_path = f"/System/Library/Sounds/{sound_name}.aiff"
        if os.path.exists(sound_path):
            subprocess.Popen(["afplay", sound_path])

    def _notify(
        self,
        title: str = "NecroTongue",
        subtitle: str = "",
        message: str = "",
        sound: str = None,
    ):
        self.title = f"🎙️ ({subtitle}"

        # rumps.notification(title, subtitle, message)
        if sound:
            self._play_sound(sound)


if __name__ == "__main__":
    settings = Settings()
    NecroTongueApp(settings=settings).run()
