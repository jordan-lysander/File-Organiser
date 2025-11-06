import logging
from pathlib import Path
import ffmpeg
import numpy as np
from PIL import Image
from local_llm import LocalLLM
from metadata import Metadata
import zipfile

logger = logging.getLogger(__name__)

class ContentAnalyser:
    """Performs content analysis on a given file using various tools."""
    def __init__(self):
        self.llm = LocalLLM()

    def get_text_summary(self, text: str, **kwargs):
        """Generates a summary for the given text."""
        if not text or not text.strip():
            return ""
        return self.llm.summarise_text(text, **kwargs)
    
    def get_image_summary(self, image: Path | Image.Image, **kwargs):
        """Generates a summary for the given image."""
        if not image:
            return None
        return self.llm.summarise_image(image, **kwargs)
    
    def get_media_summary(self, metadata: Metadata):
        """Creates a summary from existing video/audio metadata."""
        parts = []
        media_type = metadata.mime.split('/')[0]
        if metadata.resolution:
            parts.append(f"{metadata.resolution}")
        if metadata.duration_secs:
            duration = int(metadata.duration_secs)
            parts.append(f"{duration // 60}m {duration % 60}s")
        if metadata.codec:
            parts.append(f"({metadata.codec} codec)")
        
        return f"A {media_type} file: " + ", ".join(parts) if parts else f"A {media_type} file."
    
    def get_rich_media_summary(self, media: Path, metadata: Metadata):
        """Generates an in-depth summary for a video file by analysing a representative frame."""
        summary = ""
        try:
            logger.info(f"Analysing a frame from '{media.name}'...")
            duration = float(metadata.duration_secs or 10)
            seek_time = duration * 0.25
            if not metadata.resolution:
                logger.error(f"Resolution not found in metadata for '{media.name}'")
                return ""
            
            height, width = (int(v) for v in metadata.resolution.split('x'))

            out, _ = (
                ffmpeg.input(media, ss=seek_time)
                .output('pipe:', vframes=1, format='rawvideo', pix_fmt='rgb24')
                .run(capture_stdout=True, quiet=True)
            )
            frame = np.frombuffer(out, np.uint8).reshape([height, width, 3])
            frame_image = Image.fromarray(frame)

            summary = self.get_image_summary(frame_image)

        except Exception as e:
            logger.warning(f"Could not analyse frame for {media.name}: {e}")

        return summary
    
    def get_archive_summary(self, file: Path, max_files: int = 5):
        """Creates a summary by listing the contents of a zipe file."""
        try:
            with zipfile.ZipFile(file, 'r') as zf:
                files = zf.namelist()
                num_files = len(files)

                summary_files = ", ".join(f"'{f}'" for f in files[:max_files])
                etc = "..." if num_files > max_files else ""

                return f"A zip archive containing {num_files} files, including: {summary_files}{etc}"
        except (zipfile.BadZipFile, IOError) as e:
            logger.error(f"Could not read archive '{file.name}': {e}")
            return "A corrupted or unreadable zip archive."