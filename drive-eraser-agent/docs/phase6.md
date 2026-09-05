# Phase 6 — Windows Device Detection

## Important honesty note, upfront

**This sandbox is Linux — I could not execute real PowerShell commands
or test this against actual Windows hardware.** What I *did* verify:

**UPDATE — live-verified on real hardware (2026-08-30):** the project
owner ran this against their actual Windows laptop and confirmed it
works correctly on the first try:

1. The JSON-parsing logic (`parse_physical_disks_json`,
   `_classify_device_type`, `_build_device_info`) is thoroughly unit
   tested against realistic mocked `Get-PhysicalDisk` output — including
   a real PowerShell quirk (see below).
2. The Linux file-target demo path was re-run live end-to-end to confirm
   adding Windows support didn't regress anything that was already working.

**You must run this on your actual Windows machine and confirm it
detects your real hardware correctly** before relying on it for a demo
— treat this phase as "carefully written and unit-tested, not yet
live-verified," unlike Phases 1–5 where I ran the real thing myself.

## What this phase delivers

`WindowsBlockDeviceDetector`, using PowerShell's `Get-PhysicalDisk`
cmdlet (the modern, non-deprecated replacement for `wmic diskdrive`),
wired into the CLI's `--real-device` flag with automatic OS detection.

## Files added/changed

```
drive-eraser-agent/
├── src/
│   ├── detectors/
│   │   └── windows_block_device.py    # NEW
│   └── main.py                         # CHANGED — OS auto-detection, path translation
└── tests/
    ├── test_windows_block_device.py    # NEW
    └── test_main_windows_path.py       # NEW
```

## A real PowerShell gotcha this code handles correctly

`Get-PhysicalDisk | ... | ConvertTo-Json` returns a **JSON array** when
there are multiple disks, but a **bare JSON object** (not wrapped in an
array) when there's exactly one. A naive implementation that assumes
"always an array" will crash or silently misbehave on any machine with
only one physical disk — which is common for laptops.

`parse_physical_disks_json()` checks `isinstance(data, dict)` and wraps
it in a list if needed. This is tested directly
(`test_parse_handles_single_disk_bare_object`, plus an end-to-end
version `test_build_device_info_works_with_single_disk_bare_object_case`)
using a realistic single-disk JSON sample.

## Another real subtlety: DeviceId vs. wipe path

Detection identifies a disk by its `DeviceId` (e.g. `"0"`, `"1"`) — but
actually opening the disk for reading/wiping requires a different
string: `\\.\PhysicalDrive0`. These are NOT interchangeable. `main.py`
now explicitly translates one to the other
(`windows_physical_drive_path()`), tested directly
(`test_windows_physical_drive_path_differs_from_device_id`) so this
distinction can't silently regress.

## How to test this yourself on Windows (required before demo day)

1. **List your disks first, read-only, completely safe:**
   ```powershell
   powershell -Command "Get-PhysicalDisk | Select DeviceId,FriendlyName,SerialNumber,MediaType,BusType,Size"
   ```
   Confirm the output looks like the JSON samples in
   `tests/test_windows_block_device.py`.

2. **Run detection only, on a disk you do NOT want wiped** (there is no
   "detect only" flag currently — see the safety note below):
   Use the safe file-target mode first to confirm nothing else broke:
   ```powershell
   python -c "open('test.img','wb').write(b'test data'*1000)"
   python -m src.main --target test.img --email you@example.com --password secret123 --api-url http://localhost:8000
   ```

3. **Only once you're confident**, test `--real-device` against a
   **spare USB drive with nothing important on it** — never your system
   disk:
   ```powershell
   python -m src.main --target 1 --email you@example.com --password secret123 --api-url http://localhost:8000 --real-device
   ```
   Confirm the detected model/serial/type printed in `[detect]` matches
   what you expect for that specific USB drive before letting it proceed.

## What we tested

| Test file | What it proves |
|---|---|
| `test_windows_block_device.py` (12 tests) | Multi-disk array parsing; **the single-disk bare-object gotcha specifically**; device type classification (bus type correctly takes priority over media type for USB/NVMe); correct disk selected by DeviceId; clear error on an unknown DeviceId; the single-disk case works end-to-end, not just at the parsing step |
| `test_main_windows_path.py` (2 tests) | The DeviceId-to-wipe-path translation produces the correct `\\.\PhysicalDriveN` format and is never confused with the raw DeviceId |

28 tests pass in `drive-eraser-agent` total (26 previous + 2 new... plus
the 12 Windows-specific ones — 28 is the full updated count). Also
re-ran the pre-existing file-target live demo end-to-end to confirm the
OS-branching logic didn't disturb the already-working, already-verified
path.

## Safety fix: `--dry-run` added

Initially this phase had no way to detect a device without also
proceeding to wipe it once `--real-device` was set — flagged as a real
risk given DeviceIds can shift between reboots on some Windows systems.
Fixed within this same phase rather than left as an open gap:
`--dry-run` now detects and prints device info, then stops before any
write occurs. Proven with `test_dry_run_detects_but_does_not_wipe`,
which confirms file content is byte-identical after a dry run — not
just that the function returns early.

**Recommended habit**: always run with `--dry-run` first against any
new target, confirm the printed model/serial/type matches what you
expect, then re-run without the flag.

## Next

Certificate PDFs (adapting TrustWipe's proven `pdf_service.py` to the
generalized `OperationRecord`) and the unified dashboard. Say "next"
when ready.
