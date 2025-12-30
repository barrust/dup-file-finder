"""
Tests for deduper core functionality.
"""

import os
import shutil
import tempfile
import unittest

# from pathlib import Path
from dup_file_finder.core import DuplicateFileFinder


class TestDuplicateFileFinder(unittest.TestCase):
    """Test cases for DuplicateFileFinder class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test.db")
        self.finder = DuplicateFileFinder(db_path=self.db_path)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init_database(self):
        """Test database initialization."""
        self.assertTrue(os.path.exists(self.db_path))

    def test_calculate_file_hash(self):
        """Test file hash calculation."""
        # Create a test file
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("Hello, World!")

        # Calculate hash
        hash_val = self.finder.calculate_file_hash(test_file)

        # Hash should be non-empty and consistent
        self.assertTrue(len(hash_val) > 0)
        hash_val2 = self.finder.calculate_file_hash(test_file)
        self.assertEqual(hash_val, hash_val2)

    def test_scan_directory(self):
        """Test directory scanning."""
        # Create test files in a subdirectory to avoid scanning the db
        scan_dir = os.path.join(self.test_dir, "scan")
        os.makedirs(scan_dir)

        test_file1 = os.path.join(scan_dir, "file1.txt")
        test_file2 = os.path.join(scan_dir, "file2.txt")

        with open(test_file1, "w") as f:
            f.write("Content 1")
        with open(test_file2, "w") as f:
            f.write("Content 2")

        # Scan directory
        count = self.finder.scan_directory(scan_dir, recursive=False)

        # Should have scanned both files
        self.assertEqual(count, 2)

    def test_find_no_duplicates(self):
        """Test finding duplicates when none exist."""
        # Create unique files
        test_file1 = os.path.join(self.test_dir, "file1.txt")
        test_file2 = os.path.join(self.test_dir, "file2.txt")

        with open(test_file1, "w") as f:
            f.write("Content 1")
        with open(test_file2, "w") as f:
            f.write("Content 2")

        self.finder.scan_directory(self.test_dir, recursive=False)
        duplicates = self.finder.find_duplicates()

        self.assertEqual(len(duplicates), 0)

    def test_find_duplicates(self):
        """Test finding duplicate files."""
        # Create duplicate files
        test_file1 = os.path.join(self.test_dir, "file1.txt")
        test_file2 = os.path.join(self.test_dir, "file2.txt")

        content = "Duplicate content"
        with open(test_file1, "w") as f:
            f.write(content)
        with open(test_file2, "w") as f:
            f.write(content)

        self.finder.scan_directory(self.test_dir, recursive=False)
        duplicates = self.finder.find_duplicates()

        # Should find one group of duplicates
        self.assertEqual(len(duplicates), 1)

        # Should have both files in the group
        for _, files in duplicates.items():
            self.assertEqual(len(files), 2)

    def test_delete_duplicates_dry_run(self):
        """Test deleting duplicates in dry run mode."""
        # Create duplicate files
        test_file1 = os.path.join(self.test_dir, "file1.txt")
        test_file2 = os.path.join(self.test_dir, "file2.txt")

        content = "Duplicate content"
        with open(test_file1, "w") as f:
            f.write(content)
        with open(test_file2, "w") as f:
            f.write(content)

        self.finder.scan_directory(self.test_dir, recursive=False)
        deleted = self.finder.delete_duplicates(keep_first=True, dry_run=True)

        # Should report one file to delete
        self.assertEqual(len(deleted), 1)

        # Both files should still exist
        self.assertTrue(os.path.exists(test_file1))
        self.assertTrue(os.path.exists(test_file2))

    def test_delete_duplicates_for_real(self):
        """Test actually deleting duplicate files."""
        # Create duplicate files
        test_file1 = os.path.join(self.test_dir, "file1.txt")
        test_file2 = os.path.join(self.test_dir, "file2.txt")

        content = "Duplicate content"
        with open(test_file1, "w") as f:
            f.write(content)
        with open(test_file2, "w") as f:
            f.write(content)

        self.finder.scan_directory(self.test_dir, recursive=False)
        deleted = self.finder.delete_duplicates(keep_first=True, dry_run=False)

        # Should delete one file
        self.assertEqual(len(deleted), 1)

        # One file should be deleted, one should remain
        files_exist = [os.path.exists(test_file1), os.path.exists(test_file2)]
        self.assertEqual(sum(files_exist), 1)

    def test_get_statistics(self):
        """Test statistics gathering."""
        # Create test files in a subdirectory to avoid scanning the db
        scan_dir = os.path.join(self.test_dir, "scan")
        os.makedirs(scan_dir)

        test_file1 = os.path.join(scan_dir, "file1.txt")
        test_file2 = os.path.join(scan_dir, "file2.txt")
        test_file3 = os.path.join(scan_dir, "file3.txt")

        with open(test_file1, "w") as f:
            f.write("Content 1")
        with open(test_file2, "w") as f:
            f.write("Content 1")  # Duplicate of file1
        with open(test_file3, "w") as f:
            f.write("Content 2")

        self.finder.scan_directory(scan_dir, recursive=False)
        stats = self.finder.get_statistics()

        self.assertEqual(stats["total_files"], 3)
        self.assertEqual(stats["duplicate_files"], 2)
        self.assertEqual(stats["unique_files"], 1)
        self.assertEqual(stats["duplicate_groups"], 1)

    def test_recursive_scan(self):
        """Test recursive directory scanning."""
        # Create nested directory structure in a subdirectory to avoid scanning the db
        scan_dir = os.path.join(self.test_dir, "scan")
        os.makedirs(scan_dir)
        subdir = os.path.join(scan_dir, "subdir")
        os.makedirs(subdir)

        test_file1 = os.path.join(scan_dir, "file1.txt")
        test_file2 = os.path.join(subdir, "file2.txt")

        with open(test_file1, "w") as f:
            f.write("Content")
        with open(test_file2, "w") as f:
            f.write("Content")

        count = self.finder.scan_directory(scan_dir, recursive=True)

        # Should scan both files
        self.assertEqual(count, 2)

    def test_clear_database(self):
        """Test clearing the database."""
        # Create and scan files
        test_file = os.path.join(self.test_dir, "file.txt")
        with open(test_file, "w") as f:
            f.write("Content")

        self.finder.scan_directory(self.test_dir, recursive=False)
        stats_before = self.finder.get_statistics()
        self.assertGreater(stats_before["total_files"], 0)

        # Clear database
        self.finder.clear_database()
        stats_after = self.finder.get_statistics()
        self.assertEqual(stats_after["total_files"], 0)

    def test_file_extension_storage(self):
        """Test that file extensions are stored correctly."""
        # Create test files with different extensions
        scan_dir = os.path.join(self.test_dir, "scan")
        os.makedirs(scan_dir)

        test_file1 = os.path.join(scan_dir, "doc.txt")
        test_file2 = os.path.join(scan_dir, "image.jpg")
        test_file3 = os.path.join(scan_dir, "noext")

        with open(test_file1, "w") as f:
            f.write("text")
        with open(test_file2, "w") as f:
            f.write("img")
        with open(test_file3, "w") as f:
            f.write("data")

        self.finder.scan_directory(scan_dir, recursive=False)

        # Get statistics by extension
        ext_stats = self.finder.get_statistics_by_extension()

        # Should have 3 different extensions (including empty for noext)
        self.assertGreaterEqual(len(ext_stats), 2)

        # Check that .txt and .jpg are present
        self.assertIn(".txt", ext_stats)
        self.assertIn(".jpg", ext_stats)

        # Check counts
        self.assertEqual(ext_stats[".txt"]["count"], 1)
        self.assertEqual(ext_stats[".jpg"]["count"], 1)


if __name__ == "__main__":
    unittest.main()
