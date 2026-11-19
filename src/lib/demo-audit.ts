import { CategoryId, getCategoryById } from "./categories";
import {
  DEMO_SCORES,
  CATEGORY_ANALYSIS,
  OVERALL_SCORE,
  EVALUATION_SUMMARY,
  DEMO_WEBSITE_URL,
  getTopRecommendations,
} from "@/data/demo-results";

export interface DemoCategoryResult {
  categoryId: CategoryId;
  score: number;
  summary: string;
}

/**
 * Landing-page preview of the same canonical demo audit used by the
 * dashboard and scanning page (src/data/demo-results.ts). This is DEMO
 * DATA ONLY — fixed constants, never randomized on render.
 */
export const DEMO_AUDIT = {
  sampleUrl: DEMO_WEBSITE_URL.replace(/^https?:\/\//, ""),
  overallScore: OVERALL_SCORE,
  isDemo: true as const,
  summary: EVALUATION_SUMMARY,
  topRecommendations: getTopRecommendations(3).map((rec) => rec.title),
};

export function getDemoCategoryResult(categoryId: CategoryId): DemoCategoryResult {
  return {
    categoryId,
    score: DEMO_SCORES[categoryId] ?? 0,
    summary: CATEGORY_ANALYSIS[categoryId].summary,
  };
}

export function getDemoCategoryWithMeta(categoryId: CategoryId) {
  return { category: getCategoryById(categoryId), result: getDemoCategoryResult(categoryId) };
}
