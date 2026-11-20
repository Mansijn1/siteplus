"""Runs real axe-core (vendored at `vendor/axe.min.js`, injected via Playwright — no CDN
fetch at scan time, no second browser) against the page Phase 2 already has open. This is the
project's actual automated accessibility testing engine: WCAG-related rules, alt text, form
labels, ARIA, color contrast, and heading structure are all axe-core's own checks, not a
hand-rolled approximation. Never invents a violation; `available=False` only when axe itself
couldn't be injected or run."""

from __future__ import annotations

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page

from config import settings
from models.scan_models import AccessibilityAudit, AxeViolation, AxeViolationNode


async def run_accessibility_audit(page: Page) -> AccessibilityAudit:
    if not settings.accessibility_audit_enabled:
        return AccessibilityAudit(available=False, reason="accessibility_audit_disabled")
    if not settings.axe_js_path.exists():
        return AccessibilityAudit(available=False, reason="axe_core_not_vendored")

    try:
        await page.add_script_tag(path=str(settings.axe_js_path))
        raw = await page.evaluate(
            "async () => { "
            "  if (!window.axe) return null; "
            "  const results = await window.axe.run(document, { resultTypes: ['violations', 'passes', 'incomplete'] }); "
            "  return { "
            "    violations: results.violations.map(v => ({ "
            "      id: v.id, impact: v.impact, description: v.description, help: v.help, helpUrl: v.helpUrl, "
            "      tags: v.tags, "
            "      nodes: v.nodes.slice(0, 10).map(n => ({ "
            "        selector: (n.target || []).join(' '), html: (n.html || '').slice(0, 300), "
            "        failureSummary: n.failureSummary || null "
            "      })) "
            "    })), "
            "    passedRuleIds: results.passes.map(p => p.id), "
            "    passesCount: results.passes.length, "
            "    incompleteCount: results.incomplete.length "
            "  }; "
            "}"
        )
    except PlaywrightError as exc:
        return AccessibilityAudit(available=False, reason=f"axe_injection_failed: {exc}"[:300])
    except Exception as exc:  # noqa: BLE001 — a bad axe response must degrade, never crash the scan
        return AccessibilityAudit(available=False, reason=f"axe_run_failed: {exc}"[:300])

    if raw is None:
        return AccessibilityAudit(available=False, reason="axe_not_loaded_on_page")

    violations = [
        AxeViolation(
            rule_id=v["id"],
            impact=v.get("impact"),
            description=v.get("description", ""),
            help_text=v.get("help"),
            help_url=v.get("helpUrl"),
            tags=v.get("tags", []),
            nodes=[
                AxeViolationNode(
                    selector=n.get("selector", ""),
                    html_snippet=n.get("html"),
                    failure_summary=n.get("failureSummary"),
                )
                for n in v.get("nodes", [])
            ],
        )
        for v in raw.get("violations", [])
    ]

    return AccessibilityAudit(
        available=True,
        violations=violations,
        passed_rule_ids=raw.get("passedRuleIds", []),
        passes_count=raw.get("passesCount", 0),
        incomplete_count=raw.get("incompleteCount", 0),
    )
