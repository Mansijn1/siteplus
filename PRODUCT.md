# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Next.js (App Router) + TypeScript + Tailwind CSS v4 + shadcn/ui + Framer Motion. User-selected explicitly over a lighter Vite/React or plain-React alternative.

## Users

Primary users are website owners, marketers, and small-business/product teams who want an outside, structured read on how their website is actually performing — not just "is it broken" but "where does it rank across the things that matter, and what should I fix first." They arrive already owning a live URL and want a fast, credible-feeling first impression before committing to deeper action.

## Product Purpose

WebRate AI evaluates a submitted website URL across 12 strictly-weighted categories — UI & Visual Design (12%), UX & Navigation (12%), Performance (12%), SEO (10%), Accessibility (10%), Mobile Responsiveness (10%), Security & Privacy (8%), Content Quality (7%), Conversion (7%), Trust & Credibility (5%), Technical Quality (5%), Innovation (2%) — and returns one overall score (`Sum(score x weight)/100`, always computed, never hardcoded) plus category-level findings and recommendations. Success means a visitor understands the evaluation model on the landing page, trusts its rigor, and can explore a complete sample evaluation in the dashboard.

## Positioning

Most website grading tools either run one narrow check (e.g. just performance or just SEO) or bury results behind a paywall-gated single score. WebRate AI's mechanism is the breadth and transparency of the rubric itself: 12 named, weighted categories a visitor can see before they even submit a URL, so the evaluation reads as a methodology, not a black box.

## Operating Context

This phase is frontend-only: no backend, no database, no real scanning API. All dashboard/report content is fixed sample data, explicitly labeled as a demo/preview. The 12 category names and their weights are defined once in a shared config (`src/lib/categories.ts`) and must not be redefined or hardcoded elsewhere. Build scope now covers both the marketing landing page (hero, product preview, features, how-it-works, evaluation-category breakdown, final CTA, footer) and the full evaluation dashboard (Overview, Website Evaluation table, Category Analysis, Recommendations, with Reports and Settings as polished placeholders) at `/dashboard`. A live scanning animation and real backend integration remain out of scope.

## Capabilities and Constraints

- URL input must validate: non-empty, http/https only, normalized safely (protocol defaulted to https when omitted), with understandable inline errors for malformed input.
- Entered URL is held in frontend/session state and used to continue the flow; no network request is made against it.
- No per-render random scoring anywhere — all sample scores are fixed constants.
- Constraint explicitly set by the requester: do not change evaluation category names or weights once defined.
- Overall score is always `calculateOverallScore()` in `src/lib/scoring-engine.ts` (`Sum(score x weight)/100`) — never a second hardcoded number. On the canonical demo scores this correctly computes 84.08; the original request's worked example stated 84.19, which does not match its own stated inputs under the stated formula, so the engine's correct output is authoritative.

## Brand Commitments

Name: WebRate AI. Primary headline: "Your Website. Evaluated From Every Angle." Quality bar explicitly named by the requester: Linear, Stripe, Vercel, and premium analytics platforms. Explicit anti-goals: generic AI-template look, excessive text, overuse of gradient backgrounds, repetitive identical card grids, unnecessary decoration, oversized empty space.

## Evidence on Hand

No real customer logos, testimonials, benchmarks, or pricing exist yet. Any proof-style content on the landing page must be either a clearly labeled sample/demo audit, or structural/methodological (e.g., showing the rubric itself) rather than a fabricated claim, testimonial, or statistic.

## Product Principles

- Breadth with structure: twelve named categories, visible and consistent everywhere they appear, are the product's credibility mechanism — never collapse or hide them.
- Demo data tells the truth about itself: every sample score or preview is clearly labeled as sample/demo, never presented as a real result.
- One rubric, one config: category names, weights, and grading thresholds live in one shared module; every surface reads from it rather than restating it.
- Momentum over friction: the only required input to start is a URL; validation explains itself in plain language rather than blocking silently.

## Accessibility & Inclusion

No product-specific accessibility requirement was stated beyond general best practice; build to standard WCAG-aligned practices (contrast, semantic structure, keyboard support) since the product itself evaluates other sites on exactly this category.
