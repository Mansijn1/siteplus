import { EVALUATION_CATEGORIES, TOTAL_WEIGHT, type CategoryId } from "./categories";

export type Grade = "excellent" | "good" | "needs-work" | "poor";
export type StatusTag = "pass" | "flag" | "critical";
export type CategoryScores = Partial<Record<CategoryId, number>>;

export interface GradeInfo {
  grade: Grade;
  label: string;
  /** One of the three reserved status inks — pass, flag, critical. Never decorative. */
  tag: StatusTag;
  textClass: string;
  bgClass: string;
}

const GRADE_THRESHOLDS: { min: number; info: GradeInfo }[] = [
  {
    min: 90,
    info: {
      grade: "excellent",
      label: "Excellent",
      tag: "pass",
      textClass: "text-pass",
      bgClass: "bg-pass",
    },
  },
  {
    min: 75,
    info: {
      grade: "good",
      label: "Good",
      tag: "pass",
      textClass: "text-pass",
      bgClass: "bg-pass",
    },
  },
  {
    min: 60,
    info: {
      grade: "needs-work",
      label: "Needs Attention",
      tag: "flag",
      textClass: "text-flag",
      bgClass: "bg-flag",
    },
  },
  {
    min: 0,
    info: {
      grade: "poor",
      label: "Critical",
      tag: "critical",
      textClass: "text-critical",
      bgClass: "bg-critical",
    },
  },
];

/** Deterministic grade lookup for a 0-100 score. Never randomized. */
export function getGradeInfo(score: number): GradeInfo {
  const clamped = Math.max(0, Math.min(100, score));
  const match = GRADE_THRESHOLDS.find((t) => clamped >= t.min);
  return match ? match.info : GRADE_THRESHOLDS[GRADE_THRESHOLDS.length - 1].info;
}

if (process.env.NODE_ENV !== "production" && TOTAL_WEIGHT !== 100) {
  console.error(
    `[scoring] Category weights sum to ${TOTAL_WEIGHT}, expected 100. Fix src/lib/categories.ts.`,
  );
}

/** Clamps a score into the valid 0-100 range; missing or invalid scores count as 0. */
function safeScore(score: number | undefined): number {
  if (typeof score !== "number" || Number.isNaN(score)) return 0;
  return Math.max(0, Math.min(100, score));
}

/**
 * Overall Score = Sum(Category Score x Category Weight) / 100
 *
 * This is the ONLY place the overall score is computed. No surface may
 * hardcode an overall score independently of this function.
 */
export function calculateOverallScore(scores: CategoryScores): number {
  const total = EVALUATION_CATEGORIES.reduce(
    (sum, category) => sum + (safeScore(scores[category.id]) * category.weight) / 100,
    0,
  );
  return Math.round(total * 100) / 100;
}

export function validateCategoryWeights(): boolean {
  return TOTAL_WEIGHT === 100;
}
