"use client";

import { useEffect, useState } from "react";
import { EVALUATION_CATEGORIES } from "@/lib/categories";
import { getGradeInfo } from "@/lib/scoring";
import { useEvaluationData } from "@/components/dashboard/evaluation-data-provider";
import { ScoreGauge } from "@/components/dashboard/score-gauge";
import { GradeChip } from "@/components/dashboard/grade-chip";
import { SeverityBadge } from "@/components/dashboard/severity-badge";
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

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-4 py-8 sm:px-6 lg:py-10">
      <div>
        <h1 className="font-display text-2xl font-semibold tracking-[-0.01em]">Reports</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          A complete, printable-style summary of this evaluation — category breakdown, every detected issue, and every recommendation.
        </p>
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
        <section>
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
        <section className="rounded-lg border border-dashed border-foreground/20 p-4 text-xs text-muted-foreground">
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

      {/* Issue details, grouped by severity */}
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
                        </div>
                        <p className="mt-1.5 text-sm font-medium text-foreground/90">{issue.title}</p>
                        <p className="mt-1 text-sm text-muted-foreground">{issue.explanation}</p>
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
                </div>
                <p className="mt-1.5 text-sm font-medium text-foreground/90">{rec.title}</p>
                <p className="mt-1 text-sm text-muted-foreground">{rec.how}</p>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
