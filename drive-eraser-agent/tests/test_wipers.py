import pytest

from src.wipers.clear import ClearWiper
from src.wipers.crypto_erase import CryptoEraseWiper
from src.wipers.purge import PurgeWiper


@pytest.fixture
def test_file(tmp_path):
    path = tmp_path / "test_volume.img"
    original_content = b"SENSITIVE-EVIDENCE-DATA-" * 1000
    path.write_bytes(original_content)
    return str(path), original_content


def test_clear_wiper_overwrites_all_content(test_file):
    path, original_content = test_file
    size = len(original_content)
    result = ClearWiper().wipe(path, size)
    assert result.passes == 1
    with open(path, "rb") as f:
        assert f.read() != original_content


def test_purge_wiper_does_three_passes(test_file):
    path, original_content = test_file
    size = len(original_content)
    result = PurgeWiper().wipe(path, size)
    assert result.passes == 3
    with open(path, "rb") as f:
        assert f.read() == b"\x00" * size


def test_crypto_erase_wiper_overwrites_content(test_file):
    path, original_content = test_file
    size = len(original_content)
    CryptoEraseWiper().wipe(path, size)
    with open(path, "rb") as f:
        assert f.read() != original_content
