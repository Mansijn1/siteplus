"""Small, targeted `page.evaluate()` captures beyond what Phase 2 already extracts — typography
consistency, broken/oversized images (with per-image detail), layout/alignment signals, and
(on the mobile viewport, at two sizes) undersized touch targets. Each is a real DOM/computed-
style measurement, not a subjective design judgment: this module counts and reports what's on
the page, it doesn't score it (that's the analyzer's job)."""

from __future__ import annotations

import re

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page

from config import settings
from models.scan_models import ImageDetail, ImageDiagnostics, LayoutSignal, MixedContentInfo, TouchTargetSignal, TypographySignal

_TYPOGRAPHY_JS = """
() => {
  const nodes = Array.from(document.querySelectorAll('body *')).filter(el => {
    if (el.children.length > 0) return false;
    if (!el.textContent || !el.textContent.trim()) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  }).slice(0, 500);
  const families = new Set();
  const sizes = new Set();
  for (const el of nodes) {
    const cs = getComputedStyle(el);
    families.add(cs.fontFamily);
    sizes.add(cs.fontSize);
  }
  return { families: Array.from(families).slice(0, 10), sizeCount: sizes.size, familyCount: families.size, sampleCount: nodes.length };
}
"""

# Images with a srcset are deliberately excluded from the oversized check: the browser may
# legitimately have picked a smaller source than "natural size vs rendered size" assumes, and
# flagging that as an issue would be a false positive against responsive-image best practice.
_IMAGE_JS = """
() => {
  const imgs = Array.from(document.querySelectorAll('img'));
  let broken = 0, oversized = 0;
  const brokenExamples = [];
  const details = [];
  for (const img of imgs) {
    const rect = img.getBoundingClientRect();
    const hasSrcset = !!img.srcset;
    let isBroken = false, isOversized = false;
    if (img.complete && img.naturalWidth === 0 && img.src) {
      isBroken = true;
      broken++;
      if (brokenExamples.length < 5) brokenExamples.push(img.src);
    } else if (img.naturalWidth > 0 && !hasSrcset) {
      if (rect.width > 10 && img.naturalWidth > rect.width * 2.5) {
        isOversized = true;
        oversized++;
      }
    }
    if (details.length < 40 && img.src) {
      details.push({
        src: img.src,
        naturalWidth: img.naturalWidth || null,
        naturalHeight: img.naturalHeight || null,
        renderedWidth: Math.round(rect.width) || null,
        renderedHeight: Math.round(rect.height) || null,
        loading: img.getAttribute('loading'),
      });
    }
  }
  return { total: imgs.length, broken, oversized, brokenExamples, details };
}
"""

# Excludes elements with zero opacity/visibility:hidden/display:none — an off-canvas or
# collapsed menu item is not a "broken" touch target, it's intentionally not interactive right
# now, and must not be reported as one.
_TOUCH_TARGET_JS = """
() => {
  const interactive = Array.from(document.querySelectorAll(
    'a[href], button, input, select, textarea, [role="button"], [onclick]'
  ));
  let undersized = 0, checked = 0;
  const examples = [];
  for (const el of interactive) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none' || parseFloat(cs.opacity) === 0) continue;
    checked++;
    if (r.width < 44 || r.height < 44) {
      undersized++;
      if (examples.length < 5) {
        const label = (el.tagName + (el.textContent ? ':' + el.textContent.trim().slice(0, 30) : '')).slice(0, 60);
        examples.push(label);
      }
    }
  }
  return { total: checked, undersized, examples };
}
"""

# Two independent, cheap real-evidence signals: (1) do heading levels get visually smaller (or
# equal) as they go deeper — h1 should never render smaller than h2, etc; (2) how many distinct
# left-edge x-offsets exist among major top-level content blocks — a tight, consistent grid
# means few distinct values, a loose/inconsistent layout means many.
_LAYOUT_JS = """
() => {
  const headingSizes = {};
  for (let level = 1; level <= 6; level++) {
    const els = document.querySelectorAll('h' + level);
    if (els.length === 0) continue;
    const sizes = Array.from(els).map(el => parseFloat(getComputedStyle(el).fontSize)).filter(n => !isNaN(n));
    if (sizes.length > 0) headingSizes[level] = Math.max(...sizes);
  }
  const levels = Object.keys(headingSizes).map(Number).sort((a, b) => a - b);
  let hierarchyOk = true;
  for (let i = 0; i < levels.length - 1; i++) {
    if (headingSizes[levels[i]] < headingSizes[levels[i + 1]]) { hierarchyOk = false; break; }
  }

  const bodyEl = document.body;
  const bodyFontSize = bodyEl ? parseFloat(getComputedStyle(bodyEl).fontSize) : null;
  const largestHeading = levels.length > 0 ? Math.max(...Object.values(headingSizes)) : null;

  const blocks = Array.from(document.querySelectorAll('body > *, main > *, [class*="container"] > *'))
    .filter(el => {
      const r = el.getBoundingClientRect();
      return r.width > 100 && r.height > 20;
    })
    .slice(0, 60);
  const leftEdges = new Set(blocks.map(el => Math.round(el.getBoundingClientRect().left / 4) * 4));

  return {
    hierarchyOk: levels.length >= 2 ? hierarchyOk : null,
    distinctLeftEdges: blocks.length >= 4 ? leftEdges.size : null,
    bodyFontSize,
    largestHeadingFontSize: largestHeading,
  };
}
"""

_HTTP_SRC_RE = re.compile(r'''(?:src|href)=["']http://[^"']+["']''', re.IGNORECASE)
_IMAGE_EXT_RE = re.compile(r"\.([a-z0-9]{2,5})(?:[?#]|$)", re.IGNORECASE)


def _guess_format(src: str) -> str | None:
    match = _IMAGE_EXT_RE.search(src.split("?")[0])
    return match.group(1).lower() if match else None


async def run_typography_signal(page: Page) -> TypographySignal:
    if not settings.page_diagnostics_enabled:
        return TypographySignal(available=False, reason="page_diagnostics_disabled")
    try:
        raw = await page.evaluate(_TYPOGRAPHY_JS)
    except PlaywrightError as exc:
        return TypographySignal(available=False, reason=f"evaluate_failed: {exc}"[:300])
    if not raw or raw.get("sampleCount", 0) == 0:
        return TypographySignal(available=False, reason="no_visible_text_nodes_sampled")
    return TypographySignal(
        available=True,
        distinct_font_families=raw.get("familyCount"),
        distinct_font_sizes=raw.get("sizeCount"),
        font_family_samples=raw.get("families", []),
    )


async def run_image_diagnostics(page: Page) -> ImageDiagnostics:
    if not settings.page_diagnostics_enabled:
        return ImageDiagnostics(available=False, reason="page_diagnostics_disabled")
    try:
        raw = await page.evaluate(_IMAGE_JS)
    except PlaywrightError as exc:
        return ImageDiagnostics(available=False, reason=f"evaluate_failed: {exc}"[:300])
    details = [
        ImageDetail(
            src=d["src"],
            natural_width=d.get("naturalWidth"),
            natural_height=d.get("naturalHeight"),
            rendered_width=d.get("renderedWidth"),
            rendered_height=d.get("renderedHeight"),
            format=_guess_format(d["src"]),
            loading=d.get("loading"),
        )
        for d in raw.get("details", [])
    ]
    return ImageDiagnostics(
        available=True,
        total_checked=raw.get("total", 0),
        broken_count=raw.get("broken", 0),
        oversized_count=raw.get("oversized", 0),
        broken_examples=raw.get("brokenExamples", []),
        details=details,
    )


async def run_touch_target_signal(page: Page) -> TouchTargetSignal:
    if not settings.page_diagnostics_enabled:
        return TouchTargetSignal(available=False, reason="page_diagnostics_disabled")
    try:
        raw = await page.evaluate(_TOUCH_TARGET_JS)
    except PlaywrightError as exc:
        return TouchTargetSignal(available=False, reason=f"evaluate_failed: {exc}"[:300])
    return TouchTargetSignal(
        available=True,
        total_checked=raw.get("total", 0),
        undersized_count=raw.get("undersized", 0),
        undersized_examples=raw.get("examples", []),
    )


async def run_layout_signal(page: Page) -> LayoutSignal:
    if not settings.page_diagnostics_enabled:
        return LayoutSignal(available=False, reason="page_diagnostics_disabled")
    try:
        raw = await page.evaluate(_LAYOUT_JS)
    except PlaywrightError as exc:
        return LayoutSignal(available=False, reason=f"evaluate_failed: {exc}"[:300])
    return LayoutSignal(
        available=True,
        heading_hierarchy_sizes_ok=raw.get("hierarchyOk"),
        distinct_left_edges=raw.get("distinctLeftEdges"),
        body_font_size_px=raw.get("bodyFontSize"),
        largest_heading_font_size_px=raw.get("largestHeadingFontSize"),
    )


def detect_mixed_content(html: str, final_url: str) -> MixedContentInfo:
    """Pure string scan of the already-captured HTML — no extra navigation or request."""
    if not final_url.startswith("https://"):
        return MixedContentInfo(available=True, insecure_resource_count=0)
    matches = _HTTP_SRC_RE.findall(html)
    return MixedContentInfo(
        available=True,
        insecure_resource_count=len(matches),
        insecure_resource_examples=matches[:5],
    )
