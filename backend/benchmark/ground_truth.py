"""Hand-verified ground truth for each benchmark fixture — manually read against the actual
fixture HTML (benchmark/fixtures/*.html) and the server's per-path header configuration
(benchmark/server.py), not generated or guessed. Each entry is `check_id: "passed" | "failed"`,
the status that check_id MUST have for this fixture if the analyzer is working correctly.

Deliberately excluded from every fixture: `https_enabled`, `tls_certificate_valid`, and
`no_mixed_content`. The benchmark server only serves plain HTTP (standing up local TLS for a
benchmark harness was judged out of scope), so these checks would always and only report
"failed" regardless of whether the detector logic is right — that's an artifact of the test
environment, not a signal about detection quality, and asserting ground truth against it would
conflate the two. Also excluded: `cookie_security_attributes` (the fixtures never set cookies,
so it's always `unavailable`, not a pass/fail case) and checks whose evidence Phase 2 doesn't
collect at all for a locally-served page (e.g. `robots_txt_present`/`sitemap_present`, since no
robots.txt/sitemap.xml is served here — these report "failed" correctly, but that's testing "is
there a robots.txt", a fact about the test server, not about SitePlus's detection logic, so it's
left out of ground truth for the same reason as the TLS checks)."""

from __future__ import annotations

GROUND_TRUTH: dict[str, dict[str, str]] = {
    "clean.html": {
        "title_present": "passed",
        "title_length": "passed",
        "meta_description_present": "passed",
        "meta_description_length": "passed",
        "canonical_present": "passed",
        "single_h1": "passed",
        "heading_hierarchy": "passed",
        "robots_meta_not_blocking": "passed",
        "open_graph_present": "passed",
        "images_alt_text": "passed",
        "internal_linking": "passed",
        "structured_data_present": "passed",
        "html_lang_attribute": "passed",
        "viewport_meta": "passed",
        "horizontal_overflow": "passed",
        "no_broken_images": "passed",
        "images_not_oversized": "passed",
        "navigation_landmark_present": "passed",
        "forms_have_inputs": "passed",
        "structured_content_sections": "passed",
        "ctas_or_forms_present": "passed",
        "no_js_console_errors": "passed",
        "about_page_linked": "passed",
        "privacy_policy_linked": "passed",
        "terms_linked": "passed",
        "social_links_present": "passed",
        "lead_capture_mechanism_present": "passed",
        "contact_info_discoverable": "passed",
        "pwa_manifest_present": "passed",
        "theme_color_configured": "passed",
        "http_status_ok": "passed",
        "content_type_header_correct": "passed",
        "redirect_chain_minimal": "passed",
        "x_robots_tag_not_blocking": "passed",
        "header:strict-transport-security": "passed",
        "header:content-security-policy": "passed",
        "header:x-frame-options": "passed",
        "header:x-content-type-options": "passed",
        "header:referrer-policy": "passed",
    },
    "seo_broken.html": {
        "title_present": "failed",
        "meta_description_present": "failed",
        "canonical_present": "failed",
        "single_h1": "failed",  # zero H1s
        "no_duplicate_headings": "failed",  # two identical "Welcome" H2s
        "robots_meta_not_blocking": "failed",  # noindex
        "open_graph_present": "failed",
        "images_alt_text": "failed",
        "structured_data_present": "failed",
        # Should NOT be affected by the SEO-specific breakage above:
        "html_lang_attribute": "failed",  # <html> has no lang attribute in this fixture
        "viewport_meta": "passed",
        "internal_linking": "passed",
    },
    "accessibility_broken.html": {
        "html_lang_attribute": "failed",
        "axe:color-contrast": "failed",
        "axe:label": "failed",
        "axe:image-alt": "failed",
        # Should NOT be affected by the accessibility-specific breakage above:
        "title_present": "passed",
        "viewport_meta": "passed",
    },
    "mobile_broken.html": {
        "viewport_meta": "failed",
        "horizontal_overflow": "failed",
        "touch_target_size": "failed",
        # Should NOT be affected by the mobile-specific breakage above:
        "title_present": "passed",
        "html_lang_attribute": "passed",
    },
    "ui_broken.html": {
        "font_family_consistency": "failed",
        "font_size_consistency": "failed",
        "heading_size_hierarchy": "failed",
        "alignment_consistency": "failed",
        "no_broken_images": "failed",
        # Should NOT be affected by the UI-specific breakage above:
        "title_present": "passed",
        "viewport_meta": "passed",
    },
    "security_broken.html": {
        "header:strict-transport-security": "failed",
        "header:content-security-policy": "failed",
        "header:x-frame-options": "failed",
        "header:x-content-type-options": "failed",
        "header:referrer-policy": "failed",
        # Should NOT be affected by the security-specific breakage above:
        "title_present": "passed",
        "http_status_ok": "passed",
    },
}
