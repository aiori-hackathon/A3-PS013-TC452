export type Investigation = {
  id: string;
  name: string;
  description: string;
  created_at: string;
};
export type Evidence = {
  id: string;
  filename: string;
  source: string;
  sha256: string;
  size: number;
  imported_at: string;
  total_records: number;
  parsed_records: number;
  gap_records: number;
  timezone: string;
  year: number | null;
  offset_seconds: number;
  uncertainty_seconds: number;
  correction_reason: string;
};
export type EventRecord = {
  id: string;
  evidence_id: string;
  filename: string;
  source: string;
  line_number: number;
  byte_start: number;
  byte_end: number;
  raw_line: string;
  error: string | null;
  original_timestamp: string;
  utc_timestamp: string;
  corrected_timestamp: string;
  interval_start: string;
  interval_end: string;
  kind: string;
  message: string;
  host: string;
  service: string;
  ip: string;
  status: string;
  timezone_basis: string;
  anchor_id: string;
  offset_seconds: number;
  uncertainty_seconds: number;
  parser_version: string;
  integrity?: Verification;
};
export type Verification = {
  evidence_id: string;
  filename: string;
  expected_sha256: string;
  actual_sha256: string | null;
  status: string;
  checked_at: string;
};
export type Finding = { type: string; message: string; record_ids: string[] };
export type Audit = {
  id: number;
  action: string;
  occurred_at: string;
  details: string;
};

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch("/api" + path, init);
  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: response.statusText }));
    throw new Error(
      typeof error.detail === "string"
        ? error.detail
        : JSON.stringify(error.detail),
    );
  }
  return response.json();
}
export function jsonBody(value: unknown) {
  return {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(value),
  };
}
