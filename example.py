#!/usr/bin/env python3
"""
Example usage of the deduper library.

This script demonstrates how to use deduper programmatically.
"""

from deduper import DuplicateFileFinder
import os
import tempfile
import shutil


def main():
    """Demonstrate deduper usage."""
    
    # Create a temporary directory for the demo
    demo_dir = tempfile.mkdtemp(prefix="deduper-demo-")
    db_path = os.path.join(demo_dir, "deduper.db")
    
    print("=" * 60)
    print("Deduper Library Example")
    print("=" * 60)
    
    try:
        # Create sample files
        print("\n1. Creating sample files...")
        files_dir = os.path.join(demo_dir, "files")
        os.makedirs(files_dir)
        
        # Create some duplicate files
        with open(os.path.join(files_dir, "doc1.txt"), "w") as f:
            f.write("This is a document.\n")
        
        with open(os.path.join(files_dir, "doc2.txt"), "w") as f:
            f.write("This is a document.\n")  # Same content as doc1
        
        with open(os.path.join(files_dir, "doc3.txt"), "w") as f:
            f.write("This is a different document.\n")
        
        # Create a subdirectory with more duplicates
        subdir = os.path.join(files_dir, "subdir")
        os.makedirs(subdir)
        
        with open(os.path.join(subdir, "copy1.txt"), "w") as f:
            f.write("This is a document.\n")  # Another duplicate
        
        with open(os.path.join(subdir, "unique.txt"), "w") as f:
            f.write("Unique content.\n")
        
        print(f"   Created 5 files in {files_dir}")
        
        # Initialize the deduper
        print("\n2. Initializing DuplicateFileFinder...")
        finder = DuplicateFileFinder(db_path=db_path)
        print(f"   Database: {db_path}")
        
        # Scan the directory
        print("\n3. Scanning directory...")
        count = finder.scan_directory(files_dir, recursive=True)
        print(f"   Scanned {count} files")
        
        # Get statistics
        print("\n4. Getting statistics...")
        stats = finder.get_statistics()
        print(f"   Total files: {stats['total_files']}")
        print(f"   Unique files: {stats['unique_files']}")
        print(f"   Duplicate files: {stats['duplicate_files']}")
        print(f"   Duplicate groups: {stats['duplicate_groups']}")
        print(f"   Total size: {stats['total_size_bytes']} bytes")
        
        # Find duplicates
        print("\n5. Finding duplicate files...")
        duplicates = finder.find_duplicates()
        
        for i, (hash_val, file_list) in enumerate(duplicates.items(), 1):
            print(f"\n   Group {i} (hash: {hash_val[:16]}...):")
            for file_path in file_list:
                rel_path = os.path.relpath(file_path, demo_dir)
                print(f"     - {rel_path}")
        
        # Dry run deletion
        print("\n6. Testing deletion (dry run)...")
        to_delete = finder.delete_duplicates(keep_first=True, dry_run=True)
        print(f"   Would delete {len(to_delete)} files:")
        for file_path in to_delete:
            rel_path = os.path.relpath(file_path, demo_dir)
            print(f"     - {rel_path}")
        
        # Calculate space savings
        total_wasted = sum(
            os.path.getsize(f) for f in to_delete if os.path.exists(f)
        )
        print(f"   Would save {total_wasted} bytes")
        
        # Get grouped duplicates
        print("\n7. Getting duplicate groups...")
        groups = finder.get_duplicate_groups()
        print(f"   Found {len(groups)} groups:")
        for i, group in enumerate(groups, 1):
            print(f"   Group {i}: {len(group)} files")
        
        # Get statistics by extension
        print("\n8. Getting statistics by file extension...")
        ext_stats = finder.get_statistics_by_extension()
        print(f"   File types found:")
        for ext, data in ext_stats.items():
            ext_name = ext if ext else "(no extension)"
            print(f"     {ext_name}: {data['count']} file(s), {data['total_size_bytes']} bytes")
        
        print("\n" + "=" * 60)
        print("Demo completed successfully!")
        print("=" * 60)
        
    finally:
        # Clean up
        print(f"\nCleaning up temporary directory: {demo_dir}")
        shutil.rmtree(demo_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
