import type { OperationRecord, OperationType } from "@/lib/types";

const TYPE_LABELS: Record<OperationType, string> = {
  DRIVE_ERASE: "Drive Erase",
  FILE_ERASE: "File / Folder Erase",
  RECOVERY: "Recovery",
};

// Literal Tailwind class strings per type — kept explicit (not derived
// via string manipulation) so Tailwind's static scanner can find them.
const TYPE_DOT: Record<OperationType, string> = {
  DRIVE_ERASE: "bg-typeblue",
  FILE_ERASE: "bg-amber",
  RECOVERY: "bg-typeviolet",
};

const TYPE_TEXT: Record<OperationType, string> = {
  DRIVE_ERASE: "text-typeblue",
  FILE_ERASE: "text-amber",
  RECOVERY: "text-typeviolet",
};

export const TYPE_SPINE: Record<OperationType, string> = {
  DRIVE_ERASE: "border-l-typeblue",
  FILE_ERASE: "border-l-amber",
  RECOVERY: "border-l-typeviolet",
};

export function OperationTypeTag({ type }: { type: OperationType }) {
  return (
    <span className={`inline-flex items-center gap-1.5 text-sm font-medium ${TYPE_TEXT[type]}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${TYPE_DOT[type]}`} />
      {TYPE_LABELS[type]}
    </span>
  );
}

/** Renders like an ink stamp: outlined, not filled — a verification
 * outcome is a cryptographic fact, not a UI decoration, so it should
 * read as "stamped," not "colored in." */
export function StatusStamp({ success }: { success: boolean }) {
  return (
    <span
      className={`inline-block rounded border px-2 py-0.5 text-xs font-medium tracking-wide ${
        success
          ? "border-teal/60 bg-teal-dim text-teal"
          : "border-alert/60 bg-alert-dim text-alert"
      }`}
    >
      {success ? "Verified" : "Failed"}
    </span>
  );
}

function DetailRow({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex justify-between gap-4 border-b border-line py-2.5 text-sm">
      <span className="text-muted">{label}</span>
      <span className={`max-w-[60%] break-all text-right text-gray-100 ${mono ? "font-mono text-xs" : "font-medium"}`}>
        {value}
      </span>
    </div>
  );
}

/** Type-specific fields from `details` — kept in sync manually with
 * drive-eraser-agent / file-folder-eraser / recovery-engine's
 * report_builder.py output shapes. */
export function OperationDetails({ record }: { record: OperationRecord }) {
  const d = record.details as Record<string, any>;

  if (record.operation_type === "DRIVE_ERASE") {
    return (
      <>
        <DetailRow label="Device type" value={String(d.device_type ?? "N/A")} />
        <DetailRow label="Method" value={String(d.method ?? "N/A")} />
        <DetailRow label="Bytes processed" value={String(d.bytes_processed ?? "N/A")} mono />
        <DetailRow label="Verification passed" value={d.verification_passed ? "Yes" : "No"} />
      </>
    );
  }

  if (record.operation_type === "FILE_ERASE") {
    return (
      <>
        <DetailRow label="Files deleted" value={String(d.files_deleted ?? "N/A")} mono />
        <DetailRow label="Files failed" value={String(d.files_failed ?? "N/A")} mono />
        <DetailRow label="Metadata scrubbed" value={d.metadata_scrubbed ? "Yes" : "No"} />
        <DetailRow
          label="Free space overwritten"
          value={`${d.freespace_bytes_overwritten ?? 0} bytes`}
          mono
        />
      </>
    );
  }

  if (record.operation_type === "RECOVERY") {
    return (
      <>
        <DetailRow
          label="Evidence integrity"
          value={d.evidence_integrity_preserved ? "Preserved" : "COMPROMISED"}
        />
        <DetailRow label="Files recovered" value={String(d.files_recovered ?? "N/A")} mono />
        <DetailRow label="Avg. confidence" value={String(d.avg_confidence ?? "N/A")} mono />
        <DetailRow label="Classifications" value={JSON.stringify(d.classifications ?? {})} mono />
      </>
    );
  }

  return null;
}
