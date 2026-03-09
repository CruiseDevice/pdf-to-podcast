import uuid
import os
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends
from fastapi import BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.schemas import PodcastResponse, PodcastDetail
from app.database import get_db
from app.models import Podcast, PodcastStatus
from app.services.pipeline import process_podcast
from app.utils.file_utils import get_upload_path
from app.config import settings


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/podcasts", response_model=PodcastResponse)
async def create_podcast(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a PDF and create podcast job
    """

    # validate file
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, 'Only PDF files are accepted')

    # check file size
    content = await file.read()
    if len(content) > settings.max_file_size:
        raise HTTPException(400, f"File size must be under {settings.max_file_size // (1024 * 1024)}MB")
    
    # create podcast record
    podcast_id = str(uuid.uuid4())
    filename = f"{podcast_id}_{file.filename}"
    file_path = get_upload_path(filename)

    # save file
    import aiofiles
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)

    # create database record
    podcast = Podcast(
        id=podcast_id,
        title=title,
        description=description,
        source_filename=file.filename,
        source_file_path=file_path,
        status=PodcastStatus.PENDING.value
    )

    db.add(podcast)
    db.commit()
    db.refresh(podcast)

    # start background processing
    background_tasks.add_task(process_podcast, podcast_id)

    logger.info(f"Created podcast {podcast_id}: {title}")
    return podcast


@router.get("/podcasts",
response_model=list[PodcastResponse])
async def list_podcast(db: Session = Depends(get_db)):
    """
    List all podcasts
    """
    podcasts = db.query(Podcast).order_by(Podcast.created_at.desc()).all()
    return podcasts


@router.get("/podcasts/{podcast_id}",
response_model=PodcastDetail)
async def get_podcast(podcast_id: str, db: Session = Depends(get_db)):
    """
    Get podcast details including extracted text and transcript
    """
    podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
    if not podcast:
        raise HTTPException(404, "Podcast not found")
    return podcast


@router.get("/podcasts/{podcast_id}/status")
async def get_podcast_status(podcast_id: str, db: Session = Depends(get_db)):
    """Get just the status of a podcast (for polling)"""
    podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
    if not podcast:
        raise HTTPException(404, "Podcast not found")

    return {
        "id": podcast.id,
        "status": podcast.status,
        "error_message": podcast.error_message
    }


@router.delete("/podcasts/{podcast_id}")
async def delete_podcast(podcast_id: str, db: Session = Depends(get_db)):
    """Delete podcast and associated files"""
    podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
    if not podcast:
        raise HTTPException(404, "Podcast not found")

    # Delete files
    if podcast.source_file_path and os.path.exists(podcast.source_file_path):
        os.remove(podcast.source_file_path)
    if podcast.audio_file_path and os.path.exists(podcast.audio_file_path):
        os.remove(podcast.audio_file_path)

    db.delete(podcast)
    db.commit()

    return {"message": "Podcast deleted"}


@router.post("/test/script-generator")
async def test_script_generator(
    text: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Test endpoint: Generate script from raw text (bypasses PDF)
    """
    from app.services.script_generator import ScriptGenerator
    
    generator = ScriptGenerator()
    script = generator.generate_podcast_script(text)

    return {
        "script": script
    }


@router.post("/process")
async def process(background_tasks: BackgroundTasks):
    # view pending tasks
    print(background_tasks.tasks)   # List of pending tasks
    return {
        "status": "processing"
    }


@router.post("/test/tts")
async def test_tts(
    text: str = Form(...),
    voice: Optional[str] = Form(None)
):
    """Test endpoint: Convert text to speech and return audio"""
    from app.services.tts_service import TTSService
    import tempfile

    tts = TTSService()

    # Create temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        audio_path = tmp.name

    await tts.text_to_speech(text, audio_path, voice)

    return FileResponse(
        audio_path,
        media_type="audio/mpeg",
        filename="test_output.mp3"
    )


@router.get("/podcasts/{podcast_id}/audio")
async def get_audio(podcast_id: str, db: Session = Depends(get_db)):
    """Download podcast audio"""
    podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
    if not podcast:
        raise HTTPException(404, "Podcast not found")

    if podcast.status != PodcastStatus.COMPLETED.value:
        raise HTTPException(400, f"Podcast not ready. Status: {podcast.status}")

    return FileResponse(
        podcast.audio_file_path,
        media_type="audio/mpeg",
        filename=f"{podcast.title}.mp3"
    )

@router.get("/podcasts/{podcast_id}/transcript")
async def get_transcript(podcast_id: str, db: Session = Depends(get_db)):
    """Get podcast transcript"""
    podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
    if not podcast:
        raise HTTPException(404, "Podcast not found")

    return {
        "transcript": podcast.transcript,
        "extracted_text": podcast.extracted_text
    }