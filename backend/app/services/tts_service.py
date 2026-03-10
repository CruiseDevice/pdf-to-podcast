# TTS Service
import logging
import re
import asyncio
import tempfile
import os
import random
from typing import Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor
import edge_tts

logger = logging.getLogger(__name__)

# Thread pool for blocking operations
_executor = ThreadPoolExecutor(max_workers=2)


class TTSService:
    def __init__(self):
        # Edge TTS voices - free and high availability
        self.default_voice = "en-US-AvaNeural"  # Female, natural
        self.alternative_voices = {
            "male": "en-US-GuyNeural",
            "female": "en-US-AvaNeural",
            "british": "en-GB-SoniaNeural"
        }
        self.voice_presets = {
            "default": {"SPEAKER_A": "en-US-AvaNeural", "SPEAKER_B": "en-US-GuyNeural"},
            "female_female": {"SPEAKER_A": "en-US-AvaNeural", "SPEAKER_B": "en-GB-SoniaNeural"},
            "male_male": {"SPEAKER_A": "en-US-GuyNeural", "SPEAKER_B": "en-US-ChristopherNeural"},
            "british": {"SPEAKER_A": "en-GB-SoniaNeural", "SPEAKER_B": "en-GB-RyanNeural"},
        }
        # Speaking rate variation range (Edge TTS supports +/- percentage)
        self.rate_variation = (-5, 5)  # +/- 5% variation for naturalness

    def _get_random_rate(self) -> str:
        """Get a randomized speaking rate for natural variation."""
        variation = random.randint(*self.rate_variation)
        if variation > 0:
            return f"+{variation}%"
        elif variation < 0:
            return f"{variation}%"
        return "+0%"

    def _normalize_script(self, script: str) -> str:
        """Normalize script to handle common variations in speaker labels and strip markdown."""
        # First, strip markdown formatting around speaker labels (e.g., **SPEAKER_A:** -> SPEAKER_A:)
        script = re.sub(r'\*{1,2}\s*(SPEAKER_[AB])\s*\*{0,2}\s*:', r'\1:', script, flags=re.IGNORECASE)
        script = re.sub(r'_{1,2}\s*(SPEAKER_[AB])\s*_{0,2}\s*:', r'\1:', script, flags=re.IGNORECASE)

        # Normalize speaker labels to uppercase with underscore
        script = re.sub(r'\b[Ss]peaker[-_]?[Aa]\b', 'SPEAKER_A', script)
        script = re.sub(r'\b[Ss]peaker[-_]?[Bb]\b', 'SPEAKER_B', script)
        # Also handle variations like "Host A:", "Host 1:", etc.
        script = re.sub(r'\bHost\s*[-_]?[Aa1]\b', 'SPEAKER_A', script)
        script = re.sub(r'\bHost\s*[-_]?[Bb2]\b', 'SPEAKER_B', script)

        # Strip any remaining markdown bold/italic around dialogue text
        # But be careful not to strip emphasis that's part of the actual speech

        return script

    def parse_dialogue(self, script: str) -> List[Tuple[str, str]]:
        """
        Parse a dual-host script into speaker/text pairs.
        Returns list of (speaker, text) tuples.
        Handles edge cases like malformed labels, multi-line text, etc.
        """
        # Normalize the script first
        script = self._normalize_script(script)

        # More flexible regex that handles:
        # - Optional whitespace after colon
        # - Multi-line text until next speaker or end
        # - Empty lines between dialogue
        pattern = r'(SPEAKER_[AB])\s*:\s*(.*?)(?=\n\s*(?:SPEAKER_[AB])\s*:|$)'
        matches = re.findall(pattern, script, re.DOTALL | re.IGNORECASE)

        # Clean up the results
        result = []
        for speaker, text in matches:
            text = text.strip()
            # Skip empty dialogue
            if text:
                result.append((speaker.upper(), text))

        return result

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

    def _sync_concatenate(self, audio_files: List[str], output_path: str, pause_ms: int = 300):
        """Synchronous audio concatenation using pydub."""
        from pydub import AudioSegment

        combined = AudioSegment.empty()
        for audio_file in audio_files:
            segment = AudioSegment.from_mp3(audio_file)
            combined += segment
            combined += AudioSegment.silent(duration=pause_ms)

        combined.export(output_path, format="mp3")

    async def _concatenate_audio(self, audio_files: List[str], output_path: str, pause_ms: int = 300):
        """Concatenate MP3 files using pydub with natural pauses (non-blocking)."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(_executor, self._sync_concatenate, audio_files, output_path, pause_ms)

    async def text_to_speech_dual(
        self,
        script: str,
        output_path: str,
        voice_preset: str = "default"
    ) -> Tuple[str, bool]:
        """
        Convert dual-host script to speech with different voices per speaker.
        Returns (path to audio file, fallback_to_single flag).
        If dialogue parsing fails, falls back to single-host mode.
        """
        # Parse dialogue
        dialogue_parts = self.parse_dialogue(script)
        if not dialogue_parts:
            # Fallback: treat as single-host
            logger.warning("No dialogue parts found in dual-host script, falling back to single-host mode")
            audio_path = await self.text_to_speech(script, output_path)
            return audio_path, True  # Return True to indicate fallback

        logger.info(f"Parsed {len(dialogue_parts)} dialogue segments")

        # Get voice mapping
        voices = self.voice_presets.get(voice_preset, self.voice_presets["default"])

        # Generate audio for each segment in parallel with rate limiting
        temp_dir = tempfile.mkdtemp()
        temp_files = []

        try:
            # Create tasks for parallel generation with semaphore for rate limiting
            semaphore = asyncio.Semaphore(3)  # Max 3 concurrent TTS requests

            async def generate_segment(idx: int, speaker: str, text: str) -> Tuple[int, str]:
                async with semaphore:
                    voice = voices.get(speaker, self.default_voice)
                    temp_path = os.path.join(temp_dir, f"segment_{idx}.mp3")

                    # Add slight rate variation for naturalness (+/- 5%)
                    rate = self._get_random_rate()
                    communicate = edge_tts.Communicate(text, voice, rate=rate)
                    await communicate.save(temp_path)

                    logger.info(f"Generated segment {idx + 1}/{len(dialogue_parts)} for {speaker} at rate {rate}")
                    return idx, temp_path

            # Generate all segments in parallel
            tasks = [
                generate_segment(i, speaker, text)
                for i, (speaker, text) in enumerate(dialogue_parts)
            ]

            results = await asyncio.gather(*tasks)

            # Sort by index to maintain order
            results.sort(key=lambda x: x[0])
            temp_files = [path for _, path in results]

            # Concatenate all segments
            await self._concatenate_audio(temp_files, output_path)

            logger.info(f"Dual-host audio saved to {output_path}")
            return output_path, False

        finally:
            # Cleanup temp files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            try:
                os.rmdir(temp_dir)
            except OSError:
                pass  # Directory not empty or already removed

    async def generate_audio(
        self,
        script: str,
        output_path: str,
        mode: str = "single",
        voice_preset: str = "default",
        voice: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Unified method for audio generation supporting both single and dual host modes.
        Returns (path to audio file, warning message if fallback occurred).
        """
        if mode == "dual":
            audio_path, fallback = await self.text_to_speech_dual(script, output_path, voice_preset)
            if fallback:
                return audio_path, "Dual-host script could not be parsed. Falling back to single-host narration."
            return audio_path, None
        else:
            audio_path = await self.text_to_speech(script, output_path, voice)
            return audio_path, None

    def get_available_voices(self) -> list:
        """Return list of available voices"""
        return [
            {"id": "en-US-AvaNeural", "name": "Ava (Female, US)", "gender": "female"},
            {"id": "en-US-GuyNeural", "name": "Guy (Male, US)", "gender": "male"},
            {"id": "en-GB-SoniaNeural", "name": "Sonia (Female, UK)", "gender": "female"},
            {"id": "en-AU-NatashaNeural", "name": "Natasha (Female, AU)", "gender": "female"},
        ]

    def get_voice_presets(self) -> dict:
        """Return available voice presets for dual-host podcasts"""
        return {
            "presets": [
                {
                    "id": "default",
                    "name": "Female + Male (US)",
                    "speakers": {
                        "SPEAKER_A": {"voice": "en-US-AvaNeural", "gender": "female"},
                        "SPEAKER_B": {"voice": "en-US-GuyNeural", "gender": "male"}
                    }
                },
                {
                    "id": "female_female",
                    "name": "Female Duo",
                    "speakers": {
                        "SPEAKER_A": {"voice": "en-US-AvaNeural", "gender": "female"},
                        "SPEAKER_B": {"voice": "en-GB-SoniaNeural", "gender": "female"}
                    }
                },
                {
                    "id": "male_male",
                    "name": "Male Duo",
                    "speakers": {
                        "SPEAKER_A": {"voice": "en-US-GuyNeural", "gender": "male"},
                        "SPEAKER_B": {"voice": "en-US-ChristopherNeural", "gender": "male"}
                    }
                },
                {
                    "id": "british",
                    "name": "British Duo",
                    "speakers": {
                        "SPEAKER_A": {"voice": "en-GB-SoniaNeural", "gender": "female"},
                        "SPEAKER_B": {"voice": "en-GB-RyanNeural", "gender": "male"}
                    }
                }
            ]
        }
