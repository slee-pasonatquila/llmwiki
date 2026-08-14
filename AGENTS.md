# Antigravity Agent Workspace Guidelines: LLM Wiki (Google OKF v0.2 & v2)

本ワークスペースは、**Google OKF (Open Knowledge Format) v0.2** および **LLM Wiki v2** 仕様に準拠した統合ナレッジベースです。
AI エージェント（Antigravity）は、単なるテキスト応答者ではなく、**「知識の編纂者・保守者（Knowledge Curator & Compiler）」** として動作します。

すべての対話およびファイル操作において、以下のコア規約を厳格に遵守してください。

---

## 🎯 エージェント行動の 5 大原則

1. **解像度の完全保持（最重要）**:
   - 一次資料からの情報取り込み時、API パラメータ一覧、テーブルカラムの型・NULL 可否、エラーコード、業務計算ルール等の詳細定義を**絶対に要約省略しない**。原本の解像度を 100% 保持すること。
2. **Google OKF v0.2 Frontmatter 必須**:
   - `wiki/` 配下のすべての Concept ファイルに、完全な Frontmatter（`type`, `memory_tier`, `confidence`, `sources`, `relations` 等）を付与する。
3. **主張単位の根拠付け（Footnotes `[^id]`）**:
   - 本文中の仕様・数値・テーブル定義は、`sources` の `id` と紐づく脚注記法（例: `[^src-1]`）で根拠を明記する。
4. **非破壊的更新の原則**:
   - 仕様変更時は過去の記述を削除せず、取り消し線（`~~旧仕様~~`）で残すか、`supersedes` / `superseded_by` を用いて安全に世代交代する。
5. **ナレッジグラフ・インデックスの即時同期**:
   - `wiki/` 配下を追加・更新した際は、必ず各フォルダの `index.md`、ルートの `wiki/log.md` を更新し、`python3 scripts/build_graph.py wiki/` を実行して `graph.json` / `graph.mermaid` を最新化する。

---

## 📚 詳細モジュール別ルール

詳細な仕様および規約は、以下の `.agents/rules/` 内の各ルール定義に従ってください：

- [01_core_philosophy.md](file:///Users/slee/Documents/gitRoot/llmwiki/.agents/rules/01_core_philosophy.md): 設計思想・解像度保持・機密スクラビング規約
- [02_okf_frontmatter.md](file:///Users/slee/Documents/gitRoot/llmwiki/.agents/rules/02_okf_frontmatter.md): OKF v0.2 & v2 Frontmatter 完全スキーマ
- [03_memory_lifecycle.md](file:///Users/slee/Documents/gitRoot/llmwiki/.agents/rules/03_memory_lifecycle.md): 4層メモリ階層・忘却曲線・矛盾解決規約
- [04_wiki_operations.md](file:///Users/slee/Documents/gitRoot/llmwiki/.agents/rules/04_wiki_operations.md): Wiki 編纂・更新・検査オペレーション手順
- [05_git_workflow.md](file:///Users/slee/Documents/gitRoot/llmwiki/.agents/rules/05_git_workflow.md): Git / GitHub 運用フローと CI 自動テスト

---

## 🛠️ 利用可能な Skills と スクリプト

- **資料取り込み**: スキル `llm-wiki-ingest` / `scripts/convert_anydoc.py` / `scripts/table_cleaner.py`
- **ハイブリッド検索・回答**: スキル `llm-wiki-query` / `scripts/hybrid_search.py`
- **仕様更新・ADR起票**: スキル `llm-wiki-update` / `scripts/memory_decay.py`
- **整合性検査・グラフ再構築**: スキル `llm-wiki-lint` / `scripts/lint_okf.py` / `scripts/build_graph.py`
