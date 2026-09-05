"""
NIST 800-88 Purge via Crypto Erase — for self-encrypting SSD/NVMe
drives. Real hardware: hdparm --security-erase-enhanced / TCG Opal
tooling. This simulates key destruction + a fast overwrite so the
before/after content visibly differs in a demo.
"""
import os
import secrets

from src.wipers.base import Wiper, WipeResult

CHUNK_SIZE = 4 * 1024 * 1024


class CryptoEraseWiper(Wiper):
    method_name = "NIST 800-88 Purge - Crypto Erase"

    def wipe(self, target: str, size_bytes: int) -> WipeResult:
        _ephemeral_key = secrets.token_bytes(32)
        del _ephemeral_key

        bytes_written = 0
        with open(target, "r+b") as f:
            f.seek(0)
            while bytes_written < size_bytes:
                chunk = min(CHUNK_SIZE, size_bytes - bytes_written)
                f.write(os.urandom(chunk))
                bytes_written += chunk
            f.flush()
            os.fsync(f.fileno())

        return WipeResult(
            method_name=self.method_name, passes=1, bytes_processed=bytes_written
        )
