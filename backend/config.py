from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # CORS — explicit allowed origins plus a regex for Vercel preview deployments. Never "*":
    # this API will later accept state-changing requests, and an open CORS policy would let
    # any third-party page trigger scans on a visitor's behalf.
    cors_allow_origins: list[str] = [
        "http://localhost:3000",
        "https://siteplus-three.vercel.app",
    ]
    cors_allow_origin_regex: str = r"^https://siteplus-.*\.vercel\.app$"

    # Scan limits — bound every external call so one hostile or broken target can't hang a
    # worker indefinitely or exhaust disk/memory.
    navigation_timeout_ms: int = 30_000
    # Generous on purpose: verified live on Render's free tier that a real Lighthouse run can
    # take well over 90s under its shared, limited CPU (90s timed out there; the browser scan
    # itself — screenshots, extraction — completed fine in the same window). This still fails
    # closed to available=false on a genuinely hung process, just with more realistic headroom.
    lighthouse_timeout_s: int = 170
    max_response_body_bytes: int = 15 * 1024 * 1024  # 15 MB cap on the main document response
    max_concurrent_scans: int = 3

    # Lighthouse. Set LIGHTHOUSE_CHROME_PATH to pin a specific Chrome/Chromium binary (e.g. the
    # one Playwright already downloaded) instead of letting chrome-launcher search the system.
    lighthouse_chrome_path: str | None = None
    # Deliberately named so neither reads the ENABLE_LIGHTHOUSE / ENABLE_MOBILE_LIGHTHOUSE env
    # vars already set on the live Render service (the CLI used to deploy it has no command to
    # remove or edit a service's env vars after creation): Lighthouse's own Chrome process
    # reliably OOM-restarts that service's free-tier 512MB container mid-scan, confirmed live
    # even after trimming Chrome's flags — so this ships OFF there by default. Flip to True (and
    # rename back to enable_lighthouse, or set LIGHTHOUSE_ENABLED=true) once the plan has more
    # headroom, or run locally where this isn't a constraint.
    lighthouse_enabled: bool = False
    lighthouse_mobile_enabled: bool = False

    screenshot_dir: Path = BACKEND_ROOT / "storage" / "screenshots"
    lighthouse_dir: Path = BACKEND_ROOT / "storage" / "lighthouse"

    desktop_viewport: tuple[int, int] = (1440, 900)
    mobile_viewport: tuple[int, int] = (390, 844)


def _detect_chromium_path() -> str | None:
    """Asks Playwright directly where it installed Chromium, rather than guessing a path and
    browser-revision number that can silently drift out of date (or differ across platforms)
    from whatever `playwright==X.Y.Z` in requirements.txt actually pins. This only queries
    Playwright's driver for metadata — it does not launch a browser — and runs once at import
    time, before uvicorn's event loop starts, so the sync API here is safe."""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            path = p.chromium.executable_path
            return path if path else None
    except Exception:
        return None


settings = Settings()
settings.screenshot_dir.mkdir(parents=True, exist_ok=True)
settings.lighthouse_dir.mkdir(parents=True, exist_ok=True)

if not settings.lighthouse_chrome_path:
    settings.lighthouse_chrome_path = _detect_chromium_path()
