# File Utilities
import os
from app.config import settings


def get_upload_path(filename: str) -> str:
    """Get the full path for an uploaded file, creating the directory if needed."""
    os.makedirs(settings.upload_dir, exist_ok=True)
    return os.path.join(settings.upload_dir, filename)


def get_audio_path(podcast_id: str) -> str:
    """Get the full path for an audio file, creating the directory if needed."""
    os.makedirs(settings.audio_dir, exist_ok=True)
    return os.path.join(settings.audio_dir, f"{podcast_id}.mp3")