from app.services.pdf_service import generate_operation_pdf

DRIVE_ERASE_RECORD = {
    "certificate_id": "c-drive-001",
    "operation_type": "DRIVE_ERASE",
    "target_description": "SSD-WD2023-88451",
    "started_at": "2026-08-30T10:00:00+00:00",
    "completed_at": "2026-08-30T10:00:05+00:00",
    "success": True,
    "operator": "investigator@forensicguard.example",
    "details": {
        "device_type": "NVMe SSD", "method": "NIST 800-88 Purge - Crypto Erase",
        "passes": 1, "bytes_processed": 512000000000, "verification_passed": True,
    },
    "report_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b85",
    "signature": "3045022100" + "a" * 100,
    "ledger_sequence_number": 1,
    "created_at": "2026-08-30T10:00:06+00:00",
}

FILE_ERASE_RECORD = {
    **DRIVE_ERASE_RECORD,
    "certificate_id": "c-file-002",
    "operation_type": "FILE_ERASE",
    "target_description": "3 file(s) across 1 target(s)",
    "details": {
        "files_deleted": 3, "files_failed": 0, "metadata_scrubbed": True,
        "total_bytes_overwritten": 45000, "freespace_bytes_overwritten": 2000000,
    },
}

RECOVERY_RECORD = {
    **DRIVE_ERASE_RECORD,
    "certificate_id": "c-recovery-003",
    "operation_type": "RECOVERY",
    "target_description": "seized_drive_001.dd",
    "details": {
        "evidence_integrity_preserved": True,
        "files_recovered": 2, "avg_confidence": 0.95,
        "classifications": {"JPEG": 1, "ZIP": 1},
        "files": [
            {"type": "JPEG", "offset": 5000, "size": 4300, "confidence": 1.0},
            {"type": "ZIP", "offset": 12000, "size": 190, "confidence": 1.0},
        ],
    },
}


def test_drive_erase_pdf_is_valid():
    pdf = generate_operation_pdf(DRIVE_ERASE_RECORD)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000


def test_file_erase_pdf_is_valid():
    pdf = generate_operation_pdf(FILE_ERASE_RECORD)
    assert pdf.startswith(b"%PDF")


def test_recovery_pdf_is_valid():
    pdf = generate_operation_pdf(RECOVERY_RECORD)
    assert pdf.startswith(b"%PDF")


def test_recovery_pdf_handles_many_files_without_crashing():
    """The per-file table caps displayed rows — must not crash or
    produce a broken PDF for a recovery run with a large number of
    recovered files."""
    record = dict(RECOVERY_RECORD)
    record["details"] = dict(RECOVERY_RECORD["details"])
    record["details"]["files"] = [
        {"type": "JPEG", "offset": i * 1000, "size": 4000, "confidence": 0.9}
        for i in range(50)
    ]
    pdf = generate_operation_pdf(record)
    assert pdf.startswith(b"%PDF")


def test_pdf_handles_missing_details_keys_gracefully():
    """A record with an EMPTY details dict (e.g. a minimal/malformed
    submission) must still render a PDF, showing 'N/A' rather than
    crashing on a missing key."""
    record = dict(DRIVE_ERASE_RECORD)
    record["details"] = {}
    pdf = generate_operation_pdf(record)
    assert pdf.startswith(b"%PDF")


def test_unknown_operation_type_falls_back_to_generic_title():
    record = dict(DRIVE_ERASE_RECORD)
    record["operation_type"] = "SOME_FUTURE_MODULE"
    record["details"] = {}
    pdf = generate_operation_pdf(record)
    assert pdf.startswith(b"%PDF")
