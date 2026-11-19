# WebRate AI — Scanner Backend (Phase 2)

A FastAPI service that performs **real, passive** website scanning: it launches a real
Chromium browser via Playwright, captures desktop and mobile screenshots, runs Lighthouse,
and extracts SEO/content/technical data from the live page. It does **not** compute the
12-category evaluation scores — that scoring engine is a later phase. This phase is raw data
collection only, and every field that couldn't genuinely be collected comes back
`available: false` with a `reason`, never a fabricated number.

## Architecture

```
backend/
├── main.py                 FastAPI app, CORS, health check, static screenshot serving
├── config.py                Settings (CORS origins, timeouts, viewport sizes, feature flags)
├── api/
│   └── scan_routes.py       POST /api/scans, GET .../status, GET .../results
├── models/
│   └── scan_models.py        Pydantic request/response/result models
├── security/
│   └── url_validation.py     SSRF/DNS-rebinding defense — see "Security" below
├── scanner/
│   ├── browser.py             Playwright: navigation, screenshots, console/network capture
│   ├── page_extractor.py      BeautifulSoup: SEO/content/technical extraction from the DOM
│   ├── lighthouse.py          Shells out to the Lighthouse CLI, parses its JSON report
│   ├── screenshot.py          Screenshot file persistence
│   └── network_inspector.py   Console + failed-request listeners attached to the page
└── services/
    └── scan_service.py        In-memory scan store + the async pipeline that runs every stage
```

No database: scan state lives in an in-memory dict (`services/scan_service.py`), which is
fine for this phase's scope (consistent with "no backend services/database" in Phase 1,
now intentionally relaxed only as far as this scanning service, per Phase 2). Restarting the
process loses in-flight/completed scan records — screenshots and Lighthouse reports on disk
survive a restart, but there's no way to look them up without the scan_id that was already
handed back to the frontend.

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Health check (used by Render) |
| `POST` | `/api/scans` | Validates the URL and starts a scan. `{"url": "https://example.com"}` → `{"scan_id": "...", "status": "queued"}` (202) |
| `GET` | `/api/scans/{scan_id}/status` | `{"scan_id", "status", "progress" (0-100), "current_stage", "error"}` |
| `GET` | `/api/scans/{scan_id}/results` | Full raw results once `status == "completed"`; 409 while still running, returns the error object if `status == "failed"` |

### Example: a completed scan's results (abridged)

```json
{
  "scan_id": "9f251f9f407e42b6",
  "status": "completed",
  "results": {
    "submitted_url": "https://example.com",
    "extracted": {
      "basic": { "title": "Example Domain", "final_url": "https://example.com/", "html_size_bytes": 2373 },
      "seo": { "heading_counts": { "h1": 0 }, "images_total": 0, "internal_links": 0, "external_links": 1 },
      "content": { "word_count": 91 },
      "technical": { "https": true, "status_code": 200, "was_redirected": false, "failed_requests": [] }
    },
    "screenshots": {
      "desktop": { "available": true, "url": "/static/screenshots/9f251f9f-desktop.png", "width": 1440, "height": 900 },
      "mobile":  { "available": true, "url": "/static/screenshots/9f251f9f-mobile.png", "width": 390, "height": 844 }
    },
    "lighthouse": {
      "desktop": { "available": true, "scores": { "performance": { "value": 100 }, "accessibility": { "value": 96 }, "seo": { "value": 80 }, "best_practices": { "value": 100 } } },
      "mobile":  { "available": true, "scores": { "performance": { "value": 100 }, "accessibility": { "value": 96 }, "seo": { "value": 80 }, "best_practices": { "value": 100 } } }
    }
  }
}
```

## Running it locally

```bash
cd backend
python -m venv venv
source venv/Scripts/activate      # Windows Git Bash; use `venv\Scripts\activate.bat` for cmd.exe
pip install -r requirements.txt
python -m playwright install chromium

cp .env.example .env
# Edit .env: set LIGHTHOUSE_CHROME_PATH to the path `python -c "from playwright.sync_api import sync_playwright;
# p = sync_playwright().start(); print(p.chromium.executable_path)"` prints, so Lighthouse reuses
# the same browser instead of trying to find or download its own.

uvicorn main:app --reload --port 8000
```

Lighthouse also needs Node.js + `npx` on PATH (it's invoked as a subprocess) — if neither is
found, Lighthouse results come back `available: false, reason: "lighthouse_cli_not_found"`
rather than the scan failing outright; everything else still works.

Then point the frontend at it: in `siteplus/.env.local`, set `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000` (or whatever port you ran it on — this repo's own dev setup used 8787 to avoid a port clash).

## Deployment (Render or any container host)

```bash
docker build -t webrate-ai-scanner ./backend
docker run -p 8000:8000 webrate-ai-scanner
```

`render.yaml` is set up for Render's Docker-based web service (`env: docker`). Before deploying:

1. **CORS** — `config.py`'s `cors_allow_origins`/`cors_allow_origin_regex` are hardcoded to the
   known frontend origins (`http://localhost:3000`, `https://siteplus-three.vercel.app`, and
   Vercel preview URLs matching `siteplus-*.vercel.app`). Update these if the frontend's
   deployed URL changes.
2. **Frontend env var** — once deployed, set `NEXT_PUBLIC_API_URL` to the Render service's
   public URL in Vercel's project settings (Production and/or Preview environment).
3. The Dockerfile is prepared and documented but **not build-tested in this environment**
   (no Docker available here) — verify the build once on a machine or CI that has it before
   relying on it for a real deploy. See "Known limitations" below.

## Security measures (SSRF / DNS-rebinding defense)

`security/url_validation.py` is the single gate every URL passes through:

- Only `http`/`https` schemes accepted.
- `localhost` and `*.localhost` explicitly blocked by name (defends against the hostname
  resolving differently than expected).
- DNS is resolved and **every** returned address is checked against private, loopback,
  link-local, reserved, multicast, and unspecified ranges (Python's `ipaddress` module) —
  catches a hostname that resolves to multiple IPs, some public, some not.
- The same hostname check runs again inside the browser via Playwright route interception on
  every main-frame document request — this is what catches a redirect to an internal address
  *after* the initial URL already passed validation, including the cloud metadata address
  (`169.254.169.254`) and IPv6 loopback (`::1`).
- Main document response size is capped (`max_response_body_bytes`) before any content is
  extracted.
- Every navigation has a hard timeout (`navigation_timeout_ms`).
- No active probing of any kind — this only observes what the target willingly serves when
  loaded normally, the same as a real visitor's browser would.

**Residual, honestly-stated risk:** this validates DNS resolution *before* each navigation, not
the live TCP connection's actual peer address. A sufficiently time-boxed DNS-rebinding attack
(the DNS record changing between the check and Chromium's own connect) is a known, hard-to-fully
close gap for any scanner built on a full browser engine rather than a hand-rolled HTTP client
with IP pinning. This closes the common cases without claiming to be a formally proven SSRF-proof
system.

## Tests performed (manual, against this running instance)

| Case | Target | Result |
|---|---|---|
| Normal public site | `https://example.com` | ✅ Full extraction, both screenshots, both Lighthouse runs (Performance 100, Accessibility 96, SEO 80, Best Practices 100) |
| Redirects | `http://github.com` | ✅ `was_redirected: true`, `redirect_chain` and `final_url` correctly captured |
| Slow loading | `https://httpbin.org/delay/3` | ✅ Completes normally within the navigation timeout |
| Invalid URL | `""`, `"not a url"`, `"ftp://example.com"` | ✅ Rejected with 422/400 and a specific reason each |
| Unresolvable domain | `http://this-domain-does-not-exist-xyz123.invalid` | ✅ 400 `dns_resolution_failed` |
| localhost | `http://localhost:8787` | ✅ 400 `blocked_host` |
| Private/internal IPs | `127.0.0.1`, `169.254.169.254` (cloud metadata), `10.0.0.1`, `192.168.1.1`, `::1` | ✅ All 400 `private_address_blocked` |
| Fails to load | `https://expired.badssl.com` (expired cert) | ✅ `status: "failed"`, meaningful error (`net::ERR_CERT_DATE_INVALID`), no fake score |
| Status/results lifecycle | — | ✅ `/results` returns 409 while running, 404 for an unknown scan_id, the error object for a failed scan |

Not yet exercised: a target whose Lighthouse run specifically fails while the browser scan
succeeds (the degrade-gracefully code path exists and was exercised indirectly while fixing a
real Windows `npx` resolution bug and a Lighthouse desktop-preset bug during development, but
wasn't separately tested against a live site that reliably fails only Lighthouse).

## Known limitations

- **In-memory scan store** — restarting the process loses all scan records (not results files
  on disk, just the ability to look them up by scan_id). Fine for this phase; would need Redis
  or a DB for anything long-lived.
- **Lighthouse is disabled by default in `config.py`** (`lighthouse_enabled`/
  `lighthouse_mobile_enabled`) — confirmed live on Render's free tier (512MB RAM, shared with
  the Python/uvicorn process) that Lighthouse's own separately-launched Chrome process reliably
  OOM-restarts the whole container mid-scan, even after both fixing `LIGHTHOUSE_CHROME_PATH`
  resolution (see the Dockerfile's `entrypoint.sh`) and trimming Chrome's launch flags for
  memory. Screenshots, console/network capture, and SEO/content extraction are unaffected and
  work reliably on the free tier — only Lighthouse needs more headroom. Set `LIGHTHOUSE_ENABLED`
  and `LIGHTHOUSE_MOBILE_ENABLED` to `true` on a plan with more memory (Render's `starter` tier
  or above) to turn it back on.
- **Lighthouse requires Node.js in the runtime environment** — this is the one place the
  backend needs both language runtimes; the Dockerfile installs Node explicitly for this
  reason. A plain `pip install`-only deployment (no Docker, no Node) will run the browser scan
  fine but Lighthouse will come back `unavailable`.
- **No rate limiting / queueing beyond a concurrency semaphore** (`max_concurrent_scans`) —
  fine for a demo; a public-facing deployment would want per-IP rate limiting.
- **Main-document response size is capped, but total page weight (all subresources) isn't** —
  a page with huge subresources could still take a while to fully load within the navigation
  timeout.
