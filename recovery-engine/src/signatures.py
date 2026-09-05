"""
Known file-type signatures for carving. Every common file format has a
recognizable byte pattern at its start (a "magic number") and often a
predictable end marker. Carving works by scanning raw bytes for these
patterns — no filesystem metadata required.

MAX_SIZE exists because footer-less carving (e.g. a header found but no
matching footer within a reasonable window) has to stop SOMEWHERE — we
cap it and mark that recovery as lower-confidence/truncated rather than
scanning indefinitely into unrelated data.
"""
from dataclasses import dataclass


@dataclass
class FileSignature:
    name: str
    extension: str
    header: bytes
    footer: bytes | None  # None means "no reliable footer, rely on max_size"
    max_size: int
    # Some formats' footer marker is followed by a FIXED-size trailer of
    # additional required bytes that aren't part of the marker itself
    # but ARE required for the extracted file to be structurally valid.
    # ZIP's End-Of-Central-Directory record is the clearest example: the
    # 4-byte "PK\x05\x06" signature is followed by 18 more fixed bytes
    # (disk numbers, record counts, central directory size/offset,
    # comment length) that must be included or the recovered ZIP fails
    # to open even though the signature matched correctly.
    footer_trailing_fixed_bytes: int = 0


SIGNATURES: list[FileSignature] = [
    FileSignature(
        name="JPEG", extension=".jpg",
        header=b"\xff\xd8\xff",
        footer=b"\xff\xd9",
        max_size=20 * 1024 * 1024,
    ),
    FileSignature(
        name="PNG", extension=".png",
        header=b"\x89PNG\r\n\x1a\n",
        footer=b"IEND\xae\x42\x60\x82",
        max_size=20 * 1024 * 1024,
    ),
    FileSignature(
        name="PDF", extension=".pdf",
        header=b"%PDF-",
        footer=b"%%EOF",
        max_size=50 * 1024 * 1024,
    ),
    FileSignature(
        name="GIF", extension=".gif",
        header=b"GIF89a",
        footer=b"\x00\x3b",
        max_size=10 * 1024 * 1024,
    ),
    FileSignature(
        name="ZIP", extension=".zip",
        header=b"PK\x03\x04",
        footer=b"PK\x05\x06",
        max_size=100 * 1024 * 1024,
        # 18 fixed bytes follow the 4-byte EOCD signature (disk numbers,
        # central directory record counts/size/offset, comment length).
        # We don't additionally consume the variable-length comment
        # field itself — acceptable for this MVP since comment_length
        # is 0 for files created without an explicit ZIP comment, which
        # covers the vast majority of real-world files.
        footer_trailing_fixed_bytes=18,
    ),
]
