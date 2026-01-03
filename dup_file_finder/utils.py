"""
Utility functions for deduper.
"""


def format_size(size_bytes: int) -> str:
    """Format byte size to human-readable format."""
    size_bytes_float = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes_float < 1024.0:
            return f"{size_bytes_float:.2f} {unit}"
        size_bytes_float /= 1024.0
    return f"{size_bytes_float:.2f} PB"
