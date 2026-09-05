"""
Free-space overwriting.

Deleting a file's directory entry doesn't erase its content — the OS
just marks those disk blocks "free" for reuse. Until something else
happens to write over them, a forensic recovery tool (including our own
Module 3!) can carve the "deleted" file straight back out. This module
closes that gap by writing a temp file full of random data into the
free space on the same volume until it's full (or a caller-specified
cap is reached), then deleting that temp file too.

MAX_BYTES exists specifically so automated tests and quick demos don't
have to fill an entire real disk to prove the mechanism works — in a
real deployment, omit the cap (or set it very high) to genuinely
saturate free space.
"""
import os
import shutil
from dataclasses import dataclass

CHUNK_SIZE = 4 * 1024 * 1024  # 4 MB


@dataclass
class FreeSpaceOverwriteResult:
    bytes_written: int
    capped: bool


def overwrite_free_space(directory: str, max_bytes: int | None = None) -> FreeSpaceOverwriteResult:
    """Write random data to a temp file in `directory` until free space
    on that volume is exhausted or `max_bytes` is reached, then delete
    the temp file. Returns how much was actually written.

    Raises OSError if `directory` isn't writable — callers should
    surface that clearly rather than silently skip this step, since a
    skipped free-space pass is a real, non-obvious gap in the erasure
    guarantee.
    """
    fill_path = os.path.join(directory, ".fg_freespace_fill.tmp")
    bytes_written = 0
    capped = False

    try:
        with open(fill_path, "wb") as f:
            while True:
                free_bytes = shutil.disk_usage(directory).free
                if free_bytes < CHUNK_SIZE:
                    break
                if max_bytes is not None and bytes_written >= max_bytes:
                    capped = True
                    break

                chunk_size = CHUNK_SIZE
                if max_bytes is not None:
                    chunk_size = min(chunk_size, max_bytes - bytes_written)
                    if chunk_size <= 0:
                        capped = True
                        break

                f.write(os.urandom(chunk_size))
                bytes_written += chunk_size
            f.flush()
            os.fsync(f.fileno())
    finally:
        if os.path.exists(fill_path):
            os.remove(fill_path)

    return FreeSpaceOverwriteResult(bytes_written=bytes_written, capped=capped)
