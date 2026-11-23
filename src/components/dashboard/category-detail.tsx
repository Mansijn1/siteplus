"use client";

import { CheckCircle2, CircleCheck } from "lucide-react";
import type { CategoryId } from "@/lib/categories";
import { getCategoryById } from "@/lib/categories";
import { ScoreGauge } from "./score-gauge";
import { SeverityBadge } from "./severity-badge";
import { getGradeInfo } from "@/lib/scoring";
import { useEvaluationData } from "./evaluation-data-provider";

export function CategoryDetail({ categoryId }: { categoryId: CategoryId }) {
  const { data } = useEvaluationData();
  const category = getCategoryById(categoryId);
  const score = data.scores[categoryId] ?? 0;
  const analysis = data.getCategoryAnalysis(categoryId);
  const grade = getGradeInfo(score);
  const Icon = category.icon;

  return (
    <div className="space-y-8">
      {/* A. Category overview */}
      <div className="rounded-lg border border-foreground/12 bg-popover p-6 sm:p-7">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center">
          <ScoreGauge score={score} gradeLabel={grade.label} tag={grade.tag} size={132} />
          <div className="min-w-0">
            <div className="flex items-center gap-2.5 text-muted-foreground">
              <Icon className="size-[18px]" strokeWidth={1.75} />
              <span className="font-mono text-xs uppercase tracking-[0.1em]">
                Weight {category.weight}% of overall score
              </span>
            </div>
            <h2 className="mt-1.5 font-display text-2xl font-semibold tracking-[-0.01em]">{category.name}</h2>
            <p className="mt-2 max-w-xl text-[15px] leading-relaxed text-foreground/85">{analysis.summary}</p>
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* B. What was evaluated */}
        <section>
          <h3 className="font-mono text-xs font-medium uppercase tracking-[0.12em] text-muted-foreground">
            What Was Evaluated
          </h3>
          <ul className="mt-3 space-y-2.5">
            {analysis.whatWasEvaluated.map((item) => (
              <li key={item} className="flex items-start gap-2.5 text-sm text-foreground/85">
                <span className="mt-2 size-1 shrink-0 rounded-full bg-muted-foreground" />
                {item}
              </li>
            ))}
          </ul>
        </section>

        {/* C. Positive observations */}
        <section>
          <h3 className="font-mono text-xs font-medium uppercase tracking-[0.12em] text-muted-foreground">
            Positive Observations
          </h3>
          <ul className="mt-3 space-y-2.5">
            {analysis.positives.map((item) => (
              <li key={item} className="flex items-start gap-2.5 text-sm text-foreground/85">
                <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-pass" strokeWidth={1.75} />
                {item}
              </li>
            ))}
          </ul>
        </section>
      </div>

      {/* D. Issues detected */}
      <section>
        <h3 className="font-mono text-xs font-medium uppercase tracking-[0.12em] text-muted-foreground">
          Issues Detected ({analysis.issues.length})
        </h3>
        {analysis.issues.length === 0 ? (
          <div className="mt-3 flex items-center gap-2.5 rounded-lg border border-border bg-popover px-5 py-6 text-sm text-muted-foreground">
            <CircleCheck className="size-4 text-pass" />
            No issues detected in this category.
          </div>
        ) : (
          <div className="mt-3 divide-y divide-border rounded-lg border border-foreground/12 bg-popover">
            {analysis.issues.map((issue) => (
              <div key={issue.issueId ?? issue.title} className="p-5">
                <div className="flex flex-wrap items-center gap-2.5">
                  <SeverityBadge severity={issue.severity} />
                  {issue.priority && (
                    <span className="rounded-sm bg-secondary px-2 py-0.5 font-mono text-[10px] font-medium uppercase tracking-[0.08em] text-muted-foreground">
                      {issue.priority}
                    </span>
                  )}
                  {issue.confidenceLevel && (
                    <span
                      className={`rounded-sm px-2 py-0.5 font-mono text-[10px] font-medium uppercase tracking-[0.08em] ${
                        issue.verificationStatus === "needs_review"
                          ? "bg-flag/10 text-flag"
                          : "bg-pass/10 text-pass"
                      }`}
                      title={`Confidence: ${Math.round((issue.confidence ?? 0) * 100)}% (${issue.evidenceSource ?? "unknown source"})`}
                    >
                      {issue.confidenceLevel.replace("_", " ")} confidence
                    </span>
                  )}
                  <h4 className="text-[15px] font-medium text-foreground/90">{issue.title}</h4>
                </div>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{issue.explanation}</p>
                <p className="mt-2 text-sm leading-relaxed text-foreground/75">
                  <span className="font-medium text-foreground/85">Impact — </span>
                  {issue.impact}
                </p>
                {issue.evidenceDetail && (
                  <details className="mt-2.5">
                    <summary className="cursor-pointer text-xs font-medium text-muted-foreground hover:text-foreground">
                      View evidence
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
                    </dl>
                  </details>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* E. Recommendations */}
      <section>
        <h3 className="font-mono text-xs font-medium uppercase tracking-[0.12em] text-muted-foreground">
          Recommendations ({analysis.recommendations.length})
        </h3>
        <div className="mt-3 divide-y divide-border rounded-lg border border-foreground/12 bg-popover">
          {analysis.recommendations.map((rec) => (
            <div key={rec.issueId ?? rec.title} className="p-5">
              <div className="flex flex-wrap items-center gap-2.5">
                <h4 className="text-[15px] font-medium text-foreground/90">{rec.title}</h4>
                {rec.priority && (
                  <span className="rounded-sm bg-secondary px-2 py-0.5 font-mono text-[10px] font-medium uppercase tracking-[0.08em] text-muted-foreground">
                    {rec.priority}
                  </span>
                )}
                {rec.estimatedEffort && (
                  <span className="font-mono text-[10px] uppercase tracking-[0.08em] text-muted-foreground">
                    {rec.estimatedEffort} effort
                  </span>
                )}
                {rec.bucket && (
                  <span className="rounded-sm bg-flag/10 px-2 py-0.5 font-mono text-[10px] font-medium uppercase tracking-[0.08em] text-flag">
                    {rec.bucket.replace("_", " ")}
                  </span>
                )}
              </div>
              <dl className="mt-3 space-y-2 text-sm leading-relaxed">
                {rec.rootCause && (
                  <div>
                    <dt className="inline font-medium text-foreground/85">Root cause — </dt>
                    <dd className="inline text-muted-foreground">{rec.rootCause}</dd>
                  </div>
                )}
                <div>
                  <dt className="inline font-medium text-foreground/85">Why it matters — </dt>
                  <dd className="inline text-muted-foreground">{rec.why}</dd>
                </div>
                <div>
                  <dt className="inline font-medium text-foreground/85">How to improve — </dt>
                  <dd className="inline text-muted-foreground">{rec.how}</dd>
                </div>
                <div>
                  <dt className="inline font-medium text-foreground/85">Expected impact — </dt>
                  <dd className="inline text-muted-foreground">{rec.expectedImpact}</dd>
                </div>
                {rec.documentationUrl && (
                  <div>
                    <dt className="inline font-medium text-foreground/85">Reference — </dt>
                    <dd className="inline">
                      <a href={rec.documentationUrl} target="_blank" rel="noreferrer" className="text-flag underline underline-offset-4 hover:text-flag/80">
                        {rec.documentationUrl}
                      </a>
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
