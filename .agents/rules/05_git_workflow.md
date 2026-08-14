# Rule 05: Git & GitHub Workflow Rules

## 1. ブランチ戦略 (Branching Strategy)
- `main` ブランチへの直接 push は原則禁止。
- 以下の命名規則に従ってトピックブランチを作成して作業する：
  - 資料取り込み: `feature/ingest-<topic>` (例: `feature/ingest-auth-specs`)
  - 仕様更新・ADR: `feature/update-<topic>` または `docs/adr-<number>`
  - 整合性修復・リファクタ: `fix/wiki-lint-<topic>`

## 2. コミットメッセージ規約 (Conventional Commits)
- `feat(ingest): <新規資料の取り込み概要>`
- `update(wiki): <仕様変更・再強化概要>`
- `fix(lint): <リンク切れ・OKFスキーマ修正>`
- `docs(adr): <新規ADR起票>`
- `chore(graph): <ナレッジグラフ再生成>`

## 3. Pull Request & CI 自動検証
Pull Request 作成時、GitHub Actions ワークフロー (`.github/workflows/ci.yml`) により以下のチェックが自動実行される：
1. **OKF v0.2 スキーマ検証**: `python3 scripts/lint_okf.py wiki/`
2. **ナレッジグラフ整合性検査**: `python3 scripts/build_graph.py wiki/`

すべての CI チェックが GREEN であることを確認した上でマージを行うこと。
