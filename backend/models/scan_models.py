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


class SeoInfo(BaseModel):
    headings: list[HeadingInfo]
    heading_counts: dict[str, int]
    images_total: int
    images_missing_alt: int
    meta_robots: str | None = None
    open_graph: dict[str, str]
    internal_links: int
    external_links: int


class ContentInfo(BaseModel):
    word_count: int
    main_sections: int
    empty_headings: int
    duplicate_headings: list[str]


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


class ScanResults(BaseModel):
    scan_id: str
    submitted_url: str
    extracted: ExtractedData | None = None
    screenshots: dict[str, ScreenshotResult]
    lighthouse: dict[str, LighthouseRun]
    console_messages: list[ConsoleMessage]
    response: ResponseInfo
    load_timing: LoadTiming
    started_at: str
    completed_at: str | None = None


class ScanResultsResponse(BaseModel):
    scan_id: str
    status: ScanStatus
    results: ScanResults | None = None
    error: ScanError | None = None


ScanStatusResponse.model_rebuild()
