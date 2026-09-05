import pytest

from src.detectors.windows_block_device import (
    WindowsBlockDeviceDetector,
    _classify_device_type,
    parse_physical_disks_json,
)

# Realistic sample output from:
#   Get-PhysicalDisk | Select DeviceId,FriendlyName,SerialNumber,MediaType,BusType,Size | ConvertTo-Json
MULTI_DISK_JSON = """
[
  {
    "DeviceId": "0",
    "FriendlyName": "Samsung SSD 970 EVO 1TB",
    "SerialNumber": "S466NF0M123456",
    "MediaType": "SSD",
    "BusType": "NVMe",
    "Size": 1000204886016
  },
  {
    "DeviceId": "1",
    "FriendlyName": "WD My Passport 25E2",
    "SerialNumber": "575836314135",
    "MediaType": "HDD",
    "BusType": "USB",
    "Size": 2000398934016
  },
  {
    "DeviceId": "2",
    "FriendlyName": "ST2000DM008-2FR102",
    "SerialNumber": "ZFL2ABCD",
    "MediaType": "HDD",
    "BusType": "SATA",
    "Size": 2000398934016
  }
]
"""

# The classic PowerShell gotcha: ConvertTo-Json returns a bare OBJECT,
# not an array, when there's exactly one result.
SINGLE_DISK_JSON = """
{
  "DeviceId": "0",
  "FriendlyName": "Kingston SA400S37240G",
  "SerialNumber": "50026B7782A1B2C3",
  "MediaType": "SSD",
  "BusType": "SATA",
  "Size": 240057409536
}
"""


def test_parse_handles_multi_disk_array():
    disks = parse_physical_disks_json(MULTI_DISK_JSON)
    assert len(disks) == 3
    assert disks[0]["DeviceId"] == "0"


def test_parse_handles_single_disk_bare_object():
    """This is the exact bug a naive implementation would hit: assuming
    PowerShell always returns a JSON array and crashing/misbehaving on
    the single-disk case, which returns a bare object instead."""
    disks = parse_physical_disks_json(SINGLE_DISK_JSON)
    assert isinstance(disks, list)
    assert len(disks) == 1
    assert disks[0]["DeviceId"] == "0"


@pytest.mark.parametrize(
    "media_type,bus_type,expected",
    [
        ("SSD", "NVMe", "NVMe"),       # bus type wins over media type for NVMe
        ("HDD", "USB", "USB"),          # bus type wins over media type for USB
        ("SSD", "SATA", "SSD"),
        ("HDD", "SATA", "HDD"),
        ("Unspecified", "SATA", "UNKNOWN"),
        ("", "", "UNKNOWN"),
    ],
)
def test_classify_device_type(media_type, bus_type, expected):
    assert _classify_device_type(media_type, bus_type) == expected


def test_build_device_info_finds_correct_disk_by_device_id():
    disks = parse_physical_disks_json(MULTI_DISK_JSON)
    device = WindowsBlockDeviceDetector._build_device_info(disks, "1")

    assert device.model == "WD My Passport 25E2"
    assert device.serial == "575836314135"
    assert device.device_type == "USB"
    assert device.size_bytes == 2000398934016
    assert device.supports_encryption is False  # USB, not SSD/NVMe


def test_build_device_info_nvme_supports_encryption():
    disks = parse_physical_disks_json(MULTI_DISK_JSON)
    device = WindowsBlockDeviceDetector._build_device_info(disks, "0")

    assert device.device_type == "NVMe"
    assert device.supports_encryption is True


def test_build_device_info_raises_clear_error_for_unknown_device_id():
    disks = parse_physical_disks_json(MULTI_DISK_JSON)

    with pytest.raises(ValueError, match="No physical disk found"):
        WindowsBlockDeviceDetector._build_device_info(disks, "99")


def test_build_device_info_works_with_single_disk_bare_object_case():
    """End-to-end proof that the single-disk PowerShell quirk doesn't
    break actual device selection, not just the parsing step in isolation."""
    disks = parse_physical_disks_json(SINGLE_DISK_JSON)
    device = WindowsBlockDeviceDetector._build_device_info(disks, "0")

    assert device.model == "Kingston SA400S37240G"
    assert device.device_type == "SSD"
