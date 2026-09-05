"""
Tamper-evident ledger service, shared by all three modules.

Every signed operation record gets one ledger entry, regardless of
whether it came from the drive eraser, file eraser, or recovery module.
Each entry's `entry_hash` is sha256(previous_entry_hash + this_record's
report_hash) — so entry N can only be correctly recomputed if every
entry before it, of any operation type, is unchanged.

GENESIS_HASH is a fixed, publicly known starting value (64 zeros) so the
first ledger entry has something deterministic to chain from.
"""
from dataclasses import dataclass

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import sha256_hex
from app.models.operation_record import LedgerEntry, OperationRecord

GENESIS_HASH = "0" * 64


@dataclass
class ChainVerificationResult:
    valid: bool
    total_entries: int
    broken_at_sequence: int | None = None
    reason: str | None = None


async def get_latest_entry(db: AsyncSession) -> LedgerEntry | None:
    result = await db.execute(
        select(LedgerEntry).order_by(LedgerEntry.sequence_number.desc()).limit(1)
    )
    return result.scalar_one_or_none()


async def append_to_ledger(db: AsyncSession, record: OperationRecord) -> LedgerEntry:
    """Append a new entry for the given (already-signed) operation record.
    Must be called inside the same transaction that creates the record,
    so both commit atomically."""
    latest = await get_latest_entry(db)
    previous_hash = latest.entry_hash if latest else GENESIS_HASH
    next_sequence = (latest.sequence_number + 1) if latest else 1

    entry_hash = sha256_hex((previous_hash + record.report_hash).encode())

    entry = LedgerEntry(
        sequence_number=next_sequence,
        operation_record_id=record.id,
        report_hash=record.report_hash,
        previous_hash=previous_hash,
        entry_hash=entry_hash,
    )
    db.add(entry)
    return entry


async def verify_chain_integrity(
    db: AsyncSession, up_to_sequence: int | None = None
) -> ChainVerificationResult:
    """Recompute the entire hash chain from genesis and compare against
    what's stored. O(n) — fine for demo/MVP scale."""
    query = select(LedgerEntry).order_by(LedgerEntry.sequence_number.asc())
    if up_to_sequence is not None:
        query = query.where(LedgerEntry.sequence_number <= up_to_sequence)

    result = await db.execute(query)
    entries = result.scalars().all()

    expected_previous = GENESIS_HASH
    for entry in entries:
        if entry.previous_hash != expected_previous:
            return ChainVerificationResult(
                valid=False,
                total_entries=len(entries),
                broken_at_sequence=entry.sequence_number,
                reason="previous_hash does not match prior entry's stored hash",
            )
        recomputed = sha256_hex((entry.previous_hash + entry.report_hash).encode())
        if recomputed != entry.entry_hash:
            return ChainVerificationResult(
                valid=False,
                total_entries=len(entries),
                broken_at_sequence=entry.sequence_number,
                reason="entry_hash does not match recomputed hash — record was altered",
            )
        expected_previous = entry.entry_hash

    return ChainVerificationResult(valid=True, total_entries=len(entries))


async def get_ledger_length(db: AsyncSession) -> int:
    result = await db.execute(select(func.count()).select_from(LedgerEntry))
    return result.scalar_one()
