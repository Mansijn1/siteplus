import { EvaluationTable } from "@/components/dashboard/evaluation-table";

export default function WebsiteEvaluationPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8 sm:px-6 lg:py-10">
      <div>
        <h1 className="font-display text-2xl font-semibold tracking-[-0.01em]">Website Evaluation</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          All 12 weighted categories from the shared rubric. Click a row to expand a quick summary, or open
          the full category analysis.
        </p>
      </div>
      <EvaluationTable />
    </div>
  );
}
