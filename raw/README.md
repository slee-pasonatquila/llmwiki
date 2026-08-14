# 一次資料保管庫 (raw/)

本ディレクトリは、人間やクライアントから受領した一次資料（原本）をそのまま保存する場所です。
Git でバージョン管理され、`wiki/` の各 Concept ドキュメントから `# Citations` で参照されます。

## ディレクトリの役割

- `01_customer_requests/`: 顧客要望、ヒアリングシート、議事メモ、RFP
- `02_requirements/`: 要件定義書、業務フロー図、機能一覧
- `03_basic_designs/`: 概要設計書、システム構成図、外部連携仕様書
- `04_detailed_designs/`: 詳細設計書、テーブル定義書 (Excel/DDL)、API 仕様書 (OpenAPI/Excel)
- `99_others/`: 参考技術資料、規約、その他メモ

## 取り込みの流れ
1. 一次資料（`.xlsx`, `.docx`, `.pdf`, `.sql`, `.txt` 等）を適切なフォルダに配置します。
2. Antigravity Skill `llm-wiki-ingest` または `scripts/convert_anydoc.py` を実行して `wiki/` に OKF 形式で構造化 Markdown を出力します。
