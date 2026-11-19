import { Suspense } from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { ScoreGauge } from "@/components/dashboard/score-gauge";
import { GradeChip } from "@/components/dashboard/grade-chip";
import { EvaluationSummaryStats } from "@/components/dashboard/evaluation-summary-stats";
import { ScoreDistributionChart } from "@/components/dashboard/score-distribution-chart";
import { RecommendationCard } from "@/components/dashboard/recommendation-card";
import { RealScanBanner } from "@/components/dashboard/real-scan-banner";
import { EVALUATION_CATEGORIES } from "@/lib/categories";
import { getGradeInfo } from "@/lib/scoring";
import { getWebsiteUrl } from "@/lib/website-url.server";
import {
  DEMO_SCORES,
  OVERALL_SCORE,
  EVALUATION_SUMMARY,
  AUDIT_STATUS,
  getTopRecommendations,
} from "@/data/demo-results";

const COLUMN_SIZE = Math.ceil(EVALUATION_CATEGORIES.length / 3);
const CATEGORY_COLUMNS = [
  EVALUATION_CATEGORIES.slice(0, COLUMN_SIZE),
  EVALUATION_CATEGORIES.slice(COLUMN_SIZE, COLUMN_SIZE * 2),
  EVALUATION_CATEGORIES.slice(COLUMN_SIZE * 2),
];

export default function DashboardOverviewPage() {
  return (
    <Suspense fallback={<div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:py-10" />}>
      <OverviewContent />
    </Suspense>
  );
}

async function OverviewContent() {
  const websiteUrl = await getWebsiteUrl();
  const displayUrl = websiteUrl.replace(/^https?:\/\//, "");
  const grade = getGradeInfo(OVERALL_SCORE);
  const topRecommendations = getTopRecommendations(3);

  return (
    <div className="mx-auto max-w-6xl space-y-8 px-4 py-8 sm:px-6 lg:py-10">
      <div>
        <h1 className="font-display text-2xl font-semibold tracking-[-0.01em]">Overview</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          A complete read on {displayUrl}, inspected across 12 weighted categories.
        </p>
      </div>

      <RealScanBanner />

      {/* Prominent overall score section */}
      <div className="rounded-lg border border-foreground/12 bg-popover p-6 sm:p-8">
        <div className="flex flex-col gap-8 sm:flex-row sm:items-center">
          <ScoreGauge score={OVERALL_SCORE} gradeLabel={grade.label} tag={grade.tag} size={168} />
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="rounded-sm bg-pass/10 px-2.5 py-1 font-mono text-[11px] font-medium uppercase tracking-[0.08em] text-pass">
                {AUDIT_STATUS}
              </span>
              <span className="rounded-sm bg-secondary px-2.5 py-1 font-mono text-[11px] font-medium uppercase tracking-[0.08em] text-muted-foreground">
                Demo Audit
              </span>
            </div>
            <p className="mt-3 font-mono text-sm text-muted-foreground">{websiteUrl}</p>
            <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-foreground/85">{EVALUATION_SUMMARY}</p>
          </div>
        </div>
      </div>

      <EvaluationSummaryStats />

      <div className="grid gap-6 lg:grid-cols-[1.3fr_1fr]">
        <div className="rounded-lg border border-foreground/12 bg-popover p-6 sm:p-7">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-lg font-semibold tracking-[-0.01em]">Score Distribution</h2>
            <Link
              href="/dashboard/evaluation"
              className="inline-flex items-center gap-1.5 text-sm font-medium text-flag hover:text-flag/80"
            >
              Full table
              <ArrowRight className="size-3.5" />
            </Link>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">All 12 categories, ranked by score.</p>
          <div className="mt-4">
            <ScoreDistributionChart />
          </div>
        </div>

        <div className="rounded-lg border border-foreground/12 bg-popover p-6 sm:p-7">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-lg font-semibold tracking-[-0.01em]">Top Recommendations</h2>
            <Link
              href="/dashboard/recommendations"
              className="inline-flex items-center gap-1.5 text-sm font-medium text-flag hover:text-flag/80"
            >
              All
              <ArrowRight className="size-3.5" />
            </Link>
          </div>
          <div className="mt-1">
            {topRecommendations.map((rec) => (
              <RecommendationCard
                key={rec.title}
                categoryId={rec.categoryId}
                categoryName={rec.categoryName}
                title={rec.title}
                why={rec.why}
                how={rec.how}
                expectedImpact={rec.expectedImpact}
                topSeverity={rec.topSeverity}
              />
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-foreground/12 bg-popover p-6 sm:p-7">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-lg font-semibold tracking-[-0.01em]">Category Scores</h2>
          <Link
            href="/dashboard/categories"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-flag hover:text-flag/80"
          >
            Analyze categories
            <ArrowRight className="size-3.5" />
          </Link>
        </div>
        <div className="mt-4 grid grid-cols-1 gap-x-8 sm:grid-cols-2 lg:grid-cols-3">
          {CATEGORY_COLUMNS.map((column, columnIndex) => (
            <div key={columnIndex} className="flex flex-col divide-y divide-border">
              {column.map((category) => {
                const score = DEMO_SCORES[category.id] ?? 0;
                const Icon = category.icon;
                return (
                  <Link
                    key={category.id}
                    href={`/dashboard/categories?id=${category.id}`}
                    className="flex items-center justify-between gap-3 py-3 transition-colors hover:text-flag"
                  >
                    <span className="flex min-w-0 items-center gap-2.5">
                      <Icon className="size-4 shrink-0 text-muted-foreground" strokeWidth={1.75} />
                      <span className="truncate text-sm text-foreground/85">{category.shortName}</span>
                    </span>
                    <span className="flex shrink-0 items-center gap-2">
                      <span className="font-mono text-sm font-medium tabular-nums">{score}</span>
                      <GradeChip score={score} />
                    </span>
                  </Link>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
