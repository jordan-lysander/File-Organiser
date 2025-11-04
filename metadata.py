import logging
from pathlib import Path
import mimetypes
import filetype
from PIL import Image
import ffmpeg

from rules import EXTENSION_TO_CATEGORY as ext_to_cat

logger = logging.getLogger(__name__)

class Metadata:
    """A container class to extract and hold a file's metadata."""
    def __init__(self, file: str | Path):
        file = file if isinstance(file, Path) else Path(file)
        self.path: Path = file.absolute()
        self.name: str      = file.name
        self.extension: str = file.suffix.lower()
        self.mime: str      = self._get_mime(file)

        # File system stats
        stats = file.stat()
        self.size_kb: float     = round(stats.st_size / 1024, 1)
        self.created: float     = stats.st_birthtime
        self.modified: float    = stats.st_mtime

        # Media specifics
        self.resolution: str | None = None
        self.duration_secs: float | None = None
        self.codec : str | None = None

        # Populate media attributes based on Mime type
        self._populate_media_attributes(file)

    def _get_mime(self, file: Path) -> str:
        """Determines the MIME type of a file using multiple strategies for accuracy."""
        try:
            kind = filetype.guess_mime(file)
            if kind:
                return kind
            
            mime, _ = mimetypes.guess_type(file)
            if mime:
                return mime
            
            return ""
        except (PermissionError, OSError):
            logger.warning(f"Permission denied while trying to read '{file.name}'")
            return ""
        
    def _populate_media_attributes(self, file: Path):
        """Dispatcher to call the correct metadata extraction method based on MIME type."""
        if not self.mime:
            return
        
        media_type = self.mime.split("/")[0]

        if media_type == 'image':
            self._extract_image_data(file)
        elif media_type == 'video':
            self._extract_video_data(file)

    def _extract_image_data(self, file: Path):
        """Extracts metadata specific to image files."""
        try:
            with Image.open(file) as img:
                width, height = img.size
                self.resolution = f"{width}x{height}"
        except IOError:
            logger.error(f"Could not open image file '{file.name}'. Unsupported format?")

    def _extract_video_data(self, file: Path):
        """Extracts metadata specific to video files."""
        try:
            probe = ffmpeg.probe(str(file))
            video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
            
            if not video_stream:
                logger.error(f"Could not access video streams in '{file.name}' via ffprobe.")
                return
            
            width = video_stream.get('width')
            height = video_stream.get('height')
            if width and height:
                self.resolution = f"{width}x{height}"

            self.codec = video_stream.get('codec_name', 'N/A')
            duration_str = video_stream.get('duration') or probe.get('format', {}).get('duration')
            if duration_str:
                self.duration = round(float(duration_str), 2)
                
        except ffmpeg.Error as e:
            logger.error(f"Could not read video file '{file.name}'. Error: {e}")
    
    def to_json(self) -> dict | None:
        """Returns a dictionary representation of this object's attributes."""
        return {key: value for key, value in self.__dict__.items() if not key.startswith('_')}

if __name__ == "__main__":
    path = Path("C:/2025 Software Dev/Portfolio Projects/File Organiser/Root/Disorganised Files/istockphoto-1138600688-1024x1024.jpg")
    file = Metadata(path)
    print(file.to_json())