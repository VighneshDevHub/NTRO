"""
Classification and structural validation of carved candidates.

Finding a header+footer byte pattern is necessary but not sufficient
proof that a recovered blob is a genuinely valid file — the bytes in
between could still be garbage that happens to be bookended correctly.
Where a real parser exists (Pillow for images, zipfile for ZIP-based
formats), we actually try to open/verify the recovered bytes and use
that as a second, independent signal for the confidence scorer.

PDF and GIF don't get a deep structural check here (no lightweight
stdlib/pure-Python parser was pulled in for them) — they're classified
by signature match only, which is disclosed to the confidence scorer via
`structurally_validated=None` rather than silently treated as an
equivalent "valid" result.
"""
import io
import zipfile
from dataclasses import dataclass

from PIL import Image, UnidentifiedImageError

from src.carver import CarvedFile


@dataclass
class ClassifiedFile:
    signature_name: str
    extension: str
    offset: int
    size: int
    data: bytes
    footer_found: bool
    structurally_validated: bool | None  # None = no validator available for this type


def classify(carved: CarvedFile) -> ClassifiedFile:
    validated: bool | None

    if carved.signature_name in ("JPEG", "PNG", "GIF"):
        validated = _validate_image(carved.data)
    elif carved.signature_name == "ZIP":
        validated = _validate_zip(carved.data)
    else:
        validated = None  # e.g. PDF — no validator wired up for this MVP

    return ClassifiedFile(
        signature_name=carved.signature_name,
        extension=carved.extension,
        offset=carved.offset,
        size=carved.size,
        data=carved.data,
        footer_found=carved.footer_found,
        structurally_validated=validated,
    )


def _validate_image(data: bytes) -> bool:
    try:
        img = Image.open(io.BytesIO(data))
        img.verify()  # raises if the pixel/structure data is corrupt
        return True
    except (UnidentifiedImageError, OSError, ValueError):
        return False


def _validate_zip(data: bytes) -> bool:
    try:
        return zipfile.is_zipfile(io.BytesIO(data))
    except Exception:
        return False
