# Configuration and Setup

## Purpose
設定解決と setup フローは、利用可能な source・認証・ローカル依存の有無を決定し、初回利用時のセットアップを最小の操作で完了させる。

## Requirements

### Requirement: Config resolution has explicit precedence
The system SHALL resolve runtime configuration with the precedence `os.environ` > project `.claude/last30days.env` > global `~/.config/last30days/.env`.

#### Scenario: Same key exists in multiple sources
- GIVEN 同じ設定キーが process env と project config と global config に存在する
- WHEN `get_config()` が設定を構築する
- THEN process env の値が採用される
- AND process env に値が無い場合のみ project config が global config を上書きする

#### Scenario: Project config is discovered from a parent directory
- GIVEN 現在の作業ディレクトリ配下ではなく親ディレクトリに `.claude/last30days.env` がある
- WHEN `get_config()` が設定を構築する
- THEN 親方向に探索して最初に見つかった project config を使用する

### Requirement: Browser cookie extraction is opt-in and bounded
The system SHALL only use explicit browser-cookie extraction rules defined for supported services.

#### Scenario: Default browser extraction mode
- GIVEN `FROM_BROWSER` が未設定である
- WHEN browser credential extraction が走る
- THEN Firefox と Safari のみを対象にする
- AND Chrome は既定では対象にしない

#### Scenario: Browser extraction disabled
- GIVEN `FROM_BROWSER=off` である
- WHEN browser credential extraction が走る
- THEN browser cookie extraction は行わない

### Requirement: X backend resolution is explicit
The system SHALL resolve the X retrieval backend from explicit credentials and backend preferences.

#### Scenario: xAI key is present
- GIVEN `XAI_API_KEY` が設定されている
- WHEN X backend を解決する
- THEN X source は `xai` になる
- AND Bird cookie auth の探索は不要である

#### Scenario: Explicit Bird cookies are present
- GIVEN `AUTH_TOKEN` と `CT0` があり Bird CLI が利用可能である
- WHEN X backend を解決する
- THEN X source は `bird` になる

#### Scenario: No explicit X credentials are present
- GIVEN `XAI_API_KEY` も `AUTH_TOKEN`/`CT0` も無い
- WHEN X backend を解決する
- THEN X source は未設定として扱う

### Requirement: Auto setup probes cookies and yt-dlp
The system SHALL run auto setup by probing supported cookie domains and checking `yt-dlp` availability.

#### Scenario: Cookies are found in a browser
- GIVEN サポート対象ドメインの cookie がローカル browser から取得できる
- WHEN `run_auto_setup()` を実行する
- THEN source ごとに検出した browser 名を `cookies_found` に含める

#### Scenario: yt-dlp is already installed
- GIVEN `yt-dlp` が PATH 上にある
- WHEN `run_auto_setup()` を実行する
- THEN `ytdlp_installed` は true になる
- AND `ytdlp_action` は `already_installed` になる

#### Scenario: yt-dlp is missing but Homebrew is available
- GIVEN `yt-dlp` は無いが `brew` は利用可能である
- WHEN `run_auto_setup()` を実行する
- THEN Homebrew 経由で `yt-dlp` install を試みる
- AND 成功時は `ytdlp_action=installed` を返す
- AND 失敗時は `ytdlp_action=install_failed` を返す

### Requirement: Setup config appends without overwriting existing keys
The system SHALL append setup markers to the env file without overwriting existing user-provided keys.

#### Scenario: Fresh env file is created
- GIVEN setup config の出力先 env file が存在しない
- WHEN `write_setup_config()` を実行する
- THEN 親ディレクトリを作成する
- AND `SETUP_COMPLETE=true` と `FROM_BROWSER=<value>` を書き込む

#### Scenario: Existing env file already contains setup keys
- GIVEN env file に `SETUP_COMPLETE` または `FROM_BROWSER` が既にある
- WHEN `write_setup_config()` を実行する
- THEN 既存値は保持される
- AND 同じキーは重複して追加されない

### Requirement: OpenClaw setup probe reports tools and key presence
The system SHALL provide a server-side setup probe for OpenClaw without requiring browser access.

#### Scenario: OpenClaw setup probe runs
- GIVEN `run_openclaw_setup()` が呼ばれる
- WHEN server-side setup probe を実行する
- THEN `yt_dlp` `node` `python3` の有無を返す
- AND 主要 API key の有無を返す
- AND X access method を `xai` `cookies` または null で返す

### Requirement: Device auth polling is retry-oriented
The system SHALL continue polling for access tokens across expected transient failures.

#### Scenario: Authorization is still pending
- GIVEN device auth polling 中に `authorization_pending` が返る
- WHEN polling loop が継続する
- THEN CLI は interval 後に再試行する

#### Scenario: Poll endpoint returns expected transient HTTP status
- GIVEN polling 中に HTTP 400, 403, 428 のいずれかが返る
- WHEN device auth polling を継続する
- THEN その場で失敗せず再試行する

#### Scenario: Device auth is denied or expired
- GIVEN polling response が `expired_token` または `access_denied` を返す
- WHEN polling loop が処理する
- THEN polling は失敗として終了し None を返す


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