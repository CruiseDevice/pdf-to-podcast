# Processing Pipeline
import logging
from datetime import datetime
from app.models import PodcastStatus
from app.database import SessionLocal
from app.models import Podcast

logger = logging.getLogger(__name__)


def update_progress(db, podcast_id: str, status: str, progress: int, message: str):
    """Update podcast progress in database."""
    podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
    if podcast:
        podcast.status = status
        podcast.progress = str(progress)
        podcast.progress_message = message
        db.commit()


def process_podcast(podcast_id: str):
    """
    Main processing pipeline for converting PDF to podcast.
    Runs as background task.

    Step 1: Extract text from PDF (0-20%)
    Step 2: Generate podcast script using LLM (20-60%)
    Step 3: Convert script to audio using TTS (60-100%)
    """
    db = SessionLocal()

    try:
        podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
        if not podcast:
            logger.error(f"Podcast {podcast_id} not found")
            return

        # Step 1: Extract text from PDF (0-20%)
        logger.info(f"[{podcast_id}] Extracting text from PDF...")
        update_progress(db, podcast_id, PodcastStatus.EXTRACTING.value, 5, "Opening PDF file...")

        from app.services.pdf_extractor import PDFExtractor
        extractor = PDFExtractor()

        def on_extract_progress(page: int, total: int):
            # Map extraction to 5-20% range
            progress = 5 + int((page / total) * 15)
            update_progress(db, podcast_id, PodcastStatus.EXTRACTING.value, progress,
                          f"Extracting page {page} of {total}...")

        raw_text = extractor.extract_text(podcast.source_file_path, on_extract_progress)

        # Store extracted text
        podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
        podcast.extracted_text = raw_text
        db.commit()

        logger.info(f"[{podcast_id}] Extracted {len(raw_text)} characters")

        # Step 2: Generate podcast script (20-60%)
        logger.info(f"[{podcast_id}] Generating podcast script...")
        update_progress(db, podcast_id, PodcastStatus.GENERATING.value, 22, "Analyzing document content...")

        from app.services.script_generator import ScriptGenerator
        generator = ScriptGenerator()

        # Get mode and voice_preset from podcast (with defaults for backward compatibility)
        podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
        mode = getattr(podcast, 'mode', 'single') or 'single'
        voice_preset = getattr(podcast, 'voice_preset', 'default') or 'default'

        update_progress(db, podcast_id, PodcastStatus.GENERATING.value, 28, "Identifying key topics...")
        update_progress(db, podcast_id, PodcastStatus.GENERATING.value, 35, "Creating podcast outline...")

        script = generator.generate_podcast_script(raw_text, mode=mode)

        update_progress(db, podcast_id, PodcastStatus.GENERATING.value, 55, "Polishing script...")

        # Save transcript
        podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
        podcast.transcript = script
        db.commit()

        logger.info(f"[{podcast_id}] Generated script of {len(script)} characters")

        # Step 3: Convert to audio (60-100%)
        logger.info(f"[{podcast_id}] Converting to audio...")
        update_progress(db, podcast_id, PodcastStatus.CONVERTING.value, 62, "Preparing text for synthesis...")

        from app.services.tts_service import TTSService
        from app.utils.file_utils import get_audio_path
        import asyncio

        update_progress(db, podcast_id, PodcastStatus.CONVERTING.value, 68, "Initializing voice synthesizer...")

        tts = TTSService()
        audio_path = get_audio_path(podcast_id)

        update_progress(db, podcast_id, PodcastStatus.CONVERTING.value, 75, "Converting text to speech...")

        audio_path, warning = asyncio.run(tts.generate_audio(script, audio_path, mode=mode, voice_preset=voice_preset))

        # Log warning if fallback occurred
        if warning:
            logger.warning(f"[{podcast_id}] {warning}")
            # Store warning in error_message so user can see it (but don't fail the podcast)
            podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
            podcast.error_message = warning
            db.commit()

        update_progress(db, podcast_id, PodcastStatus.CONVERTING.value, 95, "Finalizing audio file...")

        # save audio path and complete
        podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
        podcast.audio_file_path = audio_path
        podcast.status = PodcastStatus.COMPLETED.value
        podcast.progress = "100"
        podcast.progress_message = "Ready to play!"
        podcast.completed_at = datetime.utcnow()
        podcast.error_message = None    # clear any previous error

        db.commit()
        logger.info(f"[{podcast_id}] Processing complete!")

    except Exception as e:
        logger.error(f"[{podcast_id}] Processing failed: {str(e)}")
        # Rollback to clear any failed transaction state
        db.rollback()
        try:
            # Re-fetch podcast in case session was invalidated
            podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
            if podcast:
                podcast.status = PodcastStatus.FAILED.value
                podcast.error_message = str(e)
                db.commit()
        except Exception as commit_error:
            logger.error(f"[{podcast_id}] Failed to update error state: {str(commit_error)}")
            db.rollback()
    finally:
        db.close()
