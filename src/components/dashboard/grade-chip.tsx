import { getGradeInfo } from "@/lib/scoring";

const BG_SOFT: Record<string, string> = {
  pass: "bg-pass/10 text-pass",
  flag: "bg-flag/10 text-flag",
  critical: "bg-critical/10 text-critical",
};

export function GradeChip({ score, className = "" }: { score: number; className?: string }) {
  const grade = getGradeInfo(score);
  return (
    <span
      className={`inline-flex items-center rounded-sm px-2 py-0.5 font-mono text-[10px] font-medium uppercase tracking-[0.08em] ${BG_SOFT[grade.tag]} ${className}`}
    >
      {grade.label}
    </span>
  );
}

export function ScoreBar({ score, className = "" }: { score: number; className?: string }) {
  const grade = getGradeInfo(score);
  const width = Math.max(0, Math.min(100, score));
  return (
    <div className={`h-[5px] w-full rounded-sm bg-border ${className}`}>
      <div className={`h-full rounded-sm ${grade.bgClass}`} style={{ width: `${width}%` }} />
    </div>
  );
}
