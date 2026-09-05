"""
Safe demo detector: treats a regular file (or loopback image) as the
"device" being wiped. Use this for all live demos — never touches real
hardware. For real hardware, see linux_block_device.py.
"""
import hashlib
import os

from src.detectors.base import DeviceDetector, DeviceInfo


class FileTargetDetector(DeviceDetector):
    def detect(self, target: str) -> DeviceInfo:
        if not os.path.isfile(target):
            raise FileNotFoundError(
                f"Target file not found: {target}. For safety, this agent "
                f"only wipes regular files or explicit block devices you "
                f"pass with --target."
            )

        size_bytes = os.path.getsize(target)
        path_hash = hashlib.sha256(os.path.abspath(target).encode()).hexdigest()[:12]
        serial = f"TESTFILE-{path_hash.upper()}"

        return DeviceInfo(
            serial=serial,
            model=f"Simulated test volume ({os.path.basename(target)})",
            device_type="TEST_FILE",
            size_bytes=size_bytes,
            supports_encryption=False,
        )
