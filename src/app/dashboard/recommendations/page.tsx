import { RecommendationCard } from "@/components/dashboard/recommendation-card";
import { getAllRecommendationsRanked, getHighPriorityIssueCount } from "@/data/demo-results";

export default function RecommendationsPage() {
  const recommendations = getAllRecommendationsRanked();

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-8 sm:px-6 lg:py-10">
      <div>
        <h1 className="font-display text-2xl font-semibold tracking-[-0.01em]">Recommendations</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {recommendations.length} recommendations across all categories, ranked by severity —{" "}
          {getHighPriorityIssueCount()} tied to a critical or high-severity issue.
        </p>
      </div>

      <div className="rounded-lg border border-foreground/12 bg-popover px-6">
        {recommendations.map((rec) => (
          <RecommendationCard
            key={`${rec.categoryId}-${rec.title}`}
            categoryId={rec.categoryId}
            categoryName={rec.categoryName}
            title={rec.title}
            why={rec.why}
            how={rec.how}
            expectedImpact={rec.expectedImpact}
            topSeverity={rec.topSeverity}
            expanded
          />
        ))}
      </div>
    </div>
  );
}
