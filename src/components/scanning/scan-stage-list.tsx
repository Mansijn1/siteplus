import { CheckCircle2, Circle, Loader2 } from "lucide-react";
import { EVALUATION_CATEGORIES } from "@/lib/categories";
import { getCategoryAnalysis } from "@/data/demo-results";

export type StageStatus = "pending" | "active" | "complete";

export function getStageStatus(index: number, activeIndex: number): StageStatus {
  if (index < activeIndex) return "complete";
  if (index === activeIndex) return "active";
  return "pending";
}

export function ScanStageList({ activeIndex }: { activeIndex: number }) {
  return (
    <div className="relative pl-9">
      <div className="absolute left-[11px] top-2 h-[calc(100%-1rem)] w-px bg-border" aria-hidden="true">
        <div
          className="w-full bg-flag transition-[height] duration-500 ease-out"
          style={{ height: `${(Math.min(activeIndex, EVALUATION_CATEGORIES.length) / EVALUATION_CATEGORIES.length) * 100}%` }}
        />
      </div>

      <div className="flex flex-col gap-4">
        {EVALUATION_CATEGORIES.map((category, index) => {
          const status = getStageStatus(index, activeIndex);
          const analysis = getCategoryAnalysis(category.id);

          return (
            <div key={category.id} className="relative flex items-start gap-3">
              <span
                className="absolute -left-9 top-0.5 flex size-[22px] shrink-0 items-center justify-center rounded-full bg-background"
                aria-hidden="true"
              >
                {status === "complete" && <CheckCircle2 className="size-[18px] text-pass" strokeWidth={2} />}
                {status === "active" && <Loader2 className="size-[18px] animate-spin text-flag" strokeWidth={2} />}
                {status === "pending" && <Circle className="size-[14px] text-border" strokeWidth={2} />}
              </span>

              <div className="min-w-0">
                <p
                  className={`text-sm font-medium transition-colors ${
                    status === "pending" ? "text-muted-foreground" : "text-foreground/90"
                  }`}
                >
                  {category.name}
                </p>
                {status === "active" && (
                  <p className="mt-0.5 text-xs text-muted-foreground">{analysis.whatWasEvaluated[0]}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
