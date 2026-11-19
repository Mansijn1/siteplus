import { EVALUATION_CATEGORIES, TOTAL_WEIGHT } from "@/lib/categories";

const MAX_WEIGHT = Math.max(...EVALUATION_CATEGORIES.map((c) => c.weight));
const COLUMN_SPLIT = Math.ceil(EVALUATION_CATEGORIES.length / 2);
const COLUMNS = [
  EVALUATION_CATEGORIES.slice(0, COLUMN_SPLIT),
  EVALUATION_CATEGORIES.slice(COLUMN_SPLIT),
];

export function EvaluationCategories() {
  return (
    <section id="evaluation" className="border-t border-border py-24">
      <div className="mx-auto max-w-6xl px-6">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div className="max-w-2xl">
            <h2 className="font-display text-3xl font-semibold tracking-[-0.02em] sm:text-4xl">
              The full rubric, in the open.
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-muted-foreground">
              Twelve categories, each weighted by how much it actually moves
              outcomes — the same rubric behind every evaluation.
            </p>
          </div>
          <p className="shrink-0 font-mono text-xs text-muted-foreground">
            Total weight: {TOTAL_WEIGHT}%
          </p>
        </div>

        <div className="mt-14 grid grid-cols-1 gap-x-14 gap-y-0 sm:grid-cols-2">
          {COLUMNS.map((column, columnIndex) => (
            <div key={columnIndex} className="relative pl-7">
              <div className="absolute left-0 top-3 bottom-3 w-px bg-border" aria-hidden="true" />
              {column.map((category) => {
                const Icon = category.icon;
                const fillPercent = (category.weight / MAX_WEIGHT) * 100;
                return (
                  <div key={category.id} className="relative border-b border-border py-5 last:border-b-0">
                    <span
                      className="absolute -left-7 top-6 size-[7px] -translate-x-1/2 bg-foreground/70"
                      aria-hidden="true"
                    />
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex min-w-0 items-center gap-3">
                        <Icon className="size-[18px] shrink-0 text-muted-foreground" strokeWidth={1.6} />
                        <span className="truncate text-[15px] font-medium text-foreground/90">
                          {category.name}
                        </span>
                      </div>
                      <span className="shrink-0 font-mono text-base font-medium tabular-nums">
                        {category.weight}%
                      </span>
                    </div>
                    <p className="mt-1.5 pl-[30px] text-sm leading-relaxed text-muted-foreground">
                      {category.description}
                    </p>
                    <div className="relative mt-3 ml-[30px] h-[3px] max-w-[220px] bg-border">
                      <span
                        className="absolute top-1/2 h-[9px] w-[2px] -translate-y-1/2 bg-foreground/70"
                        style={{ left: `${fillPercent}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
