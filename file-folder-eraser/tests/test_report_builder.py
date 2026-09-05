from datetime import datetime, timezone

from src.batch_runner import BatchResult
from src.report_builder import build_report


def test_build_report_success_true_when_all_deleted():
    batch_result = BatchResult(
        targets_requested=2, files_deleted=2, files_failed=0,
        total_bytes_overwritten=1000, metadata_scrubbed=True,
        freespace_bytes_overwritten=500_000, per_file_results=[],
    )
    now = datetime.now(timezone.utc)

    report = build_report(batch_result, now, now, "operator-1", "2 files")

    assert report["operation_type"] == "FILE_ERASE"
    assert report["success"] is True
    assert report["details"]["files_deleted"] == 2
    assert report["details"]["metadata_scrubbed"] is True


def test_build_report_success_false_on_any_failure():
    batch_result = BatchResult(
        targets_requested=2, files_deleted=1, files_failed=1,
        total_bytes_overwritten=500, metadata_scrubbed=False,
        freespace_bytes_overwritten=0, per_file_results=[],
    )
    now = datetime.now(timezone.utc)

    report = build_report(batch_result, now, now, "operator-1", "2 files")

    assert report["success"] is False
    assert report["details"]["files_failed"] == 1
