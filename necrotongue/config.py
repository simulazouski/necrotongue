from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings


class TranscribeServerSettings(BaseModel):
    model_path: Path
    port: int = 8981


class RefineServerSettings(BaseModel):
    model_path: Path
    port: int = 8980


class AppSettings(BaseModel):
    entrypoint: str = "necrotongue/app.py"


class Settings(BaseSettings):
    transcribe: TranscribeServerSettings
    refine: RefineServerSettings
    app: AppSettings

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
