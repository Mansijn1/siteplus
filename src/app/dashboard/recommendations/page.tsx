"use client";

import { RecommendationCard } from "@/components/dashboard/recommendation-card";
import { useEvaluationData } from "@/components/dashboard/evaluation-data-provider";

export default function RecommendationsPage() {
  const { data } = useEvaluationData();
  const recommendations = data.getAllRecommendationsRanked();
  const highPriorityCount = data
    .getAllIssues()
    .filter((i) => i.severity === "critical" || i.severity === "high").length;

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-8 sm:px-6 lg:py-10">
      <div>
        <h1 className="font-display text-2xl font-semibold tracking-[-0.01em]">Recommendations</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {recommendations.length} recommendations across all categories, ranked by severity —{" "}
          {highPriorityCount} tied to a critical or high-severity issue.
        </p>
      </div>

      {recommendations.length === 0 ? (
        <div className="rounded-lg border border-foreground/12 bg-popover px-6 py-10 text-center text-sm text-muted-foreground">
          No recommendations — every checked item passed.
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
