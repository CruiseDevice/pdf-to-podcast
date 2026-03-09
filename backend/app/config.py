import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Base directory (backend folder)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "PDF to Podcast"
    database_url: str = f"sqlite:///{BASE_DIR}/pdfpodcast.db"
    groq_api_key: str = ""
    upload_dir: str = str(BASE_DIR / "uploads")
    audio_dir: str = str(BASE_DIR / "audio")
    max_file_size: int = 10 * 1024 * 1024  # 10MB

    # Script Generator settings
    groq_model: str = "llama-3.1-8b-instant"
    script_chunk_size: int = 3000  # chars per chunk for LLM processing

    class Config:
        env_file = ".env"


settings = Settings()
