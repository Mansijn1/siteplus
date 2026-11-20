"""Small, targeted `page.evaluate()` captures beyond what Phase 2 already extracts — typography
consistency, broken/oversized images, and (on the mobile viewport) undersized touch targets.
Each is a real DOM/computed-style measurement, not a subjective design judgment: this module
counts and reports what's on the page, it doesn't score it (that's the analyzer's job)."""

from __future__ import annotations

import re

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page

from config import settings
from models.scan_models import ImageDiagnostics, MixedContentInfo, TouchTargetSignal, TypographySignal

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

_IMAGE_JS = """
() => {
  const imgs = Array.from(document.querySelectorAll('img'));
  let broken = 0, oversized = 0;
  const brokenExamples = [];
  for (const img of imgs) {
    if (img.complete && img.naturalWidth === 0 && img.src) {
      broken++;
      if (brokenExamples.length < 5) brokenExamples.push(img.src);
    } else if (img.naturalWidth > 0) {
      const rect = img.getBoundingClientRect();
      if (rect.width > 10 && img.naturalWidth > rect.width * 2.5) {
        oversized++;
      }
    }
  }
  return { total: imgs.length, broken, oversized, brokenExamples };
}
"""

_TOUCH_TARGET_JS = """
() => {
  const interactive = Array.from(document.querySelectorAll(
    'a[href], button, input, select, textarea, [role="button"], [onclick]'
  ));
  let undersized = 0;
  const examples = [];
  for (const el of interactive) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    if (r.width < 44 || r.height < 44) {
      undersized++;
      if (examples.length < 5) {
        const label = (el.tagName + (el.textContent ? ':' + el.textContent.trim().slice(0, 30) : '')).slice(0, 60);
        examples.push(label);
      }
    }
  }
  return { total: interactive.length, undersized, examples };
}
"""

_HTTP_SRC_RE = re.compile(r'''(?:src|href)=["']http://[^"']+["']''', re.IGNORECASE)


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
    return ImageDiagnostics(
        available=True,
        total_checked=raw.get("total", 0),
        broken_count=raw.get("broken", 0),
        oversized_count=raw.get("oversized", 0),
        broken_examples=raw.get("brokenExamples", []),
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
