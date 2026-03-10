from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PodcastResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    source_filename: str
    status: str
    mode: str = "single"
    voice_preset: str = "default"
    created_at: datetime

    class Config:
        from_attributes = True


class PodcastDetail(PodcastResponse):
    """
    Extracted response with extracted text and transcript
    """
    extracted_text: Optional[str] = None
    transcript: Optional[str] = None
    error_message: Optional[str] = None