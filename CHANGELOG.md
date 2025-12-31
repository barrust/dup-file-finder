# Changelog

### Version 0.0.3 ()

* Add `GroupDuplicates` class to make library usage easier

``` python
dff = DuplicateFileFinder()
dff.scan_directory(".")

dups = dff.get_duplicate_groups()

for dg in dups:
    print(dg.total_size())
    print(dg.wasted_space())
    dg.delete_duplicates_alt(keep_idx=0)  # keeps idx 0
```

### Version 0.0.2 (v2025-12-30-2000)

* Update CLI name from `deduper` to `dupFileFinder`

### Version 0.0.1 (tag v0.1.0)

* Inital release
    * Walk directories and calculate hashes to find duplicate files
    * Uses filesize and partial hash (default 8kb) to speed up the process
    * When partial and filesizes collide, calculate full hash
* CLI provided
* Basic library