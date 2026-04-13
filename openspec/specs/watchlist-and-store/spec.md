# Watchlist and Store

## Purpose
watchlist と store は、定期調査対象の管理・調査 run の記録・finding の重複排除付き保存・通知 delivery を提供する。

## Requirements

### Requirement: Watchlist topics are managed as named scheduled entries
The system SHALL manage watchlist topics as named records with optional search query overrides and a schedule.

#### Scenario: Topic is added with defaults
- GIVEN 利用者が `watchlist add <topic>` を実行する
- WHEN topic を追加する
- THEN named topic record を作成または更新する
- AND 既定 schedule は `0 8 * * *` になる

#### Scenario: Weekly schedule is requested
- GIVEN 利用者が `watchlist add <topic> --weekly` を実行する
- WHEN topic を追加する
- THEN schedule は `0 8 * * 1` になる

#### Scenario: Custom search queries are supplied
- GIVEN 利用者が `--queries` を指定する
- WHEN topic を追加する
- THEN watchlist は query list を JSON として保存する

### Requirement: Removing a topic cascades its stored history
The system SHALL remove findings and research runs when a topic is deleted from the watchlist.

#### Scenario: Existing topic is removed
- GIVEN topic が watchlist と store に存在する
- WHEN `watchlist remove <topic>` を実行する
- THEN topic record は削除される
- AND related research runs は削除される
- AND related findings は削除される

#### Scenario: Nonexistent topic is removed
- GIVEN 指定 topic が存在しない
- WHEN `watchlist remove <topic>` を実行する
- THEN `not_found` 応答を返す
- AND 副作用は発生しない

### Requirement: Run-one executes quick JSON research over a 90-day window
The system SHALL run watchlist research by invoking `last30days.py` in JSON quick mode with a 90-day lookback.

#### Scenario: Watchlist topic runs successfully
- GIVEN enabled topic が存在する
- WHEN watchlist がその topic を実行する
- THEN subprocess で `last30days.py <search_term> --emit=json --quick --lookback-days 90` を呼び出す
- AND report を finding に変換して保存する
- AND `completed` status と new/updated 件数を返す

#### Scenario: Topic-specific search query override exists
- GIVEN topic に保存済み search query list がある
- WHEN watchlist がその topic を実行する
- THEN query list の先頭要素を search term として使う
- AND topic 名そのものは search term に使わない

### Requirement: Failed watchlist runs are recorded as failed runs
The system SHALL record failed research runs with a failed status and a user-visible error result.

#### Scenario: Research subprocess returns non-zero
- GIVEN `last30days.py` subprocess が non-zero で終了する
- WHEN watchlist が結果を処理する
- THEN research run は `failed` として更新される
- AND stderr の一部を error message として保持する
- AND watchlist result は failed status を返す

#### Scenario: Research subprocess times out
- GIVEN subprocess が 300 秒以内に完了しない
- WHEN watchlist が timeout を検出する
- THEN research run は `failed` として更新される
- AND result は `timeout` error を返す

### Requirement: Run-all respects the daily budget cap
The system SHALL skip additional watchlist topics once the configured daily budget has been reached.

#### Scenario: Budget already exceeded before a topic starts
- GIVEN `daily_budget` を超える token cost が既に記録されている
- WHEN `watchlist run-all` を実行する
- THEN 追加 topic は research を開始しない
- AND 各 topic を `skipped` として返す
- AND skip reason に現在コストと budget 上限を含める

### Requirement: Delivery notifications are optional and non-blocking
The system SHALL send delivery notifications only when configured and only for runs with new findings.

#### Scenario: Delivery channel is configured and new findings exist
- GIVEN delivery channel が設定されている
- AND run の `new` 件数が 1 以上である
- WHEN watchlist run が完了する
- THEN configured webhook に通知を送る

#### Scenario: No new findings or no channel configured
- GIVEN delivery channel が空である、または `new` 件数が 0 である
- WHEN watchlist run が完了する
- THEN delivery は行わない

#### Scenario: Delivery fails
- GIVEN webhook delivery が例外を投げる
- WHEN watchlist run が通知を試みる
- THEN watchlist run 自体は失敗扱いにしない
- AND delivery failure は標準エラーに記録される

### Requirement: Findings are deduplicated by source URL
The system SHALL deduplicate persisted findings by `source_url` across runs.

#### Scenario: New finding with a new URL
- GIVEN finding の URL が store に存在しない
- WHEN `store_findings()` を実行する
- THEN finding は新規行として保存される
- AND `new` 件数が増える

#### Scenario: Finding with an existing URL is re-sighted
- GIVEN 同じ `source_url` を持つ finding が既に存在する
- WHEN `store_findings()` を実行する
- THEN 新規行は作られない
- AND既存 finding の `last_seen` を更新する
- AND `sighting_count` を 1 増やす
- AND `engagement_score` は既存値と新値の最大値で更新する

#### Scenario: Finding lacks a URL
- GIVEN finding に `source_url` も `url` も無い
- WHEN `store_findings()` を実行する
- THEN その finding は保存しない

### Requirement: Findings extraction prefers ranked candidates but preserves HN and Polymarket raw items
The system SHALL convert reports to persisted findings by preferring ranked candidates and supplementing with selected raw-source items.

#### Scenario: Ranked candidates exist
- GIVEN report に ranked candidates がある
- WHEN `findings_from_report()` を実行する
- THEN ranked candidates を優先して finding に変換する
- AND candidate URL を重複検知に使う

#### Scenario: HN or Polymarket raw items were not ranked
- GIVEN `hackernews` または `polymarket` の item が ranked candidates に入っていない
- WHEN `findings_from_report()` を実行する
- THEN それら raw item も persistence 用 finding として補完する

### Requirement: Store exposes operator-facing query and search commands
The system SHALL provide CLI access to query findings, full-text search, trending topics, and stats.

#### Scenario: Query findings for a topic
- GIVEN operator が `store.py query <topic>` を実行する
- WHEN topic が存在する
- THENその topic の findings 一覧を JSON で返す

#### Scenario: Search findings full-text
- GIVEN operator が `store.py search <query>` を実行する
- WHEN FTS search を行う
- THEN relevance 順の結果を JSON で返す

#### Scenario: No store command is supplied
- GIVEN operator が subcommand 無しで `store.py` を実行する
- WHEN CLI が起動する
- THEN help を表示して終了コード 1 で終了する
