"""
Drive Eraser Agent CLI.

Since Phase 5, the operator identity comes from login (--email/--password),
not a free-text --operator flag — the backend now cryptographically ties
every record to a real authenticated account rather than self-reported text.

Safe demo mode (wipes a regular file, never real hardware):
    python -m src.main --target test_volume.img --email investigator@example.com --password secret123

Real Linux block device (DANGEROUS):
    python -m src.main --target /dev/sdb --email investigator@example.com --password secret123 --real-device

Real Windows physical disk (DANGEROUS):
    # First list available disks:
    powershell -Command "Get-PhysicalDisk | Select DeviceId,FriendlyName,SerialNumber,MediaType,BusType,Size"
    # --target is the DeviceId (e.g. "1"), NOT a drive letter or path:
    python -m src.main --target 1 --email investigator@example.com --password secret123 --real-device
"""
import argparse
import platform
import sys
from datetime import datetime, timezone

from src.api_client import ApiClient
from src.detectors.file_target import FileTargetDetector
from src.method_selector import select_wiper
from src.report_builder import build_report
from src.verifier import capture_pre_wipe_samples, verify_wipe


def windows_physical_drive_path(device_id: str) -> str:
    """Windows raw device paths for wiping look like \\\\.\\PhysicalDrive0
    — this is NOT the same string as the DeviceId used to identify the
    disk via Get-PhysicalDisk. Detection uses the DeviceId; actual
    read/write access uses this path."""
    return f"\\\\.\\PhysicalDrive{device_id}"


def run(
    target: str, api_url: str, real_device: bool, email: str, password: str,
    dry_run: bool = False,
) -> dict | None:
    wipe_target = target  # the path actually opened for reading/wiping

    if real_device:
        current_os = platform.system()
        if current_os == "Windows":
            from src.detectors.windows_block_device import WindowsBlockDeviceDetector

            detector = WindowsBlockDeviceDetector()
            # On Windows, --target is a Get-PhysicalDisk DeviceId (e.g.
            # "0"), NOT a file path — the actual wipe target path is
            # derived separately (see windows_physical_drive_path).
            wipe_target = windows_physical_drive_path(target)
            print(
                f"[WARNING] --real-device set on Windows. About to detect and "
                f"wipe PhysicalDrive{target} ({wipe_target}). This is "
                f"IRREVERSIBLE. Press Ctrl+C now to abort.",
                file=sys.stderr,
            )
        elif current_os == "Linux":
            from src.detectors.linux_block_device import LinuxBlockDeviceDetector

            detector = LinuxBlockDeviceDetector()
            print(
                f"[WARNING] --real-device set. About to detect and wipe {target}. "
                f"This is IRREVERSIBLE. Press Ctrl+C now to abort.",
                file=sys.stderr,
            )
        else:
            raise NotImplementedError(
                f"--real-device is not implemented for {current_os}. "
                f"Supported: Windows, Linux. Use file-target mode (omit "
                f"--real-device) for a safe demo on any platform."
            )
    else:
        detector = FileTargetDetector()

    device = detector.detect(target)
    print(f"[detect] {device.device_type} — {device.model} (serial: {device.serial})")

    if dry_run:
        print(
            f"[dry-run] Stopping here — no data was touched. Re-run without "
            f"--dry-run to actually wipe this device."
        )
        return None

    wiper = select_wiper(device.device_type, device.supports_encryption)
    print(f"[select] Method: {wiper.method_name}")

    pre_wipe_samples = capture_pre_wipe_samples(wipe_target, device.size_bytes)

    started_at = datetime.now(timezone.utc)
    print("[wipe] Starting...")
    wipe_result = wiper.wipe(wipe_target, device.size_bytes)
    completed_at = datetime.now(timezone.utc)
    print(
        f"[wipe] Done — {wipe_result.passes} pass(es), "
        f"{wipe_result.bytes_processed} bytes processed."
    )

    print("[verify] Sampling random offsets for read-back verification...")
    verification = verify_wipe(wipe_target, pre_wipe_samples)
    print(
        f"[verify] {verification.samples_changed}/{verification.samples_checked} "
        f"sampled regions confirmed wiped."
    )

    # `operator` is sent for schema compatibility but the backend
    # authoritatively overrides it with the logged-in identity (`email`)
    # regardless of what's sent here — see backend Phase 5 notes.
    report = build_report(
        device=device,
        wipe_result=wipe_result,
        started_at=started_at,
        completed_at=completed_at,
        verification_passed=verification.passed,
        operator=email,
    )

    print(f"[report] Logging in as {email} and submitting DRIVE_ERASE operation to {api_url}...")
    client = ApiClient(base_url=api_url, email=email, password=password)
    record = client.submit_operation_report(report)
    print(f"[report] Certificate issued: {record['certificate_id']}")
    print(f"[report] Recorded operator (authenticated): {record['operator']}")
    print(f"[report] Ledger sequence number: {record['ledger_sequence_number']}")

    return record


def main():
    parser = argparse.ArgumentParser(description="ForensicGuard Drive Eraser agent")
    parser.add_argument("--target", required=True, help="Path to file or device to wipe")
    parser.add_argument("--api-url", default="http://localhost:8000", help="Backend base URL")
    parser.add_argument(
        "--real-device",
        action="store_true",
        help="DANGER: treat --target as a real Linux block device, not a test file",
    )
    parser.add_argument("--email", required=True, help="Operator login email (auto-registers on first use)")
    parser.add_argument("--password", required=True, help="Operator login password")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Detect and print device info only — never wipes anything. "
             "Strongly recommended before your first --real-device run.",
    )
    args = parser.parse_args()

    run(
        target=args.target,
        api_url=args.api_url,
        real_device=args.real_device,
        email=args.email,
        password=args.password,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
