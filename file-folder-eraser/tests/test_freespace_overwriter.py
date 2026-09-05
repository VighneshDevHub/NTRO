import os
import sys

import pytest

from src.freespace_overwriter import overwrite_free_space


def _running_as_unix_root() -> bool:
    """os.geteuid() doesn't exist on Windows at all — must guard with
    hasattr rather than assume Unix. On Windows this always returns
    False, since admin-vs-user Windows permission semantics are
    different enough that this specific test's premise (chmod-based
    unwritable directory) doesn't map onto Windows regardless."""
    return hasattr(os, "geteuid") and os.geteuid() == 0


def test_overwrite_free_space_respects_max_bytes_cap(tmp_path):
    result = overwrite_free_space(str(tmp_path), max_bytes=1_000_000)  # 1 MB cap

    assert result.bytes_written <= 1_000_000
    assert result.bytes_written > 0
    assert result.capped is True


def test_overwrite_free_space_cleans_up_temp_file(tmp_path):
    overwrite_free_space(str(tmp_path), max_bytes=500_000)

    remaining_files = os.listdir(tmp_path)
    assert ".fg_freespace_fill.tmp" not in remaining_files


@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="chmod-based read-only directories don't reliably block writes "
           "on Windows the way they do on POSIX — this test's premise is "
           "Unix-specific. Windows ACL-based permission testing would need "
           "a different approach (e.g. icacls) if this needs re-covering there.",
)
@pytest.mark.skipif(
    _running_as_unix_root(),
    reason="Running as root bypasses Unix permission checks entirely, "
           "so an 'unwritable' directory isn't actually unwritable — "
           "this test only means something under a non-root Unix user.",
)
def test_overwrite_free_space_raises_on_unwritable_directory(tmp_path):
    """A skipped free-space pass is a real gap in the erasure guarantee
    — this must fail loudly, not silently no-op. (POSIX-only test.)"""
    unwritable_dir = tmp_path / "readonly"
    unwritable_dir.mkdir()
    unwritable_dir.chmod(0o444)

    try:
        raised = False
        try:
            overwrite_free_space(str(unwritable_dir), max_bytes=100_000)
        except OSError:
            raised = True
        assert raised is True
    finally:
        unwritable_dir.chmod(0o755)  # restore so pytest can clean up tmp_path