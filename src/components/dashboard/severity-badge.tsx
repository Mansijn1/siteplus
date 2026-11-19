import { SEVERITY_LABEL, type Severity } from "@/data/demo-results";

const SEVERITY_CLASSES: Record<Severity, string> = {
  critical: "bg-critical text-primary-foreground",
  high: "border border-critical/40 text-critical bg-critical/8",
  medium: "border border-flag/40 text-flag bg-flag/8",
  low: "border border-border text-muted-foreground",
};

export function SeverityBadge({ severity, className = "" }: { severity: Severity; className?: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-sm px-2 py-0.5 font-mono text-[10px] font-medium uppercase tracking-[0.08em] ${SEVERITY_CLASSES[severity]} ${className}`}
    >
      {SEVERITY_LABEL[severity]}
    </span>
  );
}
