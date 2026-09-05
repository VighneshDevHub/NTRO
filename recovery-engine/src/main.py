"""
Recovery Engine CLI.

Since Phase 5, the operator identity comes from login (--email/--password)
— the backend cryptographically ties every record to a real authenticated
account rather than self-reported text.

Usage:
    python -m src.main --image seized_drive.dd --output-dir recovered/ --email investigator@example.com --password secret123
"""
import argparse
from datetime import datetime, timezone

from src.api_client import ApiClient
from src.recovery_engine import run_recovery
from src.report_builder import build_report


def run(image_path: str, output_dir: str, api_url: str, email: str, password: str) -> dict:
    print(f"[recovery] Reading evidence image (read-only): {image_path}")
    started_at = datetime.now(timezone.utc)

    summary = run_recovery(image_path, output_dir)
    completed_at = datetime.now(timezone.utc)

    integrity_ok = summary.source_hash_before == summary.source_hash_after
    print(f"[recovery] Evidence integrity preserved: {integrity_ok}")
    if not integrity_ok:
        print("[recovery] CRITICAL: source hash changed during recovery — this must never happen.")

    print(f"[recovery] Files recovered: {summary.files_recovered}")
    print(f"[recovery] Average confidence: {summary.avg_confidence}")
    print(f"[recovery] Classifications: {summary.classifications}")
    for r in summary.recovered_files:
        flag = "✓" if r.footer_found else "~"
        print(f"  [{flag}] {r.file_type} @ offset {r.offset}, {r.size} bytes, confidence {r.confidence}")

    # `operator` sent for schema compatibility but authoritatively
    # overridden server-side by the logged-in identity.
    report = build_report(summary, started_at, completed_at, email)

    print(f"[report] Logging in as {email} and submitting RECOVERY operation to {api_url}...")
    client = ApiClient(base_url=api_url, email=email, password=password)
    record = client.submit_operation_report(report)
    print(f"[report] Certificate issued: {record['certificate_id']}")
    print(f"[report] Recorded operator (authenticated): {record['operator']}")
    print(f"[report] Ledger sequence number: {record['ledger_sequence_number']}")

    return record


def main():
    parser = argparse.ArgumentParser(description="ForensicGuard Recovery Engine")
    parser.add_argument("--image", required=True, help="Path to the evidence image (read-only)")
    parser.add_argument("--output-dir", required=True, help="Where to write recovered files")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--email", required=True, help="Operator login email (auto-registers on first use)")
    parser.add_argument("--password", required=True, help="Operator login password")
    args = parser.parse_args()

    run(
        image_path=args.image, output_dir=args.output_dir, api_url=args.api_url,
        email=args.email, password=args.password,
    )


if __name__ == "__main__":
    main()
