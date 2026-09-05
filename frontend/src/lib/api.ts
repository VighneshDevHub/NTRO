import type { OperationRecord, VerificationResult } from "./types";
import { getToken } from "./auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class NotFoundError extends Error {}
export class UnauthorizedError extends Error {}

async function fetchJson<T>(path: string, requireAuth = false): Promise<T> {
  const headers: HeadersInit = {};
  if (requireAuth) {
    const token = getToken();
    if (!token) throw new UnauthorizedError("Not logged in");
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store", headers });
  if (res.status === 404) throw new NotFoundError(`Not found: ${path}`);
  if (res.status === 401) throw new UnauthorizedError("Session expired, please sign in again");
  if (!res.ok) throw new Error(`Request to ${path} failed with status ${res.status}`);
  return res.json() as Promise<T>;
}

export async function getOperation(certificateId: string): Promise<OperationRecord> {
  return fetchJson<OperationRecord>(`/api/v1/operations/${certificateId}`);
}

export async function verifyOperation(certificateId: string): Promise<VerificationResult> {
  return fetchJson<VerificationResult>(`/api/v1/verify/${certificateId}`);
}

export async function listOperations(): Promise<OperationRecord[]> {
  return fetchJson<OperationRecord[]>(`/api/v1/operations`, true);
}

export function getOperationPdfUrl(certificateId: string): string {
  return `${API_BASE_URL}/api/v1/operations/${certificateId}/pdf`;
}
