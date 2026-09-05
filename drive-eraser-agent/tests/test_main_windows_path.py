from src.main import windows_physical_drive_path


def test_windows_physical_drive_path_format():
    assert windows_physical_drive_path("0") == r"\\.\PhysicalDrive0"
    assert windows_physical_drive_path("1") == r"\\.\PhysicalDrive1"


def test_windows_physical_drive_path_differs_from_device_id():
    """The whole point of this helper: the DeviceId used for DETECTION
    ("0") must not be confused with the path used for actual WIPING
    (\\\\.\\PhysicalDrive0) — they are different strings."""
    device_id = "0"
    wipe_path = windows_physical_drive_path(device_id)
    assert wipe_path != device_id


def test_dry_run_detects_but_does_not_wipe(tmp_path):
    """Safety-critical: --dry-run must detect and print info, then stop
    BEFORE any write happens — proven here by confirming file content
    is byte-identical after a dry run."""
    from src.main import run

    test_file = tmp_path / "test.img"
    original_content = b"UNTOUCHED-CONTENT" * 100
    test_file.write_bytes(original_content)

    result = run(
        target=str(test_file), api_url="http://unused:9999",
        real_device=False, email="x@example.com", password="x",
        dry_run=True,
    )

    assert result is None  # dry run never returns a submitted record
    assert test_file.read_bytes() == original_content  # untouched
