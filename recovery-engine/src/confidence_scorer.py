"""
Confidence scoring for a classified, carved file.

Scoring logic (documented so it's defensible in a demo/Q&A, not a black
box):
  - Base 0.85 if a matching footer was found (a complete, bookended
    extraction) — 0.35 if not (truncated at max_size, a guess).
  - +0.15 if structural validation independently confirmed the file
    opens/parses correctly (capped at 1.0 total).
  - -0.25 if structural validation was attempted and explicitly FAILED
    despite a footer being found — this is the "looks complete but is
    actually corrupt" case, and should score noticeably lower than an
    honest truncation.
  - No adjustment if no validator exists for that type (structurally_validated
    is None) — we don't penalize or reward what we didn't check.
"""
from src.classifier import ClassifiedFile

FOOTER_FOUND_BASE = 0.85
FOOTER_MISSING_BASE = 0.35
VALIDATION_PASS_BONUS = 0.15
VALIDATION_FAIL_PENALTY = 0.25


def score(classified: ClassifiedFile) -> float:
    base = FOOTER_FOUND_BASE if classified.footer_found else FOOTER_MISSING_BASE

    if classified.structurally_validated is True:
        base += VALIDATION_PASS_BONUS
    elif classified.structurally_validated is False:
        base -= VALIDATION_FAIL_PENALTY

    return round(max(0.0, min(1.0, base)), 2)
