"use client";

import { Button } from "@/components/ui/button";
import { scrollToHeroInput } from "@/lib/scroll-to-hero";

export function FinalCta() {
  return (
    <section className="border-t border-border py-24">
      <div className="mx-auto max-w-4xl px-6">
        <div className="relative overflow-hidden rounded-lg bg-popover px-6 py-16 text-center shadow-[0_28px_60px_-28px_oklch(0.2_0.02_60_/_30%)] sm:px-16">
          <svg
            className="pointer-events-none absolute -right-16 top-1/2 h-[320px] w-[320px] -translate-y-1/2 opacity-[0.06]"
            viewBox="0 0 220 220"
            aria-hidden="true"
          >
            <circle cx="110" cy="110" r="100" fill="none" stroke="var(--flag)" strokeWidth="2" />
            <circle cx="110" cy="110" r="76" fill="none" stroke="var(--flag)" strokeWidth="1.5" />
            <path d="M70 112 L98 140 L152 82" fill="none" stroke="var(--flag)" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>

          <div className="relative">
            <h2 className="font-display text-3xl font-semibold tracking-[-0.02em] text-balance sm:text-4xl">
              Your Website Has Room to Be Better.
            </h2>
            <p className="mx-auto mt-4 max-w-[48ch] text-lg leading-relaxed text-muted-foreground">
              Find out where your website stands and discover opportunities
              to improve it.
            </p>
            <Button
              size="lg"
              onClick={scrollToHeroInput}
              className="mt-8 h-13 bg-flag px-7 text-[15px] font-medium text-primary-foreground hover:bg-flag/90"
            >
              Evaluate Your Website
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
