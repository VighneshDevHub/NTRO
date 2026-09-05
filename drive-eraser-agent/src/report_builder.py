"""
Builds the payload for POST /api/v1/operations (see
backend/app/schemas/operation.py::OperationReportIn). This is the ONE
thing that differs from TrustWipe's wipe agent: instead of a flat
wipe-specific schema, we set operation_type="DRIVE_ERASE" and pack
drive-specific fields into `details`, so this same backend endpoint can
also accept FILE_ERASE and RECOVERY reports from Phases 3 and 4.
"""
from datetime import datetime, timezone

from src.detectors.base import DeviceInfo
from src.wipers.base import WipeResult


def build_report(
    device: DeviceInfo,
    wipe_result: WipeResult,
    started_at: datetime,
    completed_at: datetime,
    verification_passed: bool,
    operator: str,
) -> dict:
    return {
        "operation_type": "DRIVE_ERASE",
        "target_description": device.serial,
        "started_at": started_at.astimezone(timezone.utc).isoformat(),
        "completed_at": completed_at.astimezone(timezone.utc).isoformat(),
        "success": verification_passed,
        "operator": operator,
        "details": {
            "device_model": device.model,
            "device_type": device.device_type,
            "method": wipe_result.method_name,
            "passes": wipe_result.passes,
            "bytes_processed": wipe_result.bytes_processed,
            "verification_passed": verification_passed,
        },
    }
