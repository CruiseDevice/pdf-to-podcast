# Processing Pipeline
import logging
from datetime import datetime
from app.models import PodcastStatus
from app.database import SessionLocal
from app.models import Podcast

logger = logging.getLogger(__name__)


def process_podcast(podcast_id: str):
    """
    Main processing pipeline for converting PDF to podcast.
    Runs as background task.

    Step 1: Extract text from PDF
    Step 2: Generate podcast script using LLM
    Step 3: Convert script to audio using TTS
    """
    db = SessionLocal()

    try:
        podcast = db.query(Podcast).filter(Podcast.id == podcast_id).first()
        if not podcast:
            logger.error(f"Podcast {podcast_id} not found")
            return

        # Step 1: Extract text from PDF
        logger.info(f"[{podcast_id}] Extracting text from PDF...")
        podcast.status = PodcastStatus.EXTRACTING.value
        db.commit()

        from app.services.pdf_extractor import PDFExtractor
        extractor = PDFExtractor()
        raw_text = extractor.extract_text(podcast.source_file_path)

        # Store extracted text
        podcast.extracted_text = raw_text
        db.commit()

        logger.info(f"[{podcast_id}] Extracted {len(raw_text)} characters")

        # Step 2: Generate podcast script
        logger.info(f"[{podcast_id}] Generating podcast script...")
        podcast.status = PodcastStatus.GENERATING.value
        db.commit()

        from app.services.script_generator import ScriptGenerator
        generator = ScriptGenerator()
        script = generator.generate_podcast_script(raw_text)

        # Save transcript
        podcast.transcript = script
        db.commit()

        logger.info(f"[{podcast_id}] Generated script of {len(script)} characters")

        # Step 3: Convert to audio
        logger.info(f"[{podcast_id}] Converting to audio...")
        podcast.status = PodcastStatus.CONVERTING.value
        db.commit()

        from app.services.tts_service import TTSService
        from app.utils.file_utils import get_audio_path
        import asyncio

        tts = TTSService()
        audio_path = get_audio_path(podcast_id)
        asyncio.run(tts.text_to_speech(script, audio_path))

        # save audio path and complete
        podcast.audio_file_path = audio_path
        podcast.status = PodcastStatus.COMPLETED.value
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
