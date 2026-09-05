"""
Orchestrates the full recovery pipeline: read the evidence image
read-only, carve candidates, classify + validate each one, score
confidence, and write RECOVERED copies to a separate output directory
— never back to the source path.
"""
import os
from dataclasses import dataclass

from src.carver import carve
from src.classifier import classify
from src.confidence_scorer import score
from src.image_reader import ImageReader


@dataclass
class RecoveredFileResult:
    file_type: str
    offset: int
    size: int
    confidence: float
    footer_found: bool
    structurally_validated: bool | None
    output_path: str


@dataclass
class RecoverySummary:
    source_image: str
    source_hash_before: str
    source_hash_after: str
    files_recovered: int
    avg_confidence: float
    classifications: dict[str, int]
    recovered_files: list[RecoveredFileResult]


def run_recovery(image_path: str, output_dir: str) -> RecoverySummary:
    os.makedirs(output_dir, exist_ok=True)

    reader = ImageReader(image_path)
    hash_before = reader.sha256()  # evidence integrity checkpoint

    buffer = reader.read_all_bytes()
    carved_candidates = carve(buffer)

    recovered: list[RecoveredFileResult] = []
    classification_counts: dict[str, int] = {}

    for i, candidate in enumerate(carved_candidates):
        classified = classify(candidate)
        confidence = score(classified)

        output_filename = f"recovered_{i:04d}_{classified.signature_name.lower()}{classified.extension}"
        output_path = os.path.join(output_dir, output_filename)
        with open(output_path, "wb") as f:
            f.write(classified.data)

        recovered.append(RecoveredFileResult(
            file_type=classified.signature_name,
            offset=classified.offset,
            size=classified.size,
            confidence=confidence,
            footer_found=classified.footer_found,
            structurally_validated=classified.structurally_validated,
            output_path=output_path,
        ))
        classification_counts[classified.signature_name] = (
            classification_counts.get(classified.signature_name, 0) + 1
        )

    hash_after = reader.sha256()  # must be identical to hash_before

    avg_confidence = (
        round(sum(r.confidence for r in recovered) / len(recovered), 2)
        if recovered else 0.0
    )

    return RecoverySummary(
        source_image=image_path,
        source_hash_before=hash_before,
        source_hash_after=hash_after,
        files_recovered=len(recovered),
        avg_confidence=avg_confidence,
        classifications=classification_counts,
        recovered_files=recovered,
    )
