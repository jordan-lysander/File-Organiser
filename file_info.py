import logging
from pathlib import Path
from metadata import Metadata
import pymupdf

logger = logging.getLogger(__name__)

class FileInfo:
    def __init__(self, file: Path):
        self.metadata               = Metadata(file)
        self.summary: str | None    = None
        self.keywords: list[str]    = []

    def analyse_content(self, file: Path):
        mime = self.metadata.mime
        if mime.startswith('text/') or mime in ('application/pdf', 'application/msword'):
            text = self._extract_text(file)
            self.summary, self.keywords = self._summarise_text(text)

    def _extract_text(self, file: Path):
        ext = self.metadata.extension
        try:
            if ext in ['.txt', '.md']:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read(4000)
            elif ext == '.pdf':
                import pymupdf
                doc = pymupdf.open(file)
                return " ".join(page.get_text() or "" for page in doc.pages(5))
            elif ext in [".docx"]:
                from docx import Document
                doc = Document(str(file))
                return " ".join(p.text for p in doc.paragraphs[:30])
        except Exception as e:
            logger.error(f"Unknown error occured: {e}")
            return ""

    def _summarise_text(self, text: str):
        if not text.strip():
            logger.error(f"Empty or unreadable text")
            return ""

        trimmed = text[:2000]
        summary = summariser(trimmed, max_length=80, min_length=25, do_sample=False)