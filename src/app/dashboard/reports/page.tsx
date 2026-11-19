import { FileBarChart } from "lucide-react";
import { PlaceholderState } from "@/components/dashboard/placeholder-state";

export default function ReportsPage() {
  return (
    <PlaceholderState
      icon={FileBarChart}
      title="Reports"
      description="Export and historical trend reports will live here — compare evaluations over time and share polished PDF summaries."
    />
  );
}
