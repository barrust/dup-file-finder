"""
Core functionality for finding duplicate files.
"""

import os
import hashlib
import sqlite3
from typing import Dict, List, Set, Optional
from pathlib import Path


class FileDuplicateFinder:
    """
    A class to find and manage duplicate files.
    """

    def __init__(self, db_path: str = "deduper.db"):
        """
        Initialize the FileDuplicateFinder.

        Args:
            db_path: Path to the SQLite database file
        """
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
                hash TEXT NOT NULL,
                size INTEGER NOT NULL,
                extension TEXT,
                scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_hash ON files(hash)
        """)
        
        conn.commit()
        conn.close()

    def calculate_file_hash(self, file_path: str, algorithm: str = "sha256") -> str:
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

    def scan_directory(self, directory: str, recursive: bool = True) -> int:
        """
        Scan a directory for files and store their information in the database.

        Args:
            directory: Directory path to scan
            recursive: Whether to scan subdirectories recursively

        Returns:
            Number of files scanned
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        files_scanned = 0

        if recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        self._store_file(cursor, file_path)
                        files_scanned += 1
                    except (OSError, PermissionError):
                        # Skip files that can't be read
                        continue
        else:
            for item in os.listdir(directory):
                file_path = os.path.join(directory, item)
                if os.path.isfile(file_path):
                    try:
                        self._store_file(cursor, file_path)
                        files_scanned += 1
                    except (OSError, PermissionError):
                        continue

        conn.commit()
        conn.close()
        return files_scanned

    def _store_file(self, cursor, file_path: str):
        """Store file information in the database."""
        file_hash = self.calculate_file_hash(file_path)
        file_size = os.path.getsize(file_path)
        abs_path = os.path.abspath(file_path)
        
        # Extract file extension (including the dot, e.g., ".txt")
        # Use empty string if no extension
        extension = os.path.splitext(file_path)[1].lower()

        cursor.execute(
            """
            INSERT OR REPLACE INTO files (path, hash, size, extension)
            VALUES (?, ?, ?, ?)
            """,
            (abs_path, file_hash, file_size, extension)
        )

    def find_duplicates(self) -> Dict[str, List[str]]:
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

        duplicates = {}
        for hash_val, path in cursor.fetchall():
            if hash_val not in duplicates:
                duplicates[hash_val] = []
            duplicates[hash_val].append(path)

        conn.close()
        return duplicates

    def get_duplicate_groups(self) -> List[List[str]]:
        """
        Get duplicate files as a list of groups.

        Returns:
            List of lists, where each inner list contains duplicate file paths
        """
        duplicates = self.find_duplicates()
        return list(duplicates.values())

    def delete_duplicates(self, keep_first: bool = True, dry_run: bool = True) -> List[str]:
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

    def get_statistics(self) -> Dict[str, int]:
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

    def get_statistics_by_extension(self) -> Dict[str, Dict[str, int]]:
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
