import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { SeverityBadge } from "./severity-badge";
import type { Severity } from "@/data/demo-results";

interface RecommendationCardProps {
  categoryId: string;
  categoryName: string;
  title: string;
  why: string;
  how: string;
  expectedImpact: string;
  topSeverity: Severity;
  expanded?: boolean;
}

export function RecommendationCard({
  categoryId,
  categoryName,
  title,
  why,
  how,
  expectedImpact,
  topSeverity,
  expanded = false,
}: RecommendationCardProps) {
  return (
    <div className="border-b border-border py-5 last:border-b-0">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <SeverityBadge severity={topSeverity} />
            <Link
              href={`/dashboard/categories?id=${categoryId}`}
              className="font-mono text-[11px] uppercase tracking-[0.08em] text-muted-foreground hover:text-flag"
            >
              {categoryName}
            </Link>
          </div>
          <h3 className="mt-2 text-[15px] font-medium text-foreground/90">{title}</h3>
        </div>
      </div>

      {expanded ? (
        <div className="mt-3 space-y-2 text-sm leading-relaxed text-muted-foreground">
          <p>
            <span className="font-medium text-foreground/80">Why it matters — </span>
            {why}
          </p>
          <p>
            <span className="font-medium text-foreground/80">How to improve — </span>
            {how}
          </p>
          <p>
            <span className="font-medium text-foreground/80">Expected impact — </span>
            {expectedImpact}
          </p>
        </div>
      ) : (
        <p className="mt-1.5 text-sm text-muted-foreground">{why}</p>
      )}

      <Link
        href={`/dashboard/categories?id=${categoryId}`}
        className="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-flag hover:text-flag/80"
      >
        View category
        <ArrowRight className="size-3.5" />
      </Link>
    </div>
  );
}
