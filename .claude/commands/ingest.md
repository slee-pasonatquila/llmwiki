# Ingest Command (`/ingest <file_path>`)

一次資料（Excel, Word, PowerPoint, PDF, SQL, text 等）を自動クレンジング・機密除去して取り込み、Google OKF (v0.2) & LLM Wiki v2 準拠の Concept ドキュメント（Frontmatter、脚注 `[^id]`、`relations` 完備）として `wiki/` 配下に編纂します。

## 実行手順

1. **ドキュメントの変換とクレンジング**:
   - `python3 scripts/convert_anydoc.py "$1"` または `python3 scripts/table_cleaner.py "$1"` を実行して、粗い表や余分な空白・空行を除去。
   - シークレット情報（APIキー・パスワード・個人情報）をマスク。
   - API パラメータ、カラム型定義、エラーコード等の解像度を 100% 保持（要約省略禁止）。

2. **Concept 分割と配置**:
   - 「1 概念 = 1 ファイル」の原則に従い、適切なディレクトリに配置：
     - 顧客要望: `wiki/01_customer_requests/`
     - 要件定義: `wiki/02_requirements/`
     - 概要設計: `wiki/03_basic_designs/`
     - 詳細設計: `wiki/04_detailed_designs/`
     - 設計決定: `wiki/05_decisions/`
     - その他: `wiki/99_others/`

3. **OKF v0.2 Frontmatter の付与**:
   - `type`, `memory_tier`, `confidence`, `sources`, `relations` を漏れなく記述。
   - `status: draft` を設定。
   - `generated.by: agent:claude-code/<model>` を記録。
   - 本文中の各仕様に `sources` の `id` と紐づく脚注（`[^src-1]` 等）を付与。

4. **関係性推論と矛盾検知**:
   - `python3 scripts/hybrid_search.py "<キーワード>"` で関連ドキュメントを検索し、`relations`（`implements`, `depends_on`, `uses`）を自動設定。
   - 矛盾がある場合は `relations.contradicts` を付与し、ADR草案を起票。

5. **チェンジログ記録と検証**:
   - `wiki/.changelogs/YYYYMMDD_<author>_<topic>.json` を作成。
   - `python3 scripts/lint_okf.py wiki/` を実行して整合性を確認。
