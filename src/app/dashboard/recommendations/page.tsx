"use client";

import { useState } from "react";
import { RecommendationCard } from "@/components/dashboard/recommendation-card";
import { useEvaluationData } from "@/components/dashboard/evaluation-data-provider";
import type { RecommendationBucket } from "@/lib/evaluation-api";

const BUCKET_TABS: { id: RecommendationBucket | "all"; label: string }[] = [
  { id: "all", label: "All" },
  { id: "critical_fix", label: "Critical Fixes" },
  { id: "quick_win", label: "Quick Wins" },
  { id: "long_term", label: "Long-Term" },
];

export default function RecommendationsPage() {
  const { data } = useEvaluationData();
  const [activeBucket, setActiveBucket] = useState<RecommendationBucket | "all">("all");
  const allRecommendations = data.getAllRecommendationsRanked();
  const hasBucketData = data.isReal && allRecommendations.some((r) => r.bucket);
  const recommendations = hasBucketData && activeBucket !== "all"
    ? allRecommendations.filter((r) => r.bucket === activeBucket)
    : allRecommendations;
  const highPriorityCount = data
    .getAllIssues()
    .filter((i) => i.severity === "critical" || i.severity === "high").length;

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-8 sm:px-6 lg:py-10">
      <div>
        <h1 className="font-display text-2xl font-semibold tracking-[-0.01em]">Recommendations</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {allRecommendations.length} recommendations across all categories, ranked by severity —{" "}
          {highPriorityCount} tied to a critical or high-severity issue.
        </p>
      </div>

      {hasBucketData && (
        <div className="flex flex-wrap gap-2">
          {BUCKET_TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveBucket(tab.id)}
              className={`rounded-sm px-3 py-1.5 font-mono text-xs font-medium uppercase tracking-[0.06em] transition-colors ${
                activeBucket === tab.id
                  ? "bg-flag text-primary-foreground"
                  : "bg-secondary text-muted-foreground hover:text-foreground"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}

      {recommendations.length === 0 ? (
        <div className="rounded-lg border border-foreground/12 bg-popover px-6 py-10 text-center text-sm text-muted-foreground">
          {allRecommendations.length === 0
            ? "No recommendations — every checked item passed."
            : "No recommendations in this group."}
        </div>
      ) : (
        <div className="rounded-lg border border-foreground/12 bg-popover px-6">
          {recommendations.map((rec) => (
            <RecommendationCard
              key={`${rec.categoryId}-${rec.issueId ?? rec.title}`}
              categoryId={rec.categoryId}
              categoryName={rec.categoryName}
              title={rec.title}
              why={rec.why}
              how={rec.how}
              expectedImpact={rec.expectedImpact}
              topSeverity={rec.topSeverity}
              priority={rec.priority}
              estimatedEffort={rec.estimatedEffort}
              expanded
            />
          ))}
        </div>
      )}
    </div>
  );
}
