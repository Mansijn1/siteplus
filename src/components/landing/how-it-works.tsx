"use client";

import { motion } from "framer-motion";

const STEPS = [
  {
    number: "01",
    title: "Enter Your Website",
    description: "Add your website URL.",
  },
  {
    number: "02",
    title: "Comprehensive Evaluation",
    description: "Explore the evaluation across 12 categories.",
  },
  {
    number: "03",
    title: "Discover Improvements",
    description: "Understand issues and recommendations.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="border-t border-border py-24">
      <div className="mx-auto max-w-6xl px-6">
        <div className="max-w-2xl">
          <h2 className="font-display text-3xl font-semibold tracking-[-0.02em] sm:text-4xl">
            One inspection, three stops.
          </h2>
          <p className="mt-4 text-lg leading-relaxed text-muted-foreground">
            From URL to ranked recommendations — the route every evaluation
            follows.
          </p>
        </div>

        <div className="relative mt-16 max-w-2xl pl-[52px]">
          <div className="absolute left-[21px] top-2 h-[calc(100%-1rem)] w-px bg-border" aria-hidden="true">
            <motion.div
              initial={{ scaleY: 0 }}
              whileInView={{ scaleY: 1 }}
              viewport={{ once: true, amount: 0.3 }}
              transition={{ duration: 1.1, ease: [0.16, 1, 0.3, 1] }}
              style={{ transformOrigin: "top" }}
              className="h-full w-full bg-flag"
            />
          </div>

          <div className="flex flex-col gap-14">
            {STEPS.map((step, index) => (
              <motion.div
                key={step.number}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.6 }}
                transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1], delay: index * 0.08 }}
                className="relative"
              >
                <span className="absolute -left-[52px] top-0 flex size-[42px] items-center justify-center rounded-full border border-flag/40 bg-background font-mono text-sm font-medium text-flag">
                  {step.number}
                </span>
                <h3 className="font-display text-xl font-semibold tracking-[-0.01em]">
                  {step.title}
                </h3>
                <p className="mt-1.5 text-[15px] text-muted-foreground">{step.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
