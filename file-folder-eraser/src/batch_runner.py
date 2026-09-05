"""
Batch operation runner — the PS explicitly requires "batch operations"
support. Takes a list of file/folder paths, secure-deletes each, then
does one free-space overwrite pass on the volume(s) involved so freed
blocks from ALL the deletions get covered in a single pass rather than
one wasteful pass per file.
"""
import os
from dataclasses import dataclass, field

from src.freespace_overwriter import overwrite_free_space
from src.selective_deleter import DeleteResult, secure_delete_file, secure_delete_folder


def _nearest_existing_dir(path: str) -> str:
    """Walk up from `path` until we find a directory that still exists.
    Needed because a batch target can be an entire folder that
    secure_delete_folder just removed — its immediate parent directory
    is the nearest place we can still write a free-space fill file."""
    current = os.path.abspath(path)
    while not os.path.isdir(current):
        parent = os.path.dirname(current)
        if parent == current:  # reached filesystem root without finding one
            return os.path.abspath(os.sep)
        current = parent
    return current


@dataclass
class BatchResult:
    targets_requested: int
    files_deleted: int
    files_failed: int
    total_bytes_overwritten: int
    metadata_scrubbed: bool  # True only if ALL successful deletions scrubbed metadata
    freespace_bytes_overwritten: int
    per_file_results: list[DeleteResult] = field(default_factory=list)


def run_batch(
    targets: list[str],
    overwrite_freespace: bool = True,
    freespace_max_bytes: int | None = None,
) -> BatchResult:
    """Process a mixed list of file and folder paths. A folder path
    expands into all files within it (see secure_delete_folder). Never
    raises on a per-target failure — collects it into per_file_results
    so the batch as a whole always completes and reports honestly on
    what succeeded vs. failed.
    """
    all_results: list[DeleteResult] = []

    for target in targets:
        if os.path.isdir(target):
            all_results.extend(secure_delete_folder(target))
        else:
            all_results.append(secure_delete_file(target))

    files_deleted = sum(1 for r in all_results if r.success)
    files_failed = sum(1 for r in all_results if not r.success)
    total_bytes = sum(r.bytes_overwritten for r in all_results)
    all_scrubbed = files_deleted > 0 and all(
        r.metadata_scrubbed for r in all_results if r.success
    )

    freespace_bytes = 0
    if overwrite_freespace and files_deleted > 0:
        # Overwrite free space once, on the nearest still-existing
        # directory of the first successfully-processed target — covers
        # freed blocks from this whole batch in one pass. The target's
        # own directory may no longer exist if it was a folder target
        # that secure_delete_folder just removed entirely.
        first_success = next(r for r in all_results if r.success)
        directory = _nearest_existing_dir(os.path.dirname(first_success.original_path) or ".")
        fs_result = overwrite_free_space(directory, max_bytes=freespace_max_bytes)
        freespace_bytes = fs_result.bytes_written

    return BatchResult(
        targets_requested=len(targets),
        files_deleted=files_deleted,
        files_failed=files_failed,
        total_bytes_overwritten=total_bytes,
        metadata_scrubbed=all_scrubbed,
        freespace_bytes_overwritten=freespace_bytes,
        per_file_results=all_results,
    )
