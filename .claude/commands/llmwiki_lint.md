# Lint Command (`/llmwiki_lint`)

Google OKF (v0.2) および LLM Wiki v2 仕様への適合性、忘却曲線（stale ドキュメント検知）、ゴーストリンク、未インデックスファイル、ナレッジグラフの矛盾（`contradicts`）や孤立ノード、sources/脚注（Provenance）の欠落、supersedes 参照整合性を機械的に検査・検証します。

## 実行手順

1. **Linter の実行**:
   ```bash
   python3 scripts/lint_okf.py wiki/
   ```

2. **検査項目の確認**:
   - YAML Frontmatter（`type`, `memory_tier`, `confidence`, `sources`, `relations`）の充足。
   - 本文中の脚注記法（`[^src-1]`）と `sources.id` の完全一致。
   - `relations` の参照先ファイルが存在するか（ゴーストリンク防止）。
   - 忘却曲線による `confidence.current_score` の減衰・stale 状態の検知。
   - タイトル・ID の重複。

3. **自動修復の適用（必要な場合）**:
   - `python3 scripts/lint_okf.py wiki/ --fix` を実行して、軽微な構文・リンク不整合を自動修復。
