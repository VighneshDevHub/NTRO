import io
import os
import zipfile

import pytest
from PIL import Image


def make_real_jpeg_bytes() -> bytes:
    """A genuinely valid, PIL-decodable JPEG — not hand-crafted fake
    bytes. This is what lets us test structural validation for real."""
    img = Image.new("RGB", (32, 32), color=(120, 40, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_real_zip_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("case_notes.txt", "confidential witness statement")
    return buf.getvalue()


def make_fake_pdf_bytes() -> bytes:
    """A minimal but syntactically bookended PDF — doesn't need to be a
    'real' rendered PDF for carving purposes since we don't structurally
    validate PDFs in this MVP (documented limitation)."""
    return b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"


@pytest.fixture
def real_jpeg_bytes() -> bytes:
    return make_real_jpeg_bytes()


@pytest.fixture
def real_zip_bytes() -> bytes:
    return make_real_zip_bytes()


@pytest.fixture
def fake_pdf_bytes() -> bytes:
    return make_fake_pdf_bytes()


@pytest.fixture
def synthetic_evidence_image(tmp_path, real_jpeg_bytes, real_zip_bytes, fake_pdf_bytes) -> str:
    """Builds a raw byte blob simulating a formatted/corrupted drive:
    no filesystem, just random garbage with real embedded files at
    unpredictable offsets — exactly the scenario Module 3 targets."""
    garbage_1 = os.urandom(2048)
    garbage_2 = os.urandom(4096)
    garbage_3 = os.urandom(1024)

    blob = garbage_1 + real_jpeg_bytes + garbage_2 + real_zip_bytes + garbage_3 + fake_pdf_bytes

    image_path = tmp_path / "evidence_image.dd"
    image_path.write_bytes(blob)
    return str(image_path)
