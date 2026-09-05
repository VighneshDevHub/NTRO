from datetime import datetime, timezone

from src.recovery_engine import RecoverySummary, RecoveredFileResult
from src.report_builder import build_report


def test_build_report_success_true_when_integrity_preserved():
    summary = RecoverySummary(
        source_image="evidence.dd", source_hash_before="abc123", source_hash_after="abc123",
        files_recovered=2, avg_confidence=0.9, classifications={"JPEG": 2},
        recovered_files=[],
    )
    now = datetime.now(timezone.utc)

    report = build_report(summary, now, now, "investigator-1")

    assert report["operation_type"] == "RECOVERY"
    assert report["success"] is True
    assert report["details"]["evidence_integrity_preserved"] is True
    assert report["details"]["files_recovered"] == 2


def test_build_report_success_false_if_hash_changed():
    """This must be treated as a serious failure, not a warning —
    altering the evidence source invalidates the entire recovery."""
    summary = RecoverySummary(
        source_image="evidence.dd", source_hash_before="abc123", source_hash_after="DIFFERENT",
        files_recovered=5, avg_confidence=0.9, classifications={},
        recovered_files=[],
    )
    now = datetime.now(timezone.utc)

    report = build_report(summary, now, now, "investigator-1")

    assert report["success"] is False
    assert report["details"]["evidence_integrity_preserved"] is False
