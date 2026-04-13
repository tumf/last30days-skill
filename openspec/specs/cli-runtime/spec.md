# CLI Runtime

## Purpose
`last30days.py` はトピック調査 CLI の公開実行面を提供し、診断・調査・保存・setup 呼び出しを単一入口で切り替える。

## Requirements

### Requirement: CLI は Python 3.12 以上でのみ実行できる
The system SHALL reject interpreters older than Python 3.12 before loading runtime modules.

#### Scenario: Unsupported interpreter
- GIVEN 実行中の Python が 3.11 以下である
- WHEN `scripts/last30days.py` を起動する
- THEN 標準エラーに Python 3.12+ 必須であることを表示する
- AND 終了コード 1 で終了する

### Requirement: CLI は source alias を正規化する
The system SHALL normalize `--search` source aliases to canonical runtime source names before execution.

#### Scenario: Web and HN aliases are used
- GIVEN 利用者が `--search=web,reddit,hn` を指定する
- WHEN CLI が引数を解釈する
- THEN `web` は `grounding` に正規化される
- AND `hn` は `hackernews` に正規化される
- AND 重複 source は除去される

#### Scenario: Unknown search source is provided
- GIVEN 利用者が未対応 source を `--search` に含める
- WHEN CLI が引数を解釈する
- THEN CLI は実行を中断する
- AND 無効な source 名を含むエラーを返す

### Requirement: CLI は診断専用モードを提供する
The system SHALL provide a diagnostic mode that reports provider and source availability without running research.

#### Scenario: Diagnose mode requested
- GIVEN 利用者が `--diagnose` を指定する
- WHEN CLI を実行する
- THEN provider availability と source availability を JSON として出力する
- AND 調査 pipeline は実行しない

### Requirement: CLI は depth と lookback を runtime に渡す
The system SHALL translate CLI flags into runtime depth and lookback behavior.

#### Scenario: Quick mode requested
- GIVEN 利用者が `--quick` を指定する
- WHEN CLI が pipeline を呼び出す
- THEN runtime depth は `quick` になる

#### Scenario: Deep mode requested
- GIVEN 利用者が `--deep` を指定する
- WHEN CLI が pipeline を呼び出す
- THEN runtime depth は `deep` になる

#### Scenario: Watchlist-style lookback is requested
- GIVEN 利用者が `--lookback-days 90` を指定する
- WHEN CLI が pipeline を呼び出す
- THEN runtime は 90 日の期間で調査する

### Requirement: CLI は setup を通常調査と分離して扱う
The system SHALL treat `setup` as a dedicated command surface instead of a normal research topic.

#### Scenario: Auto setup requested
- GIVEN 利用者が `python scripts/last30days.py setup` を実行する
- WHEN CLI が command を処理する
- THEN 自動 setup を実行する
- AND setup 結果を標準エラーに要約表示する
- AND 成功時は終了コード 0 を返す

#### Scenario: OpenClaw setup probe requested
- GIVEN 利用者が `python scripts/last30days.py setup --openclaw` を実行する
- WHEN CLI が command を処理する
- THEN OpenClaw 用 setup probe の結果を JSON で出力する
- AND 通常調査は実行しない

#### Scenario: Device auth requested
- GIVEN 利用者が `python scripts/last30days.py setup --device-auth` を実行する
- WHEN CLI が command を処理する
- THEN 完全な device auth フローの結果を JSON で出力する
- AND 通常調査は実行しない

### Requirement: CLI は任意で結果を SQLite に永続化できる
The system SHALL persist research findings only when `--store` is explicitly requested.

#### Scenario: Store flag enabled
- GIVEN 利用者が `--store` を指定して調査を完了する
- WHEN CLI が結果を出力する前に後処理を行う
- THEN report を SQLite findings に変換して保存する
- AND 新規件数と更新件数を標準エラーに表示する

#### Scenario: Store flag omitted
- GIVEN 利用者が `--store` を指定していない
- WHEN 調査が完了する
- THEN SQLite 永続化は行わない

### Requirement: CLI は topic 未指定時に usage エラーを返す
The system SHALL exit with a usage error when no topic or setup command is provided.

#### Scenario: No topic supplied
- GIVEN 利用者が topic を渡さずに CLI を実行する
- WHEN 引数解釈が終わる
- THEN usage を標準エラーに表示する
- AND 終了コード 2 を返す


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