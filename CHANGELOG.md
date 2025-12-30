# Changelog

### Version 0.0.2 (v2025-12-30-2000)

* Update CLI name from `deduper` to `dupFileFinder`

### Version 0.0.1 (tag v0.1.0)

* Inital release
    * Walk directories and calculate hashes to find duplicate files
    * Uses filesize and partial hash (default 8kb) to speed up the process
    * When partial and filesizes collide, calculate full hash
* CLI provided
* Basic library