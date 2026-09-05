from src.classifier import ClassifiedFile
from src.confidence_scorer import score


def _make(footer_found: bool, structurally_validated: bool | None) -> ClassifiedFile:
    return ClassifiedFile(
        signature_name="JPEG", extension=".jpg", offset=0, size=100,
        data=b"x", footer_found=footer_found, structurally_validated=structurally_validated,
    )


def test_score_ordering_is_sensible():
    """The core claim: a clean, validated recovery should always score
    strictly higher than a truncated guess, which should score higher
    than nothing at all, and a validated-failure should score lower
    than an honest truncation (it LOOKS complete but is actually corrupt
    — arguably worse than admitting uncertainty)."""
    clean_validated = score(_make(footer_found=True, structurally_validated=True))
    clean_unvalidated_type = score(_make(footer_found=True, structurally_validated=None))
    clean_failed_validation = score(_make(footer_found=True, structurally_validated=False))
    truncated = score(_make(footer_found=False, structurally_validated=None))

    assert clean_validated > clean_unvalidated_type > truncated
    assert clean_failed_validation < clean_unvalidated_type


def test_score_is_bounded_between_0_and_1():
    for footer in (True, False):
        for validated in (True, False, None):
            s = score(_make(footer_found=footer, structurally_validated=validated))
            assert 0.0 <= s <= 1.0


def test_score_best_case_is_high_confidence():
    s = score(_make(footer_found=True, structurally_validated=True))
    assert s >= 0.9


def test_score_worst_case_is_low_confidence():
    s = score(_make(footer_found=False, structurally_validated=None))
    assert s <= 0.5
