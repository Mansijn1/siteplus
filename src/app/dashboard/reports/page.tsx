"use client";

import { EVALUATION_CATEGORIES } from "@/lib/categories";
import { getGradeInfo } from "@/lib/scoring";
import { useEvaluationData } from "@/components/dashboard/evaluation-data-provider";
import { ScoreGauge } from "@/components/dashboard/score-gauge";
import { GradeChip } from "@/components/dashboard/grade-chip";
import { SeverityBadge } from "@/components/dashboard/severity-badge";
import { SEVERITY_ORDER, SEVERITY_LABEL } from "@/data/demo-results";

export default function ReportsPage() {
  const { data } = useEvaluationData();
  const grade = getGradeInfo(data.overallScore);
  const allIssues = data.getAllIssues();
  const allRecommendations = data.getAllRecommendationsRanked();
  const issuesBySeverity = SEVERITY_ORDER.map((severity) => ({
    severity,
    issues: allIssues.filter((i) => i.severity === severity),
  }));

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
