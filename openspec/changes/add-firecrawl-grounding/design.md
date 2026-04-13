# Design: Firecrawl grounding backend

## Overview

This change adds Firecrawl as a native grounding backend for `/last30days` without changing the higher-level grounding contract used by pipeline, resolve, and rendering code. The integration remains search-only and uses the existing `grounding.web_search(query, date_range, config, backend="auto") -> tuple[list[dict], dict]` boundary.

## Existing constraints

- `scripts/lib/grounding.py` owns backend auto-selection and explicit backend dispatch.
- `scripts/lib/pipeline.py` determines whether `grounding` is available and reports the selected native backend in diagnostics.
- `scripts/lib/resolve.py` depends on `grounding.web_search(...)` for auto-resolve and only needs normalized search results.
- `scripts/lib/env.py` is the source of truth for supported environment keys.
- `scripts/lib/setup_wizard.py` and `scripts/lib/ui.py` surface setup hints and backend availability to users.
- Repo instructions require `uv run pytest -q` for verification, and `bash scripts/sync.sh` when `scripts/` or `SKILL.md` changes.

## Proposed backend contract

### Credential

- Add `FIRECRAWL_API_KEY` to env/config loading.
- Treat Firecrawl as available when that key is present.

### Dispatch and priority

- Support `backend="firecrawl"` explicitly in `grounding.web_search(...)`.
- Update `backend="auto"` selection order to prefer Firecrawl over Brave while preserving existing fallback behavior for Exa, Serper, Parallel, and Brave.

Recommended auto-selection order:
1. `firecrawl`
2. `exa`
3. `serper`
4. `parallel`
5. `brave`

This matches the session goal of moving from Brave to Firecrawl without breaking existing Brave users.

### Request/response mapping

Firecrawl `/v2/search` returns result groups such as `web`, `news`, and `images`. This integration should request standard web search results only and normalize them into the existing grounding item shape.

Normalized item fields should include:
- `title`
- `url`
- `snippet` (mapped from Firecrawl `description` or equivalent text summary)
- `published_at` when Firecrawl returns usable date metadata
- `source` set to the existing grounding/web source convention used by the caller

The returned artifact should identify the backend as Firecrawl and include result count metadata similar to current backends.

## Date filtering

The repo already passes `(from_date, to_date)` into grounding. Firecrawl supports `tbs` values and custom date ranges, so this change should convert the existing ISO range into a Firecrawl custom range string.

Recommended mapping:
- `cdr:1,cd_min:MM/DD/YYYY,cd_max:MM/DD/YYYY`

This keeps behavior aligned with current exact date-window expectations instead of relying on a coarse `qdr:m` approximation.

## Why search-only

Search-only is sufficient for the current grounding use cases because:
- `resolve.py` extracts subreddits, X handles, GitHub users/repos, and short context summaries from titles/snippets/URLs.
- Existing grounding consumers do not require full-page markdown.
- Avoiding scrape-on-search keeps latency and Firecrawl credit usage lower.

A later proposal can add scrape-backed enrichment if the product needs deeper web evidence.

## Verification strategy

- Unit coverage for dispatch, priority, explicit backend validation, and Firecrawl response normalization belongs in `tests/test_grounding_v3.py`.
- Backend detection changes belong in `tests/test_resolve.py` and `tests/test_setup_openclaw.py`.
- Diagnostic copy changes belong in `tests/test_ui_v3.py`.
- Repo-level verification remains `uv run pytest -q`, with `bash scripts/sync.sh` required because this proposal targets `scripts/` and skill docs.
