from dataclasses import dataclass
from pathlib import Path

@dataclass
class FileOperation:
    """
    Represents a planned operation on a file.

    - category can be a nested relative path like "Documents/Essays".
    - If final_name is provided, it will be used as-is.
    - Else if new_name (legacy) is provided, it will be used.
    - Else if new_stem is provided, final name becomes f"{new_stem}{source_path.suffix}".
    - Else falls back to the original filename.
    """
    source_path: Path
    category: str
    # Legacy: full filename including extension (kept for backward compatibility)
    new_name: str | None = None
    # Preferred: either provide a full final_name or just a new_stem (without extension)
    final_name: str | None = None
    new_stem: str | None = None

    @property
    def resolved_final_name(self) -> str:
        if self.final_name:
            return self.final_name
        if self.new_name:  # legacy path
            return self.new_name
        if self.new_stem:
            return f"{self.new_stem}{self.source_path.suffix}"
        return self.source_path.name