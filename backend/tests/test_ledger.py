from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.operation_record import LedgerEntry, OperationRecord, OperationType
from app.services import ledger_service


async def _make_record(db, op_type: OperationType, desc: str) -> OperationRecord:
    r = OperationRecord(
        operation_type=op_type,
        target_description=desc,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        success=True,
        operator="pytest",
        details={},
        report_hash=f"hash-for-{desc}",
        signature="dummy-signature",
    )
    db.add(r)
    await db.flush()
    return r


@pytest.mark.asyncio
async def test_chain_starts_from_genesis():
    async with AsyncSessionLocal() as db:
        r = await _make_record(db, OperationType.DRIVE_ERASE, "disk-1")
        entry = await ledger_service.append_to_ledger(db, r)
        await db.commit()

        assert entry.sequence_number == 1
        assert entry.previous_hash == ledger_service.GENESIS_HASH


@pytest.mark.asyncio
async def test_chain_links_across_different_operation_types():
    """The key architectural claim for Phase 1: a drive erase, a file
    erase, and a recovery operation must all sit in the SAME unbroken
    chain — proving no module's history can be tampered with in
    isolation from the others."""
    async with AsyncSessionLocal() as db:
        r1 = await _make_record(db, OperationType.DRIVE_ERASE, "disk-1")
        e1 = await ledger_service.append_to_ledger(db, r1)
        await db.commit()

        r2 = await _make_record(db, OperationType.FILE_ERASE, "folder-1")
        e2 = await ledger_service.append_to_ledger(db, r2)
        await db.commit()

        r3 = await _make_record(db, OperationType.RECOVERY, "image-1.dd")
        e3 = await ledger_service.append_to_ledger(db, r3)
        await db.commit()

        assert e1.sequence_number == 1
        assert e2.sequence_number == 2
        assert e3.sequence_number == 3
        assert e2.previous_hash == e1.entry_hash
        assert e3.previous_hash == e2.entry_hash

        result = await ledger_service.verify_chain_integrity(db)
        assert result.valid is True
        assert result.total_entries == 3


@pytest.mark.asyncio
async def test_verify_chain_integrity_detects_tampering_regardless_of_operation_type():
    async with AsyncSessionLocal() as db:
        r1 = await _make_record(db, OperationType.DRIVE_ERASE, "disk-1")
        await ledger_service.append_to_ledger(db, r1)
        await db.commit()

        r2 = await _make_record(db, OperationType.RECOVERY, "image-1.dd")
        await ledger_service.append_to_ledger(db, r2)
        await db.commit()

        # Tamper with the FIRST entry (a drive-erase record)
        result = await db.execute(
            select(LedgerEntry).where(LedgerEntry.sequence_number == 1)
        )
        entry_one = result.scalar_one()
        entry_one.report_hash = "0" * 64
        await db.commit()

        result = await ledger_service.verify_chain_integrity(db)
        assert result.valid is False
        assert result.broken_at_sequence == 1
