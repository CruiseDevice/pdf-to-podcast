import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from app.database import Base


class PodcastStatus(str, enum.Enum):
    PENDING = "pending"
    EXTRACTING = "extracting"
    GENERATING = "generating"
    CONVERTING = "converting"
    COMPLETED = "completed"
    FAILED = "failed"


class Podcast(Base):
    __tablename__ = "podcasts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    source_filename = Column(String(255), nullable=False)
    source_file_path = Column(String(500), nullable=False)
    audio_file_path = Column(String(500), nullable=True)
    extracted_text = Column(Text, nullable=True)
    transcript = Column(Text, nullable=True)
    status = Column(String(20), default=PodcastStatus.PENDING.value)
    progress = Column(String(10), default="0")  # 0-100
    progress_message = Column(String(255), nullable=True)  # e.g., "Extracting page 5 of 12"
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


