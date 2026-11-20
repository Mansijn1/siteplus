import { isBackendConfigured } from "./scan-api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL;

export class EvaluationApiError extends Error {
  constructor(
    message: string,
    public code?: string,
  ) {
    super(message);
    this.name = "EvaluationApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  if (!API_BASE) throw new EvaluationApiError("Backend API is not configured.", "no_backend");
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new EvaluationApiError("Could not reach the evaluation backend.", "network_error");
  }
  if (!res.ok) {
    let detail: { code?: string; message?: string } | null = null;
    try {
      const body = await res.json();
      detail = body?.detail ?? null;
    } catch {
      // response body wasn't JSON — fall through to the generic message below
    }
    throw new EvaluationApiError(detail?.message ?? `Request failed (${res.status})`, detail?.code);
  }
  return res.json() as Promise<T>;
}

// Shapes mirror backend/models/evaluation_models.py exactly — see that file for the
// authoritative field-by-field documentation of what each represents.

export type Severity = "critical" | "high" | "medium" | "low" | "informational";
export type Priority = "P0" | "P1" | "P2" | "P3";
export type Effort = "low" | "medium" | "high";
export type CheckStatus = "passed" | "failed" | "unavailable";

export interface Evidence {
  element?: string | null;
  selector?: string | null;
  observed_value?: unknown;
  expected_value?: unknown;
  extra?: Record<string, unknown>;
}

export interface BackendIssue {
  issue_id: string;
  category: string;
  title: string;
  description: string;
  evidence: Evidence;
  affected_url: string;
  severity: Severity;
  priority: Priority;
  impact: string;
  recommendation: string;
  estimated_effort: Effort;
}

export interface BackendRecommendation {
  issue_id: string;
  category: string;
  title: string;
  what_to_fix: string;
  why_it_matters: string;
  how_to_fix: string[];
  expected_benefit: string;
  priority: Priority;
  estimated_effort: Effort;
  affected_url: string;
}

export interface BackendCheckResult {
  check_id: string;
  label: string;
  status: CheckStatus;
  detail?: string | null;
}

export interface BackendCategoryResult {
  category: string;
  weight: number;
  score: number | null;
  checks: BackendCheckResult[];
  issues: BackendIssue[];
  recommendations: BackendRecommendation[];
  passed_count: number;
  failed_count: number;
  unavailable_count: number;
  summary: string;
}

export interface BackendEvaluationResult {
  evaluation_id: string;
  scan_id: string;
  submitted_url: string;
  status: "running" | "completed" | "failed";
  overall_score: number | null;
  score_coverage_percent: number | null;
  grade: string | null;
  categories: Record<string, BackendCategoryResult>;
  total_checks: number;
  passed_checks: number;
  failed_checks: number;
  unavailable_checks: number;
  error?: { code: string; message: string } | null;
  started_at: string;
  completed_at?: string | null;
}

export function isEvaluationBackendConfigured(): boolean {
  return isBackendConfigured();
}

export async function startEvaluation(scanId: string): Promise<BackendEvaluationResult> {
  return request<BackendEvaluationResult>("/api/evaluate", {
    method: "POST",
    body: JSON.stringify({ scan_id: scanId }),
  });
}

export async function getEvaluation(evaluationId: string): Promise<BackendEvaluationResult> {
  return request<BackendEvaluationResult>(`/api/evaluation/${evaluationId}`);
}
