from src.wipers.base import Wiper
from src.wipers.clear import ClearWiper
from src.wipers.crypto_erase import CryptoEraseWiper
from src.wipers.purge import PurgeWiper


def select_wiper(device_type: str, supports_encryption: bool) -> Wiper:
    if device_type == "TEST_FILE":
        return ClearWiper()
    if supports_encryption and device_type in ("SSD", "NVMe"):
        return CryptoEraseWiper()
    if device_type == "HDD":
        return PurgeWiper()
    return ClearWiper()
