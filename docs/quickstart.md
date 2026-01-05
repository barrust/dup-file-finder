# Quickstart Guide

This guide will help you get started using the Dup File Finder library in your own Python projects.

## Installation

First, install the library and its dependencies:

```sh
pip install dup-file-finder
```

## Basic Usage

You can use Dup File Finder as a command-line tool or import it as a library in your Python code.

### Command-Line Usage

See the [CLI documentation](cli.md) for more information!

### Library Usage

Import the main function or class from the library and use it in your script:

```python
from dup_file_finder import DuplicateFileFinder

finder = DuplicateFileFinder()
files_scanned = finder.scan_directory("/path/to/your/directory")
print(f"Scanned {files_scanned} files.")

for hash, duplicates in finder.find_duplicates().items():
  print(f"Duplicate group: {hash}")
  for filepath in duplicates.file_paths:
    print(f"  {filepath}")
```

#### Example: Scanning Multiple Directories

```python
from dup_file_finder import DuplicateFileFinder

directories = ["/path/to/your/directory", "~/other/path/to/scan"]

finder = DuplicateFileFinder()
for d in directories:
  files_scanned = finder.scan_directory(d)
  print(f"Scanned {files_scanned} files.")

for hash, duplicates in finder.find_duplicates().items():
  print(f"Duplicate group: {hash}")
  for filepath in duplicates.file_paths:
    print(f"  {filepath}")
```

### Filtering by File Extension

You can scan only specific file types by passing a list of extensions:

```python
finder = DuplicateFileFinder()
files_scanned = finder.scan_directory("/path/to/dir", extensions=[".jpg", ".png"])
print(f"Scanned {files_scanned} image files.")
```

### Ignoring Hidden Files

To skip hidden files and directories during scanning:

```python
finder = DuplicateFileFinder(ignore_hidden=True)
files_scanned = finder.scan_directory("/path/to/dir")
```

#### Example: Deleting duplicate files

```python
from dup_file_finder import DuplicateFileFinder

directories = ["/path/to/your/directory", "~/other/path/to/scan"]

finder = DuplicateFileFinder()
for d in directories:
  files_scanned = finder.scan_directory(d)
  print(f"Scanned {files_scanned} files.")

for _, duplicates in finder.find_duplicates().items():
  duplicates.delete_duplicates(0, dry_run=False)  # deletes all but the first one listed
```

## Next Steps

- See the [API Reference](api.md) for more details.
- Check the [Home](index.md) page for project overview and features.