## MODIFIED Requirements

### Requirement: OpenClaw setup probe reports tools and key presence
The system SHALL provide a server-side setup probe for OpenClaw without requiring browser access.

#### Scenario: OpenClaw setup probe reports Firecrawl credential availability
- GIVEN `FIRECRAWL_API_KEY` が設定されている
- WHEN `run_openclaw_setup()` を実行する
- THEN 返却される key availability に Firecrawl が含まれる
- AND Firecrawl key は present として報告される

## ADDED Requirements

### Requirement: Native web setup guidance recommends Firecrawl
The system SHALL present Firecrawl as the recommended native web grounding credential in setup and diagnostic guidance while preserving Brave compatibility messaging for existing users.

#### Scenario: Web setup guidance is shown without a native web backend
- GIVEN 利用者が `FIRECRAWL_API_KEY` も `BRAVE_API_KEY` も持っていない
- WHEN setup または diagnostic UI が web grounding 有効化手順を表示する
- THEN `FIRECRAWL_API_KEY` を推奨として案内する
- AND Brave は互換オプションとしてのみ案内できる
