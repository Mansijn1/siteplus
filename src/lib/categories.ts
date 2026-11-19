import {
  Palette,
  Compass,
  Gauge,
  Search,
  Accessibility,
  Smartphone,
  ShieldCheck,
  FileText,
  MousePointerClick,
  BadgeCheck,
  Code2,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

export type CategoryId =
  | "ui"
  | "ux"
  | "performance"
  | "seo"
  | "accessibility"
  | "mobile"
  | "security"
  | "content"
  | "conversion"
  | "trust"
  | "technical"
  | "innovation";

export interface EvaluationCategory {
  id: CategoryId;
  /** Exact required category name — never redefine or rename this per-component. */
  name: string;
  /** Compact label for dense UI (tables, chips). Never used where the full `name` is required. */
  shortName: string;
  weight: number;
  icon: LucideIcon;
  description: string;
}

/**
 * Single source of truth for all 12 WebRate AI evaluation categories.
 * This exact list of 12 names and weights is a strict product requirement —
 * weights must always sum to 100, and no component may redefine, rename,
 * add, or remove a category. Every surface (landing page and dashboard)
 * reads from here.
 */
export const EVALUATION_CATEGORIES: EvaluationCategory[] = [
  {
    id: "ui",
    name: "UI & Visual Design",
    shortName: "UI & Visual Design",
    weight: 12,
    icon: Palette,
    description: "Visual hierarchy, typography, and layout quality.",
  },
  {
    id: "ux",
    name: "UX & Navigation",
    shortName: "UX & Navigation",
    weight: 12,
    icon: Compass,
    description: "Information architecture and ease of navigation.",
  },
  {
    id: "performance",
    name: "Performance",
    shortName: "Performance",
    weight: 12,
    icon: Gauge,
    description: "Load speed, responsiveness, and runtime efficiency.",
  },
  {
    id: "seo",
    name: "SEO",
    shortName: "SEO",
    weight: 10,
    icon: Search,
    description: "Discoverability, metadata, and search-readiness.",
  },
  {
    id: "accessibility",
    name: "Accessibility",
    shortName: "Accessibility",
    weight: 10,
    icon: Accessibility,
    description: "Usability for people of all abilities.",
  },
  {
    id: "mobile",
    name: "Mobile Responsiveness",
    shortName: "Mobile",
    weight: 10,
    icon: Smartphone,
    description: "Behavior and layout across devices and screen sizes.",
  },
  {
    id: "security",
    name: "Security & Privacy",
    shortName: "Security",
    weight: 8,
    icon: ShieldCheck,
    description: "Transport security, privacy posture, and safe practices.",
  },
  {
    id: "content",
    name: "Content Quality",
    shortName: "Content",
    weight: 7,
    icon: FileText,
    description: "Clarity, tone, and effectiveness of on-site content.",
  },
  {
    id: "conversion",
    name: "Conversion",
    shortName: "Conversion",
    weight: 7,
    icon: MousePointerClick,
    description: "Clarity and placement of calls-to-action.",
  },
  {
    id: "trust",
    name: "Trust & Credibility",
    shortName: "Trust",
    weight: 5,
    icon: BadgeCheck,
    description: "Signals that build visitor confidence.",
  },
  {
    id: "technical",
    name: "Technical Quality",
    shortName: "Technical",
    weight: 5,
    icon: Code2,
    description: "Code quality, errors, and technical best practices.",
  },
  {
    id: "innovation",
    name: "Innovation",
    shortName: "Innovation",
    weight: 2,
    icon: Sparkles,
    description: "Distinctive, modern use of the web platform.",
  },
];

export const TOTAL_WEIGHT = EVALUATION_CATEGORIES.reduce(
  (sum, category) => sum + category.weight,
  0,
);

export function getCategoryById(id: CategoryId): EvaluationCategory {
  const category = EVALUATION_CATEGORIES.find((c) => c.id === id);
  if (!category) {
    throw new Error(`Unknown evaluation category id: ${id}`);
  }
  return category;
}
