# Sync Command (`/sync`)

`wiki/` 配下のすべての Concept ドキュメントおよび `.changelogs/` の変更断片を読み込み、`wiki/index.md`（全体索引）、`wiki/log.md`（統合変更履歴）、`wiki/graph.json` および `wiki/graph.mmd`（ナレッジグラフ）を一括自動再構築します。

## 実行手順

1. **一括同期スクリプトの実行**:
   ```bash
   python3 scripts/sync_wiki.py
   ```

2. **生成される成果物**:
   - `wiki/index.md`: 各カテゴリ（01〜99）別の全ドキュメント索引、ステータス、確信度、タグ一覧。
   - `wiki/log.md`: 日付順・アクター別のチェンジログ集約。
   - `wiki/graph.json`: 全 Concept 間の有向関係グラフデータ。
   - `wiki/graph.mmd`: Mermaid 形式のナレッジグラフ可視化ファイル。

3. **コミット準備**:
   - 同期完了後、`git status` で差分を確認し、コミット・プッシュ可能な状態にします。
