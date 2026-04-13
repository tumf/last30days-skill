## Implementation Tasks

- [ ] Add an `xcom-rs` X adapter module that executes `xcom-rs` via `dotenvx`, parses JSON output, and normalizes tweet/search results for the pipeline (verification: integration - `uv run pytest -q tests/test_xcom_rs_x.py`)
- [ ] Update X backend resolution in runtime/config code to support `xcom_rs`, define backend precedence, and expose status metadata for diagnostics (verification: unit - `uv run pytest -q tests/test_env_x_backend.py`)
- [ ] Replace Bird-only supplemental handle search wiring in the pipeline with adapter-compatible targeted search behavior using `from:<handle>` queries (verification: integration - `uv run pytest -q tests/test_pipeline_x_backend.py -k xcom_rs`)
- [ ] Update diagnostic/UI output and setup-facing help text to describe `xcom-rs` prerequisites and migration expectations (verification: unit - `uv run pytest -q tests/test_ui_v3.py -k xcom`)
- [ ] Update operator/skill documentation for X search runtime expectations, including mini-specific invocation assumptions and migration notes (verification: manual - review `skills/last30days/SKILL.md`, `AGENTS.md`, and any changed docs for consistency)
- [ ] Run repository verification for the change set and confirm proposal-linked implementation paths remain green (verification: integration - `uv run pytest -q`)

## Future Work

- If legacy Bird support is retained temporarily, decide when to formally deprecate and remove it after `xcom-rs` rollout is stable.
- If `xcom-rs` command output evolves, add a version-compatibility policy or adapter contract tests against pinned CLI versions.
