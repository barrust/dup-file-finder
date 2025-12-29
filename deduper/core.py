"""
Core functionality for finding duplicate files.
"""

import os
import hashlib
import sqlite3
from pathlib import Path


class DuplicateFileFinder:
    """
    A class to find and manage duplicate files.
    """

    db_path: Path

    def __init__(self, db_path: Path | str = "deduper.db"):
        """
        Initialize the DuplicateFileFinder.

        Args:
            db_path: Path to the SQLite database file
        """
        if isinstance(db_path, str):
            db_path = Path(db_path)
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize the SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL UNIQUE,
                filename TEXT,
                extension TEXT,
                hash TEXT NOT NULL,
                size INTEGER NOT NULL,
                scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_hash ON files(hash)
        """)

        # New table for unreadable files
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS unreadable_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                error_type TEXT NOT NULL,
                scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def calculate_file_hash(self, file_path: Path, algorithm: str = "sha256") -> str:
        """
        Calculate the hash of a file.

        Args:
            file_path: Path to the file
            algorithm: Hashing algorithm to use (md5, sha256)

        Returns:
            Hexadecimal hash string
        """
        if algorithm == "md5":
            hasher = hashlib.md5()
        else:
            hasher = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)

        return hasher.hexdigest()

    def scan_directory(self, directory: Path | str, recursive: bool = True) -> int:
        """
        Scan a directory for files and store their information in the database.

        Args:
            directory: Directory path to scan
            recursive: Whether to scan subdirectories recursively

        Returns:
            Number of files scanned
        """
        if isinstance(directory, str):
            directory = Path(directory)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        files_scanned = 0

        if recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        self._store_file(cursor, file_path)
                        files_scanned += 1
                    except (OSError, PermissionError) as e:
                        # Log files that can't be read
                        self._log_unreadable_file(cursor, file_path, type(e).__name__)
                        continue
        else:
            for item in directory.iterdir():
                if item.is_file():
                    try:
                        self._store_file(cursor, item)
                        files_scanned += 1
                    except (OSError, PermissionError) as e:
                        self._log_unreadable_file(cursor, item, type(e).__name__)
                        continue
        conn.commit()
        conn.close()
        return files_scanned

    def _log_unreadable_file(self, cursor, file_path: Path, error_type: str):
        """Log unreadable file information in the database."""
        abs_path = str(file_path.resolve())
        cursor.execute(
            """
            INSERT INTO unreadable_files (path, error_type)
            VALUES (?, ?)
            """,
            (abs_path, error_type)
        )



    def _store_file(self, cursor, file_path: Path):
        """Store file information in the database."""
        file_hash = self.calculate_file_hash(file_path)
        file_size = file_path.stat().st_size
        abs_path = str(file_path.resolve())
        filename = file_path.stem
        extension = file_path.suffix.lower()

        cursor.execute(
            """
            INSERT OR REPLACE INTO files (path, filename, extension, hash, size)
            VALUES (?, ?, ?, ?, ?)
            """,
            (abs_path, filename, extension, file_hash, file_size)
        )

    def find_duplicates(self) -> dict[str, list[str]]:
        """
        Find all duplicate files in the database.

        Returns:
            Dictionary mapping hash to list of file paths
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT hash, path
            FROM files
            WHERE hash IN (
                SELECT hash
                FROM files
                GROUP BY hash
                HAVING COUNT(*) > 1
            )
            ORDER BY hash, path
        """)

        duplicates: dict[str, list[str]] = {}
        for hash_val, path in cursor.fetchall():
            if hash_val not in duplicates:
                duplicates[hash_val] = []
            duplicates[hash_val].append(path)

        conn.close()
        return duplicates

    def get_duplicate_groups(self) -> list[list[str]]:
        """
        Get duplicate files as a list of groups.

        Returns:
            List of lists, where each inner list contains duplicate file paths
        """
        duplicates = self.find_duplicates()
        return list(duplicates.values())

    def delete_duplicates(self, keep_first: bool = True, dry_run: bool = True) -> list[str]:
        """
        Delete duplicate files, keeping one copy.

        Args:
            keep_first: If True, keep the first file (alphabetically), else keep the last
            dry_run: If True, only return files that would be deleted without deleting

        Returns:
            List of file paths that were (or would be) deleted
        """
        duplicates = self.find_duplicates()
        deleted_files = []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for hash_val, file_list in duplicates.items():
            sorted_files = sorted(file_list)

            if keep_first:
                files_to_delete = sorted_files[1:]
            else:
                files_to_delete = sorted_files[:-1]

            for file_path in files_to_delete:
                if not dry_run:
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            cursor.execute("DELETE FROM files WHERE path = ?", (file_path,))
                            deleted_files.append(file_path)
                    except (OSError, PermissionError):
                        # Skip files that can't be deleted
                        continue
                else:
                    deleted_files.append(file_path)

        if not dry_run:
            conn.commit()
        conn.close()

        return deleted_files

    def clear_database(self):
        """Clear all entries from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM files")
        conn.commit()
        conn.close()

    def get_statistics(self) -> dict[str, int]:
        """
        Get statistics about scanned files and duplicates.

        Returns:
            Dictionary with statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM files")
        total_files = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(DISTINCT hash)
            FROM files
            WHERE hash IN (
                SELECT hash
                FROM files
                GROUP BY hash
                HAVING COUNT(*) > 1
            )
        """)
        duplicate_groups = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM files
            WHERE hash IN (
                SELECT hash
                FROM files
                GROUP BY hash
                HAVING COUNT(*) > 1
            )
        """)
        duplicate_files = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(size) FROM files")
        total_size = cursor.fetchone()[0] or 0

        conn.close()

        return {
            "total_files": total_files,
            "duplicate_groups": duplicate_groups,
            "duplicate_files": duplicate_files,
            "unique_files": total_files - duplicate_files,
            "total_size_bytes": total_size
        }

    def get_statistics_by_extension(self) -> dict[str, dict[str, int]]:
        """
        Get statistics grouped by file extension.

        Returns:
            Dictionary mapping extension to statistics (count, total_size)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                extension,
                COUNT(*) as count,
                SUM(size) as total_size
            FROM files
            GROUP BY extension
            ORDER BY count DESC
        """)

        result = {}
        for ext, count, total_size in cursor.fetchall():
            # Use empty string as key for files without extension
            key = ext if ext else ""
            result[key] = {
                "count": count,
                "total_size_bytes": total_size or 0
            }

        conn.close()
        return result
