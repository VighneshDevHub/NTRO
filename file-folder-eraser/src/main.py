"""
File & Folder Eraser CLI.

Since Phase 5, the operator identity comes from login (--email/--password)
— the backend cryptographically ties every record to a real authenticated
account rather than self-reported text.

Usage:
    python -m src.main --targets file1.txt case_notes/ --email investigator@example.com --password secret123

Add --no-freespace-overwrite to skip the free-space pass (faster, but
leaves freed blocks potentially recoverable until something else
overwrites them).
"""
import argparse
from datetime import datetime, timezone

from src.api_client import ApiClient
from src.batch_runner import run_batch
from src.report_builder import build_report


def run(
    targets: list[str],
    api_url: str,
    overwrite_freespace: bool,
    freespace_max_bytes: int | None,
    email: str,
    password: str,
) -> dict:
    print(f"[batch] Processing {len(targets)} target(s)...")
    started_at = datetime.now(timezone.utc)

    batch_result = run_batch(
        targets, overwrite_freespace=overwrite_freespace, freespace_max_bytes=freespace_max_bytes
    )
    completed_at = datetime.now(timezone.utc)

    print(f"[batch] Deleted: {batch_result.files_deleted}, Failed: {batch_result.files_failed}")
    print(f"[batch] Bytes overwritten (content): {batch_result.total_bytes_overwritten}")
    print(f"[batch] Metadata scrubbed: {batch_result.metadata_scrubbed}")
    if overwrite_freespace:
        print(f"[batch] Free space overwritten: {batch_result.freespace_bytes_overwritten} bytes")
    if batch_result.files_failed:
        for r in batch_result.per_file_results:
            if not r.success:
                print(f"  [failed] {r.original_path}: {r.error}")

    target_summary = f"{batch_result.files_deleted} file(s) across {len(targets)} target(s)"
    # `operator` sent for schema compatibility but authoritatively
    # overridden server-side by the logged-in identity.
    report = build_report(batch_result, started_at, completed_at, email, target_summary)

    print(f"[report] Logging in as {email} and submitting FILE_ERASE operation to {api_url}...")
    client = ApiClient(base_url=api_url, email=email, password=password)
    record = client.submit_operation_report(report)
    print(f"[report] Certificate issued: {record['certificate_id']}")
    print(f"[report] Recorded operator (authenticated): {record['operator']}")
    print(f"[report] Ledger sequence number: {record['ledger_sequence_number']}")

    return record


def main():
    parser = argparse.ArgumentParser(description="ForensicGuard File & Folder Eraser")
    parser.add_argument("--targets", nargs="+", required=True, help="Files/folders to securely delete")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--no-freespace-overwrite", action="store_true")
    parser.add_argument(
        "--freespace-max-bytes", type=int, default=None,
        help="Cap the free-space overwrite pass (useful for quick demos)",
    )
    parser.add_argument("--email", required=True, help="Operator login email (auto-registers on first use)")
    parser.add_argument("--password", required=True, help="Operator login password")
    args = parser.parse_args()

    run(
        targets=args.targets,
        api_url=args.api_url,
        overwrite_freespace=not args.no_freespace_overwrite,
        freespace_max_bytes=args.freespace_max_bytes,
        email=args.email,
        password=args.password,
    )


if __name__ == "__main__":
    main()
