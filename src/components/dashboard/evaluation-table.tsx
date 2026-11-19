"use client";

import { useState } from "react";
import Link from "next/link";
import { ChevronDown, ArrowRight } from "lucide-react";
import { EVALUATION_CATEGORIES, TOTAL_WEIGHT } from "@/lib/categories";
import { DEMO_SCORES, CATEGORY_ANALYSIS } from "@/data/demo-results";
import { ScoreBar, GradeChip } from "./grade-chip";
import { SeverityBadge } from "./severity-badge";

export function EvaluationTable() {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <div className="overflow-hidden rounded-lg border border-foreground/12 bg-popover">
      <div className="hidden grid-cols-[1fr_80px_200px_72px_24px] gap-4 border-b border-border px-5 py-3 font-mono text-[11px] font-medium uppercase tracking-[0.08em] text-muted-foreground sm:grid">
        <span>Evaluation Category</span>
        <span className="text-right">Weight</span>
        <span>Score</span>
        <span className="text-right">Status</span>
        <span aria-hidden="true" />
      </div>

      <div className="divide-y divide-border">
        {EVALUATION_CATEGORIES.map((category) => {
          const score = DEMO_SCORES[category.id] ?? 0;
          const analysis = CATEGORY_ANALYSIS[category.id];
          const expanded = expandedId === category.id;
          const topIssue = analysis.issues[0];
          const topRecommendation = analysis.recommendations[0];
          const Icon = category.icon;

          return (
            <div key={category.id}>
              <button
                type="button"
                onClick={() => setExpandedId(expanded ? null : category.id)}
                aria-expanded={expanded}
                aria-controls={`category-panel-${category.id}`}
                className="grid w-full grid-cols-[1fr_auto] items-center gap-3 px-5 py-4 text-left transition-colors hover:bg-secondary/40 sm:grid-cols-[1fr_80px_200px_72px_24px] sm:gap-4"
              >
                <span className="flex min-w-0 items-center gap-3">
                  <Icon className="size-[18px] shrink-0 text-muted-foreground" strokeWidth={1.75} />
                  <span className="truncate text-[15px] font-medium text-foreground/90">{category.name}</span>
                </span>

                <span className="font-mono text-sm text-muted-foreground sm:text-right">
                  {category.weight}%
                </span>

                <span className="hidden items-center gap-3 sm:flex">
                  <ScoreBar score={score} className="w-28" />
                  <span className="font-mono text-sm font-medium tabular-nums">{score}</span>
                </span>

                <span className="hidden justify-end sm:flex">
                  <GradeChip score={score} />
                </span>

                <ChevronDown
                  className={`col-start-2 row-start-1 size-4 shrink-0 text-muted-foreground transition-transform sm:col-auto sm:row-auto ${expanded ? "rotate-180" : ""}`}
                />

                <span className="col-span-2 flex items-center gap-3 sm:hidden">
                  <ScoreBar score={score} className="flex-1" />
                  <span className="font-mono text-sm font-medium tabular-nums">{score}</span>
                  <GradeChip score={score} />
                </span>
              </button>

              {expanded && (
                <div id={`category-panel-${category.id}`} className="border-t border-border bg-secondary/20 px-5 py-5">
                  <p className="text-[15px] leading-relaxed text-foreground/85">{analysis.summary}</p>

                  <div className="mt-4 grid gap-4 sm:grid-cols-2">
                    {topIssue && (
                      <div>
                        <p className="font-mono text-[10px] font-medium uppercase tracking-[0.1em] text-muted-foreground">
                          Top Issue
                        </p>
                        <div className="mt-2 flex items-start gap-2">
                          <SeverityBadge severity={topIssue.severity} className="mt-0.5 shrink-0" />
                          <p className="text-sm text-foreground/85">{topIssue.title}</p>
                        </div>
                      </div>
                    )}
                    {topRecommendation && (
                      <div>
                        <p className="font-mono text-[10px] font-medium uppercase tracking-[0.1em] text-muted-foreground">
                          Top Recommendation
                        </p>
                        <p className="mt-2 text-sm text-foreground/85">{topRecommendation.title}</p>
                      </div>
                    )}
                  </div>

                  <Link
                    href={`/dashboard/categories?id=${category.id}`}
                    className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-flag hover:text-flag/80"
                  >
                    View full category analysis
                    <ArrowRight className="size-3.5" />
                  </Link>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="flex items-center justify-between border-t border-border px-5 py-3 font-mono text-xs text-muted-foreground">
        <span>{EVALUATION_CATEGORIES.length} categories</span>
        <span>Total weight: {TOTAL_WEIGHT}%</span>
      </div>
    </div>
  );
}
