---
change_type: implementation
priority: medium
dependencies: []
references:
  - scripts/lib/pipeline.py
  - scripts/lib/env.py
  - scripts/lib/schema.py
  - scripts/lib/ui.py
  - scripts/lib/bird_x.py
  - skills/last30days/SKILL.md
  - AGENTS.md
---

# switch-x-search-to-xcom-rs

**Change Type**: implementation

## Problem / Context

- The current X retrieval path only supports `bird` and `xai` backends in `scripts/lib/pipeline.py`.
- The repo currently treats Bird cookies (`AUTH_TOKEN` / `CT0`) or `XAI_API_KEY` as the only X search prerequisites, which does not match the desired `xcom-rs` CLI workflow on mini.
- Session context established that the desired direction is to invoke `xcom-rs` as a CLI boundary rather than wiring direct X API requests into `last30days` itself.
- mini machine conventions already define the required invocation shape for `xcom-rs`: `dotenvx run -f ~/.env -- xcom-rs ... --output json --non-interactive`.

## Proposed Solution

- Add an `xcom-rs`-backed X search adapter for `last30days` that executes `xcom-rs` in non-interactive JSON mode and normalizes results into the existing X item shape.
- Update runtime backend selection so X search can resolve to `xcom_rs`, while preserving compatibility behavior for existing `xai` / legacy `bird` flows during migration.
- Replace Bird-specific handle-search assumptions in the pipeline with an adapter-compatible targeted search flow using `from:<handle>` queries through `xcom-rs`.
- Update diagnostics and operator-facing documentation so setup and status output describe `xcom-rs` requirements instead of Bird cookies as the primary path.

## Acceptance Criteria

1. `last30days` can execute X searches through `xcom-rs` CLI without adding direct X API HTTP calls to the Python codebase.
2. Runtime selection and diagnostics can report `xcom_rs` as an X backend and explain the required local prerequisites clearly.
3. Primary X search and supplemental handle-based search both work through the adapter and return normalized items compatible with the current ranking pipeline.
4. Existing X backend behavior remains explicitly defined during migration, with clear precedence and fallback rules.
5. Documentation and skill/runtime expectations describe `xcom-rs` as the intended mini workflow for X retrieval.

## Out of Scope

- Posting, replying, likes, or any other write operation through `xcom-rs`.
- Changing `xcom-rs` internals or adding new commands to the external repository.
- Eliminating X API usage inside `xcom-rs` itself.
