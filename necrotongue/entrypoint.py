import socket
import subprocess
import time

from config import Settings

settings = Settings()


def wait_for_port(port: str, host: str = "localhost", timeout: int = 30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    raise TimeoutError(f"Timeout waiting for port {port} on {host}")


# Launch local transcription model
whisper = subprocess.Popen(
    [
        "whisper-server",
        "--model",
        str(settings.transcribe.model_path),
        "--port",
        str(settings.transcribe.port),
    ]
)
wait_for_port(settings.transcribe.port)


# Launch local text refinement model
llama = subprocess.Popen(
    [
        "llama-server",
        "-m",
        str(settings.refine.model_path),
        "--port",
        str(settings.refine.port),
    ]
)
wait_for_port(settings.refine.port)


# Launch the main app
app = subprocess.Popen(["poetry", "run", "python3", settings.app.entrypoint])

try:
    while True:
        time.sleep(1)
        if any(p.poll() is not None for p in [llama, whisper, app]):
            break
finally:
    for proc in [llama, whisper, app]:
        if proc.poll() is None:
            proc.terminate()
