import { TrendingUp, TrendingDown, AlertTriangle, Flame } from "lucide-react";
import {
  getStrongestCategory,
  getWeakestCategory,
  getTotalIssueCount,
  getHighPriorityIssueCount,
} from "@/data/demo-results";

export function EvaluationSummaryStats() {
  const strongest = getStrongestCategory();
  const weakest = getWeakestCategory();
  const totalIssues = getTotalIssueCount();
  const highPriority = getHighPriorityIssueCount();

  const stats = [
    {
      label: "Strongest Category",
      value: strongest.name,
      meta: `${strongest.score} / 100`,
      icon: TrendingUp,
      tone: "text-pass",
    },
    {
      label: "Weakest Category",
      value: weakest.name,
      meta: `${weakest.score} / 100`,
      icon: TrendingDown,
      tone: "text-flag",
    },
    {
      label: "Issues Found",
      value: String(totalIssues),
      meta: "across all categories",
      icon: AlertTriangle,
      tone: "text-muted-foreground",
    },
    {
      label: "High-Priority Items",
      value: String(highPriority),
      meta: "critical + high severity",
      icon: Flame,
      tone: "text-critical",
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-px overflow-hidden rounded-lg border border-foreground/12 bg-border sm:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <div key={stat.label} className="bg-popover p-5">
          <div className="flex items-center gap-2">
            <stat.icon className={`size-4 ${stat.tone}`} strokeWidth={1.75} />
            <span className="font-mono text-[11px] font-medium uppercase tracking-[0.08em] text-muted-foreground">
              {stat.label}
            </span>
          </div>
          <p className="mt-3 truncate text-lg font-semibold tracking-[-0.01em]">{stat.value}</p>
          <p className="mt-0.5 text-xs text-muted-foreground">{stat.meta}</p>
        </div>
      ))}
    </div>
  );
}
