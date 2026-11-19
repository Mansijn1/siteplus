"""Screenshot persistence. Screenshots are saved to local disk under storage/screenshots and
referenced by path/URL in API responses — never embedded as base64 in JSON, which would bloat
every status/results payload."""

from __future__ import annotations

from pathlib import Path

from config import settings


def screenshot_path(scan_id: str, variant: str) -> Path:
    """variant is e.g. 'desktop' or 'mobile'."""
    return settings.screenshot_dir / f"{scan_id}-{variant}.png"


def save_screenshot(scan_id: str, variant: str, image_bytes: bytes) -> Path:
    path = screenshot_path(scan_id, variant)
    path.write_bytes(image_bytes)
    return path


def public_screenshot_url(scan_id: str, variant: str) -> str:
    """Relative path the API serves these from (mounted as a static route in main.py)."""
    return f"/static/screenshots/{scan_id}-{variant}.png"
