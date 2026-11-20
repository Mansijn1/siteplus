"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { getDemoDataSource, adaptEvaluation, type EvaluationDataSource } from "@/lib/evaluation-data";
import { startEvaluation, getEvaluation, isEvaluationBackendConfigured, EvaluationApiError } from "@/lib/evaluation-api";

const SCAN_ID_KEY = "webrate:lastScanId";
const EVALUATION_ID_KEY = "webrate:lastEvaluationId";

type Phase = "demo" | "loading" | "real" | "evaluation-error";

interface ContextValue {
  data: EvaluationDataSource;
  phase: Phase;
  errorMessage: string | null;
}

const EvaluationDataContext = createContext<ContextValue | null>(null);

export function EvaluationDataProvider({ children }: { children: React.ReactNode }) {
  const [phase, setPhase] = useState<Phase>("demo");
  const [data, setData] = useState<EvaluationDataSource>(() => getDemoDataSource());
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Resolves the real evaluation (if any) once on mount. A missing scan_id/backend leaves the
  // demo dataset in place untouched — this is the same fallback contract as the scanning page.
  useEffect(() => {
    if (!isEvaluationBackendConfigured()) return;
    const scanId = sessionStorage.getItem(SCAN_ID_KEY);
    if (!scanId) return;

    let cancelled = false;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- capability/session check, not derivable during render
    setPhase("loading");

    async function resolve() {
      try {
        const existingEvaluationId = sessionStorage.getItem(EVALUATION_ID_KEY);
        const evaluation = existingEvaluationId
          ? await getEvaluation(existingEvaluationId)
          : await startEvaluation(scanId!);
        if (cancelled) return;
        if (!existingEvaluationId) sessionStorage.setItem(EVALUATION_ID_KEY, evaluation.evaluation_id);

        if (evaluation.status === "failed") {
          setErrorMessage(evaluation.error?.message ?? "The evaluation failed for an unknown reason.");
          setPhase("evaluation-error");
          return;
        }
        setData(adaptEvaluation(evaluation));
        setPhase("real");
      } catch (err) {
        if (cancelled) return;
        setErrorMessage(err instanceof EvaluationApiError ? err.message : "Could not load the real evaluation.");
        setPhase("evaluation-error");
      }
    }

    resolve();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <EvaluationDataContext.Provider value={{ data, phase, errorMessage }}>{children}</EvaluationDataContext.Provider>
  );
}

export function useEvaluationData(): ContextValue {
  const ctx = useContext(EvaluationDataContext);
  if (!ctx) {
    throw new Error("useEvaluationData must be used within an EvaluationDataProvider");
  }
  return ctx;
}
