from datetime import datetime, timezone

from src.batch_runner import BatchResult


def build_report(
    batch_result: BatchResult,
    started_at: datetime,
    completed_at: datetime,
    operator: str,
    target_summary: str,
) -> dict:
    """`target_summary` is a short human-readable description (e.g.
    "3 files in /cases/1234/notes/") since target_description is a
    single string field — the full per-file breakdown lives in details."""
    return {
        "operation_type": "FILE_ERASE",
        "target_description": target_summary,
        "started_at": started_at.astimezone(timezone.utc).isoformat(),
        "completed_at": completed_at.astimezone(timezone.utc).isoformat(),
        "success": batch_result.files_failed == 0 and batch_result.files_deleted > 0,
        "operator": operator,
        "details": {
            "targets_requested": batch_result.targets_requested,
            "files_deleted": batch_result.files_deleted,
            "files_failed": batch_result.files_failed,
            "total_bytes_overwritten": batch_result.total_bytes_overwritten,
            "metadata_scrubbed": batch_result.metadata_scrubbed,
            "freespace_bytes_overwritten": batch_result.freespace_bytes_overwritten,
            "failures": [
                {"path": r.original_path, "error": r.error}
                for r in batch_result.per_file_results
                if not r.success
            ],
        },
    }
