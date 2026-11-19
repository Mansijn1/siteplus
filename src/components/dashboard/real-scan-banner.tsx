"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, ScanLine } from "lucide-react";

/** Shown only when a real backend scan ran this session — invisible otherwise, so the demo
 * dashboard experience is unchanged for anyone who hasn't scanned with a live backend. */
export function RealScanBanner() {
  const [hasScan, setHasScan] = useState(false);

  useEffect(() => {
    try {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- reads client-only sessionStorage once on mount
      setHasScan(Boolean(sessionStorage.getItem("webrate:lastScanId")));
    } catch {
      // sessionStorage unavailable — treat as no scan.
    }
  }, []);

  if (!hasScan) return null;

  return (
    <Link
      href="/dashboard/raw-scan"
      className="flex items-center justify-between gap-3 rounded-lg border border-flag/30 bg-flag/5 px-5 py-3.5 text-sm transition-colors hover:bg-flag/10"
    >
      <span className="flex items-center gap-2.5 text-foreground/85">
        <ScanLine className="size-4 text-flag" />
        A real browser scan just ran for this URL — view the raw technical data it collected.
      </span>
      <span className="flex shrink-0 items-center gap-1 font-medium text-flag">
        View raw scan data
        <ArrowRight className="size-3.5" />
      </span>
    </Link>
  );
}
