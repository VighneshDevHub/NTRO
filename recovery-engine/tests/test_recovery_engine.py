import os

from PIL import Image

from src.recovery_engine import run_recovery


def test_recovery_finds_and_writes_files(synthetic_evidence_image, tmp_path):
    output_dir = str(tmp_path / "recovered")

    summary = run_recovery(synthetic_evidence_image, output_dir)

    assert summary.files_recovered >= 3  # JPEG, ZIP, PDF at minimum
    assert "JPEG" in summary.classifications
    assert "ZIP" in summary.classifications
    assert "PDF" in summary.classifications
    assert os.path.isdir(output_dir)
    assert len(os.listdir(output_dir)) == summary.files_recovered


def test_recovered_jpeg_is_actually_openable(synthetic_evidence_image, tmp_path):
    """End-to-end proof: the file we wrote to disk as 'recovered' isn't
    just bytes that matched a pattern — it's a genuinely valid image
    that PIL can open again, fresh, from the output file."""
    output_dir = str(tmp_path / "recovered")
    summary = run_recovery(synthetic_evidence_image, output_dir)

    jpeg_result = next(r for r in summary.recovered_files if r.file_type == "JPEG")
    img = Image.open(jpeg_result.output_path)
    img.verify()  # raises if corrupt — test fails loudly if so


def test_recovery_never_alters_source_evidence(synthetic_evidence_image, tmp_path):
    """THE most important test in this module: the evidence source's
    hash must be byte-for-byte identical before and after recovery.
    This is the forensic integrity requirement from the PS (NFR1),
    verified directly rather than just asserted in a docstring."""
    output_dir = str(tmp_path / "recovered")

    original_mtime = os.path.getmtime(synthetic_evidence_image)
    with open(synthetic_evidence_image, "rb") as f:
        original_bytes = f.read()

    summary = run_recovery(synthetic_evidence_image, output_dir)

    with open(synthetic_evidence_image, "rb") as f:
        bytes_after = f.read()

    assert bytes_after == original_bytes
    assert os.path.getmtime(synthetic_evidence_image) == original_mtime
    assert summary.source_hash_before == summary.source_hash_after


def test_recovery_on_pure_garbage_finds_nothing_but_still_preserves_integrity(tmp_path):
    garbage_image = tmp_path / "empty_drive.dd"
    garbage_image.write_bytes(os.urandom(50_000))
    output_dir = str(tmp_path / "recovered")

    summary = run_recovery(str(garbage_image), output_dir)

    assert summary.files_recovered == 0
    assert summary.avg_confidence == 0.0
    assert summary.source_hash_before == summary.source_hash_after
