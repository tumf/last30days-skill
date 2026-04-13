## Implementation Tasks

- [ ] Add Firecrawl request/normalization support in `scripts/lib/grounding.py`, including explicit `firecrawl` dispatch and `auto` priority ahead of Brave while keeping Brave fallback compatibility. (verification: unit - tests/test_grounding_v3.py)
- [ ] Add `FIRECRAWL_API_KEY` to config loading and backend detection paths in `scripts/lib/env.py`, `scripts/lib/pipeline.py`, `scripts/lib/resolve.py`, and `scripts/lib/setup_wizard.py`. (verification: unit - tests/test_resolve.py tests/test_setup_openclaw.py)
- [ ] Update UI and diagnostics copy in `scripts/lib/ui.py` so native web availability and setup hints mention Firecrawl as the recommended option without regressing Brave wording needed for compatibility. (verification: unit - tests/test_ui_v3.py)
- [ ] Update user-facing documentation in `README.md`, `SKILL.md`, and `skills/last30days/SKILL.md` to recommend `FIRECRAWL_API_KEY`, document Brave as compatibility-only, and keep setup guidance aligned with backend behavior. (verification: manual - README.md SKILL.md skills/last30days/SKILL.md plus uv run pytest -q tests/test_ui_v3.py and bash scripts/sync.sh)
- [ ] Run targeted regression coverage for grounding/backend selection and setup/UI behavior. (verification: unit - uv run pytest -q tests/test_grounding_v3.py tests/test_resolve.py tests/test_setup_openclaw.py tests/test_ui_v3.py)
- [ ] Run the repository verification commands required by this repo for touched distribution artifacts. (verification: integration - uv run pytest -q && bash scripts/sync.sh)

## Future Work

- Validate real Firecrawl result quality and cost characteristics with a live key after implementation.
- Consider a follow-up proposal if Firecrawl scrape-backed enrichment is needed beyond search-only grounding.
