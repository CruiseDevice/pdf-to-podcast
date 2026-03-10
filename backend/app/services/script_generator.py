# Script Generator Service
from groq import Groq
from app.config import settings
from typing import Optional
import logging
import time

logger = logging.getLogger(__name__)


class ScriptGenerator:
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.groq_model
        self.chunk_size = settings.script_chunk_size

    def _chunk_text(self, text: str, chunk_size: int) -> list[str]:
        """Split text into chunks at paragraph boundaries."""
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _generate_chunk_script(self, chunk: str, is_first: bool, is_last: bool, mode: str = "single") -> str:
        """Generate script for a single chunk."""
        intro = "This is the beginning of the podcast. " if is_first else ""
        outro = " This concludes our podcast." if is_last else ""

        if mode == "dual":
            prompt = f"""You are a podcast script writer. Convert the following content into an engaging, conversational podcast script with TWO hosts having a NATURAL, HUMAN-LIKE conversation.

Guidelines:
- Write as a dialogue between two hosts (SPEAKER_A and SPEAKER_B)
- Each line MUST start with either "SPEAKER_A:" or "SPEAKER_B:" (plain text, NO markdown or special formatting)
- SPEAKER_A is the primary presenter, SPEAKER_B asks questions and adds insights

Make it sound natural and human:
- Use contractions always (don't, we're, it's instead of do not, we are, it is)
- Vary sentence length - mix short punchy remarks with longer explanations
- Add natural reactions like "Oh interesting", "Right", "Exactly", "That makes sense"
- Include occasional fillers like "well", "you know", "I mean" (but don't overdo it)
- Let speakers occasionally agree or build on each other's points
- Add moments of genuine curiosity or surprise

Dialogue flow:
- Alternate between speakers naturally
- Let conversations feel spontaneous, not scripted
- Include brief tangents that get steered back to the topic

CRITICAL - Do NOT include:
- Sound effects or music cues
- Narrator text
- Episode titles or headers
- Markdown formatting (no **, _, #, or any special characters)
- Any text that would be read aloud as punctuation (like "asterisk", "underscore", "hash")

Output format: Plain text only. Just speaker labels followed by dialogue.
Example:
SPEAKER_A: Hello and welcome...
SPEAKER_B: Thanks for having me...

{intro}{outro}

Source Content:
{chunk}

Podcast Script:"""
            system_message = "You are an expert podcast script writer who creates authentic, human-sounding conversations. Output plain text only - never use markdown, bold, italics, or any special formatting characters."
        else:
            prompt = f"""You are a podcast script writer. Convert the following content into an engaging, conversational podcast script.

Guidelines:
- Write in a natural, conversational tone
- Use clear transitions between topics
- Make complex ideas accessible
- Keep the audience engaged
- Do NOT include sound effects or music cues
- Do NOT include speaker names or labels
- Just write the narration text that will be read aloud
{intro}{outro}

Source Content:
{chunk}

Podcast Script:"""
            system_message = "You are an expert podcast script writer who creates engaging, conversational content."

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )

        return response.choices[0].message.content

    def generate_podcast_script(
        self,
        source_text: str,
        style: str = "conversational",
        max_length: int = 30000,
        mode: str = "single"
    ) -> str:
        """
        Convert source text into an engaging podcast script.
        Handles large texts by chunking.
        """
        # If text is small enough, process directly
        if len(source_text) <= self.chunk_size:
            return self._generate_chunk_script(source_text, is_first=True, is_last=True, mode=mode)

        # Chunk large texts
        chunks = self._chunk_text(source_text, self.chunk_size)
        logger.info(f"Split text into {len(chunks)} chunks")

        scripts = []
        for i, chunk in enumerate(chunks):
            is_first = (i == 0)
            is_last = (i == len(chunks) - 1)

            logger.info(f"Processing chunk {i + 1}/{len(chunks)}")
            script_part = self._generate_chunk_script(chunk, is_first, is_last, mode=mode)
            scripts.append(script_part)

            # Rate limit: wait between chunks to avoid TPM limits
            if i < len(chunks) - 1:
                time.sleep(2)

        full_script = "\n\n".join(scripts)
        logger.info(f"Generated script of {len(full_script)} characters")
        return full_script
