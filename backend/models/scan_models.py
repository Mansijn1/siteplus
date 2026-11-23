from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ScanStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScanRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048, description="The website URL to scan.")


class StartScanResponse(BaseModel):
    scan_id: str
    status: ScanStatus


class ScanStatusResponse(BaseModel):
    scan_id: str
    status: ScanStatus
    progress: int = Field(ge=0, le=100)
    current_stage: str
    error: ScanError | None = None


class ScanError(BaseModel):
    code: str
    message: str


class MetricResult(BaseModel):
    """A single collected metric that may legitimately be unavailable — never fabricated."""

    available: bool
    value: float | str | None = None
    reason: str | None = None


class LighthouseCategoryScores(BaseModel):
    performance: MetricResult
    accessibility: MetricResult
    seo: MetricResult
    best_practices: MetricResult


class LighthouseMetrics(BaseModel):
    first_contentful_paint: MetricResult
    largest_contentful_paint: MetricResult
    speed_index: MetricResult
    total_blocking_time: MetricResult
    cumulative_layout_shift: MetricResult


class LighthouseRun(BaseModel):
    available: bool
    reason: str | None = None
    form_factor: str
    scores: LighthouseCategoryScores | None = None
    metrics: LighthouseMetrics | None = None
    raw_report_path: str | None = None


class ScreenshotResult(BaseModel):
    available: bool
    reason: str | None = None
    path: str | None = None
    url: str | None = None
    width: int | None = None
    height: int | None = None


class ConsoleMessage(BaseModel):
    type: str
    text: str
    location: str | None = None


class FailedRequest(BaseModel):
    url: str
    method: str
    failure_text: str | None = None
    resource_type: str | None = None


class ResponseInfo(BaseModel):
    status_code: int | None = None
    final_url: str | None = None
    redirect_chain: list[str] = Field(default_factory=list)
    headers: dict[str, str] = Field(default_factory=dict)
    https: bool = False


class LoadTiming(BaseModel):
    dom_content_loaded_ms: float | None = None
    load_event_ms: float | None = None
    response_time_ms: float | None = None


class BasicInfo(BaseModel):
    url: str
    final_url: str
    title: str | None = None
    meta_description: str | None = None
    canonical_url: str | None = None
    language: str | None = None
    html_size_bytes: int


class HeadingInfo(BaseModel):
    level: int
    text: str


class StructuredDataInfo(BaseModel):
    has_json_ld: bool = False
    json_ld_types: list[str] = Field(default_factory=list)
    count: int = 0


class SeoInfo(BaseModel):
    headings: list[HeadingInfo]
    heading_counts: dict[str, int]
    images_total: int
    images_missing_alt: int
    meta_robots: str | None = None
    open_graph: dict[str, str]
    internal_links: int
    external_links: int
    # Absolute, deduped internal link URLs (capped) — Phase 4 adds this for two consumers: the
    # multi-page crawler's page discovery, and the technical/SEO analyzers' real broken-internal
    # -link check once other pages in the same crawl have also been scanned.
    internal_link_urls: list[str] = Field(default_factory=list)
    structured_data: StructuredDataInfo = Field(default_factory=StructuredDataInfo)


class ContentInfo(BaseModel):
    word_count: int
    main_sections: int
    empty_headings: int
    duplicate_headings: list[str]
    # First ~1500 chars of visible body text (same extraction pass as word_count, no new
    # capture step) — real content for anything that needs to judge relevance/quality rather
    # than just count words, e.g. services/llm_seo_agent.py.
    content_excerpt: str = ""


class TechnicalInfo(BaseModel):
    https: bool
    status_code: int | None
    was_redirected: bool
    redirect_count: int
    response_headers: dict[str, str]
    image_count: int
    script_count: int
    stylesheet_count: int
    failed_requests: list[FailedRequest]


class PageSignalsInfo(BaseModel):
    """Presence signals detected from anchor href/text patterns on the SINGLE scanned page —
    e.g. a link whose href contains '/contact'. This detects presence of a link pointing
    somewhere, not the destination page's actual content; analyzers that use this say so."""

    has_contact_link: bool = False
    has_about_link: bool = False
    has_privacy_link: bool = False
    has_terms_link: bool = False
    has_pricing_link: bool = False
    social_platforms: list[str] = Field(default_factory=list)
    has_manifest_link: bool = False
    has_theme_color_meta: bool = False


class UxInfo(BaseModel):
    nav_elements: int
    buttons: int
    links: int
    forms: int
    input_fields: int
    has_viewport_meta: bool
    viewport_content: str | None = None
    horizontal_overflow: bool | None = None


class ExtractedData(BaseModel):
    basic: BasicInfo
    seo: SeoInfo
    content: ContentInfo
    technical: TechnicalInfo
    ux: UxInfo
    page_signals: PageSignalsInfo


class AxeViolationNode(BaseModel):
    selector: str
    html_snippet: str | None = None
    failure_summary: str | None = None


class AxeViolation(BaseModel):
    rule_id: str
    impact: str | None = None  # minor / moderate / serious / critical — axe-core's own scale
    description: str
    help_text: str | None = None
    help_url: str | None = None
    tags: list[str] = Field(default_factory=list)
    nodes: list[AxeViolationNode] = Field(default_factory=list)


class AccessibilityAudit(BaseModel):
    """Real axe-core results, injected into the same page Phase 2 already loaded — never a
    second browser launch. `available=False` (not a clean pass) when axe itself couldn't run."""

    available: bool
    reason: str | None = None
    violations: list[AxeViolation] = Field(default_factory=list)
    passed_rule_ids: list[str] = Field(default_factory=list)
    passes_count: int = 0
    incomplete_count: int = 0


class TlsCertificateInfo(BaseModel):
    """From Playwright's own `response.security_details()` on the main document response —
    unavailable for plain http or when the browser doesn't expose it for this connection."""

    available: bool
    reason: str | None = None
    protocol: str | None = None
    issuer: str | None = None
    valid_from: float | None = None
    valid_to: float | None = None
    subject_name: str | None = None


class TypographySignal(BaseModel):
    """Distinct computed font-family/font-size values sampled from up to 500 leaf text nodes —
    a real, if approximate, typography-consistency signal, not a subjective design judgment."""

    available: bool
    reason: str | None = None
    distinct_font_families: int | None = None
    distinct_font_sizes: int | None = None
    font_family_samples: list[str] = Field(default_factory=list)


class ImageDetail(BaseModel):
    src: str
    natural_width: int | None = None
    natural_height: int | None = None
    rendered_width: int | None = None
    rendered_height: int | None = None
    format: str | None = None  # guessed from the URL's file extension — best-effort, not content-sniffed
    loading: str | None = None  # the `loading` attribute (e.g. "lazy") — absence doesn't mean broken


class ImageDiagnostics(BaseModel):
    available: bool
    reason: str | None = None
    total_checked: int = 0
    broken_count: int = 0
    oversized_count: int = 0
    broken_examples: list[str] = Field(default_factory=list)
    details: list[ImageDetail] = Field(default_factory=list)  # capped — see page_diagnostics.py


class TouchTargetSignal(BaseModel):
    """Interactive elements below the ~44x44 CSS px minimum recommended touch-target size,
    measured on the real mobile viewport Phase 2 already renders."""

    available: bool
    reason: str | None = None
    total_checked: int = 0
    undersized_count: int = 0
    undersized_examples: list[str] = Field(default_factory=list)


class RobotsSitemapInfo(BaseModel):
    available: bool
    reason: str | None = None
    robots_txt_present: bool = False
    robots_txt_status: int | None = None
    robots_txt_disallow_all: bool = False
    sitemap_declared_in_robots: bool = False
    sitemap_xml_present: bool = False
    sitemap_xml_status: int | None = None
    # Page 4: URLs listed in the sitemap (same-domain, capped) — real page-discovery evidence
    # for the multi-page crawler, not just a presence check.
    sitemap_urls: list[str] = Field(default_factory=list)


class MixedContentInfo(BaseModel):
    available: bool
    insecure_resource_count: int = 0
    insecure_resource_examples: list[str] = Field(default_factory=list)


class LayoutSignal(BaseModel):
    """Alignment/typography-hierarchy evidence — real computed-style/bounding-box measurements,
    not a subjective design judgment. Added in Phase 4 to cover the UI module's "measure
    typography hierarchy" / "analyze visual alignment" checks, which Phase 3 had marked
    unavailable for lack of this exact evidence."""

    available: bool
    reason: str | None = None
    heading_hierarchy_sizes_ok: bool | None = None
    distinct_left_edges: int | None = None
    body_font_size_px: float | None = None
    largest_heading_font_size_px: float | None = None


class AuditExtras(BaseModel):
    """Additive Phase 3 evidence captured during the SAME Phase 2 browser session (no second
    browser launch, no re-scan) plus two passive same-origin HTTP GETs for robots/sitemap.
    Entirely optional on `ScanResults` — Phase 2's existing contract is unaffected when this
    is None (e.g. a scan that predates this field, or one where every sub-capture failed).

    `touch_targets_tablet` reuses the existing mobile-context page at a second viewport size
    (a `set_viewport_size` call, not a second navigation) — real "multiple viewport" coverage
    without a third full page load."""

    accessibility: AccessibilityAudit
    tls: TlsCertificateInfo
    typography: TypographySignal
    images: ImageDiagnostics
    touch_targets: TouchTargetSignal
    touch_targets_tablet: TouchTargetSignal = TouchTargetSignal(available=False, reason="not_run")
    robots_sitemap: RobotsSitemapInfo
    mixed_content: MixedContentInfo
    layout: LayoutSignal = LayoutSignal(available=False, reason="not_run")


class ScanResults(BaseModel):
    scan_id: str
    submitted_url: str
    extracted: ExtractedData | None = None
    screenshots: dict[str, ScreenshotResult]
    lighthouse: dict[str, LighthouseRun]
    console_messages: list[ConsoleMessage]
    response: ResponseInfo
    load_timing: LoadTiming
    audit_extras: AuditExtras | None = None
    started_at: str
    completed_at: str | None = None


class ScanResultsResponse(BaseModel):
    scan_id: str
    status: ScanStatus
    results: ScanResults | None = None
    error: ScanError | None = None


ScanStatusResponse.model_rebuild()
