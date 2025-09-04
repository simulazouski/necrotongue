import threading
from typing import Callable

from loguru import logger
from pynput import keyboard
from pynput.keyboard import Key


class InputMonitor:
    """
    Monitors for a specific key combo and calls
    on_press / on_release callbacks.

    Designed to run in a background thread.
    """

    def __init__(self, base_keys: set[Key], task_keys: set[Key]):
        self.base_keys = base_keys
        self.task_keys = task_keys

        self.pressed_keys = set()
        self.combo_triggered_key = None
        self._combo_triggered = False

        self.on_press = None
        self.on_release = None
        self._thread = None
        self._running = False

    def start(
        self,
        on_press: Callable[[], None] = None,
        on_release: Callable[[], None] = None,
    ):
        """Start the listener in a background thread"""
        self.on_press = on_press
        self.on_release = on_release
        self._running = True

        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the listener (not cleanly due to pynput limitation)"""
        self._running = False
        # pynput's listener.join() will block forever unless key is pressed again;
        # you may want to switch libraries if hard stop is required

    def _listen(self):
        def _on_press(key):
            if key not in self.base_keys and key not in self.task_keys:
                return

            self.pressed_keys.add(key)
            logger.debug(f"{key} | Currently pressed: {self.pressed_keys}")

            # Only call combo callback once per press
            for task_key in self.task_keys:
                combo_keys = {*self.base_keys, task_key}
                if combo_keys.issubset(self.pressed_keys) and not self._combo_triggered:
                    logger.debug("✅ Ctrl + Shift + Task key combo pressed")

                    self._combo_triggered = True
                    self.combo_triggered_key = task_key

                    if self._combo_triggered:
                        try:
                            self.on_press()
                        except Exception as e:
                            logger.debug(f"on_press error: {e}")

        def _on_release(key):
            if key not in self.base_keys and key not in self.task_keys:
                return

            self.pressed_keys.discard(key)

            logger.debug(f"{key} | Remaining: {self.pressed_keys}")

            if self.on_release and self._combo_triggered:
                try:
                    self.on_release()
                except Exception as e:
                    logger.debug(f"on_release error: {e}")

            # Reset combo trigger when either key is released
            self._combo_triggered = False

        try:
            with keyboard.Listener(
                on_press=_on_press,
                on_release=_on_release,
            ) as listener:
                logger.debug("Listening for Ctrl + Shift combo...")
                self._listener = listener
                listener.join()
        except Exception as e:
            logger.debug(f"Error: {e}")
            logger.debug("⚠️ Check accessibility permissions on macOS.")
