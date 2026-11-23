# SitePlus (WebRate AI)

SitePlus evaluates a submitted website URL across **12 weighted categories** — UI, UX,
Performance, SEO, Accessibility, Mobile, Security, Content, Conversion, Trust, Technical,
Innovation — and returns one overall score, category-level findings, and actionable
recommendations. Every finding is generated from real, passively-collected evidence: nothing is
hardcoded, randomized, or invented.

The project is a Next.js frontend talking to a separate FastAPI backend. It was built in four
phases, each adding a layer on top of the last; this README walks through what each layer does
and where to find it in the code.

## At a glance

```
Submitted URL
  → Phase 2: real browser scan (Playwright)            backend/scanner/
  → Phase 3: 12 category analyzers score the evidence   backend/services/analyzers/
  → Phase 4: confidence scoring, multi-page crawling,   backend/services/confidence_engine.py
             a benchmark that measures detection          backend/services/validation_engine.py
             accuracy, and an optional LLM SEO layer       backend/benchmark/
  → Dashboard renders the real result                   src/app/dashboard/
```

## Repository layout

```
siteplus/
├── src/                        Next.js frontend (App Router, TypeScript, Tailwind v4, shadcn/ui)
│   ├── app/
│   │   ├── page.tsx              Marketing landing page (hero, URL input, category breakdown)
│   │   ├── scanning/              Animated scan-in-progress page, threads the URL to the backend
│   │   └── dashboard/
│   │       ├── page.tsx           Overview — overall score, grade, top recommendations
│   │       ├── evaluation/        Full table of all 12 categories
│   │       ├── categories/        Per-category deep dive (what was tested/passed/failed/why)
│   │       ├── recommendations/   All fixes, ranked, with Quick Win / Critical Fix / Long-Term filters
│   │       ├── reports/           Full printable summary + confidence distribution + benchmark accuracy
│   │       └── raw-scan/          Raw Phase 2 evidence (screenshots, Lighthouse, console/network)
│   ├── components/dashboard/      EvaluationDataProvider (demo-vs-real data switch), score/issue UI
│   ├── lib/
│   │   ├── categories.ts          The 12 categories + weights — single source of truth
│   │   ├── scoring.ts             Overall-score formula + grade thresholds (mirrored in the backend)
│   │   ├── scan-api.ts            Client for Phase 2's scan endpoints
│   │   └── evaluation-api.ts      Client for Phase 3/4's evaluation endpoints
│   └── data/demo-results.ts       Fixed demo dataset — what renders when no backend is scanning
│
└── backend/                    FastAPI backend (Python)
    ├── main.py                    App entrypoint, mounts every router below
    ├── config.py                  All settings (timeouts, feature flags, API keys), one place
    ├── scanner/                   Phase 2: Playwright-driven real browser scanning
    ├── security/url_validation.py SSRF/DNS-rebinding defense — every scan target passes through this
    ├── models/                    Pydantic schemas (scan results, evaluation results, website results)
    ├── services/
    │   ├── analyzers/              The 12 category analyzers (Phase 3)
    │   ├── evaluation_engine.py     Runs all 12 + merges in the optional LLM layer (Phase 4)
    │   ├── scoring_engine.py        Overall-score formula + per-category explanations
    │   ├── confidence_engine.py     Confidence/verification tagging per finding (Phase 4)
    │   ├── validation_engine.py     Same-page duplicate detection (Phase 4)
    │   ├── website_evaluation_service.py / site_crawler.py   Multi-page crawling (Phase 4)
    │   ├── calibration.py           Reads real benchmark output, flags miscalibration
    │   ├── llm_seo_agent.py         Optional OpenAI-based SEO judgment layer (Phase 4)
    │   └── recommendation_engine.py Aggregates + classifies recommendations
    ├── api/                        scan_routes.py, evaluation_routes.py, website_routes.py, benchmark_routes.py
    ├── benchmark/                  Phase 4's precision/recall/F1 framework — see below
    └── tests/                      94 pytest tests covering all of the above
```

## The evaluation pipeline, step by step

1. **Submit a URL** (landing page, or `POST /api/scans`). `security/url_validation.py` rejects
   anything that isn't a public http(s) host — localhost, private IPs, and cloud metadata
   addresses are all blocked before Chromium ever connects, and redirects are re-checked on
   every hop.
2. **Real browser scan** (`scanner/browser.py`) — Playwright loads the page at both desktop and
   mobile viewports (plus a tablet re-measurement, no extra navigation) and collects: the
   rendered DOM, console errors, failed network requests, response headers, redirect chain,
   screenshots, real axe-core accessibility results, TLS details, per-image dimensions/format,
   typography/alignment signals, and (optionally) Lighthouse scores.
3. **Extraction** (`scanner/page_extractor.py`) parses that into structured data: title, meta
   description, heading hierarchy, internal/external links, structured data (JSON-LD), forms,
   and page-type signals (about/contact/privacy/terms/social links).
4. **12 analyzers run** (`services/analyzers/*.py`, triggered via `POST /api/evaluate`) — each
   one independently inspects the relevant evidence and produces pass/fail/unavailable checks.
   A check is `unavailable` (never silently "pass") when the needed evidence genuinely couldn't
   be collected — missing data is never scored as a failure.
5. **Confidence + validation** (`services/confidence_engine.py`,
   `services/validation_engine.py`) — every finding gets tagged with how directly its evidence
   supports it (a missing HTML attribute is near-certain; a 44px touch-target threshold or an
   LLM's qualitative judgment is marked lower-confidence and flagged `needs_review`), and
   same-page duplicates are collapsed.
6. **Optional LLM SEO layer** (`services/llm_seo_agent.py`) — if `OPENAI_API_KEY` is set, adds a
   qualitative pass on top of the rule-based SEO checks (title/content quality, keyword
   coverage), grounded in the same real evidence. With no key set, this is a no-op with zero
   network calls.
7. **Scoring** (`services/scoring_engine.py`) — `Overall Score = Σ(category score × weight) /
   Σ(weight of scored categories)`, renormalized when some categories have no evidence, so
   missing data never silently inflates or deflates the score. Every category also gets a
   one-line explanation of exactly why it scored what it did.
8. **Recommendations** (`services/recommendation_engine.py`) — one per issue, with root cause,
   step-by-step fix, priority, and a Quick Win / Critical Fix / Long-Term classification.
9. **Multi-page sites** (`services/website_evaluation_service.py`, via
   `POST /api/website/evaluate`) — discovers same-domain pages from the sitemap and nav links,
   runs steps 2–8 per page, and aggregates: sitewide recurring issues are grouped once (not
   double-counted), and genuinely broken internal links are detected using other crawled pages'
   real status codes.
10. **Dashboard** renders the result. With no backend configured, every page falls back to the
    fixed demo dataset (`src/data/demo-results.ts`) — the same visual experience either way.

## The 12 categories

| Category | Weight |
|---|---:|
| UI & Visual Design | 12% |
| UX & Navigation | 12% |
| Performance | 12% |
| SEO | 10% |
| Accessibility | 10% |
| Mobile Responsiveness | 10% |
| Security & Privacy | 8% |
| Content Quality | 7% |
| Conversion | 7% |
| Trust & Credibility | 5% |
| Technical Quality | 5% |
| Innovation | 2% |

Defined once in `src/lib/categories.ts`; the backend's `CATEGORY_WEIGHTS` in
`backend/models/evaluation_models.py` is checked against it in `backend/tests/test_scoring.py`
so the two can never silently drift apart.

## Running it locally

**Frontend:**
```bash
npm install
npm run dev          # http://localhost:3000
```

**Backend:**
```bash
cd backend
python -m venv venv && source venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
python -m playwright install chromium
cp .env.example .env    # see backend/README.md for what to set
uvicorn main:app --reload --port 8787
```

Then set `NEXT_PUBLIC_API_URL=http://127.0.0.1:8787` in `.env.local` so the frontend talks to
your local backend instead of showing demo data. Full backend details — deployment, security
model, known limitations — are in `backend/README.md`.

## The benchmark (`backend/benchmark/`)

A real precision/recall/F1 framework, not a claimed number: 6 hand-authored local fixture pages
with precisely known, verified defects, served by a tiny local server, scanned through the
actual production pipeline. Run it with:

```bash
cd backend
python -m benchmark.runner
```

It prints and saves (`benchmark/results/latest.json`) precision/recall/F1 overall and per
category, false-positive/negative rates, and confidence calibration (do true positives actually
get rated more confidently than false positives?). `services/calibration.py` reads that output
and flags signs of miscalibration — it does not change scoring weights automatically; the spec
this project follows is explicit that weights must not change without benchmark evidence to
justify it.

This validates correctness on 6 reproducible fixtures, not real-world accuracy across the full
diversity of live websites — that's stated plainly in the benchmark's own output, not glossed
over.

## Testing

```bash
cd backend
pip install -r requirements-dev.txt
pytest tests/ -q     # 94 tests, ~15s, includes a live end-to-end benchmark run
```

Frontend: `npx tsc --noEmit`, `npx eslint src/`, `npm run build`.

## Known limitations

- In-memory stores only (scans, evaluations, benchmark results on disk but no history across
  restarts) — fine for this phase, would need a database for anything long-lived.
- No multi-page comparison UI yet — the backend capability (`/api/website/evaluate`) is built
  and tested, but the frontend's scanning flow is still single-page; a new entry point for
  "scan a whole site" is a separate follow-on, not an upgrade to an existing page.
- Lighthouse and the LLM SEO layer are both off by default (the former due to free-tier hosting
  memory limits, the latter because it needs your own `OPENAI_API_KEY`) — see
  `backend/README.md` for how to turn each on.
