/**
 * Typed client for the Phase 2 scanning backend. The backend URL is never hardcoded — it comes
 * from NEXT_PUBLIC_API_URL, which is unset in any environment where the backend hasn't been
 * deployed yet (every call below fails fast and clearly in that case, rather than hanging).
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

export type ScanStatusValue = "queued" | "running" | "completed" | "failed";

export interface ScanErrorBody {
  code: string;
  message: string;
}

export interface StartScanResponse {
  scan_id: string;
  status: ScanStatusValue;
}

export interface ScanStatusResponse {
  scan_id: string;
  status: ScanStatusValue;
  progress: number;
  current_stage: string;
  error: ScanErrorBody | null;
}

export class ScanApiError extends Error {
  code: string;
  constructor(code: string, message: string) {
    super(message);
    this.code = code;
    this.name = "ScanApiError";
  }
}

function requireBaseUrl(): string {
  if (!API_BASE_URL) {
    throw new ScanApiError("backend_not_configured", "The scanning backend isn't configured for this environment.");
  }
  return API_BASE_URL.replace(/\/$/, "");
}

async function parseErrorBody(res: Response): Promise<ScanErrorBody> {
  try {
    const body = await res.json();
    const detail = body?.detail;
    if (detail?.code && detail?.message) return detail as ScanErrorBody;
    return { code: "unknown_error", message: typeof detail === "string" ? detail : `Request failed (${res.status}).` };
  } catch {
    return { code: "unknown_error", message: `Request failed (${res.status}).` };
  }
}

export async function startScan(url: string): Promise<StartScanResponse> {
  const base = requireBaseUrl();
  let res: Response;
  try {
    res = await fetch(`${base}/api/scans`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
  } catch {
    throw new ScanApiError("backend_unreachable", "Could not reach the scanning backend. Is it running?");
  }
  if (!res.ok) {
    const err = await parseErrorBody(res);
    throw new ScanApiError(err.code, err.message);
  }
  return res.json();
}

export async function getScanStatus(scanId: string): Promise<ScanStatusResponse> {
  const base = requireBaseUrl();
  let res: Response;
  try {
    res = await fetch(`${base}/api/scans/${scanId}/status`, { cache: "no-store" });
  } catch {
    throw new ScanApiError("backend_unreachable", "Lost contact with the scanning backend.");
  }
  if (!res.ok) {
    const err = await parseErrorBody(res);
    throw new ScanApiError(err.code, err.message);
  }
  return res.json();
}

export function isBackendConfigured(): boolean {
  return Boolean(API_BASE_URL);
}

// Loosely typed on purpose — this mirrors the backend's raw, exploratory output (Phase 2:
// real data collection only, no scoring engine yet). Fields are read defensively wherever
// this is displayed rather than assumed present.
export interface ScanResultsPayload {
  scan_id: string;
  status: ScanStatusValue;
  results: Record<string, unknown> | null;
  error: ScanErrorBody | null;
}

export async function getScanResults(scanId: string): Promise<ScanResultsPayload> {
  const base = requireBaseUrl();
  let res: Response;
  try {
    res = await fetch(`${base}/api/scans/${scanId}/results`, { cache: "no-store" });
  } catch {
    throw new ScanApiError("backend_unreachable", "Could not reach the scanning backend.");
  }
  if (!res.ok && res.status !== 409) {
    const err = await parseErrorBody(res);
    throw new ScanApiError(err.code, err.message);
  }
  return res.json();
}

export function screenshotSrc(url: string | null | undefined): string | null {
  if (!url || !API_BASE_URL) return null;
  return `${API_BASE_URL.replace(/\/$/, "")}${url}`;
}
