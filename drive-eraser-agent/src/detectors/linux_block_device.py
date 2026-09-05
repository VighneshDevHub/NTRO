"""
Real hardware detector for Linux block devices via lsblk.
WARNING: only wire this to devices you intend to genuinely wipe.
"""
import json
import subprocess

from src.detectors.base import DeviceDetector, DeviceInfo


class LinuxBlockDeviceDetector(DeviceDetector):
    def detect(self, target: str) -> DeviceInfo:
        result = subprocess.run(
            ["lsblk", "-b", "-J", "-o", "NAME,MODEL,SERIAL,SIZE,ROTA,TYPE", target],
            capture_output=True, text=True, check=True,
        )
        data = json.loads(result.stdout)
        device = data["blockdevices"][0]

        is_rotational = device.get("rota", True)
        is_nvme = "nvme" in target.lower()

        if is_nvme:
            device_type = "NVMe"
        elif not is_rotational:
            device_type = "SSD"
        else:
            device_type = "HDD"

        return DeviceInfo(
            serial=device.get("serial") or "UNKNOWN",
            model=device.get("model") or "UNKNOWN",
            device_type=device_type,
            size_bytes=int(device.get("size", 0)),
            supports_encryption=(device_type in ("SSD", "NVMe")),
        )
