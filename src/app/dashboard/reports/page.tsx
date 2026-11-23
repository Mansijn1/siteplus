"use client";

import { useEffect, useRef, useState } from "react";
import { Download } from "lucide-react";
import { EVALUATION_CATEGORIES } from "@/lib/categories";
import { getGradeInfo } from "@/lib/scoring";
import { useEvaluationData } from "@/components/dashboard/evaluation-data-provider";
import { ScoreGauge } from "@/components/dashboard/score-gauge";
import { GradeChip } from "@/components/dashboard/grade-chip";
import { SeverityBadge } from "@/components/dashboard/severity-badge";
import { Button } from "@/components/ui/button";
import { SEVERITY_ORDER, SEVERITY_LABEL } from "@/data/demo-results";
import { getLatestBenchmark, type BenchmarkReport, type ConfidenceLevel } from "@/lib/evaluation-api";

const CONFIDENCE_LEVELS: ConfidenceLevel[] = ["very_high", "high", "medium", "low"];

function useBenchmarkReport() {
  const [report, setReport] = useState<BenchmarkReport | null | "loading">("loading");
  useEffect(() => {
    let cancelled = false;
    getLatestBenchmark()
      .then((r) => {
        if (!cancelled) setReport(r);
      })
      .catch(() => {
        if (!cancelled) setReport(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);
  return report;
}

/** Browsers hide a closed <details>'s content at the UA level — CSS alone can't reliably
 * reveal it in print across browsers, so every evidence block is force-opened right before
 * printing (and restored to however the reader had it after), via the native print events. */
function usePrintExpandsDetails(containerRef: React.RefObject<HTMLDivElement | null>) {
  useEffect(() => {
    const previouslyOpen = new Set<HTMLDetailsElement>();
    const handleBeforePrint = () => {
      const container = containerRef.current;
      if (!container) return;
      container.querySelectorAll("details").forEach((el) => {
        if (el.open) previouslyOpen.add(el);
        el.open = true;
      });
    };
    const handleAfterPrint = () => {
      const container = containerRef.current;
      if (!container) return;
      container.querySelectorAll("details").forEach((el) => {
        el.open = previouslyOpen.has(el);
      });
      previouslyOpen.clear();
    };
    window.addEventListener("beforeprint", handleBeforePrint);
    window.addEventListener("afterprint", handleAfterPrint);
    return () => {
      window.removeEventListener("beforeprint", handleBeforePrint);
      window.removeEventListener("afterprint", handleAfterPrint);
    };
  }, [containerRef]);
}

export default function ReportsPage() {
  const { data } = useEvaluationData();
  const benchmark = useBenchmarkReport();
  const grade = getGradeInfo(data.overallScore);
  const allIssues = data.getAllIssues();
  const allRecommendations = data.getAllRecommendationsRanked();
  const issuesBySeverity = SEVERITY_ORDER.map((severity) => ({
    severity,
    issues: allIssues.filter((i) => i.severity === severity),
  }));

  const confidenceCounts = CONFIDENCE_LEVELS.map((level) => ({
    level,
    count: allIssues.filter((i) => i.confidenceLevel === level).length,
  }));
  const verifiedCount = allIssues.filter((i) => i.verificationStatus === "verified").length;
  const needsReviewCount = allIssues.filter((i) => i.verificationStatus === "needs_review").length;
  const hasConfidenceData = data.isReal && allIssues.some((i) => i.confidenceLevel);

  const containerRef = useRef<HTMLDivElement>(null);
  usePrintExpandsDetails(containerRef);
  const generatedAt = useGeneratedTimestamp();

  return (
    <div ref={containerRef} className="mx-auto max-w-5xl space-y-8 px-4 py-8 sm:px-6 lg:py-10">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-[-0.01em]">Reports</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            A complete, printable summary of this evaluation — category breakdown, every detected
            issue with its evidence, and every recommendation.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="no-print shrink-0 gap-2"
          onClick={() => window.print()}
        >
          <Download className="size-3.5" />
          Download Report
        </Button>
      </div>

      {/* Report header — only meaningful once printed/exported; invisible in the live dashboard */}
      <div className="hidden border-b border-foreground/20 pb-4 font-mono text-xs text-muted-foreground print:block">
        <p className="text-base font-semibold text-foreground">Website Evaluation Report</p>
        <p className="mt-1">{data.websiteUrl}</p>
        <p>Generated {generatedAt}</p>
      </div>

      {/* Summary */}
      <section className="rounded-lg border border-foreground/12 bg-popover p-6 sm:p-8">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center">
          <ScoreGauge score={data.overallScore} gradeLabel={grade.label} tag={grade.tag} size={120} />
          <div className="min-w-0">
            <p className="font-mono text-sm text-muted-foreground">{data.websiteUrl}</p>
            <p className="mt-2 text-[15px] leading-relaxed text-foreground/85">{data.summary}</p>
            <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 font-mono text-xs text-muted-foreground">
              <span>{allIssues.length} issue(s) found</span>
              <span>{allRecommendations.length} recommendation(s)</span>
              {data.isReal && (
                <span>
                  {data.passedChecks} passed / {data.failedChecks} failed / {data.unavailableChecks} unavailable of{" "}
                  {data.totalChecks} checks
                </span>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Confidence & verification */}
      {hasConfidenceData && (
        <section>
          <h2 className="font-display text-lg font-semibold tracking-[-0.01em]">Confidence & Verification</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            How strongly the collected evidence supports each finding — not severity, and not the website score.
          </p>
          <div className="mt-3 grid grid-cols-1 gap-px overflow-hidden rounded-lg border border-foreground/12 bg-border sm:grid-cols-2 lg:grid-cols-6">
            {confidenceCounts.map(({ level, count }) => (
              <div key={level} className="bg-popover p-4">
                <p className="font-mono text-[10px] font-medium uppercase tracking-[0.08em] text-muted-foreground">
                  {level.replace("_", " ")}
                </p>
                <p className="mt-1.5 text-lg font-semibold tabular-nums">{count}</p>
              </div>
            ))}
            <div className="bg-popover p-4">
              <p className="font-mono text-[10px] font-medium uppercase tracking-[0.08em] text-pass">verified</p>
              <p className="mt-1.5 text-lg font-semibold tabular-nums">{verifiedCount}</p>
            </div>
            <div className="bg-popover p-4">
              <p className="font-mono text-[10px] font-medium uppercase tracking-[0.08em] text-flag">needs review</p>
              <p className="mt-1.5 text-lg font-semibold tabular-nums">{needsReviewCount}</p>
            </div>
          </div>
        </section>
      )}

      {/* Benchmark accuracy — a separate, system-wide measurement, never a per-scan number */}
      {benchmark !== "loading" && benchmark !== null && (
        <section className="no-print">
          <h2 className="font-display text-lg font-semibold tracking-[-0.01em]">Accuracy & Coverage (Benchmark)</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Measured once against a fixed set of known-defect test pages — a property of the detection engine
            itself, not of this specific scan. See the note below for exactly what this does and doesn&apos;t cover.
          </p>
          <div className="mt-3 grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-foreground/12 bg-border sm:grid-cols-4">
            <div className="bg-popover p-4">
              <p className="font-mono text-[10px] font-medium uppercase tracking-[0.08em] text-muted-foreground">Precision</p>
              <p className="mt-1.5 text-lg font-semibold tabular-nums">{benchmark.overall.precision ?? "—"}</p>
            </div>
            <div className="bg-popover p-4">
              <p className="font-mono text-[10px] font-medium uppercase tracking-[0.08em] text-muted-foreground">Recall</p>
              <p className="mt-1.5 text-lg font-semibold tabular-nums">{benchmark.overall.recall ?? "—"}</p>
            </div>
            <div className="bg-popover p-4">
              <p className="font-mono text-[10px] font-medium uppercase tracking-[0.08em] text-muted-foreground">F1</p>
              <p className="mt-1.5 text-lg font-semibold tabular-nums">{benchmark.overall.f1 ?? "—"}</p>
            </div>
            <div className="bg-popover p-4">
              <p className="font-mono text-[10px] font-medium uppercase tracking-[0.08em] text-muted-foreground">Coverage</p>
              <p className="mt-1.5 text-lg font-semibold tabular-nums">{benchmark.evaluation_coverage.coverage_percent ?? "—"}%</p>
            </div>
          </div>
          <p className="mt-3 text-xs leading-relaxed text-muted-foreground">{benchmark.scope_note}</p>
        </section>
      )}
      {benchmark === null && (
        <section className="no-print rounded-lg border border-dashed border-foreground/20 p-4 text-xs text-muted-foreground">
          No benchmark has been run yet in this backend environment.
        </section>
      )}

      {/* Category-wise breakdown */}
      <section>
        <h2 className="font-display text-lg font-semibold tracking-[-0.01em]">Category Breakdown</h2>
        <div className="mt-3 divide-y divide-border rounded-lg border border-foreground/12 bg-popover">
          {EVALUATION_CATEGORIES.map((category) => {
            const score = data.scores[category.id];
            const analysis = data.getCategoryAnalysis(category.id);
            const Icon = category.icon;
            return (
              <div key={category.id} className="flex items-center justify-between gap-4 px-5 py-4">
                <span className="flex min-w-0 items-center gap-2.5">
                  <Icon className="size-4 shrink-0 text-muted-foreground" strokeWidth={1.75} />
                  <span className="truncate text-sm text-foreground/85">{category.name}</span>
                  <span className="shrink-0 font-mono text-xs text-muted-foreground">{category.weight}%</span>
                </span>
                <span className="flex shrink-0 items-center gap-3">
                  <span className="font-mono text-xs text-muted-foreground">{analysis.issues.length} issue(s)</span>
                  {score !== undefined ? (
                    <>
                      <span className="font-mono text-sm font-medium tabular-nums">{score}</span>
                      <GradeChip score={score} />
                    </>
                  ) : (
                    <span className="font-mono text-xs uppercase tracking-[0.08em] text-muted-foreground">
                      No evidence
                    </span>
                  )}
                </span>
              </div>
            );
          })}
        </div>
      </section>

      {/* Issue details, grouped by severity, with full evidence */}
      <section>
        <h2 className="font-display text-lg font-semibold tracking-[-0.01em]">Issue Details</h2>
        <div className="mt-3 space-y-6">
          {issuesBySeverity.map(
            ({ severity, issues }) =>
              issues.length > 0 && (
                <div key={severity}>
                  <h3 className="font-mono text-xs font-medium uppercase tracking-[0.12em] text-muted-foreground">
                    {SEVERITY_LABEL[severity]} ({issues.length})
                  </h3>
                  <div className="mt-2 divide-y divide-border rounded-lg border border-foreground/12 bg-popover">
                    {issues.map((issue) => (
                      <div key={`${issue.categoryId}-${issue.issueId ?? issue.title}`} className="p-4">
                        <div className="flex flex-wrap items-center gap-2">
                          <SeverityBadge severity={issue.severity} />
                          <span className="font-mono text-[11px] uppercase tracking-[0.08em] text-muted-foreground">
                            {issue.categoryName}
                          </span>
                          {issue.priority && (
                            <span className="font-mono text-[10px] uppercase tracking-[0.08em] text-muted-foreground">
                              {issue.priority}
                            </span>
                          )}
                          {issue.confidenceLevel && (
                            <span
                              className={`font-mono text-[10px] uppercase tracking-[0.08em] ${
                                issue.verificationStatus === "needs_review" ? "text-flag" : "text-pass"
                              }`}
                            >
                              {issue.confidenceLevel.replace("_", " ")} confidence
                            </span>
                          )}
                        </div>
                        <p className="mt-1.5 text-sm font-medium text-foreground/90">{issue.title}</p>
                        <p className="mt-1 text-sm text-muted-foreground">{issue.explanation}</p>
                        {issue.affectedUrl && (
                          <p className="mt-1 break-all font-mono text-xs text-muted-foreground">{issue.affectedUrl}</p>
                        )}
                        {issue.evidenceDetail && (
                          <details className="mt-2">
                            <summary className="cursor-pointer text-xs font-medium text-muted-foreground hover:text-foreground">
                              Evidence
                            </summary>
                            <dl className="mt-2 space-y-1 rounded-sm bg-secondary/40 p-3 font-mono text-xs text-foreground/80">
                              {issue.evidenceDetail.selector && (
                                <div><dt className="inline text-muted-foreground">selector: </dt><dd className="inline break-all">{issue.evidenceDetail.selector}</dd></div>
                              )}
                              {issue.evidenceDetail.observed_value !== undefined && issue.evidenceDetail.observed_value !== null && (
                                <div><dt className="inline text-muted-foreground">observed: </dt><dd className="inline break-all">{JSON.stringify(issue.evidenceDetail.observed_value)}</dd></div>
                              )}
                              {issue.evidenceDetail.expected_value !== undefined && issue.evidenceDetail.expected_value !== null && (
                                <div><dt className="inline text-muted-foreground">expected: </dt><dd className="inline break-all">{JSON.stringify(issue.evidenceDetail.expected_value)}</dd></div>
                              )}
                              {issue.evidenceSource && (
                                <div><dt className="inline text-muted-foreground">source: </dt><dd className="inline">{issue.evidenceSource}</dd></div>
                              )}
                            </dl>
                          </details>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ),
          )}
          {allIssues.length === 0 && (
            <p className="text-sm text-muted-foreground">No issues detected across any category.</p>
          )}
        </div>
      </section>

      {/* Recommendations */}
      <section>
        <h2 className="font-display text-lg font-semibold tracking-[-0.01em]">Recommendations</h2>
        <div className="mt-3 divide-y divide-border rounded-lg border border-foreground/12 bg-popover">
          {allRecommendations.length === 0 ? (
            <p className="p-5 text-sm text-muted-foreground">No recommendations — every checked item passed.</p>
          ) : (
            allRecommendations.map((rec) => (
              <div key={`${rec.categoryId}-${rec.issueId ?? rec.title}`} className="p-5">
                <div className="flex flex-wrap items-center gap-2">
                  <SeverityBadge severity={rec.topSeverity} />
                  <span className="font-mono text-[11px] uppercase tracking-[0.08em] text-muted-foreground">
                    {rec.categoryName}
                  </span>
                  {rec.estimatedEffort && (
                    <span className="font-mono text-[10px] uppercase tracking-[0.08em] text-muted-foreground">
                      {rec.estimatedEffort} effort
                    </span>
                  )}
                  {rec.bucket && (
                    <span className="font-mono text-[10px] uppercase tracking-[0.08em] text-flag">
                      {rec.bucket.replace("_", " ")}
                    </span>
                  )}
                </div>
                <p className="mt-1.5 text-sm font-medium text-foreground/90">{rec.title}</p>
                {rec.rootCause && (
                  <p className="mt-1 text-sm text-muted-foreground">
                    <span className="font-medium text-foreground/80">Root cause — </span>
                    {rec.rootCause}
                  </p>
                )}
                <p className="mt-1 text-sm text-muted-foreground">
                  <span className="font-medium text-foreground/80">Fix — </span>
                  {rec.how}
                </p>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}

function useGeneratedTimestamp(): string {
  // Resolved client-only (not available during server render) — a static fallback avoids a
  // hydration mismatch, and the real timestamp is only meaningful at the moment of download.
  const [timestamp, setTimestamp] = useState("—");
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- resolves a client-only Date once on mount
    setTimestamp(new Date().toLocaleString());
  }, []);
  return timestamp;
}
