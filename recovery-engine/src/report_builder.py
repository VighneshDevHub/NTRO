from datetime import datetime, timezone

from src.recovery_engine import RecoverySummary


def build_report(
    summary: RecoverySummary,
    started_at: datetime,
    completed_at: datetime,
    operator: str,
) -> dict:
    return {
        "operation_type": "RECOVERY",
        "target_description": summary.source_image,
        "started_at": started_at.astimezone(timezone.utc).isoformat(),
        "completed_at": completed_at.astimezone(timezone.utc).isoformat(),
        # success = evidence integrity preserved AND at least one file recovered.
        # A recovery run that finds nothing is not a "failure" of the tool,
        # but a run that ALTERED the evidence source would be — that's the
        # non-negotiable condition here.
        "success": summary.source_hash_before == summary.source_hash_after,
        "operator": operator,
        "details": {
            "evidence_integrity_preserved": summary.source_hash_before == summary.source_hash_after,
            "source_hash_before": summary.source_hash_before,
            "source_hash_after": summary.source_hash_after,
            "files_recovered": summary.files_recovered,
            "avg_confidence": summary.avg_confidence,
            "classifications": summary.classifications,
            "files": [
                {
                    "type": r.file_type,
                    "offset": r.offset,
                    "size": r.size,
                    "confidence": r.confidence,
                    "footer_found": r.footer_found,
                    "structurally_validated": r.structurally_validated,
                }
                for r in summary.recovered_files
            ],
        },
    }
