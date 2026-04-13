# AGENTS.md

## このリポジトリでまず見る場所
- 実行入口は `scripts/last30days.py`。CLI フラグ、setup サブコマンド、保存/SQLite 永続化の配線はここ。
- 実オーケストレーションは `scripts/lib/pipeline.py`。利用可能ソース判定、depth (`quick/default/deep`)、GitHub person/project mode の切り替えはここが正。
- 環境変数の優先順位と設定ファイル探索は `scripts/lib/env.py` が正。
- 配布物同期は `scripts/sync.sh`。`SKILL.md` や `scripts/` を触ったらこれを実行。

## 実行・検証コマンド
- 依存導入: `uv sync --dev`
- 軽い疎通: `uv run python scripts/last30days.py "test query" --mock --emit=json`
- 診断: `uv run python scripts/last30days.py --diagnose`
- 全テスト: `uv run pytest -q`
- 単体テスト1件: `uv run pytest -q tests/test_cli_v3.py -k test_mock_json_cli`
- 複数の要点だけ見るなら: `uv run pytest -q tests/test_cli_v3.py tests/test_setup_wizard.py`

## 変更後の必須確認
- この repo には lint / typecheck の設定が見当たらない。現状の検証は `uv run pytest -q` が基準。
- `scripts/`, `SKILL.md`, `fixtures/` を変更したら `bash scripts/sync.sh` も実行して、配布先コピーと import check を通す。

## 重要な配線・前提
- Python は 3.12+ 必須。CLI 自身が 3.12 未満を即終了する (`scripts/last30days.py`)。
- X 検索の推奨バックエンドは `xcom-rs` CLI (`scripts/lib/xcom_rs_x.py`)。`dotenvx run -f ~/.env -- xcom-rs search recent ...` で実行。`LAST30DAYS_X_BACKEND=xcom_rs` で明示指定も可。
- レガシー Bird client (`scripts/lib/bird_x.py`) は Node 22+ 前提で移行期間中のフォールバック。`xcom-rs` が利用可能なら自動的に優先される。
- `scripts/lib/__init__.py` は comment-only の package marker を維持すること。eager import を足さない。
- `--search=web,hn,...` の別名正規化は `pipeline.SEARCH_ALIAS` が正。README の文言ではなくここに合わせる。
- `github` source は `GITHUB_TOKEN` がなくても `gh` があれば available 扱いになる (`scripts/lib/pipeline.py`)。

## 設定ファイルの優先順位
- 優先順位は `os.environ` > `./.claude/last30days.env` > `~/.config/last30days/.env`。
- per-project 設定は cwd から親へ向かって `.claude/last30days.env` を探索する。repo 直下に置く前提で考える。
- secrets file は権限警告が出る。`600` 以外だと hook / env loader が警告する。

## フックと初回セットアップ
- セッション開始時に `hooks/scripts/check-config.sh` が走る。`.claude/last30days.env` と global config を見て ready メッセージを変える。
- `setup` は通常の subcommand ではなく `python scripts/last30days.py setup ...`。`--device-auth`, `--github`, `--openclaw` は `parse_known_args()` で通している。
- `run_auto_setup()` は macOS で `yt-dlp` が無ければ Homebrew 経由の自動 install を試す。setup 系テストは `subprocess.run` / `shutil.which` をモックしているので、同系統で書く。

## sync.sh の罠
- `scripts/sync.sh` は `~/.claude/plugins/cache/...`, `~/.agents/skills/last30days`, `~/.codex/skills/last30days` に配る。
- 意図的に `~/.claude/skills/last30days` には配らない。ここへ追加すると slash command が重複する。
- OpenClaw 向け同期は `variants/open` がある private repo のときだけ走る。public repo では skip が正常。
