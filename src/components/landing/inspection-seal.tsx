import type { StatusTag } from "@/lib/scoring";

const TAG_COLOR: Record<StatusTag, string> = {
  pass: "var(--pass)",
  flag: "var(--flag)",
  critical: "var(--critical)",
};

interface InspectionSealProps {
  score: number;
  gradeLabel: string;
  tag: StatusTag;
  topText?: string;
  bottomText?: string;
  size?: number;
  className?: string;
}

/**
 * A certificate/stamp motif for the overall score — concentric rings with a
 * rim of fixed tick marks and curved labels, not a data-driven progress ring.
 */
export function InspectionSeal({
  score,
  gradeLabel,
  tag,
  topText = "WEBRATE INSPECTION",
  bottomText = "SAMPLE AUDIT",
  size = 220,
  className = "",
}: InspectionSealProps) {
  const color = TAG_COLOR[tag];
  const ticks = Array.from({ length: 48 }, (_, i) => i);

  return (
    <div
      className={`relative select-none ${className}`}
      style={{ width: size, height: size, transform: "rotate(-3deg)" }}
    >
      <svg viewBox="0 0 220 220" className="absolute inset-0 h-full w-full overflow-visible">
        <defs>
          <path id="seal-top-arc" d="M 30 110 A 80 80 0 0 1 190 110" fill="none" />
          <path id="seal-bottom-arc" d="M 190 112 A 80 80 0 0 1 30 112" fill="none" />
        </defs>

        {ticks.map((i) => {
          const angle = (i / ticks.length) * 360;
          const long = i % 4 === 0;
          return (
            <rect
              key={i}
              x={109}
              y={long ? 4 : 8}
              width={2}
              height={long ? 10 : 6}
              fill={color}
              opacity={0.75}
              transform={`rotate(${angle} 110 110)`}
            />
          );
        })}

        <circle cx="110" cy="110" r="88" fill="none" stroke={color} strokeWidth="1.5" opacity="0.55" />
        <circle cx="110" cy="110" r="62" fill="none" stroke={color} strokeWidth="1" opacity="0.35" />

        <text
          fill={color}
          fontFamily="var(--font-mono)"
          fontSize="9.5"
          letterSpacing="0.28em"
          opacity="0.85"
        >
          <textPath href="#seal-top-arc" startOffset="50%" textAnchor="middle">
            {topText}
          </textPath>
        </text>
        <text
          fill={color}
          fontFamily="var(--font-mono)"
          fontSize="9.5"
          letterSpacing="0.28em"
          opacity="0.85"
        >
          <textPath href="#seal-bottom-arc" startOffset="50%" textAnchor="middle">
            {bottomText}
          </textPath>
        </text>
      </svg>

      <div
        className="absolute inset-0 flex flex-col items-center justify-center"
        style={{ transform: "rotate(3deg)" }}
      >
        <span
          className="font-display font-semibold tabular-nums leading-none"
          style={{ fontSize: size * 0.26, color }}
        >
          {score}
        </span>
        <span
          className="mt-1 font-mono text-[11px] font-medium uppercase tracking-[0.18em]"
          style={{ color }}
        >
          {gradeLabel}
        </span>
      </div>
    </div>
  );
}
