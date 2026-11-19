"""Attaches passive listeners to a Playwright page to collect console output and failed
network requests during navigation. Nothing here sends any additional request — it only
observes what the page itself does."""

from __future__ import annotations

from playwright.async_api import Page, Request

from models.scan_models import ConsoleMessage, FailedRequest


class NetworkInspector:
    def __init__(self) -> None:
        self.console_messages: list[ConsoleMessage] = []
        self.failed_requests: list[FailedRequest] = []
        self._response_headers_by_url: dict[str, dict[str, str]] = {}

    def attach(self, page: Page) -> None:
        page.on("console", self._on_console)
        page.on("requestfailed", self._on_request_failed)
        page.on("response", self._on_response)

    def _on_console(self, msg) -> None:  # playwright's ConsoleMessage type
        if msg.type not in ("error", "warning"):
            return
        location = None
        try:
            loc = msg.location
            if loc and loc.get("url"):
                location = f"{loc['url']}:{loc.get('lineNumber', '?')}"
        except Exception:
            pass
        # Cap stored text length — a pathological page could log megabytes.
        self.console_messages.append(ConsoleMessage(type=msg.type, text=msg.text[:500], location=location))

    def _on_request_failed(self, request: Request) -> None:
        failure = request.failure
        self.failed_requests.append(
            FailedRequest(
                url=request.url[:500],
                method=request.method,
                failure_text=(failure or "unknown")[:300] if isinstance(failure, str) else str(failure)[:300],
                resource_type=request.resource_type,
            )
        )

    def _on_response(self, response) -> None:
        try:
            self._response_headers_by_url[response.url] = dict(response.headers)
        except Exception:
            pass

    def headers_for(self, url: str) -> dict[str, str]:
        return self._response_headers_by_url.get(url, {})
