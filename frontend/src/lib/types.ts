// Mirrors backend/app/schemas/operation.py — keep in sync manually.

export type OperationType = "DRIVE_ERASE" | "FILE_ERASE" | "RECOVERY";

export interface OperationRecord {
  certificate_id: string;
  operation_type: OperationType;
  target_description: string;
  started_at: string;
  completed_at: string;
  success: boolean;
  operator: string;
  details: Record<string, unknown>;
  report_hash: string;
  signature: string;
  ledger_sequence_number: number;
  created_at: string;
}

export interface VerificationResult {
  certificate_id: string;
  signature_valid: boolean;
  chain_intact: boolean;
  overall_verified: boolean;
  detail: string;
}
