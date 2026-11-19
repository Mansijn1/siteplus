import {
  LayoutGrid,
  Palette,
  Compass,
  Gauge,
  Search,
  Accessibility,
  Smartphone,
  ShieldCheck,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

export interface PlatformFeature {
  id: string;
  title: string;
  description: string;
  icon: LucideIcon;
  /** Controls the bento-grid sizing in the features section. */
  size: "lg" | "md" | "sm";
}

/**
 * Marketing copy for the Features section. Distinct from the 12
 * evaluation categories in `categories.ts` — this is a shorter,
 * promotional list describing platform capabilities.
 *
 * Order matters: on the 6-column bento grid in features.tsx, each
 * consecutive run's spans must sum to 6 so rows tile without gaps.
 * Row plan: [4,2] [2,2,2] [3,3] [2,4].
 */
export const PLATFORM_FEATURES: PlatformFeature[] = [
  {
    id: "complete-evaluation",
    title: "Complete Website Evaluation",
    description:
      "Twelve weighted categories combine into one clear, comprehensive score for your entire site.",
    icon: LayoutGrid,
    size: "lg",
  },
  {
    id: "performance",
    title: "Performance Evaluation",
    description: "Load speed and responsiveness under real-world conditions.",
    icon: Gauge,
    size: "sm",
  },
  {
    id: "ui-visual-design",
    title: "UI & Visual Design Analysis",
    description: "Typography, spacing, color, and layout benchmarked against modern standards.",
    icon: Palette,
    size: "md",
  },
  {
    id: "ux-navigation",
    title: "UX & Navigation Review",
    description: "How intuitively visitors find what they need and move through your site.",
    icon: Compass,
    size: "md",
  },
  {
    id: "seo",
    title: "SEO Analysis",
    description: "On-page structure and discoverability signals search engines rely on.",
    icon: Search,
    size: "md",
  },
  {
    id: "security-privacy",
    title: "Security & Privacy Review",
    description: "Transport security and privacy practices worth your attention.",
    icon: ShieldCheck,
    size: "md",
  },
  {
    id: "accessibility",
    title: "Accessibility Evaluation",
    description: "Contrast, semantics, and keyboard support against WCAG-aligned practices.",
    icon: Accessibility,
    size: "md",
  },
  {
    id: "mobile-responsiveness",
    title: "Mobile Responsiveness",
    description: "Layouts, touch targets, and readability across phones and tablets.",
    icon: Smartphone,
    size: "sm",
  },
  {
    id: "ai-recommendations",
    title: "AI-Powered Recommendations",
    description:
      "Prioritized, plain-language guidance generated from every category in your evaluation.",
    icon: Sparkles,
    size: "lg",
  },
];
