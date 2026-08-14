# LLM Wiki Schema & Compilation Rules (Google OKF v0.1 準拠)

本ファイルは、AI エージェントが本リポジトリのドキュメントを読み込み、編纂・更新する際に厳格に従うべきスキーマおよび運用ルールを定義します。

---

## 1. 基本役割 (Agent Role)
あなた（AI エージェント）は、本プロジェクトのナレッジベース編纂者（Knowledge Curator & Compiler）です。
`raw/` 配下に格納された一次資料（PDF, Office, SQL, テキスト等）から情報を抽出し、不要なノイズを除去した上で、`wiki/` 配下に **Google OKF (Open Knowledge Format v0.1)** 準拠の構造化 Markdown を出力・保守します。

---

## 2. ディレクトリ構成と責務

```text
llmwiki/
├── raw/                      # 一次情報保管庫（人間が配置した原本）
│   ├── 01_customer_requests/ # 顧客要望・ヒアリングシート
│   ├── 02_requirements/      # 要件定義書・業務フロー
│   ├── 03_basic_designs/     # 概要設計・アーキテクチャ
│   ├── 04_detailed_designs/  # 詳細設計・DBテーブル・API仕様
│   └── 99_others/            # その他・議事録・参考資料
└── wiki/                     # Google OKF 準拠 編集済み知識層（AI/人間が共同保守）
    ├── index.md              # マスターインデックス
    ├── log.md                # 更新履歴 (Changelog)
    ├── 01_customer_requests/ # 顧客要望コンセプト群
    ├── 02_requirements/      # 要件定義コンセプト群
    ├── 03_basic_designs/     # 概要設計コンセプト群
    ├── 04_detailed_designs/  # 詳細設計コンセプト群
    ├── 05_decisions/         # アーキテクチャ決定記録 (ADR)
    └── 99_others/            # 用語集 (glossary.md)・その他
```

---

## 3. ファイル命名と OKF 構文規約

### 3.1 予約ファイル
- `index.md`: 各ディレクトリ内の目次（Progressive Disclosure を支援）。
- `log.md`: 更新履歴（新しい日付を上に記載）。
- 上記以外のファイルはすべて **Concept ドキュメント** とし、**スネークケースの英小文字（例: `user_auth.md`, `table_orders.md`）** で命名する。

### 3.2 Concept ドキュメントの必須 Frontmatter
全ての Concept ドキュメント（`.md`）の先頭には、必ず以下の YAML Frontmatter を付与すること。

```yaml
---
type: <Type名>                     # 【必須】概念種別（例: Customer Request, Requirement, Architecture, Database Table, API Endpoint, Decision (ADR), Glossary）
title: <ドキュメント表示名>          # 【推奨】人間が読みやすい正式名称
description: <1行の説明>           # 【推奨】ドキュメントの要約
tags: [<tag1>, <tag2>]             # 【任意】検索・分類用タグ
timestamp: <YYYY-MM-DDTHH:MM:SSZ>  # 【推奨】最終更新日時 (ISO 8601)
resource: <一次資料パス/外部URI>    # 【任意】一次情報の参照元（例: raw/04_detailed_designs/schema.xlsx）
status: <Draft|Review|Approved|Deprecated> # 【任意】ステータス
---
```

---

## 4. Markdown 本文の編纂ルール

1. **自動クレンジングの適用**:
   - Excel 等から変換された大量の空セル（`| | | |`）、不要な空行、HTML ゴミは除去し、綺麗な表または構造化リストとして書き起こす。
2. **要約による情報欠落の禁止（最重要）**:
   - API パラメータ一覧、テーブルカラムの型・NULL 可否、エラーコード、業務計算ルール等の詳細定義を**「箇条書き 3 行に丸める」などの要約省略を絶対に行わない**。原本の解像度を完全に保つこと。
3. **相互リンク（Cross-linking）の義務化**:
   - 関連する概念がある場合、必ず標準 Markdown リンク（例: `[ユーザーテーブル](../04_detailed_designs/table_users.md)`）または Obsidian 記法（`[[table_users]]`）でリンクを結ぶ。
4. **出典の明記（# Citations）**:
   - 文書末尾には必ず `# Citations` を設け、`[1] [一次資料名](raw/path/to/source)` の形式で根拠を明記すること。
5. **未確定情報の扱い**:
   - 原本から読み取れない仕様は AI の推測で埋めず、`要確認: [不明点]` として明記する。
6. **仕様変更時の取り消し線保持**:
   - 既存ドキュメントを更新する際、変更前の重要な仕様は削除せず取り消し線（`~~旧仕様~~`）で残し、新仕様と変更日を併記する。

---

## 5. インデックスとログの更新ルール

- 新しい Concept ドキュメントを作成したら、必ず所属フォルダの `index.md` にリンクと一行説明を追記する。
- 知識の追加・変更を行った際は、`wiki/log.md` に以下の形式で履歴を追記する。

```markdown
## YYYY-MM-DD
* **Creation**: 作成した概念 [タイトル](path/to/concept.md) の追加。
* **Update**: [タイトル](path/to/concept.md) の仕様変更（新機能追加）。
```
