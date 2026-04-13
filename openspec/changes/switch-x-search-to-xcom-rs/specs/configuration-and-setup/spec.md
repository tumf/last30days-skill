## MODIFIED Requirements

### Requirement: X backend resolution is explicit

The system SHALL resolve the X retrieval backend from explicit credentials, local CLI prerequisites, and backend preferences.

#### Scenario: xcom-rs is explicitly preferred and available
- GIVEN `LAST30DAYS_X_BACKEND=xcom_rs` である
- AND `xcom-rs` と `dotenvx` が利用可能である
- AND `xcom-rs` が必要な認証コンテキストで読み取り検索を実行できる
- WHEN X backend を解決する
- THEN X source は `xcom_rs` になる

#### Scenario: xcom-rs is preferred automatically on mini when available
- GIVEN `LAST30DAYS_X_BACKEND` が未指定である
- AND `xcom-rs` と `dotenvx` が利用可能である
- AND `xcom-rs` が必要な認証コンテキストで読み取り検索を実行できる
- WHEN X backend を解決する
- THEN X source は `xcom_rs` になる
- AND `xai` や legacy Bird より優先される

#### Scenario: xAI key is present and xcom-rs is unavailable
- GIVEN `XAI_API_KEY` が設定されている
- AND `xcom-rs` prerequisites は満たされない
- WHEN X backend を解決する
- THEN X source は `xai` になる

#### Scenario: Explicit Bird cookies are present for legacy fallback
- GIVEN `AUTH_TOKEN` と `CT0` がある
- AND legacy Bird backend が互換モードで有効化されている
- AND `xcom-rs` prerequisites は満たされない
- WHEN X backend を解決する
- THEN X source は `bird` になる

#### Scenario: No explicit X backend is usable
- GIVEN `xcom-rs` prerequisites も `XAI_API_KEY` も `AUTH_TOKEN`/`CT0` も利用できない
- WHEN X backend を解決する
- THEN X source は未設定として扱う

### Requirement: Setup and diagnostics report xcom-rs prerequisites for X retrieval

The system SHALL describe `xcom-rs` prerequisites and the resolved X backend in diagnostic and setup-oriented status output.

#### Scenario: Diagnose mode reports xcom-rs backend metadata
- GIVEN X backend として `xcom_rs` が解決されている
- WHEN 診断または source status を出力する
- THEN resolved backend は `xcom_rs` として表示される
- AND operator が必要な local prerequisites を判別できる情報を含む

#### Scenario: Missing xcom-rs prerequisites are explained
- GIVEN X retrieval が `xcom-rs` prerequisites 不足で利用できない
- WHEN 診断または source status を出力する
- THEN 不足している prerequisite を明示する
- AND Bird cookies ではなく `xcom-rs` setup を優先 remediation として案内する
