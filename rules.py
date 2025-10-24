from pathlib import Path
import mimetypes
import filetype

file_types = {
    'image': ['jpg', 'png', 'gif', 'tif', 'bmp', 'svg'],
    'video': ['mp4', 'avi', 'wmv', 'mov', 'mpeg'],
    'audio': ['mp3', 'wav', 'aac', 'ogg', 'flac', 'midi'],
    'document': ['docx', 'pdf', 'txt', 'odt'],
    'presentation': ['pptx', 'odp'],
    'spreadsheets': ['xlsx', 'csv', 'ods'],
    'archives': ['zip', 'rar', '7z', 'tar', 'gz']
}

if __name__ == "__main__":
    pass