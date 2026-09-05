import os

from src.selective_deleter import _overwrite_content, secure_delete_file, secure_delete_folder


def test_overwrite_content_changes_bytes_before_deletion(tmp_path):
    """Isolates the content-overwrite step to prove it actually happens
    BEFORE the file is renamed/removed — this is the step that defeats
    file-carving recovery of the deleted content."""
    path = tmp_path / "evidence.txt"
    original = b"CASE-1234-CONFIDENTIAL-WITNESS-STATEMENT"
    path.write_bytes(original)

    bytes_written = _overwrite_content(str(path))

    assert bytes_written == len(original)
    with open(path, "rb") as f:
        assert f.read() != original


def test_secure_delete_file_removes_file_and_scrubs_metadata(tmp_path):
    path = tmp_path / "confidential.pdf"
    path.write_bytes(b"CONFIDENTIAL-DATA" * 100)

    result = secure_delete_file(str(path))

    assert result.success is True
    assert result.metadata_scrubbed is True
    assert result.bytes_overwritten == len(b"CONFIDENTIAL-DATA" * 100)
    assert not os.path.exists(path)
    # The original filename must not exist anywhere in the directory
    assert "confidential.pdf" not in os.listdir(tmp_path)


def test_secure_delete_file_handles_missing_file_gracefully(tmp_path):
    missing = tmp_path / "does_not_exist.txt"

    result = secure_delete_file(str(missing))

    assert result.success is False
    assert result.error == "File not found"


def test_secure_delete_folder_removes_all_files_and_the_folder_itself(tmp_path):
    folder = tmp_path / "case_1234_notes"
    folder.mkdir()
    (folder / "note1.txt").write_bytes(b"data one")
    (folder / "note2.txt").write_bytes(b"data two")
    subfolder = folder / "attachments"
    subfolder.mkdir()
    (subfolder / "photo.jpg").write_bytes(b"fake jpg data")

    results = secure_delete_folder(str(folder))

    assert len(results) == 3
    assert all(r.success for r in results)
    assert not os.path.exists(folder)


def test_secure_delete_folder_on_nonexistent_folder_returns_failure(tmp_path):
    missing = tmp_path / "nonexistent_folder"
    results = secure_delete_folder(str(missing))
    assert len(results) == 1
    assert results[0].success is False
