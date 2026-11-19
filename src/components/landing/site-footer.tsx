"use client";

import { useEffect, useState } from "react";
import { Wordmark } from "@/components/shared/brand-mark";

/** Deferred to a client effect so the build year is never captured in the prerendered shell. */
function CopyrightYear() {
  const [year, setYear] = useState(2026);
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- intentional: must run after mount, not during prerender
    setYear(new Date().getFullYear());
  }, []);
  return <>{year}</>;
}

const PRODUCT_LINKS = [
  { href: "#product", label: "Product Preview" },
  { href: "#features", label: "Features" },
  { href: "#how-it-works", label: "How It Works" },
];

const EVALUATION_LINKS = [
  { href: "#evaluation", label: "Evaluation Categories" },
  { href: "#top", label: "Analyze a Website" },
];

export function SiteFooter() {
  return (
    <footer className="border-t border-border py-16">
      <div className="mx-auto max-w-6xl px-6">
        <div className="grid grid-cols-2 gap-10 sm:grid-cols-[1.4fr_1fr_1fr_1fr]">
          <div className="col-span-2 sm:col-span-1">
            <Wordmark />
            <p className="mt-4 max-w-[36ch] text-sm leading-relaxed text-muted-foreground">
              A structured, 12-category inspection for your website — what&apos;s
              working, what isn&apos;t, and what to fix first.
            </p>
          </div>

          <div>
            <h3 className="font-mono text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
              Product
            </h3>
            <ul className="mt-4 space-y-2.5">
              {PRODUCT_LINKS.map((link) => (
                <li key={link.label}>
                  <a href={link.href} className="text-sm text-foreground/80 hover:text-foreground">
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="font-mono text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
              Evaluation
            </h3>
            <ul className="mt-4 space-y-2.5">
              {EVALUATION_LINKS.map((link) => (
                <li key={link.label}>
                  <a href={link.href} className="text-sm text-foreground/80 hover:text-foreground">
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="font-mono text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
              Contact
            </h3>
            <ul className="mt-4 space-y-2.5">
              <li>
                <a href="mailto:hello@webrate.ai" className="text-sm text-foreground/80 hover:text-foreground">
                  hello@webrate.ai
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-14 flex flex-col-reverse items-start justify-between gap-4 border-t border-border pt-6 sm:flex-row sm:items-center">
          <p className="text-xs text-muted-foreground">
            © <CopyrightYear /> WebRate AI. All rights reserved.
          </p>
          <p className="font-mono text-[11px] uppercase tracking-[0.1em] text-muted-foreground">
            All audit data shown on this page is sample data.
          </p>
        </div>
      </div>
    </footer>
  );
}
