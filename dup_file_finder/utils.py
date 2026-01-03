"""
Utility functions for deduper.
"""

import hashlib
import os
from pathlib import Path


def format_size(size_bytes: int) -> str:
    """Format byte size to human-readable format

    Args:
        size_bytes (int): Size in bytes

    Returns:
        str: Human-readable size string
    """
    size_bytes_float = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes_float < 1024.0:
            return f"{size_bytes_float:.2f} {unit}"
        size_bytes_float /= 1024.0
    return f"{size_bytes_float:.2f} PB"


def calculate_hash(file_path: Path, algorithm: str = "sha256", chunk_size: int = 8192) -> str:
    """Calculate the hash of a file using the specified algorithm.

    Args:
        file_path (Path): Path to the file
        algorithm (str): Hash algorithm ('md5' or 'sha256')
        chunk_size (int): Size of chunks to read the file

    Returns:
        str: Hexadecimal hash string
    """
    hasher = hashlib.md5() if algorithm == "md5" else hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def calculate_partial_hash(file_path: Path, algorithm: str = "sha256", num_bytes: int = 8192) -> str:
    """Calculate the hash of the first num_bytes of a file using the specified algorithm.
    Args:
        file_path (Path): Path to the file
        algorithm (str): Hash algorithm ('md5' or 'sha256')
        num_bytes (int): Number of bytes to read from the start of the file
    Returns:
        str: Hexadecimal hash string
    """
    hasher = hashlib.md5() if algorithm == "md5" else hashlib.sha256()
    with open(file_path, "rb") as f:
        chunk = f.read(num_bytes)
        hasher.update(chunk)
    return hasher.hexdigest()


def safe_remove(file_path: str) -> bool:
    """Attempt to remove a file, returning True if successful, False otherwise.

    Args:
        file_path (str): Path to the file to remove

    Returns:
        bool: True if file was removed, False otherwise
    """
    try:
        os.remove(file_path)
        return True
    except (OSError, PermissionError):
        return False
