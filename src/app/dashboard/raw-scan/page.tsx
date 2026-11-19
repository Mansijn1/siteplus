"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { ArrowLeft, Loader2, ShieldAlert } from "lucide-react";
import { getScanResults, screenshotSrc, ScanApiError, type ScanResultsPayload } from "@/lib/scan-api";

type ViewState =
  | { kind: "loading" }
  | { kind: "no-scan" }
  | { kind: "error"; message: string }
  | { kind: "ready"; payload: ScanResultsPayload };

// The raw backend payload is intentionally loosely typed (see ScanResultsPayload) — this is an
// exploratory Phase 2 view of whatever shape the scanner returns, read defensively throughout.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyRecord = Record<string, any>;

export default function RawScanPage() {
  const [state, setState] = useState<ViewState>({ kind: "loading" });

  useEffect(() => {
    const scanId = sessionStorage.getItem("webrate:lastScanId");
    if (!scanId) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- reads client-only sessionStorage once on mount
      setState({ kind: "no-scan" });
      return;
    }
    getScanResults(scanId)
      .then((payload) => setState({ kind: "ready", payload }))
      .catch((err) =>
        setState({ kind: "error", message: err instanceof ScanApiError ? err.message : "Could not load scan results." }),
      );
  }, []);

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-4 py-8 sm:px-6 lg:py-10">
      <div>
        <Link href="/dashboard" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="size-3.5" />
          Back to Overview
        </Link>
        <h1 className="mt-3 font-display text-2xl font-semibold tracking-[-0.01em]">Raw Scan Data</h1>
        <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
          Real, live data collected by an actual browser scan — screenshots, response details, and technical
          extraction. This is separate from the 12-category evaluation above, which is still fixed demo data;
          turning this raw data into real category scores is a future phase.
        </p>
      </div>

      {state.kind === "loading" && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          Loading scan results…
        </div>
      )}

      {state.kind === "no-scan" && (
        <div className="rounded-lg border border-foreground/12 bg-popover p-8 text-center">
          <ShieldAlert className="mx-auto size-6 text-muted-foreground" />
          <p className="mt-3 text-sm text-muted-foreground">
            No real scan has been run yet in this session.{" "}
            <Link href="/" className="font-medium text-flag hover:text-flag/80">
              Analyze a website
            </Link>{" "}
            to see real scan data here.
          </p>
        </div>
      )}

      {state.kind === "error" && (
        <div className="rounded-lg border border-critical/30 bg-critical/5 p-6 text-sm text-critical">{state.message}</div>
      )}

      {state.kind === "ready" && <ScanResultsView payload={state.payload} />}
    </div>
  );
}

function ScanResultsView({ payload }: { payload: ScanResultsPayload }) {
  if (payload.status === "failed") {
    return (
      <div className="rounded-lg border border-critical/30 bg-critical/5 p-6">
        <p className="text-sm font-medium text-critical">Scan failed</p>
        <p className="mt-1 text-sm text-critical/90">{payload.error?.message}</p>
      </div>
    );
  }

  const r = payload.results as AnyRecord | null;
  if (!r) {
    return <p className="text-sm text-muted-foreground">No results available yet — try again shortly.</p>;
  }

  const screenshots = r.screenshots ?? {};
  const lighthouse = r.lighthouse ?? {};
  const extracted = r.extracted ?? {};

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2">
        {["desktop", "mobile"].map((variant) => {
          const shot = screenshots[variant];
          const src = screenshotSrc(shot?.url);
          return (
            <div key={variant} className="overflow-hidden rounded-lg border border-foreground/12 bg-popover">
              <p className="border-b border-border px-4 py-2 font-mono text-[11px] font-medium uppercase tracking-[0.08em] text-muted-foreground">
                {variant} screenshot
              </p>
              {shot?.available && src ? (
                <Image src={src} alt={`${variant} screenshot`} width={shot.width ?? 1440} height={shot.height ?? 900} className="w-full" unoptimized />
              ) : (
                <p className="p-4 text-sm text-muted-foreground">Unavailable: {shot?.reason ?? "unknown"}</p>
              )}
            </div>
          );
        })}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {["desktop", "mobile"].map((variant) => {
          const lh = lighthouse[variant];
          return (
            <div key={variant} className="rounded-lg border border-foreground/12 bg-popover p-5">
              <p className="font-mono text-[11px] font-medium uppercase tracking-[0.08em] text-muted-foreground">
                Lighthouse · {variant}
              </p>
              {lh?.available ? (
                <div className="mt-3 grid grid-cols-2 gap-3">
                  {Object.entries(lh.scores ?? {}).map(([key, metricValue]) => {
                    const metric = metricValue as AnyRecord;
                    return (
                    <div key={key}>
                      <p className="font-mono text-2xl font-semibold tabular-nums">
                        {metric.available ? metric.value : "—"}
                      </p>
                      <p className="text-xs capitalize text-muted-foreground">{key.replace("_", " ")}</p>
                    </div>
                    );
                  })}
                </div>
              ) : (
                <p className="mt-2 text-sm text-muted-foreground">Unavailable: {lh?.reason ?? "unknown"}</p>
              )}
            </div>
          );
        })}
      </div>

      <div className="rounded-lg border border-foreground/12 bg-popover p-5">
        <p className="font-mono text-[11px] font-medium uppercase tracking-[0.08em] text-muted-foreground">
          Extracted page info
        </p>
        <dl className="mt-3 grid gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
          <Row label="Title" value={extracted?.basic?.title} />
          <Row label="Final URL" value={extracted?.basic?.final_url} />
          <Row label="Meta description" value={extracted?.basic?.meta_description ?? "— none —"} />
          <Row label="Language" value={extracted?.basic?.language} />
          <Row label="Word count" value={extracted?.content?.word_count} />
          <Row label="H1 count" value={extracted?.seo?.heading_counts?.h1} />
          <Row label="Images (missing alt)" value={`${extracted?.seo?.images_total ?? 0} (${extracted?.seo?.images_missing_alt ?? 0})`} />
          <Row label="Internal / external links" value={`${extracted?.seo?.internal_links ?? 0} / ${extracted?.seo?.external_links ?? 0}`} />
          <Row label="HTTPS" value={extracted?.technical?.https ? "Yes" : "No"} />
          <Row label="Status code" value={extracted?.technical?.status_code} />
          <Row label="Redirected" value={extracted?.technical?.was_redirected ? `Yes (${extracted?.technical?.redirect_count})` : "No"} />
          <Row label="Failed requests" value={extracted?.technical?.failed_requests?.length ?? 0} />
        </dl>
      </div>

      {Array.isArray(r.console_messages) && r.console_messages.length > 0 && (
        <div className="rounded-lg border border-foreground/12 bg-popover p-5">
          <p className="font-mono text-[11px] font-medium uppercase tracking-[0.08em] text-muted-foreground">
            Console messages ({r.console_messages.length})
          </p>
          <ul className="mt-3 space-y-1.5">
            {r.console_messages.slice(0, 10).map((m: AnyRecord, i: number) => (
              <li key={i} className="font-mono text-xs text-muted-foreground">
                <span className="text-critical">[{m.type}]</span> {m.text}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value: unknown }) {
  return (
    <>
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="truncate font-medium text-foreground/90">{String(value ?? "—")}</dd>
    </>
  );
}
