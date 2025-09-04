import os

import requests


class Transcriber:
    def __init__(
        self,
        whisper_url: str,
        refine_url: str,
        whisper_timeout: int = 5,
        refine_timeout: int = 5,
    ):
        self.whisper_url = whisper_url
        self.refine_url = refine_url
        self.whisper_timeout = whisper_timeout
        self.refine_timeout = refine_timeout

    def transcribe(self, audio_path: str) -> str:
        """Send audio to whisper server and return transcribed text"""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        with open(audio_path, "rb") as f:
            try:
                response = requests.post(
                    self.whisper_url,
                    params={"response_format": "json"},
                    files={"file": f},
                    timeout=self.whisper_timeout,
                )
                response.raise_for_status()
                data = response.json()
                return data.get("text", "").strip()
            except requests.RequestException as e:
                raise RuntimeError(f"Transcription failed: {e}")

    def refine(self, transcription: str, prompt: str) -> str:
        """Refine transcription using a local LLM chat interface"""
        if not self.refine_url:
            return transcription

        payload = {
            "model": "local-model",  # ignored by some local LLM servers
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Refine this: {transcription}"},
            ],
        }

        try:
            response = requests.post(
                self.refine_url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=self.refine_timeout,
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        except requests.RequestException as e:
            raise RuntimeError(f"Refinement failed: {e}")
