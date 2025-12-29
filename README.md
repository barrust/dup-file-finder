# Deduper

A Python library to find and manage duplicate files. Deduper scans directories, identifies duplicate files using hash algorithms, stores the information in a SQLite database, and provides tools to manage and delete duplicates.

## Features

- 🔍 **Fast duplicate detection** using SHA256 or MD5 hashing
- 💾 **SQLite database** for storing file information
- 🗑️ **Safe deletion** with dry-run mode and confirmation prompts
- 🖥️ **Command-line interface** for easy automation
- 📊 **Statistics** about scanned files and duplicates

## Installation

```bash
pip install -e .
```

Or install from source:

```bash
git clone https://github.com/barrust/deduper.git
cd deduper
pip install -e .
```

## Quick Start

### Using the CLI

#### 1. Scan a directory
```bash
deduper scan /path/to/directory
```

#### 2. Find duplicates
```bash
deduper find --show-all
```

#### 3. View statistics
```bash
deduper stats
```

#### 4. Delete duplicates (dry run)
```bash
deduper delete --dry-run
```

#### 5. Delete duplicates (for real)
```bash
deduper delete --confirm
```

### Using as a Library

```python
from deduper import FileDuplicateFinder

# Initialize the finder
finder = FileDuplicateFinder(db_path="my_duplicates.db")

# Scan a directory
count = finder.scan_directory("/path/to/directory", recursive=True)
print(f"Scanned {count} files")

# Find duplicates
duplicates = finder.find_duplicates()
for hash_val, files in duplicates.items():
    print(f"Duplicate group: {files}")

# Get statistics
stats = finder.get_statistics()
print(f"Total files: {stats['total_files']}")
print(f"Duplicate files: {stats['duplicate_files']}")

# Get statistics by file extension
ext_stats = finder.get_statistics_by_extension()
for ext, data in ext_stats.items():
    print(f"{ext}: {data['count']} files, {data['total_size_bytes']} bytes")

# Delete duplicates (dry run first!)
deleted = finder.delete_duplicates(keep_first=True, dry_run=True)
print(f"Would delete: {deleted}")

# Actually delete
deleted = finder.delete_duplicates(keep_first=True, dry_run=False)
print(f"Deleted: {deleted}")
```

## CLI Commands

### `scan`
Scan a directory for files and store them in the database.

```bash
deduper scan /path/to/directory [--no-recursive]
```

Options:
- `--no-recursive`: Don't scan subdirectories

### `find`
Find and display duplicate files.

```bash
deduper find [--show-all]
```

Options:
- `--show-all`: Display all duplicate files (default: show summary)

### `delete`
Delete duplicate files.

```bash
deduper delete [--keep-first|--keep-last] [--dry-run|--confirm]
```

Options:
- `--keep-first`: Keep the first file alphabetically (default)
- `--keep-last`: Keep the last file alphabetically
- `--dry-run`: Show what would be deleted without deleting (default)
- `--confirm`: Actually delete files

### `stats`
Display statistics about scanned files.

```bash
deduper stats [--by-extension]
```

Options:
- `--by-extension`: Show statistics grouped by file extension

### `clear`
Clear all data from the database.

```bash
deduper clear --confirm
```

## Database

By default, deduper uses a SQLite database file named `deduper.db` in the current directory. You can specify a custom database path:

```bash
deduper --db /path/to/custom.db scan /directory
```

The database stores:
- File paths (absolute paths)
- File hashes (SHA256 by default)
- File sizes
- File extensions (for filtering and statistics)
- Scan timestamps

**Note:** If you have an existing database from an earlier version without the extension column, you'll need to rebuild it by clearing and rescanning your files.

## Safety Features

- **Dry run mode** by default for deletions
- **Confirmation prompts** for destructive operations
- **Keeps one copy** of each duplicate file
- **Error handling** for inaccessible files
- **Database transactions** for data integrity

## Example Usage

See `example.py` for a complete working example. Run it with:

```bash
python example.py
```

## License

MIT License - see LICENSE file for details.

## Author

Tyler Barrus