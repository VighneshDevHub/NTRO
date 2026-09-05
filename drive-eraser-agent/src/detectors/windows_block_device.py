"""
Real hardware detector for Windows, via PowerShell's Get-PhysicalDisk
cmdlet — the modern replacement for the deprecated `wmic diskdrive`.
Returns model, serial, media type (SSD/HDD/Unspecified), bus type
(USB/NVMe/SATA/SAS/RAID), and size, as structured JSON.

`target` for this detector is the disk's DeviceId as reported by
Get-PhysicalDisk (e.g. "0", "1", "2") — list them yourself first with:

    powershell -Command "Get-PhysicalDisk | Select DeviceId,FriendlyName,SerialNumber,MediaType,BusType,Size"

WARNING: only wire this to a disk you intend to genuinely wipe.
DeviceId "0" is very often the system/boot disk — double, triple check
before running --real-device against it.

DESIGN NOTE: the subprocess call and the JSON parsing are deliberately
split into two functions. This is what makes the parsing logic testable
on ANY platform (including this Linux dev environment) using realistic
mocked PowerShell output, without needing a live Windows machine or
admin rights just to run the unit tests.
"""
import json
import subprocess

from src.detectors.base import DeviceDetector, DeviceInfo

POWERSHELL_COMMAND = (
    "Get-PhysicalDisk | "
    "Select-Object DeviceId,FriendlyName,SerialNumber,MediaType,BusType,Size | "
    "ConvertTo-Json"
)


def run_get_physical_disk() -> str:
    """Executes the actual PowerShell command. Isolated in its own
    function so tests can bypass it entirely and feed parse_physical_disks_json()
    directly."""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", POWERSHELL_COMMAND],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def parse_physical_disks_json(raw_json: str) -> list[dict]:
    """Parses Get-PhysicalDisk's ConvertTo-Json output into a normalized
    list of dicts. Handles a classic PowerShell gotcha: ConvertTo-Json
    returns a single JSON OBJECT (not wrapped in a list) when there's
    only one result, but a JSON ARRAY when there are multiple — calling
    code must not assume it's always a list.
    """
    data = json.loads(raw_json)
    if isinstance(data, dict):
        data = [data]
    return data


def _classify_device_type(media_type: str, bus_type: str) -> str:
    """MediaType from Windows is authoritative for SSD vs HDD when
    available ('SSD', 'HDD', or 'Unspecified'). BusType distinguishes
    USB and NVMe, which MediaType alone doesn't capture."""
    bus_type_upper = (bus_type or "").upper()
    media_type_upper = (media_type or "").upper()

    if bus_type_upper == "USB":
        return "USB"
    if bus_type_upper == "NVME":
        return "NVMe"
    if media_type_upper == "SSD":
        return "SSD"
    if media_type_upper == "HDD":
        return "HDD"
    return "UNKNOWN"


class WindowsBlockDeviceDetector(DeviceDetector):
    def detect(self, target: str) -> DeviceInfo:
        raw_json = run_get_physical_disk()
        disks = parse_physical_disks_json(raw_json)
        return self._build_device_info(disks, target)

    @staticmethod
    def _build_device_info(disks: list[dict], target: str) -> DeviceInfo:
        matching = [d for d in disks if str(d.get("DeviceId")) == str(target)]
        if not matching:
            available = [str(d.get("DeviceId")) for d in disks]
            raise ValueError(
                f"No physical disk found with DeviceId '{target}'. "
                f"Available DeviceIds: {available}"
            )

        disk = matching[0]
        device_type = _classify_device_type(disk.get("MediaType", ""), disk.get("BusType", ""))

        return DeviceInfo(
            serial=disk.get("SerialNumber") or "UNKNOWN",
            model=disk.get("FriendlyName") or "UNKNOWN",
            device_type=device_type,
            size_bytes=int(disk.get("Size") or 0),
            supports_encryption=(device_type in ("SSD", "NVMe")),
        )
