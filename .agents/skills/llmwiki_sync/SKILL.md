---
name: llmwiki_sync
description: "wiki/ 配下の全ドキュメントと .changelogs/ を読み込み、index.md, log.md, graph.json, graph.mermaid を一括自動再構築する同期スキル。"
---

# LLM Wiki Sync Skill (`llmwiki_sync`) (OKF v0.2 & LLM Wiki v2 準拠)

このスキルは、`wiki/` 配下のすべての Concept ドキュメントおよび `.changelogs/` の変更断片を読み込み、`wiki/index.md`（全体索引）、`wiki/log.md`（統合変更履歴）、`wiki/graph.json` および `wiki/graph.mermaid`（ナレッジグラフ）を一括自動再構築します。

---

## 実行手順

1. **一括同期スクリプトの実行**:
   ```bash
   python3 scripts/sync_wiki.py
   ```

2. **生成される成果物**:
   - `wiki/index.md`: 各カテゴリ（01〜99）別の全ドキュメント索引、ステータス、確信度、タグ一覧。
   - `wiki/log.md`: 日付順・アクター別のチェンジログ集約。
   - `wiki/graph.json`: 全 Concept 間の有向関係グラフデータ。
   - `wiki/graph.mermaid`: Mermaid 形式のナレッジグラフ可視化ファイル。

3. **整合性の確認**:
   - 同期実行後、孤立ノード（Orphan Concepts）や矛盾（Contradictions）のレポートを確認します。
