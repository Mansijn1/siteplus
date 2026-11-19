import { ArrowUpRight } from "lucide-react";
import { EVALUATION_CATEGORIES } from "@/lib/categories";
import { DEMO_AUDIT, getDemoCategoryResult } from "@/lib/demo-audit";
import { getGradeInfo } from "@/lib/scoring";
import { InspectionSeal } from "./inspection-seal";

const FEATURED_IDS = ["performance", "seo"] as const;

export function ProductPreview() {
  const overallGrade = getGradeInfo(DEMO_AUDIT.overallScore);
  const otherCategories = EVALUATION_CATEGORIES.filter(
    (c) => !FEATURED_IDS.includes(c.id as (typeof FEATURED_IDS)[number]),
  );

  return (
    <section id="product" className="border-t border-border py-24">
      <div className="mx-auto max-w-6xl px-6">
        <div className="max-w-2xl">
          <h2 className="font-display text-3xl font-semibold tracking-[-0.02em] sm:text-4xl">
            See the full inspection report.
          </h2>
          <p className="mt-4 text-lg leading-relaxed text-muted-foreground">
            Every evaluation reads like this — one overall score, every
            category accounted for, and recommendations ranked by impact.
          </p>
        </div>

        <div className="mt-12 rounded-lg border border-foreground/12 bg-popover">
          <div className="flex flex-col gap-6 border-b border-border p-6 sm:flex-row sm:items-center sm:justify-between sm:p-8">
            <div className="flex items-center gap-6">
              <InspectionSeal
                score={DEMO_AUDIT.overallScore}
                gradeLabel={overallGrade.label}
                tag={overallGrade.tag}
                size={128}
              />
              <div>
                <p className="font-mono text-xs text-muted-foreground">{DEMO_AUDIT.sampleUrl}</p>
                <p className="mt-1 max-w-md text-[15px] leading-relaxed text-foreground/85">
                  {DEMO_AUDIT.summary}
                </p>
              </div>
            </div>
            <span className="shrink-0 self-start rounded-sm bg-secondary px-2.5 py-1 font-mono text-[10px] font-medium uppercase tracking-[0.1em] text-muted-foreground sm:self-center">
              Sample Preview · Demo Audit Data
            </span>
          </div>

          <div className="grid gap-px bg-border sm:grid-cols-2">
            {FEATURED_IDS.map((id) => {
              const category = EVALUATION_CATEGORIES.find((c) => c.id === id)!;
              const result = getDemoCategoryResult(id);
              const grade = getGradeInfo(result.score);
              const Icon = category.icon;
              return (
                <div key={id} className="bg-popover p-6 sm:p-8">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5 text-sm font-medium text-foreground/90">
                      <Icon className="size-4 text-muted-foreground" />
                      {category.name}
                    </div>
                    <span className={`font-mono text-xs font-medium uppercase tracking-[0.08em] ${grade.textClass}`}>
                      {grade.label}
                    </span>
                  </div>
                  <div className="mt-4 flex items-baseline gap-2">
                    <span className="font-display text-4xl font-semibold tabular-nums">
                      {result.score}
                    </span>
                    <span className="text-sm text-muted-foreground">/ 100</span>
                  </div>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                    {result.summary}
                  </p>
                </div>
              );
            })}
          </div>

          <div className="grid grid-cols-1 gap-x-10 border-t border-border px-6 sm:grid-cols-2 sm:px-8">
            {otherCategories.map((category) => {
              const result = getDemoCategoryResult(category.id);
              const grade = getGradeInfo(result.score);
              return (
                <div
                  key={category.id}
                  className="flex items-center justify-between gap-4 border-b border-border py-3.5 last:border-b-0 sm:[&:nth-last-child(2)]:border-b-0"
                >
                  <div className="flex min-w-0 items-center gap-2.5">
                    <category.icon className="size-4 shrink-0 text-muted-foreground" />
                    <span className="truncate text-sm text-foreground/85">{category.shortName}</span>
                    <span className="shrink-0 font-mono text-xs text-muted-foreground">
                      {category.weight}%
                    </span>
                  </div>
                  <span className={`shrink-0 font-mono text-sm font-medium tabular-nums ${grade.textClass}`}>
                    {result.score}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="border-t border-border p-6 sm:p-8">
            <h3 className="font-mono text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
              Top Recommendations
            </h3>
            <ul className="mt-4 space-y-3">
              {DEMO_AUDIT.topRecommendations.map((rec) => (
                <li key={rec} className="flex items-start gap-2.5 text-[15px] leading-relaxed text-foreground/90">
                  <ArrowUpRight className="mt-1 size-4 shrink-0 text-flag" />
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
