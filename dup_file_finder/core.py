"""
Core functionality for finding duplicate files.
"""

import hashlib
import os
import sqlite3
from pathlib import Path


class DuplicateFileFinder:
    """
    A class to find and manage duplicate files.
    """

    __slots__ = ("db_path", "bulk_size", "algorithm")

    db_path: Path
    bulk_size: int
    algorithm: str

    def __init__(self, bulk_size: int = 1000, algorithm: str = "sha256", db_path: Path | str = "deduper.db"):
        """
        Initialize the DuplicateFileFinder.

        Args:
            bulk_size: Number of files to process before committing to the database
            algorithm: Hashing algorithm to use (md5, sha256)
            db_path: Path to the SQLite database file
        """
        if isinstance(db_path, str):
            db_path = Path(db_path).absolute()
        self.db_path = db_path
        self.bulk_size = bulk_size
        self.algorithm = algorithm
        self._init_database()

    def _init_database(self):
        """Initialize the SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL UNIQUE, -- unique, absolute file path
                filename TEXT, -- file name without path or extension
                extension TEXT, -- file extension
                partial_hash TEXT NOT NULL, -- hash of the first chunk of the file
                hash TEXT, -- full file hash, if needed
                size INTEGER NOT NULL, -- file size in bytes
                scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_partial_hash_and_size ON files(partial_hash, size)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_hash ON files(hash)
        """)

        # New table for unreadable files
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS unreadable_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL, -- absolute file path
                error_type TEXT NOT NULL, -- type of error encountered
                scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def calculate_partial_hash(self, file_path: Path, chunk_size: int = 8192) -> str:
        """
        Calculate the hash of the first chunk_size bytes of a file.
        """
        hasher = hashlib.md5() if self.algorithm == "md5" else hashlib.sha256()
        with open(file_path, "rb") as f:
            chunk = f.read(chunk_size)
            hasher.update(chunk)
        return hasher.hexdigest()

    def calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate the hash of a file.

        Args:
            file_path: Path to the file

        Returns:
            Hexadecimal hash string
        """
        hasher = hashlib.md5() if self.algorithm == "md5" else hashlib.sha256()

        with open(file_path, "rb") as f:
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

                        if files_scanned % self.bulk_size == 0:
                            conn.commit()

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

        # After scanning, update full hashes for candidates
        self._update_partial_hashes(cursor)
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
            (abs_path, error_type),
        )

    def _store_file(self, cursor, file_path: Path):
        """Store file information in the database."""
        file_size = file_path.stat().st_size
        abs_path = str(file_path.resolve())
        filename = file_path.stem
        extension = file_path.suffix.lower()
        partial_hash = self.calculate_partial_hash(file_path)
        cursor.execute(
            """
            INSERT OR REPLACE INTO files (path, filename, extension, partial_hash, hash, size)
            VALUES (?, ?, ?, ?, NULL, ?)
            """,
            (abs_path, filename, extension, partial_hash, file_size),
        )

    def find_duplicates(self) -> dict[str, "DuplicateGroup"]:
        """
        Find all duplicate files in the database.

        Returns:
            Dictionary mapping hash to DuplicateGroup
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Only update full hashes for files missing them, not every time
        self._update_partial_hashes(cursor)
        conn.commit()

        # Now find duplicates by full hash
        cursor.execute("""
            SELECT hash, path, size
            FROM files
            WHERE hash IN (
                SELECT hash
                FROM files
                WHERE hash IS NOT NULL
                GROUP BY hash
                HAVING COUNT(*) > 1
            )
            ORDER BY hash, path
        """)

        groups: dict[str, list[tuple[str, int]]] = {}
        for hash_val, path, size in cursor.fetchall():
            if hash_val not in groups:
                groups[hash_val] = []
            groups[hash_val].append((path, size))

        duplicates: dict[str, DuplicateGroup] = {}
        for hash_val, files in groups.items():
            file_paths = [p for p, _ in files]
            file_size = files[0][1] if files else 0
            duplicates[hash_val] = DuplicateGroup(hash_val, file_size, file_paths)

        conn.close()
        return duplicates

    def _update_partial_hashes(self, cursor):
        """
        Find all (partial_hash, size) groups with more than one file, and for each,
        compute and store full hashes for files missing them.
        """
        cursor.execute(
            """
            SELECT partial_hash, size
            FROM files
            GROUP BY partial_hash, size
            HAVING COUNT(*) > 1
            """
        )
        candidates = cursor.fetchall()
        for partial_hash, size in candidates:
            cursor.execute(
                "SELECT path, hash FROM files WHERE partial_hash = ? AND size = ?",
                (partial_hash, size),
            )
            rows = cursor.fetchall()
            for path, full_hash in rows:
                if not full_hash:
                    file_path = Path(path)
                    try:
                        computed_hash = self.calculate_file_hash(file_path)
                        cursor.execute(
                            "UPDATE files SET hash = ? WHERE path = ?",
                            (computed_hash, path),
                        )
                    except Exception:
                        continue

    def get_duplicate_groups(self) -> list["DuplicateGroup"]:
        """
        Get duplicate files as a list of DuplicateGroup.

        Returns:
            List of DuplicateGroup instances
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

        for group in duplicates.values():
            sorted_files = sorted(group.file_paths)
            keep_path = sorted_files[0] if keep_first else sorted_files[-1]
            group.file_paths = sorted_files  # Ensure order matches
            files_to_delete = group.delete_duplicates(keep_path, dry_run=dry_run)
            if not dry_run:
                for file_path in files_to_delete:
                    cursor.execute("DELETE FROM files WHERE path = ?", (file_path,))
            deleted_files.extend(files_to_delete)

        if not dry_run:
            conn.commit()
        conn.close()

        return deleted_files

    def clear_database(self):
        """Clear all entries from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM files")
        cursor.execute("DELETE FROM unreadable_files")
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
            "total_size_bytes": total_size,
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
            result[key] = {"count": count, "total_size_bytes": total_size or 0}

        conn.close()
        return result


class DuplicateGroup:
    """
    Represents a group of duplicate files.
    """

    __slots__ = ("hash", "file_size", "file_paths")

    hash: str
    file_paths: list[str]
    file_size: int

    def __init__(self, hash: str, file_size: int, file_paths: list[str]):
        self.hash = hash
        self.file_size = file_size
        self.file_paths = file_paths

    def __len__(self) -> int:
        return len(self.file_paths)

    def __iter__(self):
        return iter(self.file_paths)

    def __getitem__(self, index: int) -> str:
        return self.file_paths[index]

    def __repr__(self) -> str:
        return f"DuplicateGroup(hash={self.hash}, files={len(self.file_paths)})"

    def total_size(self) -> int:
        """Calculate the total size of all files in the group."""
        return self.file_size * len(self.file_paths)

    def wasted_space(self) -> int:
        """Calculate the wasted space due to duplicates (excluding one copy)."""
        return self.file_size * (len(self.file_paths) - 1)

    # TODO: The order of the files list could be changed... we may need to adjust keep logic
    def delete_duplicates_by_idx(self, keep_idx: int, dry_run: bool = True) -> list[str]:
        """
        Delete duplicate files in the group, keeping one specified by index.

        Args:
            keep_idx: Index of the file to keep
            dry_run: If True, only return files that would be deleted without deleting
        Returns:
            List of file paths that were (or would be) deleted
        """
        keep_path = self.file_paths[keep_idx]
        return self.delete_duplicates(keep_path, dry_run)

    def delete_duplicates(self, keep_path: str, dry_run: bool = True) -> list[str]:
        """
        Delete duplicate files in the group, keeping the specified file path.

        Args:
            keep_path: File path to keep
            dry_run: If True, only return files that would be deleted without deleting
        Returns:
            List of file paths that were (or would be) deleted
        """
        deleted_files = []
        for file_path in self.file_paths:
            if file_path != keep_path:
                if not dry_run:
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            deleted_files.append(file_path)
                    except (OSError, PermissionError):
                        continue
                else:
                    deleted_files.append(file_path)
        return deleted_files
