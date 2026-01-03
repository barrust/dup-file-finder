"""
Command-line interface for deduper.
"""

import argparse
import sys

from dup_file_finder.core import DuplicateFileFinder


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Deduper - Find and manage duplicate files")
    parser.add_argument(
        "--db",
        default="deduper.db",
        help="Path to database file (default: deduper.db)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan directory for files")
    scan_parser.add_argument("directory", help="Directory to scan")
    scan_parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Don't scan subdirectories",
    )

    # Find command
    find_parser = subparsers.add_parser("find", help="Find duplicate files")
    find_parser.add_argument(
        "--show-all",
        action="store_true",
        help="Show all duplicates (default: show summary)",
    )

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete duplicate files")
    delete_parser.add_argument(
        "--keep-first",
        action="store_true",
        help="Keep the first file (alphabetically) - default",
    )
    delete_parser.add_argument("--keep-last", action="store_true", help="Keep the last file (alphabetically)")
    delete_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting - default",
    )
    delete_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually delete files (disables dry-run)",
    )

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    stats_parser.add_argument(
        "--by-extension",
        action="store_true",
        help="Show statistics grouped by file extension",
    )

    # Clear command
    clear_parser = subparsers.add_parser("clear", help="Clear database")
    clear_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm database clearing",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    finder = DuplicateFileFinder(db_path=args.db)

    if args.command == "scan":
        print(f"Scanning directory: {args.directory}")
        recursive = not args.no_recursive
        count = finder.scan_directory(args.directory, recursive=recursive)
        print(f"Scanned {count} files")

    elif args.command == "find":
        duplicates = finder.find_duplicates()
        if not duplicates:
            print("No duplicate files found")
        else:
            print(f"Found {len(duplicates)} groups of duplicate files:")
            if args.show_all:
                for i, (hash_val, files) in enumerate(duplicates.items(), 1):
                    print(f"\nGroup {i} (hash: {hash_val[:16]}...):")
                    for file in files:
                        print(f"  - {file}")
            else:
                total_dupes = sum(len(files) - 1 for files in duplicates.values())
                print(f"Total duplicate files: {total_dupes}")
                print("Use --show-all to see all duplicate files")

    elif args.command == "delete":
        # Default to keep_first unless keep_last is specified
        keep_first = not args.keep_last
        # Default to dry_run unless confirm is specified
        dry_run = not args.confirm

        if dry_run:
            print("DRY RUN MODE - No files will be deleted")
            print("Use --confirm to actually delete files")
        else:
            print("WARNING: This will permanently delete files!")
            response = input("Are you sure you want to continue? (yes/no): ")
            if response.lower() != "yes":
                print("Operation cancelled")
                sys.exit(0)

        deleted = finder.delete_duplicates(keep_first=keep_first, dry_run=dry_run)

        if deleted:
            print(f"\n{'Would delete' if dry_run else 'Deleted'} {len(deleted)} files:")
            for file in deleted:
                print(f"  - {file}")
        else:
            print("No duplicate files to delete")

    elif args.command == "stats":
        stats = finder.get_statistics()
        print("Database Statistics:")
        print(f"  Total files: {stats['total_files']}")
        print(f"  Unique files: {stats['unique_files']}")
        print(f"  Duplicate files: {stats['duplicate_files']}")
        print(f"  Duplicate groups: {stats['duplicate_groups']}")
        print(f"  Total size: {stats['total_size']}")

        if args.by_extension:
            print("\nStatistics by file extension:")
            ext_stats = finder.get_statistics_by_extension()
            for ext, ext_data in ext_stats.items():
                ext_name = ext if ext else "(no extension)"
                print(
                    "  "
                    f"{ext_name}: {ext_data['count']} file(s), "
                    f"{ext_data['total_size_bytes']} bytes, "
                    f"{ext_data['total_size']}"
                )

    elif args.command == "clear":
        if not args.confirm:
            print("This will clear all data from the database")
            print("Use --confirm to proceed")
            sys.exit(1)

        finder.clear_database()
        print("Database cleared")


if __name__ == "__main__":
    main()
