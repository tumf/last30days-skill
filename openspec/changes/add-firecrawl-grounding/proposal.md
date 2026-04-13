---
change_type: implementation
priority: medium
dependencies: []
references:
  - scripts/lib/grounding.py
  - scripts/lib/pipeline.py
  - scripts/lib/resolve.py
  - scripts/lib/env.py
  - scripts/lib/setup_wizard.py
  - scripts/lib/ui.py
  - README.md
  - SKILL.md
  - skills/last30days/SKILL.md
---

# Add Firecrawl Grounding Backend

**Change Type**: implementation

## Problem/Context

The current native web grounding path treats `BRAVE_API_KEY`, `EXA_API_KEY`, `SERPER_API_KEY`, and `PARALLEL_API_KEY` as supported backends, but it does not support Firecrawl even though the desired change in this session is to use Firecrawl instead of Brave for grounded web search. The repo currently wires backend selection and diagnostics through `scripts/lib/grounding.py`, `scripts/lib/pipeline.py`, `scripts/lib/resolve.py`, `scripts/lib/env.py`, `scripts/lib/setup_wizard.py`, and `scripts/lib/ui.py`, and the current docs and tests still present Brave as the default web-search option.

## Proposed Solution

Add Firecrawl as a first-class native web grounding backend keyed by `FIRECRAWL_API_KEY`, using Firecrawl's `/v2/search` API for search-only grounding results. Align the proposal with the current canonical spec split by expressing setup/config behavior under `configuration-and-setup`, CLI diagnostics under `cli-runtime`, and backend-specific grounding behavior under a dedicated `web-grounding` capability. Update backend auto-selection, source availability detection, diagnostics, setup reporting, UI copy, and user-facing docs so that Firecrawl becomes the recommended web backend while keeping Brave compatibility for existing users.

## Acceptance Criteria

- `scripts/lib/grounding.py` supports an explicit `firecrawl` backend and auto-selects it when `FIRECRAWL_API_KEY` is configured.
- Firecrawl search requests normalize returned items into the same result shape used by existing grounding backends, including title, URL, snippet/body text, and date metadata when available.
- Firecrawl date filtering uses the existing `date_range` input and maps it to a Firecrawl-compatible time filter so auto-resolve and grounding searches stay constrained to the requested window.
- `scripts/lib/pipeline.py`, `scripts/lib/resolve.py`, `scripts/lib/env.py`, and `scripts/lib/setup_wizard.py` treat `FIRECRAWL_API_KEY` as a supported grounding/backend credential.
- `scripts/lib/ui.py`, `README.md`, `SKILL.md`, and `skills/last30days/SKILL.md` describe Firecrawl as the recommended native web-search option while documenting Brave as a compatibility path.
- Regression coverage exists for backend detection/priority, setup detection, UI diagnostics, and resolve behavior affected by the new backend.
- If `scripts/`, `SKILL.md`, or `skills/last30days/SKILL.md` change, `bash scripts/sync.sh` remains part of the implementation verification plan.

## Out of Scope

- Replacing non-grounding search sources with Firecrawl.
- Enabling Firecrawl scrape/crawl features for this change; the initial integration is search-only.
- Removing Brave support or migrating existing user configuration automatically.
