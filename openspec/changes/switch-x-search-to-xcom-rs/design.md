# Design: switch-x-search-to-xcom-rs

## Overview

This change replaces the current assumption that `last30days` should search X through either a vendored Bird wrapper or xAI-native X search. The new preferred path is an adapter that shells out to `xcom-rs` in JSON mode and converts the response into the existing normalized X item format already consumed by ranking and clustering.

## Goals

- Keep `last30days` free of direct X API HTTP wiring.
- Preserve the current pipeline contract for normalized X items.
- Support both general X search and supplemental `from:<handle>` search.
- Align repo diagnostics and documentation with mini machine operating rules.

## Non-Goals

- Reworking ranking/clustering semantics for X items.
- Adding public write operations through `xcom-rs`.
- Redesigning the overall source planner.

## Proposed Architecture

### New adapter

Add a module such as `scripts/lib/xcom_rs_x.py` with responsibilities similar to the current Bird adapter:

- detect whether `xcom-rs`, `dotenvx`, and the required auth context are available
- execute commands in the required mini-safe form
- translate `depth` into result limits/timeouts
- implement retry behavior when a query returns zero results
- normalize `xcom-rs` JSON envelopes into the existing X item schema

### Pipeline integration

Update `scripts/lib/pipeline.py` so the X source branch can dispatch to `xcom_rs` for:

- primary search for planner-emitted X subqueries
- supplemental handle search using `from:<handle>` query construction

The pipeline should keep consuming normalized items and should not need to understand raw `xcom-rs` output shapes.

### Runtime/backend selection

Update `scripts/lib/schema.py` and `scripts/lib/env.py` so runtime selection can represent `xcom_rs` explicitly.

Recommended backend precedence:

1. explicit `LAST30DAYS_X_BACKEND=xcom_rs`
2. explicit `LAST30DAYS_X_BACKEND=xai`
3. legacy `bird` only when intentionally configured during migration
4. default automatic preference for `xcom_rs` when available on mini

This preserves a clear migration path while making the intended backend obvious.

## Command Contract

The adapter should invoke `xcom-rs` with the mini-specific wrapper:

```bash
dotenvx run -f ~/.env -- xcom-rs search recent "<query>" --limit <n> --output json --non-interactive
```

For targeted handle search, the adapter should emit query strings like:

```text
from:<handle> <core topic> since:YYYY-MM-DD until:YYYY-MM-DD
```

## Query Behavior

The adapter should preserve the current Bird search ergonomics where reasonable:

- extract a compact core subject from verbose planner queries
- search with date bounds
- retry with OR-group or shortened queries on zero-result responses
- score relevance locally from the normalized tweet text when the CLI does not provide ranking scores

## Diagnostics and UX

`show_diagnostic_banner()` and related status helpers should describe `xcom-rs` as the intended X retrieval path and explain missing prerequisites in operator terms.

Examples:

- `xcom-rs not installed`
- `dotenvx unavailable`
- `XCOM_RS_BEARER_TOKEN not available through ~/.env`

Bird-specific wording should no longer be the primary guidance.

## Risks and Mitigations

### Risk: CLI output drift

`xcom-rs` may evolve its JSON payload.

Mitigation:
- parse the documented envelope conservatively
- add adapter-focused tests with fixture payloads
- pin expectations to fields required by normalization only

### Risk: migration ambiguity

Supporting multiple backends can create unclear precedence.

Mitigation:
- centralize precedence in `env.py`
- expose the resolved backend in diagnostics and report runtime metadata

### Risk: local environment mismatch

mini-specific execution depends on `dotenvx` and `~/.env`.

Mitigation:
- explicitly validate prerequisites before selecting `xcom_rs`
- surface actionable diagnostic messages instead of generic X failures

## Verification Strategy

- unit tests for backend selection and diagnostic messaging
- adapter tests for JSON parsing and retry behavior
- pipeline integration tests for targeted handle search and normalized output flow
- full repo test run via `uv run pytest -q`
