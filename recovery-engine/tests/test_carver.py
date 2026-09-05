import os

from src.carver import carve
from tests.conftest import make_real_jpeg_bytes, make_real_zip_bytes


def test_carve_finds_jpeg_embedded_in_garbage(real_jpeg_bytes):
    blob = os.urandom(1000) + real_jpeg_bytes + os.urandom(1000)

    results = carve(blob)
    jpeg_results = [r for r in results if r.signature_name == "JPEG"]

    assert len(jpeg_results) == 1
    assert jpeg_results[0].offset == 1000
    assert jpeg_results[0].footer_found is True
    assert jpeg_results[0].data == real_jpeg_bytes


def test_carve_finds_multiple_different_file_types_in_one_blob(synthetic_evidence_image):
    with open(synthetic_evidence_image, "rb") as f:
        blob = f.read()

    results = carve(blob)
    types_found = {r.signature_name for r in results}

    assert "JPEG" in types_found
    assert "ZIP" in types_found
    assert "PDF" in types_found


def test_carve_finds_multiple_instances_of_same_type(real_jpeg_bytes):
    """Two separate JPEGs in the same blob must both be found, not just
    the first."""
    blob = os.urandom(500) + real_jpeg_bytes + os.urandom(500) + real_jpeg_bytes + os.urandom(500)

    results = carve(blob)
    jpeg_results = [r for r in results if r.signature_name == "JPEG"]

    assert len(jpeg_results) == 2
    assert jpeg_results[0].offset < jpeg_results[1].offset


def test_carve_marks_truncated_file_when_no_footer_found():
    """A header with no matching footer anywhere in the buffer must
    still be recovered (best-effort, cut at max_size) but flagged as
    NOT footer_found, so the confidence scorer treats it as a guess."""
    header_only = b"\xff\xd8\xff" + os.urandom(500)  # JPEG header, garbage after, no FFD9 footer

    results = carve(header_only)
    jpeg_results = [r for r in results if r.signature_name == "JPEG"]

    assert len(jpeg_results) == 1
    assert jpeg_results[0].footer_found is False


def test_carve_returns_empty_list_for_pure_garbage():
    garbage = os.urandom(10_000)
    results = carve(garbage)
    assert results == []


def test_carve_does_not_infinite_loop_on_adjacent_headers():
    """Regression-style test: two JPEG headers placed back-to-back must
    not cause an infinite scan loop or duplicate/overlapping garbage
    results."""
    jpeg = make_real_jpeg_bytes()
    blob = jpeg + jpeg  # zero gap between two complete JPEGs

    results = carve(blob)
    jpeg_results = [r for r in results if r.signature_name == "JPEG"]

    assert len(jpeg_results) == 2
