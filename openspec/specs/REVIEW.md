# OpenSpec Brownfield Baseline Review

## Proposed first-wave domains
- `openspec/specs/cli-runtime/spec.md`
- `openspec/specs/configuration-and-setup/spec.md`
- `openspec/specs/watchlist-and-store/spec.md`

この 3 つを初回スコープにした理由:
- 外部契約が明確で、将来の変更で壊しやすい
- 既存 tests が比較的多く、意図を逆算しやすい
- repo 全体を一気に spec 化するより、変更頻度と事故率が高い面を先に固定できる

## Intended behavior confirmed
- CLI は Python 3.12+ 必須で、topic 未指定時は usage error を返す
- `--search` alias は canonical source 名に正規化される
- config 優先順位は `env > project .claude/last30days.env > global ~/.config/last30days/.env`
- auto setup は cookie probe と `yt-dlp` install/check を行い、既存 env key を上書きしない
- watchlist run は `last30days.py --emit=json --quick --lookback-days 90` を subprocess 実行する
- findings は `source_url` で dedup し、再観測時は `sighting_count` と engagement を更新する

## Inferred behavior needing review
- baseline では `findings_from_report()` が ranked candidates 優先で、raw item 補完は HN/Polymarket のみとして記述した
- watchlist の query override は保存済み query list の先頭だけを実行 query に使う前提で記述した
- OpenClaw setup probe の key surface は現在の `_OPENCLAW_KEY_NAMES` に合わせたが、今後の provider 追加時は domain 分割の再検討が必要

## Likely bugs or accidental behavior not promoted to spec
- `tests/test_store.py` は reddit/x raw items も `findings_from_report()` に含まれる前提だが、現実装は HN/Polymarket raw item しか補完していない
- `tests/test_resolve.py` は `searches_run == 3` を期待するが、現実装 `resolve.auto_resolve()` は 4 クエリ（subreddit/news/x_handle/github）を投げる
- `tests/test_setup_openclaw.py` の一部は `poll_device_auth()` の `time.time()` 呼び出し回数と一致しておらず、StopIteration で落ちる
- `tests/test_generate_synthesis_inputs_v3.py` は存在しない `scripts/generate-synthesis-inputs.py` を参照している

## Future change recommendation
- 以後の仕様変更は current-state baseline を直接書き換えず、`openspec/changes/<change-id>/` で proposal/spec delta/design/tasks を作る
- 次の自然な Phase 2 候補は `pipeline orchestration`, `source availability`, `github source behavior`
