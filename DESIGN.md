---
name: WebRate AI
description: A premium, paper-and-ink building-inspection report for evaluating websites — not another dark-gradient SaaS dashboard.
colors:
  paper:
    value: "oklch(0.975 0.008 85)"
  ink:
    value: "oklch(0.2 0.012 55)"
  inspector-stamp:
    value: "oklch(0.56 0.16 55)"
  stamp-ink-foreground:
    value: "oklch(0.99 0.004 85)"
  paper-shade:
    value: "oklch(0.93 0.012 80)"
  muted-ink:
    value: "oklch(0.47 0.018 60)"
  hairline-border:
    value: "oklch(0.2 0.02 60 / 14%)"
  pass-teal:
    value: "oklch(0.45 0.09 165)"
  flag-ochre:
    value: "oklch(0.56 0.16 55)"
  critical-red:
    value: "oklch(0.5 0.18 27)"
typography:
  display:
    fontFamily: "Space Grotesk, ui-sans-serif, system-ui"
    fontSize: "clamp(2.6rem, 5vw, 3.75rem)"
    fontWeight: 600
    lineHeight: 1.08
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Space Grotesk, ui-sans-serif, system-ui"
    fontSize: "clamp(1.875rem, 3vw, 2.25rem)"
    fontWeight: 600
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Space Grotesk, ui-sans-serif, system-ui"
    fontSize: "1.25rem"
    fontWeight: 600
    letterSpacing: "-0.01em"
  body:
    fontFamily: "DM Sans, ui-sans-serif, system-ui"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "IBM Plex Mono, ui-monospace, monospace"
    fontSize: "0.75rem"
    fontWeight: 500
    letterSpacing: "0.14em"
rounded:
  sm: "0.3rem"
  md: "0.4rem"
  lg: "0.5rem"
  xl: "0.6rem"
spacing:
  sm: "0.5rem"
  md: "1.5rem"
  lg: "3.5rem"
  xl: "6rem"
components:
  button-primary:
    backgroundColor: "{colors.flag-ochre}"
    textColor: "{colors.stamp-ink-foreground}"
    rounded: "{rounded.lg}"
    padding: "0 1.75rem"
    height: "3.25rem"
  button-primary-hover:
    backgroundColor: "{colors.flag-ochre}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
  card-report:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
---

# Design System: WebRate AI

## Overview

**Creative North Star: "The Inspector's Report"**

WebRate AI reads as a professional building-inspection report lying flat under desk light, not a glowing dark-mode SaaS dashboard. The ground is warm paper/card-stock (oklch ~0.975), the ink is charcoal, and one committed amber/ochre "inspector's stamp" color carries the methodology's weight: it is the primary CTA, the connecting spine between steps, the brand mark, and the "needs attention" status — never a background glow or gradient. Two further colors are reserved strictly for status (forest-teal for Pass, red for Critical) and appear nowhere else. The page explicitly refuses both the category-default centered-headline-over-equal-cards template and its flat-data-table opposite, instead rendering categories as numbered inspection line-items with varying visual weight.

The build confirms the direction contract closely: a rotated certificate-style seal (`InspectionSeal`) stands in for a results gauge, a rotated check-mark stamp (`BrandMark`) recurs beside the wordmark, categories render as hairline-divided line-items rather than uniform bordered cards, and How It Works uses a single animated vertical spine with numbered stops rather than disconnected boxes. Depth is ambient and soft (diffuse drop shadows under the seal cards), never a hard offset "sticker" shadow — this is a paper world, not a neobrutalist one.

**Key Characteristics:**
- Light paper ground, charcoal ink, one amber/ochre accent carrying ~30-45% of visual weight
- Reserved three-color status discipline: ochre = flag, teal = pass, red = critical — never decorative
- Numbered, hairline-divided line-items replace uniform bordered cards for categories and bento-grid features
- A connecting vertical spine (animated fill) unifies multi-step sequences instead of disconnected boxes
- A rotated certificate seal and a rotated check-stamp brand mark are the system's signature found-marks

## Colors

A warm, flat paper palette with one committed ink accent and two status colors used only for status.

### Primary
- **Inspector's Stamp Ochre** (`oklch(0.56 0.16 55)`): the single committed accent — primary CTA buttons, the wordmark's "AI", the connecting spine in How It Works, the brand-mark stamp, and (doubling as the "flag/needs-attention" status). Used for weight and emphasis, never background fill at scale.

### Neutral
- **Paper** (`oklch(0.975 0.008 85)`): page background and card ground — flat, not glowing.
- **Ink** (`oklch(0.2 0.012 55)`): primary text color on paper.
- **Paper Shade** (`oklch(0.93 0.012 80)`): secondary surfaces (chips, "Sample" badges, sheet nav hover).
- **Muted Ink** (`oklch(0.47 0.018 60)`): secondary/supporting text.
- **Hairline Border** (`oklch(0.2 0.02 60 / 14%)`): all dividers, grid gutters, card outlines — always a translucent ink hairline, never a solid gray stroke.

### Status (reserved — never decorative)
- **Pass Teal** (`oklch(0.45 0.09 165)`): "Excellent"/"Good" grade labels and scores only.
- **Flag Ochre** (`oklch(0.56 0.16 55)`): "Needs Attention" grade labels and scores — same value as the primary accent by design, since ochre is simultaneously the brand's committed color and its mid-tier status ink.
- **Critical Red** (`oklch(0.5 0.18 27)`): "Critical" grade labels, scores, and form validation errors only.

### Named Rules
**The Reserved Status Rule.** Pass-teal, flag-ochre, and critical-red exist in exactly one place in the system: communicating a score's grade. They are never used for unrelated decoration, even though flag-ochre happens to double as the brand accent.

**The One Accent Rule.** Ochre is the only accent carried at scale (buttons, the spine, the seal rings, the brand stamp). No second decorative accent color is introduced anywhere in the build.

## Typography

**Display Font:** Space Grotesk (with ui-sans-serif, system-ui fallback)
**Body Font:** DM Sans (with ui-sans-serif, system-ui fallback)
**Label/Mono Font:** IBM Plex Mono (with ui-monospace, monospace fallback)

**Character:** A technical-stamp display face paired with a plain, legible body sans and a monospace used exclusively where the page is reporting a measurement — scores, weights, item numbers, sample-data labels.

### Hierarchy
- **Display** (600, `clamp(2.6rem, 5vw, 3.75rem)`, line-height 1.08, tracking -0.02em): hero headline only.
- **Headline** (600, `clamp(1.875rem, 3vw, 2.25rem)`, tracking -0.02em): section titles ("The full rubric, in the open.", "Everything a thorough review covers.").
- **Title** (600, 1.25rem, tracking -0.01em): card/step/feature-cell titles.
- **Body** (400, 1rem, line-height 1.6): paragraph copy, capped around 48-65ch per block.
- **Label** (500, 0.75rem, tracking 0.14em, uppercase, IBM Plex Mono): field labels, "Sample Preview" badges, "Total weight" readouts — always mono, always wide-tracked, always small.
- **Micro-label** (500, 0.625rem–0.6875rem / 10–11px, tracking 0.08–0.1em, uppercase, IBM Plex Mono): the smallest tier — status chips, severity badges, table column headers, sidebar footnotes. Same mono-means-measured family as Label, one step down for the densest UI (dashboard tables, chips).
- **Emphasized body** (400–500, 0.9375rem / 15px, line-height 1.6, DM Sans): a half-step between Body and Label for secondary copy that needs more presence than muted caption text but isn't a heading — category summaries, issue explanations, recommendation body text.

### Named Rules
**The Mono-Means-Measured Rule.** IBM Plex Mono is reserved for anything that is a measurement or a system label read as data: scores, percentages, category numerals, sample/demo badges, step numbers. Headline and body copy never use it.

## Layout

A single centered column (`max-w-6xl`, 1.5rem/24px side padding) with sections stacked and separated by a full-width hairline top border (`border-t border-border`), each running a consistent 6rem (`py-24`) of vertical rhythm. The hero breaks to a two-column grid at `lg` (`1.05fr/0.95fr`) with the report-cover preview on the right; most other sections keep a single `max-w-2xl` intro block above a wider content region (grid, two-column list, or bento grid). Internal component padding steps through roughly 1.25rem / 1.5rem / 1.75rem / 2rem (`p-5` to `p-8`) depending on cell size — the bento-grid feature cells deliberately vary this padding by tier rather than using one fixed value everywhere.

## Elevation & Depth

Flat by default — cards and the paper background sit at the same visual plane, separated by hairline borders rather than shadow. Depth appears only around the two "object" surfaces that are meant to feel like a physical report sitting on the desk: the hero's report-cover preview card and the final-CTA card, both lifted with a soft, diffuse, large-blur ambient shadow. No hard-offset "sticker" shadow is used anywhere; that device belongs to a different (neobrutalist) world and is not part of this build.

### Shadow Vocabulary
- **Report-lift** (`box-shadow: 0 28px 60px -28px oklch(0.2 0.02 60 / 30-35%)`): used only on the hero preview card and the final-CTA card, to read as a report lifted slightly off the page.

### Named Rules
**The Flat-Desk Rule.** Everything that isn't the hero preview or the final CTA sits flat on the paper ground, divided by hairline borders. Shadow is reserved for the two moments the page wants to feel like a physical artifact.

## Shapes

Soft, moderate corner rounding throughout (`--radius: 0.5rem`, scaled down for small controls via `--radius-sm`/`-md`/`-xl`) — never sharp/square, never pill-shaped except true icon/circular controls (the seal rings, the step-number circles in How It Works, the icon-only buttons). Borders are translucent ink hairlines (`oklch(0.2 0.02 60 / 14%)`), not solid grays. The system's two signature marks are both deliberately rotated off-axis: the `InspectionSeal` certificate sits at a small counter-rotation (outer ring -3deg, inner label +3deg) and the `BrandMark` stamp sits at -8deg — this is the only place rotation is used, and it is reserved for these found-marks, never applied to generic content blocks.

## Components

### Buttons
- **Shape:** rounded-lg (0.5rem), consistent across primary/outline/secondary/ghost variants.
- **Primary:** flag-ochre background, stamp-ink-foreground text, height 3.25rem (`h-13`) for hero/CTA-weight actions, medium-weight 15px label, icon trailing (ArrowRight) when not loading.
- **Hover / Focus:** primary darkens to ~90% opacity on hover; all buttons press with a 1px translate-y on active and use a 3px focus ring at `ring-ring/50`.
- **Ghost / Outline:** transparent or bordered, used for nav-level actions ("Sign In") and the mobile sheet's secondary action.

### Cards / Containers
- **Corner Style:** rounded-lg (0.5rem).
- **Background:** paper or popover-paper (near-identical, slightly cooler for layered surfaces).
- **Shadow Strategy:** flat by default; report-lift shadow reserved for the hero preview and final-CTA cards (see Elevation & Depth).
- **Border:** translucent ink hairline (`border-foreground/12` or `border-border`) on bordered variants; borderless where internal hairline dividers already separate content (bento grid, category lists).
- **Internal Padding:** steps from 1.25rem to 2rem by content density/tier.

### Inputs / Fields
- **Style:** translucent ink-hairline border (`border-foreground/20`), popover-paper background, rounded-lg, height 3.25rem to match the adjacent primary CTA.
- **Focus:** ring treatment inherited from the shared focus-visible system (ring-ring/50).
- **Error:** inline text below the field in critical-red, tied to `aria-invalid` and `role="alert"` — never a red border-only treatment.

### Navigation
- **Style:** sticky header, transparent until scrolled past 8px then a translucent paper blur (`bg-background/92 backdrop-blur-sm`) with a hairline bottom border. Links are muted-ink text that darkens to full ink on hover; no underline, no active-state color.
- **Mobile:** a right-side sheet with the same nav links stacked, hover state swapped for a paper-shade background fill.

### Inspection Seal (signature component — landing page)
A certificate/stamp motif for an overall score: concentric rings, a rim of 48 fixed tick marks, and curved top/bottom mono-type labels ("WEBRATE INSPECTION" / "SAMPLE AUDIT"), counter-rotated for a stamped-on-paper feel. Ring and tick color is whichever status ink matches the score's grade — this is the one place status color governs an entire illustrative motif rather than a line of text. On the landing page specifically, the geometry is fixed and never a data-driven progress ring; only color and the center score/label change there.

### Score Gauge (dashboard variant)
The dashboard's product brief explicitly asked for "a circular progress indicator or gauge" for the overall score — a real, earned exception to the landing page's fixed-geometry rule above, confined to `/dashboard` surfaces. `ScoreGauge` keeps the Inspection Seal's tick-rim and curved mono labels but adds a genuine proportional arc (`stroke-dasharray`/`stroke-dashoffset` driven by the actual score), upright rather than counter-rotated, used for the dashboard's overall-score hero and each category's detail header. The landing page's `InspectionSeal` stays static and rotated; the two never swap roles.

### Brand Mark (signature component)
A small rounded-square check-stamp at -8deg rotation, flag-ochre stroke, always paired with the "WebRate" wordmark (AI set in flag-ochre). This is the system's only recurring logomark and the only rotated element outside the Inspection Seal.

## Do's and Don'ts

### Do:
- **Do** keep flag-ochre, pass-teal, and critical-red bound to status meaning only; reuse them freely for that purpose across new category/score surfaces.
- **Do** build new multi-category lists as numbered, hairline-divided line-items (varying icon/weight/underline) rather than uniform bordered cards.
- **Do** use the ambient report-lift shadow only for a surface meant to read as a lifted physical report (preview cards, the final CTA); keep everything else flat with hairline borders.
- **Do** reserve IBM Plex Mono for scores, weights, numerals, and sample/demo labels — never headline or body copy.

### Don't:
- **Don't** introduce a second decorative accent color; ochre is the system's only committed accent.
- **Don't** add hard-offset "sticker" shadows or heavy outlined borders — this is a soft-paper world, not a neobrutalist one, and the build never uses that device.
- **Don't** repeat identical bordered card tiles for feature or category lists; the shipped bento grid and line-item patterns deliberately vary padding, icon size, and weight by tier instead.
- **Don't** apply the seal/brand-mark's off-axis rotation to ordinary content blocks; rotation is reserved for the two signature found-marks.
