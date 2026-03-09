# TTS Service
import logging
import edge_tts
from typing import Optional

logger = logging.getLogger(__name__)


class TTSService:
    def __init__(self):
        # Edge TTS voices - free and high availability
        self.default_voice = "en-US-AvaNeural"  # Female, natural
        self.alternative_voices = {
            "male": "en-US-GuyNeural",
            "female": "en-US-AvaNeural",
            "british": "en-GB-SoniaNeural"
        }

    async def text_to_speech(
        self,
        text: str,
        output_path: str,
        voice: Optional[str] = None
    ) -> str:
        """
        Convert text to speech and save as audio file.
        Returns path to audio file.
        """
        voice = voice or self.default_voice

        logger.info(f"Converting {len(text)} characters to speech with voice {voice}")

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)

        logger.info(f"Audio saved to {output_path}")
        return output_path

    def get_available_voices(self) -> list:
        """Return list of available voices"""
        return [
            {"id": "en-US-AvaNeural", "name": "Ava (Female, US)", "gender": "female"},
            {"id": "en-US-GuyNeural", "name": "Guy (Male, US)", "gender": "male"},
            {"id": "en-GB-SoniaNeural", "name": "Sonia (Female, UK)", "gender": "female"},
            {"id": "en-AU-NatashaNeural", "name": "Natasha (Female, AU)", "gender": "female"},
        ]