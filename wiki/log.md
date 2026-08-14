# Wiki Update Log

本ファイルは、ナレッジベース全体の更新履歴を時系列（最新が上）で記録します。

---

## 2026-08-14
* **agent:antigravity/gemini-3.7-flash**: Google OKF v0.2 および LLM Wiki v2 仕様への全面移行を実施。
  - 全 Concept ファイルに `generated`, `verified`, `sources`（来歴リスト）、および本文脚注（`[^source_id]`）を導入。
  - Frontmatter に `relations`（セマンティックグラフ接続）および `status` を定義。
  - [SCHEMA.md](../SCHEMA.md) および [README.md](../README.md) の運用ルール・構文規約を刷新。
  - [lint_okf.py](../scripts/lint_okf.py) を OKF v0.2 バリデータに改修。
* **human:slee**: 初期 Concept ドキュメント群の査読および `verified` 承認。
* **agent:antigravity/gemini-3.7-flash**: [Glossary](99_others/glossary.md) およびサンプル Concept（顧客要望、要件定義、概要設計、詳細設計、ADR）を登録。
