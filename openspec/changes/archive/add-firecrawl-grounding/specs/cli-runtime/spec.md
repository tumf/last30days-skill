## MODIFIED Requirements

### Requirement: CLI は診断専用モードを提供する
The system SHALL provide a diagnostic mode that reports provider availability, source availability, and the selected native web backend without running research.

#### Scenario: Diagnose mode requested
- GIVEN 利用者が `--diagnose` を指定する
- WHEN CLI を実行する
- THEN provider availability と source availability を JSON として出力する
- AND native web backend 情報も JSON に含める
- AND 調査 pipeline は実行しない

#### Scenario: Diagnose mode reports Firecrawl backend
- GIVEN `FIRECRAWL_API_KEY` が設定されている
- WHEN 利用者が `--diagnose` を実行する
- THEN `available_sources` に `grounding` を含む
- AND `native_web_backend` は `firecrawl` を返す
