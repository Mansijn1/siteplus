import type { LucideIcon } from "lucide-react";

interface PlaceholderStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
}

export function PlaceholderState({ icon: Icon, title, description }: PlaceholderStateProps) {
  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:py-10">
      <div className="flex min-h-[360px] flex-col items-center justify-center rounded-lg border border-dashed border-border bg-popover/60 px-6 py-16 text-center">
        <div className="flex size-12 items-center justify-center rounded-lg border border-foreground/12 bg-secondary/60">
          <Icon className="size-5 text-muted-foreground" strokeWidth={1.75} />
        </div>
        <h2 className="mt-5 font-display text-xl font-semibold tracking-[-0.01em]">{title}</h2>
        <p className="mt-2 max-w-sm text-sm leading-relaxed text-muted-foreground">{description}</p>
        <span className="mt-5 rounded-sm bg-secondary px-2.5 py-1 font-mono text-[10px] font-medium uppercase tracking-[0.08em] text-muted-foreground">
          Coming in a future phase
        </span>
      </div>
    </div>
  );
}
