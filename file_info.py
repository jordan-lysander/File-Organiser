import logging
from pathlib import Path
from metadata import Metadata
from content_analyser import ContentAnalyser

analyser = ContentAnalyser()

logger = logging.getLogger(__name__)

USE_RICH_MEDIA_SUMMARY = True

class FileInfo:
    def __init__(self, file: Path):
        self.metadata               = Metadata(file)
        self.summary: str | None    = None

        self.analyse_content(file)

    def analyse_content(self, file: Path):
        """Dispatcher to generate summary and keywords based on file type."""
        mime = self.metadata.mime
        if not mime:
            return
        
        type = mime.split('/')[0]

        if type == 'text' or mime in ('application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'):
            # remove the below line and move _extract_text into content_analyser to be used as part of the method
            text = self._extract_text(file)
            if text:
                self.summary = analyser.get_text_summary(text)

        elif type == 'image':
            self.summary = analyser.get_image_summary(file)

        elif type in ['video', 'audio']:
            if USE_RICH_MEDIA_SUMMARY:
                self.summary = analyser.get_rich_media_summary(file, self.metadata)
            else:
                self.summary = analyser.get_media_summary(self.metadata)

        elif mime in ['application/zip', 'application/x-zip-compressed']:
            self.summary = analyser.get_archive_summary(file)

    def _extract_text(self, file: Path):
        ext = self.metadata.extension
        try:
            if ext in ['.txt', '.md']:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read(4000)
            elif ext == '.pdf':
                import pymupdf
                doc = pymupdf.open(file)
                return " ".join(page.get_text() or "" for page in doc.pages(stop=5))
            elif ext in [".docx"]:
                from docx import Document
                doc = Document(str(file))
                return " ".join(p.text for p in doc.paragraphs[:30])
        except Exception as e:
            logger.error(f"Unknown error occured: {e}")
        return ""

if __name__ == "__main__":
    file = Path('Root/mix of images and video/VideoEffects-search-bar-modern-12-1-SD.mov')
    file_info = FileInfo(file)
    print(file_info.summary)    
    