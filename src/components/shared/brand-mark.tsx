interface BrandMarkProps {
  size?: number;
  className?: string;
}

/** The recurring found-mark: a small rotated inspection stamp beside the wordmark. */
export function BrandMark({ size = 28, className = "" }: BrandMarkProps) {
  return (
    <svg
      viewBox="0 0 28 28"
      width={size}
      height={size}
      className={className}
      style={{ transform: "rotate(-8deg)" }}
      aria-hidden="true"
    >
      <rect x="2" y="2" width="24" height="24" rx="4" fill="none" stroke="var(--flag)" strokeWidth="1.6" />
      <path d="M8.5 14.5 L12 18 L19.5 9.5" fill="none" stroke="var(--flag)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function Wordmark({ className = "" }: { className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2 font-display font-semibold tracking-tight ${className}`}>
      <BrandMark />
      <span>
        WebRate <span className="text-flag">AI</span>
      </span>
    </span>
  );
}
