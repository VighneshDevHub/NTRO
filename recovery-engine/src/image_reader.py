"""
Read-only access to the evidence image/drive. This module exists as a
deliberate chokepoint: it is the ONLY place in the recovery engine that
touches the source path, and it opens that path in binary READ mode
only. No other module should ever call open() directly on the evidence
source — this keeps the "never modify the original evidence" guarantee
enforceable at one narrow point rather than trusted throughout the
codebase.

Demo-scale limitation: loads the full image into memory. A production
version handling multi-gigabyte drive images would memory-map the file
(mmap) or scan in overlapping streamed chunks instead.
"""
import hashlib
import os


class ImageReader:
    def __init__(self, image_path: str):
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"Evidence image not found: {image_path}")
        self.image_path = image_path

    def read_all_bytes(self) -> bytes:
        """Read the entire image read-only. Never opens in 'r+b', 'w',
        or any writable mode — there is no write path in this class."""
        with open(self.image_path, "rb") as f:
            return f.read()

    def sha256(self) -> str:
        """Hash of the source evidence, computed before AND after a
        recovery run should be identical — this is how you'd prove in
        a real forensic workflow that the evidence was never altered."""
        hasher = hashlib.sha256()
        with open(self.image_path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def size_bytes(self) -> int:
        return os.path.getsize(self.image_path)
