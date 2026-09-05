import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Integer, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OperationType(str, enum.Enum):
    """Which of the three ForensicGuard modules produced this record.
    Adding a new module later means adding a new enum value here — the
    signing/ledger machinery below needs zero changes to support it."""

    DRIVE_ERASE = "DRIVE_ERASE"
    FILE_ERASE = "FILE_ERASE"
    RECOVERY = "RECOVERY"


class OperationRecord(Base):
    """One row per operation, of ANY type. This generalizes TrustWipe's
    single-purpose WipeRecord: instead of a table shaped only for drive
    wipes, `operation_type` + a flexible `details` JSON blob let all
    three modules share one signing/ledger pipeline without forcing
    unrelated fields (e.g. 'confidence_score') onto every row.

    Immutable once created — never UPDATE this row; a correction is
    always a brand-new record, so the audit trail stays honest."""

    __tablename__ = "operation_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    certificate_id: Mapped[str] = mapped_column(
        String(36), unique=True, default=_uuid, index=True
    )

    operation_type: Mapped[OperationType] = mapped_column(
        Enum(OperationType), index=True
    )

    # Fields common to every operation type, regardless of module
    target_description: Mapped[str] = mapped_column(String(256))  # e.g. device serial, file path, image name
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    operator: Mapped[str] = mapped_column(String(128))

    # Module-specific data lives here, e.g.:
    #   DRIVE_ERASE: {"method": "...", "device_type": "...", "verification_passed": true}
    #   FILE_ERASE:  {"file_count": 12, "metadata_scrubbed": true}
    #   RECOVERY:    {"files_recovered": 8, "avg_confidence": 0.81, "classifications": {...}}
    details: Mapped[dict] = mapped_column(JSON, default=dict)

    # Trust layer
    report_hash: Mapped[str] = mapped_column(String(64))
    signature: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    ledger_entry: Mapped["LedgerEntry"] = relationship(
        back_populates="operation_record", uselist=False
    )

    @staticmethod
    def _normalize_dt(dt: datetime) -> str:
        """Normalize to a UTC ISO string regardless of tzinfo presence —
        SQLite drops tzinfo on reload, which would otherwise make a
        freshly-signed record fail its own verification after a DB
        round-trip. See TrustWipe Phase 1 postmortem for the original
        bug this fixes."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()

    def to_signable_dict(self) -> dict:
        """The exact set of fields that get hashed + signed. Keep stable
        — changing it invalidates every previously issued signature."""
        return {
            "certificate_id": self.certificate_id,
            "operation_type": self.operation_type.value,
            "target_description": self.target_description,
            "started_at": self._normalize_dt(self.started_at),
            "completed_at": self._normalize_dt(self.completed_at),
            "success": self.success,
            "operator": self.operator,
            "details": self.details,
        }


class LedgerEntry(Base):
    """Append-only hash chain, shared across ALL operation types. This
    means an eraser record and a recovery record can sit back-to-back in
    the SAME chain — proving neither the erasure history nor the
    recovery history was tampered with, using one unified ledger rather
    than three separate ones per module."""

    __tablename__ = "ledger_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    sequence_number: Mapped[int] = mapped_column(Integer, unique=True, index=True)

    operation_record_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("operation_records.id"), unique=True
    )
    operation_record: Mapped["OperationRecord"] = relationship(back_populates="ledger_entry")

    report_hash: Mapped[str] = mapped_column(String(64))
    previous_hash: Mapped[str] = mapped_column(String(64))
    entry_hash: Mapped[str] = mapped_column(String(64), unique=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
