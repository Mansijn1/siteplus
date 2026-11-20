import { EVALUATION_CATEGORIES, type CategoryId } from "./categories";
import { getGradeInfo, type CategoryScores } from "./scoring";
import {
  AUDIT_STATUS,
  DEMO_WEBSITE_URL,
  EVALUATION_SUMMARY,
  OVERALL_SCORE,
  DEMO_SCORES,
  SEVERITY_ORDER,
  type CategoryAnalysis,
  type CategoryIssue,
  type CategoryRecommendation,
  type Severity,
  getCategoryAnalysis as getDemoCategoryAnalysis,
} from "@/data/demo-results";
import type { BackendEvaluationResult, Priority, Effort } from "./evaluation-api";

/**
 * A superset of the existing demo `CategoryIssue`/`CategoryRecommendation` shapes — every field
 * the current components already render, plus the richer fields the Phase 3 spec explicitly
 * asks to be shown (priority, affected URL, estimated effort). Demo data simply omits the
 * extra fields; real data populates them. Components render the extras only when present, so
 * neither data source needs a special case in the JSX beyond an optional check.
 */
export interface AdaptedIssue extends CategoryIssue {
  issueId?: string;
  priority?: Priority;
  affectedUrl?: string;
}

export interface AdaptedRecommendation extends CategoryRecommendation {
  issueId?: string;
  priority?: Priority;
  estimatedEffort?: Effort;
  affectedUrl?: string;
}

export interface AdaptedCategoryAnalysis extends Omit<CategoryAnalysis, "issues" | "recommendations"> {
  issues: AdaptedIssue[];
  recommendations: AdaptedRecommendation[];
  checksAvailableCount?: number;
  checksUnavailableCount?: number;
}

export interface FlatIssue extends AdaptedIssue {
  categoryId: CategoryId;
  categoryName: string;
}

export interface FlatRecommendation extends AdaptedRecommendation {
  categoryId: CategoryId;
  categoryName: string;
  categoryWeight: number;
  /** The severity of the specific issue this recommendation addresses — required by
   * RecommendationCard. Paired by issueId for real data, by array index for demo data
   * (matching how demo-results.ts's own authored issues/recommendations are paired). */
  topSeverity: Severity;
}

/** The single interface every dashboard page/component reads through — demo and real data are
 * both just implementations of this, so no component needs to know which one it's looking at. */
export interface EvaluationDataSource {
  isReal: boolean;
  websiteUrl: string;
  overallScore: number;
  scoreCoveragePercent: number | null;
  grade: string;
  auditStatus: string;
  summary: string;
  scores: CategoryScores;
  totalChecks: number;
  passedChecks: number;
  failedChecks: number;
  unavailableChecks: number;
  getCategoryAnalysis(id: CategoryId): AdaptedCategoryAnalysis;
  getAllIssues(): FlatIssue[];
  getAllRecommendationsRanked(): FlatRecommendation[];
}

const SEVERITY_RANK: Record<Severity, number> = { critical: 0, high: 1, medium: 2, low: 3 };
const PRIORITY_RANK: Record<Priority, number> = { P0: 0, P1: 1, P2: 2, P3: 3 };

export function getDemoDataSource(): EvaluationDataSource {
  return {
    isReal: false,
    websiteUrl: DEMO_WEBSITE_URL,
    overallScore: OVERALL_SCORE,
    scoreCoveragePercent: 100,
    grade: getGradeInfo(OVERALL_SCORE).label,
    auditStatus: AUDIT_STATUS,
    summary: EVALUATION_SUMMARY,
    scores: DEMO_SCORES,
    totalChecks: 0,
    passedChecks: 0,
    failedChecks: 0,
    unavailableChecks: 0,
    getCategoryAnalysis: (id) => getDemoCategoryAnalysis(id),
    getAllIssues: () =>
      EVALUATION_CATEGORIES.flatMap((category) =>
        getDemoCategoryAnalysis(category.id).issues.map((issue) => ({
          ...issue,
          categoryId: category.id,
          categoryName: category.name,
        })),
      ),
    getAllRecommendationsRanked: () =>
      EVALUATION_CATEGORIES.flatMap((category) => {
        const analysis = getDemoCategoryAnalysis(category.id);
        return analysis.recommendations.map((rec, index) => ({
          ...rec,
          categoryId: category.id,
          categoryName: category.name,
          categoryWeight: category.weight,
          topSeverity: analysis.issues[index]?.severity ?? "low",
        }));
      }).sort((a, b) => {
        const diff = SEVERITY_RANK[a.topSeverity] - SEVERITY_RANK[b.topSeverity];
        if (diff !== 0) return diff;
        return b.categoryWeight - a.categoryWeight;
      }),
  };
}

export function adaptEvaluation(evaluation: BackendEvaluationResult): EvaluationDataSource {
  const scores: CategoryScores = {};
  for (const [categoryId, result] of Object.entries(evaluation.categories)) {
    if (result.score !== null) scores[categoryId as CategoryId] = result.score;
  }

  const overallScore = evaluation.overall_score ?? 0;
  const grade = evaluation.grade ?? getGradeInfo(overallScore).label;

  function severityForIssueId(categoryId: CategoryId, issueId: string | undefined): Severity {
    const result = evaluation.categories[categoryId];
    const issue = result?.issues.find((i) => i.issue_id === issueId);
    return (issue?.severity as Severity) ?? "low";
  }

  function getCategoryAnalysis(id: CategoryId): AdaptedCategoryAnalysis {
    const result = evaluation.categories[id];
    if (!result) {
      return { categoryId: id, summary: "No evaluation data for this category.", whatWasEvaluated: [], positives: [], issues: [], recommendations: [] };
    }
    return {
      categoryId: id,
      summary: result.summary,
      whatWasEvaluated: result.checks.map((c) => c.label),
      positives: result.checks.filter((c) => c.status === "passed").map((c) => c.label),
      checksAvailableCount: result.passed_count + result.failed_count,
      checksUnavailableCount: result.unavailable_count,
      issues: result.issues.map((issue) => ({
        title: issue.title,
        explanation: issue.description,
        severity: issue.severity as Severity,
        impact: issue.impact,
        issueId: issue.issue_id,
        priority: issue.priority,
        affectedUrl: issue.affected_url,
      })),
      recommendations: result.recommendations.map((rec) => ({
        title: rec.title,
        why: rec.why_it_matters,
        how: rec.how_to_fix.join(" "),
        expectedImpact: rec.expected_benefit,
        issueId: rec.issue_id,
        priority: rec.priority,
        estimatedEffort: rec.estimated_effort,
        affectedUrl: rec.affected_url,
      })),
    };
  }

  function getAllIssues(): FlatIssue[] {
    return EVALUATION_CATEGORIES.flatMap((category) => {
      const analysis = getCategoryAnalysis(category.id);
      return analysis.issues.map((issue) => ({ ...issue, categoryId: category.id, categoryName: category.name }));
    }).sort((a, b) => SEVERITY_RANK[a.severity] - SEVERITY_RANK[b.severity]);
  }

  function getAllRecommendationsRanked(): FlatRecommendation[] {
    return EVALUATION_CATEGORIES.flatMap((category) => {
      const analysis = getCategoryAnalysis(category.id);
      return analysis.recommendations.map((rec) => ({
        ...rec,
        categoryId: category.id,
        categoryName: category.name,
        categoryWeight: category.weight,
        topSeverity: severityForIssueId(category.id, rec.issueId),
      }));
    }).sort((a, b) => {
      const severityDiff = SEVERITY_RANK[a.topSeverity] - SEVERITY_RANK[b.topSeverity];
      if (severityDiff !== 0) return severityDiff;
      const rankA = a.priority ? PRIORITY_RANK[a.priority] : 3;
      const rankB = b.priority ? PRIORITY_RANK[b.priority] : 3;
      if (rankA !== rankB) return rankA - rankB;
      return b.categoryWeight - a.categoryWeight;
    });
  }

  return {
    isReal: true,
    websiteUrl: evaluation.submitted_url,
    overallScore,
    scoreCoveragePercent: evaluation.score_coverage_percent,
    grade,
    auditStatus: evaluation.status === "completed" ? "Completed" : "Failed",
    summary:
      evaluation.score_coverage_percent !== null && evaluation.score_coverage_percent < 100
        ? `Based on ${evaluation.score_coverage_percent}% of the full rubric — some categories had no automatable evidence available for this scan.`
        : "A complete, evidence-based evaluation across all 12 weighted categories.",
    scores,
    totalChecks: evaluation.total_checks,
    passedChecks: evaluation.passed_checks,
    failedChecks: evaluation.failed_checks,
    unavailableChecks: evaluation.unavailable_checks,
    getCategoryAnalysis,
    getAllIssues,
    getAllRecommendationsRanked,
  };
}

export { SEVERITY_ORDER };
export type { Severity };
