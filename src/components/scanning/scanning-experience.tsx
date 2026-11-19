"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { ShieldAlert, WifiOff } from "lucide-react";
import Link from "next/link";
import { Wordmark } from "@/components/shared/brand-mark";
import { ScanStageList } from "./scan-stage-list";
import { EVALUATION_CATEGORIES } from "@/lib/categories";
import { validateAndNormalizeUrl } from "@/lib/validation";
import { storeSubmittedUrl, readSubmittedUrl } from "@/lib/site-url-storage";
import { getScanStatus, isBackendConfigured, startScan, ScanApiError } from "@/lib/scan-api";

const STAGE_DURATION_MS = 450;
const FINISH_PAUSE_MS = 900;
const POLL_INTERVAL_MS = 1200;
const TOTAL_STAGES = EVALUATION_CATEGORIES.length;

type Phase = "resolving" | "simulated" | "real" | "no-url" | "backend-error";

export function ScanningExperience() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [resolvedUrl, setResolvedUrl] = useState<string | null>(null);
  const [phase, setPhase] = useState<Phase>("resolving");
  const [activeIndex, setActiveIndex] = useState(0);
  const [currentStageText, setCurrentStageText] = useState<string | null>(null);
  const [backendError, setBackendError] = useState<string | null>(null);
  const navigatedRef = useRef(false);

  // Resolve and re-validate the URL once on mount. Never trust the query
  // string alone — an arbitrary or missing value never reaches the dashboard.
  // Intentionally sets state directly in the effect: this reads client-only
  // APIs (searchParams, sessionStorage) once on mount, not in response to a
  // prop/state change that could be derived during render instead.
  useEffect(() => {
    const fromQuery = searchParams.get("url");
    const candidate = fromQuery ?? readSubmittedUrl() ?? "";
    const result = validateAndNormalizeUrl(candidate);
    if (!result.ok) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- resolves client-only query/sessionStorage once on mount
      setPhase("no-url");
      return;
    }
    storeSubmittedUrl(result.normalizedUrl);
    setResolvedUrl(result.normalizedUrl);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Simulated local progress — used when no backend is configured for this environment, so the
  // existing demo experience keeps working exactly as before.
  useEffect(() => {
    if (!resolvedUrl || phase !== "simulated") return;
    const interval = setInterval(() => {
      setActiveIndex((prev) => (prev >= TOTAL_STAGES ? prev : prev + 1));
    }, STAGE_DURATION_MS);
    return () => clearInterval(interval);
  }, [resolvedUrl, phase]);

  // Real backend scan — start it, then poll status until it completes or fails.
  useEffect(() => {
    if (!resolvedUrl) return;

    if (!isBackendConfigured()) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- capability check, not derivable during render
      setPhase("simulated");
      return;
    }

    let cancelled = false;
    let pollTimer: ReturnType<typeof setTimeout> | undefined;

    async function run() {
      try {
        setPhase("real");
        const { scan_id } = await startScan(resolvedUrl!);
        if (cancelled) return;
        sessionStorage.setItem("webrate:lastScanId", scan_id);

        const poll = async () => {
          if (cancelled) return;
          try {
            const status = await getScanStatus(scan_id);
            if (cancelled) return;
            setActiveIndex(Math.round((status.progress / 100) * TOTAL_STAGES));
            setCurrentStageText(status.current_stage);

            if (status.status === "failed") {
              setBackendError(status.error?.message ?? "The scan failed for an unknown reason.");
              setPhase("backend-error");
              return;
            }
            if (status.status === "completed") {
              setActiveIndex(TOTAL_STAGES);
              return;
            }
            pollTimer = setTimeout(poll, POLL_INTERVAL_MS);
          } catch (err) {
            if (cancelled) return;
            setBackendError(err instanceof ScanApiError ? err.message : "Lost contact with the scanning backend.");
            setPhase("backend-error");
          }
        };

        await poll();
      } catch (err) {
        if (cancelled) return;
        setBackendError(err instanceof ScanApiError ? err.message : "Could not start the scan.");
        setPhase("backend-error");
      }
    }

    run();
    return () => {
      cancelled = true;
      if (pollTimer) clearTimeout(pollTimer);
    };
  }, [resolvedUrl]);

  useEffect(() => {
    if (activeIndex < TOTAL_STAGES || navigatedRef.current) return;
    if (phase !== "real" && phase !== "simulated") return;
    navigatedRef.current = true;
    const timeout = setTimeout(() => {
      router.replace("/dashboard");
    }, FINISH_PAUSE_MS);
    return () => clearTimeout(timeout);
  }, [activeIndex, phase, router]);

  if (phase === "no-url") {
    return (
      <StatusScreen
        icon={<ShieldAlert className="size-7 text-critical" strokeWidth={1.75} />}
        title="No Website URL Provided"
        description="Go back and enter a website URL to start an evaluation."
      />
    );
  }

  if (phase === "backend-error") {
    return (
      <StatusScreen
        icon={<WifiOff className="size-7 text-critical" strokeWidth={1.75} />}
        title="Scan Could Not Complete"
        description={backendError ?? "Something went wrong while scanning this website."}
        showRetry
      />
    );
  }

  if (phase === "resolving" || !resolvedUrl) {
    return <div className="min-h-screen bg-report-ruling" />;
  }

  const completed = Math.min(activeIndex, TOTAL_STAGES);
  const remaining = TOTAL_STAGES - completed;
  const progressPercent = Math.round((completed / TOTAL_STAGES) * 100);
  const isDone = completed >= TOTAL_STAGES;
  const isReal = phase === "real";

  return (
    <div className="flex min-h-screen flex-col items-center bg-report-ruling px-6 py-16">
      <Link href="/" className="mb-10">
        <Wordmark />
      </Link>

      <div className="w-full max-w-md">
        <div className="text-center">
          <span className="rounded-sm bg-secondary px-2.5 py-1 font-mono text-[10px] font-medium uppercase tracking-[0.08em] text-muted-foreground">
            {isReal ? "Live Technical Scan · Demo Category Scores" : "Simulated Evaluation · Demo Results"}
          </span>
          <h1 className="mt-4 font-display text-2xl font-semibold tracking-[-0.01em]">
            {isDone ? "Inspection Complete" : "Inspecting Your Website"}
          </h1>
          <p className="mt-1.5 break-all font-mono text-sm text-muted-foreground">{resolvedUrl}</p>
          {isReal && currentStageText && !isDone && (
            <p className="mt-2 text-xs text-muted-foreground">{currentStageText}</p>
          )}
        </div>

        <div className="mt-8">
          <div className="flex items-center justify-between font-mono text-xs text-muted-foreground">
            <span>
              {completed} of {TOTAL_STAGES} checks complete
            </span>
            <span>{remaining} remaining</span>
          </div>
          <div className="mt-2 h-[6px] w-full overflow-hidden rounded-sm bg-border">
            <motion.div
              className="h-full rounded-sm bg-flag"
              animate={{ width: `${progressPercent}%` }}
              transition={{ duration: 0.35, ease: "easeOut" }}
            />
          </div>
          <p className="mt-1.5 text-right font-mono text-xs text-muted-foreground">{progressPercent}%</p>
        </div>

        <div className="mt-8 rounded-lg border border-foreground/12 bg-popover p-6">
          <ScanStageList activeIndex={activeIndex} />
        </div>

        <p className="mt-6 text-center text-xs leading-relaxed text-muted-foreground">
          {isReal
            ? "A real browser scan of this site just ran — screenshots, console errors, and technical data were collected live. The 12-category breakdown next is still fixed demo/sample data; real scoring is a future phase."
            : "This is a simulated progress sequence — no live browser scan is being performed. Results shown next are fixed sample data for demonstration."}
        </p>
      </div>
    </div>
  );
}

function StatusScreen({
  icon,
  title,
  description,
  showRetry = false,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  showRetry?: boolean;
}) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-report-ruling px-6 text-center">
      <Link href="/" className="mb-10">
        <Wordmark />
      </Link>
      {icon}
      <h1 className="mt-5 font-display text-2xl font-semibold tracking-[-0.01em]">{title}</h1>
      <p className="mt-2 max-w-sm text-sm leading-relaxed text-muted-foreground">{description}</p>
      <div className="mt-6 flex items-center gap-4">
        {showRetry && (
          <Link
            href="/"
            className="text-sm font-medium text-flag underline underline-offset-4 hover:text-flag/80"
          >
            Try a different URL
          </Link>
        )}
        {!showRetry && (
          <Link
            href="/"
            className="text-sm font-medium text-flag underline underline-offset-4 hover:text-flag/80"
          >
            Back to WebRate AI
          </Link>
        )}
      </div>
    </div>
  );
}
