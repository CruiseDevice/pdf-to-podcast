# PDF Extractor Service
import logging
import fitz  # PyMuPDF
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class PDFExtractor:
    def extract_text(
        self,
        file_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """
        Extract text from PDF file.
        Returns cleaned text content.

        Args:
            file_path: Path to PDF file
            progress_callback: Optional callback(current_page, total_pages) for progress updates
        """
        text_parts = []

        doc = fitz.open(file_path)
        total_pages = len(doc)

        for i, page in enumerate(doc):
            page_text = page.get_text()
            if page_text:
                text_parts.append(page_text)

            if progress_callback:
                progress_callback(i + 1, total_pages)

        doc.close()

        full_text = "\n\n".join(text_parts)

        if not full_text.strip():
            raise ValueError("No text could be extracted from PDF")

        logger.info(f"Extracted {len(full_text)} characters from {file_path}")
        return full_text