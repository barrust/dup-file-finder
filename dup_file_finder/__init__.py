"""
Deduper - A Python library to find and manage duplicate files.
"""

__version__ = "0.0.2"

from .core import DuplicateFileFinder, DuplicateGroup

__all__ = ["DuplicateFileFinder", "DuplicateGroup"]
