import random
from dataclasses import dataclass

SAMPLE_COUNT = 20
SAMPLE_SIZE = 512


@dataclass
class VerificationResult:
    passed: bool
    samples_checked: int
    samples_changed: int


def verify_wipe(target: str, pre_wipe_samples: list[tuple[int, bytes]]) -> VerificationResult:
    changed = 0
    with open(target, "rb") as f:
        for offset, original_bytes in pre_wipe_samples:
            f.seek(offset)
            current_bytes = f.read(len(original_bytes))
            if current_bytes != original_bytes:
                changed += 1

    total = len(pre_wipe_samples)
    return VerificationResult(
        passed=(changed == total and total > 0),
        samples_checked=total,
        samples_changed=changed,
    )


def capture_pre_wipe_samples(target: str, size_bytes: int) -> list[tuple[int, bytes]]:
    if size_bytes <= SAMPLE_SIZE:
        offsets = [0]
    else:
        offsets = [random.randint(0, size_bytes - SAMPLE_SIZE) for _ in range(SAMPLE_COUNT)]

    samples = []
    with open(target, "rb") as f:
        for offset in offsets:
            f.seek(offset)
            samples.append((offset, f.read(SAMPLE_SIZE)))
    return samples
