# Rule 05: Git & GitHub Workflow Rules (Multi-User Collaboration)

## 1. ブランチ戦略 (Branching Strategy)
- `main` ブランチへの直接 push は原則禁止（PR 必須）。
- 以下の命名規則に従ってトピックブランチを作成して作業する：
  - 資料取り込み: `feature/ingest-<topic>` (例: `feature/ingest-auth-specs`)
  - 仕様更新・ADR: `feature/update-<topic>` または `docs/adr-<number>`
  - 整合性修復・リファクタ: `fix/wiki-lint-<topic>`
  - 忘却曲線同期バッチ: `chore/sync-metrics-<date>`

## 2. コミットメッセージ規約 (Conventional Commits)
- `feat(ingest): <新規資料の取り込み概要>`
- `update(wiki): <仕様変更概要>`
- `docs(adr): <新規ADR起票>`
- `fix(lint): <リンク切れ・OKFスキーマ修正>`
- `chore(sync): <インデックス・ログ・グラフ同期>`

## 3. Pull Request & CI/CD 自動化フロー
1. **PR 作成時**:
   - PR テンプレート (`.github/pull_request_template.md`) のチェックリストを満たす。
   - `wiki/log.md` や `index.md` の手動編集は含めず、ドキュメント本体および `wiki/.changelogs/` の断片ログをコミットする。
   - GitHub Actions により `python3 scripts/lint_okf.py wiki/` が自動実行され、構文・整合性・重複ID・ドラフト依存が検証される。
   - `CODEOWNERS` に基づき、担当ドメインエキスパートのレビュー承認を得る。
2. **Main マージ時**:
   - GitHub Actions CI (`.github/workflows/ci.yml`) が `python3 scripts/sync_wiki.py` を実行し、全 `index.md`, `log.md`, `graph.json`, `graph.mermaid` を自動生成して自動コミットする。
