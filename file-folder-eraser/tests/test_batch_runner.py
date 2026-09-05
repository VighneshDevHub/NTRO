import os

from src.batch_runner import run_batch


def test_run_batch_deletes_multiple_files(tmp_path):
    files = []
    for i in range(3):
        f = tmp_path / f"evidence_{i}.txt"
        f.write_bytes(f"data-{i}".encode() * 50)
        files.append(str(f))

    result = run_batch(files, overwrite_freespace=False)

    assert result.targets_requested == 3
    assert result.files_deleted == 3
    assert result.files_failed == 0
    assert result.metadata_scrubbed is True
    for f in files:
        assert not os.path.exists(f)


def test_run_batch_reports_partial_failure_without_crashing(tmp_path):
    """A batch with one bad target must still process the good ones and
    report the failure honestly, not abort the whole operation."""
    good_file = tmp_path / "good.txt"
    good_file.write_bytes(b"data")
    missing_file = str(tmp_path / "does_not_exist.txt")

    result = run_batch([str(good_file), missing_file], overwrite_freespace=False)

    assert result.targets_requested == 2
    assert result.files_deleted == 1
    assert result.files_failed == 1
    assert not os.path.exists(good_file)


def test_run_batch_expands_folders(tmp_path):
    folder = tmp_path / "case_notes"
    folder.mkdir()
    (folder / "a.txt").write_bytes(b"a")
    (folder / "b.txt").write_bytes(b"b")

    result = run_batch([str(folder)], overwrite_freespace=False)

    assert result.files_deleted == 2
    assert not os.path.exists(folder)


def test_run_batch_with_freespace_overwrite_enabled(tmp_path):
    f = tmp_path / "secret.txt"
    f.write_bytes(b"secret data" * 100)

    result = run_batch([str(f)], overwrite_freespace=True, freespace_max_bytes=500_000)

    assert result.files_deleted == 1
    assert result.freespace_bytes_overwritten > 0


def test_run_batch_freespace_overwrite_works_when_target_is_a_whole_folder(tmp_path):
    """Regression test: when the target is an entire FOLDER,
    secure_delete_folder removes the folder itself, so the free-space
    pass must fall back to the nearest still-existing ancestor
    directory instead of crashing on a path that no longer exists."""
    folder = tmp_path / "case_notes"
    folder.mkdir()
    (folder / "a.txt").write_bytes(b"a" * 100)

    result = run_batch([str(folder)], overwrite_freespace=True, freespace_max_bytes=500_000)

    assert result.files_deleted == 1
    assert not os.path.exists(folder)
    assert result.freespace_bytes_overwritten > 0


def test_run_batch_skips_freespace_pass_if_nothing_succeeded(tmp_path):
    missing = str(tmp_path / "does_not_exist.txt")

    result = run_batch([missing], overwrite_freespace=True, freespace_max_bytes=500_000)

    assert result.files_deleted == 0
    assert result.freespace_bytes_overwritten == 0
