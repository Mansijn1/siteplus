import type { StatusTag } from "@/lib/scoring";

const TAG_COLOR: Record<StatusTag, string> = {
  pass: "var(--pass)",
  flag: "var(--flag)",
  critical: "var(--critical)",
};

interface ScoreGaugeProps {
  score: number;
  gradeLabel: string;
  tag: StatusTag;
  topText?: string;
  bottomText?: string;
  size?: number;
  className?: string;
}

const RADIUS = 80;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

/**
 * The dashboard's overall-score gauge — same inspection-seal tick rim and
 * curved labels as the landing page, with an added proportional progress
 * arc (explicitly requested for the dashboard, unlike the static landing
 * page seal).
 */
export function ScoreGauge({
  score,
  gradeLabel,
  tag,
  topText = "OVERALL SCORE",
  bottomText = "OUT OF 100",
  size = 200,
  className = "",
}: ScoreGaugeProps) {
  const color = TAG_COLOR[tag];
  const ticks = Array.from({ length: 48 }, (_, i) => i);
  const progress = Math.max(0, Math.min(100, score)) / 100;
  const dashOffset = CIRCUMFERENCE * (1 - progress);

  return (
    <div className={`relative select-none ${className}`} style={{ width: size, height: size }}>
      <svg viewBox="0 0 220 220" className="absolute inset-0 h-full w-full overflow-visible">
        <defs>
          <path id="gauge-top-arc" d="M 30 110 A 80 80 0 0 1 190 110" fill="none" />
          <path id="gauge-bottom-arc" d="M 190 112 A 80 80 0 0 1 30 112" fill="none" />
        </defs>

        {ticks.map((i) => {
          const angle = (i / ticks.length) * 360;
          const long = i % 4 === 0;
          return (
            <rect
              key={i}
              x={109}
              y={long ? 2 : 6}
              width={2}
              height={long ? 8 : 5}
              fill={color}
              opacity={0.35}
              transform={`rotate(${angle} 110 110)`}
            />
          );
        })}

        <circle cx="110" cy="110" r={RADIUS} fill="none" stroke="var(--border)" strokeWidth="3" />
        <circle
          cx="110"
          cy="110"
          r={RADIUS}
          fill="none"
          stroke={color}
          strokeWidth="3"
          strokeLinecap="round"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={dashOffset}
          transform="rotate(-90 110 110)"
        />
        <circle cx="110" cy="110" r="62" fill="none" stroke={color} strokeWidth="1" opacity="0.3" />

        <text fill={color} fontFamily="var(--font-mono)" fontSize="9" letterSpacing="0.26em" opacity="0.8">
          <textPath href="#gauge-top-arc" startOffset="50%" textAnchor="middle">
            {topText}
          </textPath>
        </text>
        <text fill={color} fontFamily="var(--font-mono)" fontSize="9" letterSpacing="0.26em" opacity="0.8">
          <textPath href="#gauge-bottom-arc" startOffset="50%" textAnchor="middle">
            {bottomText}
          </textPath>
        </text>
      </svg>

      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span
          className="font-display font-semibold tabular-nums leading-none"
          style={{ fontSize: size * 0.2, color }}
        >
          {score}
        </span>
        <span className="mt-1 font-mono text-[11px] font-medium uppercase tracking-[0.18em]" style={{ color }}>
          {gradeLabel}
        </span>
      </div>
    </div>
  );
}
