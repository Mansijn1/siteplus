import { EVALUATION_CATEGORIES, getCategoryById, type CategoryId } from "@/lib/categories";
import { calculateOverallScore, type CategoryScores } from "@/lib/scoring";

/**
 * The single demo dataset for the whole application — landing page preview,
 * scanning page, dashboard, and category analysis all read from this file.
 * Every value here is a fixed constant. Nothing is randomized on render,
 * and nothing duplicates this data in a second hardcoded array.
 */

export const DEMO_WEBSITE_URL = "https://www.example-store.com";
export const AUDIT_STATUS = "Completed" as const;

/** Fixed demo scores, matching the example table in the product brief. */
export const DEMO_SCORES: CategoryScores = {
  ui: 90,
  ux: 85,
  performance: 78,
  seo: 88,
  accessibility: 72,
  mobile: 91,
  security: 95,
  content: 80,
  conversion: 76,
  trust: 84,
  technical: 82,
  innovation: 90,
};

/** The one and only computed overall score — never a separate hardcoded number. */
export const OVERALL_SCORE = calculateOverallScore(DEMO_SCORES);

export const EVALUATION_SUMMARY =
  "Your website demonstrates strong visual design and security practices, with opportunities to improve performance, accessibility and conversion experience.";

export type Severity = "critical" | "high" | "medium" | "low";

export interface CategoryIssue {
  title: string;
  explanation: string;
  severity: Severity;
  impact: string;
}

export interface CategoryRecommendation {
  title: string;
  why: string;
  how: string;
  expectedImpact: string;
}

export interface CategoryAnalysis {
  categoryId: CategoryId;
  summary: string;
  whatWasEvaluated: string[];
  positives: string[];
  issues: CategoryIssue[];
  recommendations: CategoryRecommendation[];
}

export const SEVERITY_ORDER: Severity[] = ["critical", "high", "medium", "low"];

export const SEVERITY_LABEL: Record<Severity, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
};

/**
 * Realistic, hand-authored demo analysis for all 12 categories. Each
 * category's content is specific to that category and consistent with
 * its demo score above — never a generic template repeated across
 * categories.
 */
export const CATEGORY_ANALYSIS: Record<CategoryId, CategoryAnalysis> = {
  ui: {
    categoryId: "ui",
    summary:
      "Strong, consistent visual system — clear hierarchy and a disciplined color and type system carry the site well, with only minor polish items remaining.",
    whatWasEvaluated: [
      "Visual hierarchy and layout composition",
      "Typography scale and readability",
      "Color system and contrast usage",
      "Spacing and alignment consistency",
      "Iconography and imagery quality",
      "Brand consistency across pages",
    ],
    positives: [
      "Clear, consistent typographic scale across all pages",
      "Cohesive color palette reinforces brand identity",
      "Generous, intentional whitespace improves scanability",
      "Icon set is consistent in style and weight throughout",
    ],
    issues: [
      {
        title: "Inconsistent card spacing on secondary pages",
        explanation:
          "Padding inside content cards varies by roughly 4-8px between the pricing and resources pages, breaking the otherwise tight spacing rhythm.",
        severity: "low",
        impact: "Minor visual inconsistency noticeable to design-conscious visitors; unlikely to affect conversion.",
      },
    ],
    recommendations: [
      {
        title: "Standardize card padding into a shared component",
        why: "Two pages currently hand-roll their own card spacing, which drifts over time as new sections are added.",
        how: "Extract a shared Card primitive with fixed padding tokens and migrate both pages to use it.",
        expectedImpact: "Small visual polish gain; mainly reduces future design drift.",
      },
    ],
  },

  ux: {
    categoryId: "ux",
    summary:
      "Navigation is clear and predictable, with a logical information architecture; a few deeper flows ask users to take more steps than necessary.",
    whatWasEvaluated: [
      "Primary and secondary navigation structure",
      "Information architecture and page depth",
      "Search and findability",
      "User flow efficiency for key tasks",
      "Breadcrumb and wayfinding support",
      "Mobile navigation patterns",
    ],
    positives: [
      "Primary navigation covers all major sections without overflow",
      "Consistent placement of back/cancel actions across flows",
      "Clear labeling avoids jargon in menu items",
    ],
    issues: [
      {
        title: "Checkout flow requires 5 steps where 3 would suffice",
        explanation:
          "Shipping, billing, and review are split across separate pages with full reloads, rather than a combined or single-page flow.",
        severity: "medium",
        impact: "Adds friction and drop-off risk during the highest-intent part of the journey.",
      },
      {
        title: "No breadcrumb trail on deep category pages",
        explanation:
          "Pages three levels deep into the catalog don't show how the user got there or how to go up a level besides the browser back button.",
        severity: "low",
        impact: "Slightly harder orientation for users arriving from search or deep links.",
      },
    ],
    recommendations: [
      {
        title: "Consolidate checkout into fewer steps",
        why: "Each additional step in checkout correlates with measurable cart abandonment in e-commerce benchmarks.",
        how: "Combine shipping and billing into one page with inline validation, and keep order review as the final confirmation step.",
        expectedImpact: "Likely reduction in checkout abandonment; faster path to purchase.",
      },
      {
        title: "Add breadcrumb navigation to deep pages",
        why: "Users landing from search rarely start at the homepage and need a way to understand their location in the site.",
        how: "Add a simple breadcrumb component above the page title on any page nested two or more levels deep.",
        expectedImpact: "Improves orientation and encourages exploration of sibling categories.",
      },
    ],
  },

  performance: {
    categoryId: "performance",
    summary:
      "Core pages are usable but slower than ideal on first load, mainly due to unoptimized images and render-blocking scripts above the fold.",
    whatWasEvaluated: [
      "Largest Contentful Paint (LCP)",
      "Time to Interactive (TTI)",
      "Total page weight and image optimization",
      "Render-blocking resources",
      "Caching and compression headers",
      "Third-party script impact",
    ],
    positives: [
      "Static assets are served with long-lived cache headers",
      "Text compression (gzip/brotli) is enabled site-wide",
      "Core pages use modern image formats on the homepage",
    ],
    issues: [
      {
        title: "Largest Contentful Paint exceeds 3.5s on mobile",
        explanation:
          "The hero image on the homepage loads at full resolution before being resized by the browser, delaying the LCP element.",
        severity: "high",
        impact: "Slower perceived load directly correlates with higher bounce rate on mobile traffic.",
      },
      {
        title: "Render-blocking third-party scripts in the <head>",
        explanation:
          "Two analytics scripts load synchronously before the page can paint, adding roughly 400ms of blocking time.",
        severity: "medium",
        impact: "Delays first paint across all pages, compounding the LCP issue.",
      },
      {
        title: "Unoptimized product images on category pages",
        explanation:
          "Several product thumbnails are served at 2-4x their displayed size with no responsive srcset.",
        severity: "medium",
        impact: "Increases page weight and slows loading on slower connections.",
      },
    ],
    recommendations: [
      {
        title: "Serve correctly-sized, modern-format hero images",
        why: "The hero image is the LCP element on the homepage and is currently oversized for its display size.",
        how: "Generate responsive srcset variants in WebP/AVIF and size the hero image to its actual rendered dimensions.",
        expectedImpact: "Meaningful LCP improvement on both desktop and mobile homepage loads.",
      },
      {
        title: "Defer non-critical third-party scripts",
        why: "Analytics and marketing scripts don't need to block the initial render.",
        how: "Load them with async/defer, or after the page's load event, instead of synchronously in the head.",
        expectedImpact: "Faster first paint across every page that includes these scripts.",
      },
      {
        title: "Add responsive image sizing to the product catalog",
        why: "Thumbnails are currently one-size-fits-all regardless of viewport or grid density.",
        how: "Use a responsive srcset/sizes setup so the browser requests an appropriately sized image per breakpoint.",
        expectedImpact: "Reduces average category-page weight and improves load time on mobile.",
      },
    ],
  },

  seo: {
    categoryId: "seo",
    summary:
      "Strong technical and on-page SEO foundation; a handful of pages are missing metadata that would improve their search presentation.",
    whatWasEvaluated: [
      "Title tags and meta descriptions",
      "Heading structure and semantic HTML",
      "Structured data / schema markup",
      "XML sitemap and robots.txt configuration",
      "Internal linking structure",
      "Canonical URL handling",
    ],
    positives: [
      "Clean, descriptive URL structure across the site",
      "Structured data present for product and organization pages",
      "Sitemap is up to date and correctly referenced in robots.txt",
      "Heading hierarchy is semantically correct on most templates",
    ],
    issues: [
      {
        title: "Missing meta descriptions on blog archive pages",
        explanation:
          "Category and tag archive pages for the blog have no meta description, so search engines generate their own snippet.",
        severity: "low",
        impact: "Reduces control over how these pages appear in search results, potentially lowering click-through rate.",
      },
      {
        title: "Duplicate title tags across filtered product views",
        explanation:
          "Filtered/sorted variations of category pages (by price, by color) share an identical title tag with the base category page.",
        severity: "medium",
        impact: "Can create duplicate-content ambiguity for search engines and dilute ranking signals.",
      },
    ],
    recommendations: [
      {
        title: "Add unique meta descriptions to archive templates",
        why: "These pages currently rely on search engines to auto-generate snippets, which are often less compelling.",
        how: "Generate a templated but dynamic meta description that includes the category/tag name and post count.",
        expectedImpact: "Improved click-through rate from search results for blog content.",
      },
      {
        title: "Canonicalize filtered product view URLs",
        why: "Filter/sort parameters create many near-duplicate URLs competing for the same keywords.",
        how: "Add a canonical tag on filtered views pointing back to the base category URL.",
        expectedImpact: "Consolidates ranking signals onto the primary category page instead of splitting them.",
      },
    ],
  },

  accessibility: {
    categoryId: "accessibility",
    summary:
      "Several contrast and keyboard-navigation gaps would make the site difficult to use for visitors relying on assistive technology.",
    whatWasEvaluated: [
      "Color contrast ratios for text and UI elements",
      "Keyboard navigation and focus order",
      "Alt text coverage for images",
      "Form label and error association",
      "ARIA roles and semantic landmarks",
      "Screen reader compatibility of interactive components",
    ],
    positives: [
      "Semantic HTML landmarks (header, nav, main, footer) are used correctly",
      "Most form fields have properly associated labels",
    ],
    issues: [
      {
        title: "Secondary text fails WCAG AA contrast",
        explanation:
          "Muted gray text used for captions and metadata measures roughly 3.1:1 against its background, below the 4.5:1 minimum for body text.",
        severity: "high",
        impact: "Makes secondary content difficult or impossible to read for users with low vision.",
      },
      {
        title: "Custom dropdown menu is not keyboard-operable",
        explanation:
          "The account menu in the header opens on click but cannot be opened, navigated, or closed using only the keyboard.",
        severity: "critical",
        impact: "Blocks keyboard-only and screen-reader users from accessing account functions entirely.",
      },
      {
        title: "Product images missing descriptive alt text",
        explanation:
          "Roughly a third of product images use the filename as alt text instead of a description of the product.",
        severity: "medium",
        impact: "Screen reader users can't identify products without descriptive alt text.",
      },
    ],
    recommendations: [
      {
        title: "Raise secondary text contrast to meet WCAG AA",
        why: "Current muted text color falls below the minimum readable contrast ratio.",
        how: "Darken the muted text color token until it measures at least 4.5:1 against its background.",
        expectedImpact: "Makes secondary content readable for low-vision users and clears an automated accessibility audit flag.",
      },
      {
        title: "Make the account dropdown fully keyboard-operable",
        why: "Currently only mouse users can access account settings and logout.",
        how: "Add keyboard handlers (Enter/Space to open, Arrow keys to navigate, Escape to close) following standard disclosure-menu patterns.",
        expectedImpact: "Unblocks a core account function for keyboard and screen-reader users.",
      },
      {
        title: "Write descriptive alt text for all product images",
        why: "Filename-based alt text provides no useful information to assistive technology.",
        how: "Add a required alt-text field to the product content model, pre-filled with product name and key attribute.",
        expectedImpact: "Makes the product catalog navigable by screen reader users and improves image SEO.",
      },
    ],
  },

  mobile: {
    categoryId: "mobile",
    summary:
      "Layouts adapt cleanly across breakpoints with only small touch-target spacing issues on a couple of dense screens.",
    whatWasEvaluated: [
      "Layout behavior across common breakpoints",
      "Touch target sizing and spacing",
      "Mobile navigation usability",
      "Text readability without zooming",
      "Viewport and meta configuration",
      "Media scaling and overflow handling",
    ],
    positives: [
      "No horizontal scrolling or layout breakage at any tested breakpoint",
      "Text remains legible without zooming on all core pages",
      "Mobile navigation menu is fast and easy to reach with one hand",
    ],
    issues: [
      {
        title: "Filter chips on category pages sit closer than 8px apart",
        explanation:
          "On the mobile category view, adjacent filter chips have minimal spacing, increasing the chance of mis-taps.",
        severity: "low",
        impact: "Occasional accidental filter selection, adding minor friction while browsing.",
      },
    ],
    recommendations: [
      {
        title: "Increase spacing between mobile filter chips",
        why: "Tight spacing between small tap targets increases mis-tap rate on touch devices.",
        how: "Increase the horizontal gap between filter chips to at least 8px with slightly larger touch padding.",
        expectedImpact: "Reduces accidental taps during mobile browsing.",
      },
    ],
  },

  security: {
    categoryId: "security",
    summary:
      "Security fundamentals are excellent — HTTPS is enforced everywhere with modern headers in place; only a minor hardening opportunity remains.",
    whatWasEvaluated: [
      "HTTPS enforcement and certificate configuration",
      "Security headers (CSP, HSTS, X-Content-Type-Options)",
      "Cookie security attributes",
      "Third-party script and resource trust",
      "Privacy policy presence and clarity",
      "Form data transmission security",
    ],
    positives: [
      "HTTPS enforced site-wide with automatic redirect from HTTP",
      "HSTS header present with a sensible max-age",
      "Cookies are marked Secure and SameSite where applicable",
      "Privacy policy is clearly linked from the footer and account pages",
    ],
    issues: [
      {
        title: "Content-Security-Policy is permissive on script-src",
        explanation:
          "The CSP allows 'unsafe-inline' for scripts, which weakens its effectiveness against injected script attacks.",
        severity: "low",
        impact: "Reduces the practical protection the CSP provides, though HTTPS and other headers still cover most common risks.",
      },
    ],
    recommendations: [
      {
        title: "Tighten the script-src directive in the CSP",
        why: "'unsafe-inline' allows any inline script to execute, undermining the main benefit of having a CSP.",
        how: "Move inline scripts to external files or adopt a nonce/hash-based CSP so 'unsafe-inline' can be removed.",
        expectedImpact: "Meaningfully strengthens defense against cross-site scripting, even though current exposure is already low.",
      },
    ],
  },

  content: {
    categoryId: "content",
    summary:
      "Messaging is clear and on-brand overall, though several pages run longer than necessary and bury the key takeaway.",
    whatWasEvaluated: [
      "Clarity and conciseness of copy",
      "Tone and brand voice consistency",
      "Scannability (headings, lists, emphasis)",
      "Grammar and factual consistency",
      "Readability level versus target audience",
      "Calls-to-action within body content",
    ],
    positives: [
      "Consistent, friendly brand voice across marketing pages",
      "Product descriptions highlight benefits, not just specifications",
      "No grammar or spelling errors found in core page content",
    ],
    issues: [
      {
        title: "Key value proposition buried below the fold on the About page",
        explanation:
          "The About page opens with two paragraphs of company history before stating what the company actually offers.",
        severity: "medium",
        impact: "Visitors skimming the page may leave before reaching the information most relevant to them.",
      },
      {
        title: "Long, dense paragraphs on feature pages",
        explanation:
          "Several feature pages use 5-7 sentence paragraphs with no subheadings or lists to aid scanning.",
        severity: "low",
        impact: "Reduces scanability, especially for visitors on mobile skimming between tasks.",
      },
    ],
    recommendations: [
      {
        title: "Lead the About page with the value proposition",
        why: "Company history is interesting context, not the reason most visitors land on this page.",
        how: "Move a one- or two-sentence summary of what the company does to the top, with history further down.",
        expectedImpact: "Faster comprehension for new visitors, likely reducing bounce on this page.",
      },
      {
        title: "Break up long feature-page paragraphs",
        why: "Dense text blocks are harder to scan, especially on mobile.",
        how: "Introduce subheadings every 2-3 paragraphs and convert specification-style sentences into bulleted lists.",
        expectedImpact: "Improves scanability and time-on-page for feature content.",
      },
    ],
  },

  conversion: {
    categoryId: "conversion",
    summary:
      "The purchase path works, but calls-to-action compete with secondary links and trust signals are thin near the point of decision.",
    whatWasEvaluated: [
      "Call-to-action visibility and hierarchy",
      "Friction points in the conversion funnel",
      "Trust signals near decision points",
      "Form length and required fields",
      "Exit-intent and cart-abandonment handling",
      "Pricing and offer clarity",
    ],
    positives: [
      "Primary CTA color is used consistently and nowhere else on the page",
      "Pricing is presented clearly with no hidden-fee surprises at checkout start",
    ],
    issues: [
      {
        title: "Primary CTA competes visually with secondary links",
        explanation:
          "On product pages, 'Add to Cart' sits directly beside 'Add to Wishlist' and 'Compare' at the same visual weight.",
        severity: "medium",
        impact: "Dilutes attention on the action that actually drives revenue.",
      },
      {
        title: "No trust signals near the checkout button",
        explanation:
          "Payment security badges and return-policy mentions exist on the FAQ page but not near the checkout CTA itself.",
        severity: "medium",
        impact: "Hesitant buyers don't see reassurance at the exact moment they're deciding whether to complete the purchase.",
      },
      {
        title: "No recovery flow for abandoned carts",
        explanation: "Users who leave items in their cart receive no reminder email or on-site prompt to return.",
        severity: "low",
        impact: "Missed opportunity to recover a meaningful share of near-conversions.",
      },
    ],
    recommendations: [
      {
        title: "Visually separate the primary CTA from secondary actions",
        why: "Equal visual weight across three buttons makes none of them the obvious next step.",
        how: "Style 'Add to Cart' as a solid, high-contrast button and demote wishlist/compare to text links or outline buttons.",
        expectedImpact: "Clearer decision point, likely improving add-to-cart rate.",
      },
      {
        title: "Add trust signals beside the checkout CTA",
        why: "Reassurance is most effective at the exact moment of hesitation, not three clicks away on a FAQ page.",
        how: "Place secure-payment badges and a one-line return-policy note directly beneath the checkout button.",
        expectedImpact: "Reduces last-moment checkout abandonment driven by uncertainty.",
      },
      {
        title: "Add an abandoned-cart recovery email",
        why: "Users who add items but don't purchase are a highly qualified audience with minimal extra acquisition cost.",
        how: "Trigger a single reminder email a few hours after cart abandonment, optionally with a small time-limited incentive.",
        expectedImpact: "Recovers a portion of otherwise-lost near-conversions at low cost.",
      },
    ],
  },

  trust: {
    categoryId: "trust",
    summary:
      "Core trust signals are present and credible; adding more visible social proof near key decision points would strengthen first-time visitor confidence.",
    whatWasEvaluated: [
      "Presence and placement of testimonials/reviews",
      "Trust badges and certifications",
      "Company transparency (contact info, policies)",
      "Social proof near decision points",
      "Third-party validation (press, partners)",
      "Consistency of claims across pages",
    ],
    positives: [
      "Clear, easy-to-find contact information and support channels",
      "Return and shipping policies are written in plain language",
      "Customer reviews are present on product pages with verified-purchase labeling",
    ],
    issues: [
      {
        title: "No testimonials or social proof on the homepage",
        explanation:
          "The homepage leads straight into product categories with no mention of customer reviews, press mentions, or usage numbers.",
        severity: "medium",
        impact: "First-time visitors have no early signal of credibility before browsing further.",
      },
    ],
    recommendations: [
      {
        title: "Add a social proof section to the homepage",
        why: "New visitors decide whether to trust a site within seconds, and the homepage currently offers no early credibility signal.",
        how: "Add a compact section featuring 2-3 customer quotes or an aggregate review rating near the top of the homepage.",
        expectedImpact: "Improves first-impression trust, particularly for visitors arriving from paid or social channels.",
      },
    ],
  },

  technical: {
    categoryId: "technical",
    summary:
      "The codebase is in solid shape overall, with a few outdated dependencies and minor console warnings worth cleaning up.",
    whatWasEvaluated: [
      "Browser console errors and warnings",
      "Dependency freshness and known vulnerabilities",
      "Code splitting and bundle structure",
      "Error handling and broken-link detection",
      "Cross-browser rendering consistency",
      "HTML/CSS validation",
    ],
    positives: [
      "No broken internal links detected across the crawled site",
      "JavaScript bundles are code-split by route",
      "No critical runtime errors found during testing",
    ],
    issues: [
      {
        title: "Three dependencies are flagged with known moderate vulnerabilities",
        explanation:
          "A dependency audit found three indirect packages with disclosed moderate-severity vulnerabilities, none currently patched.",
        severity: "medium",
        impact: "Low immediate risk given they're indirect dependencies, but exposure grows the longer they go unpatched.",
      },
      {
        title: "Repeated console warnings on the checkout page",
        explanation:
          "A deprecated API usage warning fires on every render of the checkout page, cluttering the console and signaling unmaintained code.",
        severity: "low",
        impact: "No user-facing impact currently, but indicates technical debt that may cause issues after a future browser update.",
      },
    ],
    recommendations: [
      {
        title: "Update flagged dependencies to patched versions",
        why: "Unpatched known vulnerabilities are a straightforward, avoidable risk.",
        how: "Run a dependency audit and update the three flagged packages to their patched versions, testing for breaking changes.",
        expectedImpact: "Removes a known, avoidable security exposure.",
      },
      {
        title: "Resolve the deprecated API warning on checkout",
        why: "Deprecated APIs are eventually removed by browser vendors, which would break the page without warning.",
        how: "Replace the deprecated call with its modern equivalent and verify checkout still functions correctly.",
        expectedImpact: "Prevents a future breakage and removes console noise during debugging.",
      },
    ],
  },

  innovation: {
    categoryId: "innovation",
    summary:
      "The site makes confident use of modern interface patterns and a few genuinely distinctive touches that set it apart from category norms.",
    whatWasEvaluated: [
      "Use of modern web platform capabilities",
      "Distinctiveness versus category-standard templates",
      "Personalization and adaptive experiences",
      "Creative use of motion and interaction",
      "Novel approaches to common UX problems",
    ],
    positives: [
      "Product configurator uses real-time preview instead of a static options list",
      "Thoughtful micro-interactions on key actions (add to cart, save) feel considered rather than decorative",
      "Visual identity avoids generic template patterns common in the category",
    ],
    issues: [
      {
        title: "No personalization based on returning-visitor behavior",
        explanation:
          "Returning visitors see an identical homepage to first-time visitors, with no recall of recently viewed items or categories.",
        severity: "low",
        impact: "Misses an easy opportunity to shorten the path back to relevant products for repeat visitors.",
      },
    ],
    recommendations: [
      {
        title: "Add a lightweight 'recently viewed' section for returning visitors",
        why: "Returning visitors often want to pick up where they left off rather than re-browse from scratch.",
        how: "Store recently viewed product IDs client-side and surface them in a homepage section for returning visitors only.",
        expectedImpact: "Reduces friction for repeat visitors and can lift return-visit conversion.",
      },
    ],
  },
};

export function getCategoryAnalysis(id: CategoryId): CategoryAnalysis {
  return CATEGORY_ANALYSIS[id];
}

export function getCategoryScore(id: CategoryId): number {
  return DEMO_SCORES[id] ?? 0;
}

interface RankedCategory {
  id: CategoryId;
  name: string;
  score: number;
}

function rankedCategories(): RankedCategory[] {
  return EVALUATION_CATEGORIES.map((c) => ({
    id: c.id,
    name: c.name,
    score: DEMO_SCORES[c.id] ?? 0,
  })).sort((a, b) => b.score - a.score);
}

export function getStrongestCategory(): RankedCategory {
  return rankedCategories()[0];
}

export function getWeakestCategory(): RankedCategory {
  const ranked = rankedCategories();
  return ranked[ranked.length - 1];
}

interface FlatIssue extends CategoryIssue {
  categoryId: CategoryId;
  categoryName: string;
}

export function getAllIssues(): FlatIssue[] {
  return EVALUATION_CATEGORIES.flatMap((category) =>
    CATEGORY_ANALYSIS[category.id].issues.map((issue) => ({
      ...issue,
      categoryId: category.id,
      categoryName: category.name,
    })),
  );
}

export function getTotalIssueCount(): number {
  return getAllIssues().length;
}

export function getHighPriorityIssueCount(): number {
  return getAllIssues().filter((issue) => issue.severity === "critical" || issue.severity === "high").length;
}

export function getIssuesBySeverity(): Record<Severity, FlatIssue[]> {
  const issues = getAllIssues();
  return Object.fromEntries(
    SEVERITY_ORDER.map((severity) => [severity, issues.filter((i) => i.severity === severity)]),
  ) as Record<Severity, FlatIssue[]>;
}

interface FlatRecommendation {
  categoryId: CategoryId;
  categoryName: string;
  categoryWeight: number;
  title: string;
  why: string;
  how: string;
  expectedImpact: string;
  topSeverity: Severity;
}

const SEVERITY_RANK: Record<Severity, number> = { critical: 0, high: 1, medium: 2, low: 3 };

/**
 * All recommendations across every category, ranked by the severity of the
 * specific issue each one addresses (recommendations are authored in the
 * same order as their category's issues, so they're paired by index rather
 * than inheriting the category's single worst severity across the board).
 */
export function getAllRecommendationsRanked(): FlatRecommendation[] {
  return EVALUATION_CATEGORIES.flatMap((category) => {
    const analysis = CATEGORY_ANALYSIS[category.id];
    return analysis.recommendations.map((rec, index) => ({
      categoryId: category.id,
      categoryName: category.name,
      categoryWeight: category.weight,
      topSeverity: analysis.issues[index]?.severity ?? "low",
      ...rec,
    }));
  }).sort((a, b) => {
    const severityDiff = SEVERITY_RANK[a.topSeverity] - SEVERITY_RANK[b.topSeverity];
    if (severityDiff !== 0) return severityDiff;
    return b.categoryWeight - a.categoryWeight;
  });
}

export function getTopRecommendations(count: number): FlatRecommendation[] {
  return getAllRecommendationsRanked().slice(0, count);
}

export { getCategoryById };
