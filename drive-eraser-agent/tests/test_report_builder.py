from datetime import datetime, timezone

from src.detectors.base import DeviceInfo
from src.report_builder import build_report
from src.wipers.base import WipeResult


def test_build_report_matches_generalized_operation_schema():
    """Confirms the DRIVE_ERASE report shape matches backend's
    OperationReportIn — the top-level keys must be exactly these, with
    all device-specific data packed into `details`, since the backend
    endpoint is shared across all three future modules."""
    device = DeviceInfo(
        serial="SN123", model="Test SSD", device_type="SSD",
        size_bytes=1024, supports_encryption=True,
    )
    wipe_result = WipeResult(
        method_name="NIST 800-88 Purge - Crypto Erase", passes=1, bytes_processed=1024
    )
    started = datetime(2026, 8, 28, 10, 0, 0, tzinfo=timezone.utc)
    completed = datetime(2026, 8, 28, 10, 0, 5, tzinfo=timezone.utc)

    report = build_report(
        device=device, wipe_result=wipe_result,
        started_at=started, completed_at=completed,
        verification_passed=True, operator="test-operator",
    )

    expected_top_level_keys = {
        "operation_type", "target_description", "started_at",
        "completed_at", "success", "operator", "details",
    }
    assert set(report.keys()) == expected_top_level_keys
    assert report["operation_type"] == "DRIVE_ERASE"
    assert report["target_description"] == "SN123"  # device serial
    assert report["success"] is True
    assert report["details"]["device_type"] == "SSD"
    assert report["details"]["method"] == "NIST 800-88 Purge - Crypto Erase"


def test_build_report_success_reflects_verification_not_just_completion():
    """A wipe can 'complete' but still fail verification — success must
    track verification_passed, not just that the wipe ran."""
    device = DeviceInfo(serial="SN999", model="X", device_type="HDD", size_bytes=100)
    wipe_result = WipeResult(method_name="Clear", passes=1, bytes_processed=100)
    now = datetime.now(timezone.utc)

    report = build_report(
        device=device, wipe_result=wipe_result,
        started_at=now, completed_at=now,
        verification_passed=False, operator="op",
    )
    assert report["success"] is False
