import sqlite3
import logging
import json
from pathlib import Path
from file_info import FileInfo

logger = logging.getLogger(__name__)

DB_PATH = "file_analysis.db"

class DatabaseManager:
    """Manages the SQLite database for storing file information."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._conn = None
        self.connect()
        self._create_table()

    def connect(self):
        """Establishes a connection to the SQLite database."""
        try:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            logger.info(f"Successfully connected to database at '{self.db_path}'")
        except sqlite3.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def _create_table(self):
        """Creates the 'files' table if it doesn't already exist."""

        try:
            with self._conn:
                self._conn.execute("""
                    CREATE TABLE IF NOT EXISTS files (
                        path TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        extension TEXT,
                        size_kb REAL,
                        created REAL,
                        modified REAL,
                        mime TEXT,
                        resolution TEXT,
                        duration_secs REAL,
                        codec TEXT,
                        summary TEXT,
                        keywords TEXT
                    )
                """)
            logger.info("Table 'files' is ready.")
        except sqlite3.Error as e:
            logger.error(f"Failed to create table: {e}")

    def file_needs_update(self, file_path: Path):
        """Checks if a file is new or has been modified since the last analysis."""
        pass

    def add_or_update_file(self, file_info: FileInfo):
        """Adds a new file record or updates an existing one."""
        metadata = file_info.metadata
        data = {
            'path': str(metadata.path),
            'name': metadata.name,
            'extension': metadata.extension,
            'size_kb': metadata.size_kb,
            "created": metadata.created,
            "modified": metadata.modified,
            "mime": metadata.mime,
            "resolution": metadata.resolution,
            "duration_secs": metadata.duration_secs,
            "codec": metadata.codec,
            "summary": file_info.summary,
            "keywords": json.dumps(file_info.keywords)
        }
        try:
            with self._conn:
                self._conn.execute("""
                    INSERT OR REPLACE INTO files (path, name, extension, size_kb, created, modified, mime, resolution, duration_secs, codec, summary, keywords)
                    VALUES (:path, :name, :extension, :size_kb, :created, :modified, :mime, :resolution, :duration_secs, :codec, :summary, :keywords)
                """, data)
            logger.info(f"Upserted file info for '{metadata.name}'")
        except sqlite3.Error as e:
            logger.error(f"Failed to upsert data for '{metadata.name}': {e}")

    def get_all_files(self):
        """Retrieves all file records from the database."""
        try:
            cursor = self._conn.execute("SELECT * FROM files")
            all_files = [dict(row) for row in cursor.fetchall()]
            logger.info(f"Retrieved {len(all_files)} records.")
            return all_files
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve all files: {e}")
            return []
        
    def close(self):
        """Closes the database connection."""
        if self._conn:
            self._conn.close()
            logger.info("Database connection closed.")