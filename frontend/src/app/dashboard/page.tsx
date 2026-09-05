"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getOperationPdfUrl, listOperations, UnauthorizedError } from "@/lib/api";
import { getStoredEmail, getToken, logout } from "@/lib/auth";
import type { OperationRecord } from "@/lib/types";
import { OperationTypeTag, StatusStamp, TYPE_SPINE } from "@/components/OperationBadges";

function InlineStat({ label, value, accentClass }: { label: string; value: number; accentClass: string }) {
  return (
    <div className="flex items-baseline gap-2 border-r border-line pr-6 last:border-r-0">
      <span className={`font-mono text-xl font-medium ${accentClass}`}>{value}</span>
      <span className="text-sm text-muted">{label}</span>
    </div>
  );
}

function toCsv(records: OperationRecord[]): string {
  const headers = [
    "certificate_id", "operation_type", "target_description", "operator",
    "success", "started_at", "completed_at", "ledger_sequence_number",
  ];
  const rows = records.map((r) =>
    headers.map((h) => JSON.stringify((r as any)[h] ?? "")).join(",")
  );
  return [headers.join(","), ...rows].join("\n");
}

function downloadCsv(records: OperationRecord[]) {
  const blob = new Blob([toCsv(records)], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `forensicguard-audit-export-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

const FILTERS: { key: "ALL" | OperationRecord["operation_type"]; label: string }[] = [
  { key: "ALL", label: "All entries" },
  { key: "DRIVE_ERASE", label: "Drive erase" },
  { key: "FILE_ERASE", label: "File / folder erase" },
  { key: "RECOVERY", label: "Recovery" },
];

export default function DashboardPage() {
  const [records, setRecords] = useState<OperationRecord[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<(typeof FILTERS)[number]["key"]>("ALL");
  const router = useRouter();

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    listOperations()
      .then(setRecords)
      .catch((err) => {
        if (err instanceof UnauthorizedError) {
          logout();
          router.push("/login");
        } else {
          setError(err instanceof Error ? err.message : "Failed to load data");
        }
      });
  }, [router]);

  function handleLogout() {
    logout();
    router.push("/login");
  }

  const filtered = records?.filter((r) => filter === "ALL" || r.operation_type === filter) ?? [];
  const failedCount = records?.filter((r) => !r.success).length ?? 0;

  return (
    <main className="min-h-screen px-6 py-8">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="mb-8 flex items-end justify-between border-b border-line pb-6">
          <div>
            <p className="mb-1 font-mono text-xs uppercase tracking-widest text-muted">
              Audit Log
            </p>
            <h1 className="text-2xl font-bold text-white">ForensicGuard</h1>
            <p className="mt-1 text-sm text-muted">{getStoredEmail() ?? "Operator"}</p>
          </div>
          <div className="flex gap-2">
            {records && records.length > 0 && (
              <button
                onClick={() => downloadCsv(filtered)}
                className="border border-line px-4 py-2 text-sm font-medium text-gray-300 hover:border-amber hover:text-amber"
              >
                Export CSV
              </button>
            )}
            <button
              onClick={handleLogout}
              className="border border-line px-4 py-2 text-sm font-medium text-gray-300 hover:border-alert hover:text-alert"
            >
              Sign out
            </button>
          </div>
        </div>

        {/* Hero metric + inline breakdown */}
        <div className="mb-8 flex flex-wrap items-center gap-6 border-l-2 border-amber bg-panel px-6 py-5">
          <div className="pr-6">
            <p className="font-mono text-4xl font-medium text-white">{records?.length ?? 0}</p>
            <p className="text-sm text-muted">Total operations logged</p>
          </div>
          <InlineStat label="drive erase" value={records?.filter((r) => r.operation_type === "DRIVE_ERASE").length ?? 0} accentClass="text-typeblue" />
          <InlineStat label="file erase" value={records?.filter((r) => r.operation_type === "FILE_ERASE").length ?? 0} accentClass="text-amber" />
          <InlineStat label="recovery" value={records?.filter((r) => r.operation_type === "RECOVERY").length ?? 0} accentClass="text-typeviolet" />
          <InlineStat label="failed" value={failedCount} accentClass="text-alert" />
        </div>

        {/* Filter tabs — folder-tab style, not pill buttons */}
        <div className="mb-4 flex gap-6 border-b border-line text-sm">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={`-mb-px border-b-2 pb-2.5 font-medium ${
                filter === f.key
                  ? "border-amber text-amber"
                  : "border-transparent text-muted hover:text-gray-300"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {error && (
          <div className="border-l-2 border-alert bg-alert-dim p-4 text-sm text-alert">
            {error}
          </div>
        )}

        {records === null && !error && (
          <div className="p-8 text-center font-mono text-sm text-muted">
            Loading audit log…
          </div>
        )}

        {records !== null && filtered.length === 0 && (
          <div className="p-8 text-center font-mono text-sm text-muted">
            No entries logged yet. Run any module against this backend to see activity here.
          </div>
        )}

        {records !== null && filtered.length > 0 && (
          <div className="border border-line">
            <table className="w-full text-sm">
              <thead className="border-b border-line text-left text-xs text-muted">
                <tr>
                  <th className="px-4 py-3 font-medium">Type</th>
                  <th className="px-4 py-3 font-medium">Target</th>
                  <th className="px-4 py-3 font-medium">Operator</th>
                  <th className="px-4 py-3 font-medium">Completed</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Seq.</th>
                  <th className="px-4 py-3 font-medium">Report</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((r) => (
                  <tr
                    key={r.certificate_id}
                    className={`border-b border-line border-l-2 last:border-b-0 hover:bg-white/[0.02] ${TYPE_SPINE[r.operation_type]}`}
                  >
                    <td className="px-4 py-3">
                      <OperationTypeTag type={r.operation_type} />
                    </td>
                    <td className="max-w-xs truncate px-4 py-3 font-mono text-xs text-gray-300">
                      {r.target_description}
                    </td>
                    <td className="px-4 py-3 text-gray-300">{r.operator}</td>
                    <td className="px-4 py-3 text-muted">
                      {new Date(r.completed_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <StatusStamp success={r.success} />
                    </td>
                    <td className="px-4 py-3 font-mono text-muted">{r.ledger_sequence_number}</td>
                    <td className="px-4 py-3">
                      <a
                        href={getOperationPdfUrl(r.certificate_id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-amber underline decoration-amber/30 underline-offset-2 hover:decoration-amber"
                      >
                        View
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  );
}
