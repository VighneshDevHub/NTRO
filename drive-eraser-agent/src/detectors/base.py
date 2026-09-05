"""
Device detection interface. A real deployment detects actual physical
drives; for safe demo/testing we detect a target file and treat it as a
stand-in "device". Identical interface either way — see file_target.py
vs linux_block_device.py.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class DeviceInfo:
    serial: str
    model: str
    device_type: str  # "HDD" | "SSD" | "NVMe" | "USB" | "TEST_FILE"
    size_bytes: int
    supports_encryption: bool = False


class DeviceDetector(ABC):
    @abstractmethod
    def detect(self, target: str) -> DeviceInfo:
        raise NotImplementedError
