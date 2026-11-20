"use client";

import Link from "next/link";
import { EVALUATION_CATEGORIES, type CategoryId } from "@/lib/categories";
import { getGradeInfo } from "@/lib/scoring";
import { useEvaluationData } from "./evaluation-data-provider";

export function CategoryPickerList({ selectedId }: { selectedId: CategoryId }) {
  const { data } = useEvaluationData();
  return (
    <nav className="overflow-hidden rounded-lg border border-foreground/12 bg-popover">
      {EVALUATION_CATEGORIES.map((category) => {
        const score = data.scores[category.id] ?? 0;
        const grade = getGradeInfo(score);
        const active = category.id === selectedId;
        const Icon = category.icon;
        return (
          <Link
            key={category.id}
            href={`/dashboard/categories?id=${category.id}`}
            className={`flex items-center justify-between gap-3 border-b border-border px-4 py-3.5 text-sm transition-colors last:border-b-0 ${
              active ? "bg-secondary" : "hover:bg-secondary/50"
            }`}
          >
            <span className="flex min-w-0 items-center gap-2.5">
              <Icon
                className={`size-4 shrink-0 ${active ? "text-flag" : "text-muted-foreground"}`}
                strokeWidth={1.75}
              />
              <span className={`truncate ${active ? "font-medium text-flag" : "text-foreground/85"}`}>
                {category.name}
              </span>
            </span>
            <span className="flex shrink-0 items-center gap-2">
              <span className="font-mono text-xs tabular-nums text-muted-foreground">{score}</span>
              <span className={`size-1.5 rounded-full ${grade.bgClass}`} aria-label={grade.label} />
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
