"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowRight, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { InspectionSeal } from "./inspection-seal";
import { HERO_URL_INPUT_ID } from "@/lib/scroll-to-hero";
import { validateAndNormalizeUrl } from "@/lib/validation";
import { storeSubmittedUrl } from "@/lib/site-url-storage";
import { DEMO_AUDIT, getDemoCategoryResult } from "@/lib/demo-audit";
import { getCategoryById } from "@/lib/categories";
import { getGradeInfo } from "@/lib/scoring";

const EASE = [0.16, 1, 0.3, 1] as const;

const fadeUp = {
  hidden: { opacity: 0, y: 18 },
  show: (delay: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: EASE, delay },
  }),
};

const PREVIEW_CATEGORY_IDS = ["performance", "seo", "accessibility"] as const;

export function Hero() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const overallGrade = getGradeInfo(DEMO_AUDIT.overallScore);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const result = validateAndNormalizeUrl(url);
    if (!result.ok) {
      setError(result.error);
      return;
    }
    setError(null);
    setSubmitting(true);
    storeSubmittedUrl(result.normalizedUrl);
    router.push(`/scanning?url=${encodeURIComponent(result.normalizedUrl)}`);
  }

  return (
    <section id="top" className="relative overflow-hidden bg-report-ruling">
      <div className="mx-auto grid max-w-6xl gap-16 px-6 pb-24 pt-20 md:pt-28 lg:grid-cols-[1.05fr_0.95fr] lg:gap-10">
        <div>
          <motion.h1
            initial="hidden"
            animate="show"
            custom={0}
            variants={fadeUp}
            className="font-display text-[2.6rem] font-semibold leading-[1.08] tracking-[-0.02em] text-balance sm:text-[3.4rem] lg:text-[3.75rem]"
          >
            Your Website.
            <br />
            <span className="text-flag">Evaluated</span> From Every Angle.
          </motion.h1>

          <motion.p
            initial="hidden"
            animate="show"
            custom={0.1}
            variants={fadeUp}
            className="mt-6 max-w-[52ch] text-lg leading-relaxed text-muted-foreground"
          >
            Discover what&apos;s working, what&apos;s holding your website back, and
            exactly how to improve it. Get a comprehensive website evaluation
            powered by intelligent analysis.
          </motion.p>

          <motion.form
            initial="hidden"
            animate="show"
            custom={0.2}
            variants={fadeUp}
            onSubmit={handleSubmit}
            className="mt-9 max-w-xl"
            noValidate
          >
            <label
              htmlFor={HERO_URL_INPUT_ID}
              className="mb-2 block font-mono text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground"
            >
              Website URL
            </label>
            <div className="flex flex-col gap-3 sm:flex-row">
              <Input
                id={HERO_URL_INPUT_ID}
                type="text"
                inputMode="url"
                autoComplete="off"
                placeholder="https://yourwebsite.com"
                value={url}
                onChange={(e) => {
                  setUrl(e.target.value);
                  if (error) setError(null);
                }}
                aria-invalid={error ? true : undefined}
                aria-describedby={error ? "hero-url-error" : undefined}
                className="h-13 flex-1 border-foreground/20 bg-popover px-4 text-base"
              />
              <Button
                type="submit"
                size="lg"
                disabled={submitting}
                className="h-13 shrink-0 gap-2 bg-flag px-6 text-[15px] font-medium text-primary-foreground hover:bg-flag/90"
              >
                {submitting ? "Opening Inspection…" : "Analyze Website"}
                {!submitting && <ArrowRight className="size-4" />}
              </Button>
            </div>
            {error && (
              <p id="hero-url-error" role="alert" className="mt-2.5 text-sm text-critical">
                {error}
              </p>
            )}
            <p className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
              <ShieldCheck className="size-4 text-pass" />
              No account needed — see your evaluation structure before you commit.
            </p>
          </motion.form>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 24, rotate: -1 }}
          animate={{ opacity: 1, y: 0, rotate: -2 }}
          transition={{ duration: 0.7, ease: EASE, delay: 0.25 }}
          className="relative mx-auto w-full max-w-sm rounded-lg bg-popover p-6 shadow-[0_28px_60px_-28px_oklch(0.2_0.02_60_/_35%)] sm:p-7"
        >
          <div className="flex items-center justify-between">
            <span className="font-mono text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
              Inspection Preview
            </span>
            <span className="rounded-sm bg-secondary px-2 py-0.5 font-mono text-[10px] font-medium uppercase tracking-[0.1em] text-muted-foreground">
              Sample
            </span>
          </div>

          <div className="mt-6 flex items-center gap-5">
            <InspectionSeal
              score={DEMO_AUDIT.overallScore}
              gradeLabel={overallGrade.label}
              tag={overallGrade.tag}
              size={120}
            />
            <div className="min-w-0">
              <p className="truncate font-mono text-xs text-muted-foreground">
                {DEMO_AUDIT.sampleUrl}
              </p>
              <p className="mt-1 text-sm leading-snug text-foreground/85">
                Overall evaluation across 12 weighted categories.
              </p>
            </div>
          </div>

          <div className="mt-6 divide-y divide-border border-t border-border">
            {PREVIEW_CATEGORY_IDS.map((id) => {
              const category = getCategoryById(id);
              const result = getDemoCategoryResult(id);
              const grade = getGradeInfo(result.score);
              return (
                <div key={id} className="flex items-center justify-between py-2.5">
                  <span className="text-sm text-foreground/85">{category.shortName}</span>
                  <span className={`font-mono text-sm font-medium tabular-nums ${grade.textClass}`}>
                    {result.score}
                  </span>
                </div>
              );
            })}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
