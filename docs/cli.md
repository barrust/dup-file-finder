# Command-Line Interface (CLI) Documentation

This page documents the available commands and options for the Dup File Finder CLI, as implemented in `dup_file_finder/cli.py`.

---

## Usage

```sh
dupFileFinder [--db PATH] <command> [options]
```

- `--db PATH`
  Path to the database file (default: `deduper.db`).

---

## Commands

### scan

Scan a directory for files and add them to the database.

**Usage:**

```sh
dupFileFinder scan [directory] [--no-recursive]
```

- `directory` (required): Directory to scan.
- `--no-recursive`: Don't scan subdirectories (default is recursive).

---

### find

Find duplicate files in the database.

**Usage:**

```sh
dupFileFinder find [--show-all]
```

- `--show-all`: Show all duplicate files (default shows summary only).

---

### delete

Delete duplicate files, keeping only one file per group.

**Usage:**

```sh
dupFileFinder delete [--keep-first|--keep-last] [--dry-run|--confirm]
```

- `--keep-first`: Keep the first file alphabetically (default).
- `--keep-last`: Keep the last file alphabetically.
- `--dry-run`: Show what would be deleted without actually deleting (default).
- `--confirm`: Actually delete files (disables dry-run).

**Safety:**
By default, this command runs in dry-run mode. Use `--confirm` to actually delete files. You will be prompted for confirmation.

---

### stats

Show statistics about the files in the database.

**Usage:**

```sh
dupFileFinder stats [--by-extension]
```

- `--by-extension`: Show statistics grouped by file extension.

---

### clear

Clear all data from the database.

**Usage:**

```sh
dupFileFinder clear [--confirm]
```

- `--confirm`: Confirm database clearing (required to proceed).

---

## Examples

Scan a directory recursively:

```sh
dupFileFinder scan ~/Downloads
```

Find duplicate files (summary):

```sh
dupFileFinder find
```

Show all duplicate files:

```sh
dupFileFinder find --show-all
```

Delete duplicates (dry run):

```sh
dupFileFinder delete
```

Delete duplicates (actually delete, keep last file):

```sh
dupFileFinder delete --keep-last --confirm
```

Show statistics by extension:

```sh
dupFileFinder stats --by-extension
```

Clear the database:

```sh
dupFileFinder clear --confirm
```

---

## Help

For help on any command, use:

```sh
dupFileFinder --help
dupFileFinder <command> --help
```