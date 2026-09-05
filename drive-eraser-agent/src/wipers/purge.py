"""
NIST 800-88 Purge. Real hardware should invoke ATA Secure Erase
(hdparm --security-erase) or NVMe Sanitize (nvme-cli sanitize) instead
of this software fallback — see docs/phase2.md.
"""
import os

from src.wipers.base import Wiper, WipeResult

CHUNK_SIZE = 1024 * 1024


class PurgeWiper(Wiper):
    method_name = "NIST 800-88 Purge (3-pass overwrite, software fallback)"

    def wipe(self, target: str, size_bytes: int) -> WipeResult:
        passes = 0
        with open(target, "r+b") as f:
            for pass_num in range(3):
                f.seek(0)
                bytes_written = 0
                while bytes_written < size_bytes:
                    chunk = min(CHUNK_SIZE, size_bytes - bytes_written)
                    if pass_num < 2:
                        f.write(os.urandom(chunk))
                    else:
                        f.write(b"\x00" * chunk)
                    bytes_written += chunk
                f.flush()
                os.fsync(f.fileno())
                passes += 1

        return WipeResult(
            method_name=self.method_name, passes=passes, bytes_processed=size_bytes
        )
