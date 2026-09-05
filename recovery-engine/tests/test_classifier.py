from src.carver import CarvedFile
from src.classifier import classify


def test_classify_validates_genuinely_valid_jpeg(real_jpeg_bytes):
    carved = CarvedFile(
        signature_name="JPEG", extension=".jpg", offset=0,
        size=len(real_jpeg_bytes), data=real_jpeg_bytes, footer_found=True,
    )
    classified = classify(carved)
    assert classified.structurally_validated is True


def test_classify_rejects_garbage_bookended_with_jpeg_markers():
    """The critical test: bytes that LOOK like a JPEG (correct header +
    footer) but contain garbage in between must be caught by structural
    validation, not blindly trusted just because the markers matched."""
    fake_jpeg = b"\xff\xd8\xff" + b"THIS IS NOT REAL IMAGE DATA" * 20 + b"\xff\xd9"

    carved = CarvedFile(
        signature_name="JPEG", extension=".jpg", offset=0,
        size=len(fake_jpeg), data=fake_jpeg, footer_found=True,
    )
    classified = classify(carved)
    assert classified.structurally_validated is False


def test_classify_validates_genuine_zip(real_zip_bytes):
    carved = CarvedFile(
        signature_name="ZIP", extension=".zip", offset=0,
        size=len(real_zip_bytes), data=real_zip_bytes, footer_found=True,
    )
    classified = classify(carved)
    assert classified.structurally_validated is True


def test_carved_zip_includes_full_eocd_record_not_just_signature(real_zip_bytes):
    """Regression test for a real bug: the ZIP End-Of-Central-Directory
    footer is a 4-byte signature FOLLOWED BY 18 more required fixed
    bytes. Carving that stops right at the signature produces a
    truncated, invalid ZIP even though the 'footer was found' — this
    must not happen. This test carves from raw bytes end-to-end
    (not just classify()) to catch the truncation at its source."""
    from src.carver import carve

    blob = real_zip_bytes  # no surrounding garbage — isolates the exact boundary
    results = [r for r in carve(blob) if r.signature_name == "ZIP"]

    assert len(results) == 1
    assert results[0].data == real_zip_bytes  # must recover the FULL file, not a truncated prefix
    classified = classify(results[0])
    assert classified.structurally_validated is True


def test_classify_rejects_garbage_bookended_with_zip_markers():
    fake_zip = b"PK\x03\x04" + b"NOT REAL ZIP CONTENT" * 10 + b"PK\x05\x06"

    carved = CarvedFile(
        signature_name="ZIP", extension=".zip", offset=0,
        size=len(fake_zip), data=fake_zip, footer_found=True,
    )
    classified = classify(carved)
    assert classified.structurally_validated is False


def test_classify_pdf_has_no_validator_and_is_disclosed_as_none(fake_pdf_bytes):
    """PDF has no structural validator in this MVP — must be explicitly
    None, never silently coerced to True/False, so the confidence
    scorer knows not to apply a bonus/penalty it can't actually justify."""
    carved = CarvedFile(
        signature_name="PDF", extension=".pdf", offset=0,
        size=len(fake_pdf_bytes), data=fake_pdf_bytes, footer_found=True,
    )
    classified = classify(carved)
    assert classified.structurally_validated is None
