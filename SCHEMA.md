# LLM Wiki Schema & Compilation Rules (Google OKF v0.2 & LLM Wiki v2 準拠)

本ファイルは、AI エージェント（知識編纂者）および開発者が本リポジトリのドキュメントを読み込み、編纂・更新・検証する際に厳格に従うべきスキーマおよび運用ルールを定義します。

---

## 1. 基本方針と役割 (Core Philosophy & Agent Role)

### 1.1 コア原則: "Stop Re-deriving, Start Compiling"
- 従来の RAG（検索拡張生成）のように毎回未構造化ドキュメントを断片的に読み直して要約するのではなく、**AI エージェント自身が継続的に整理・統合・相互リンク・検証した構造化ナレッジ層（Compiled Knowledge Layer）** を Git 上で蓄積・成長させます。
- **ドキュメントの解像度保持**: API パラメータ一覧、テーブルカラムの型・NULL 可否、エラーコード、業務計算ルール等の詳細定義を「箇条書き 3 行に丸める」などの要約省略を絶対に行いません。原本の解像度を 100% 保持します。

### 1.2 エージェントの役割 (Knowledge Curator & Compiler)
- `raw/` に配置された一次資料（原本）から情報を抽出し、不要な空行・空セル等のノイズをクレンジングした上で、`wiki/` 配下に **Google OKF (Open Knowledge Format v0.2)** 準拠の Concept ドキュメントを作成・保守します。
- 知識のライフサイクル（鮮度・信頼性・陳腐化・世代交代）を能動的に管理します。

---

## 2. ディレクトリ構成と責務

```text
llmwiki/
├── raw/                      # 【一次情報保管庫】（人間が受領・配置した原本）
│   ├── 01_customer_requests/ # 顧客要望・ヒアリングシート・RFP
│   ├── 02_requirements/      # 要件定義書・業務フロー
│   ├── 03_basic_designs/     # 概要設計・アーキテクチャ設計・外部IF
│   ├── 04_detailed_designs/  # 詳細設計・DB定義 (Excel/DDL)・API仕様
│   ├── 05_decisions/         # 意思決定の背景資料・比較検討資料
│   └── 99_others/            # その他・議事録・参考技術資料
└── wiki/                     # 【Google OKF v0.2 準拠 編集済み知識層】
    ├── index.md              # 全体マスターインデックス (Progressive Disclosure)
    ├── log.md                # 全体更新履歴 (Changelog with Actor Attribution)
    ├── 01_customer_requests/ # 顧客要望コンセプト群 (index.md 完備)
    ├── 02_requirements/      # 要件定義コンセプト群 (index.md 完備)
    ├── 03_basic_designs/     # 概要設計コンセプト群 (index.md 完備)
    ├── 04_detailed_designs/  # 詳細設計コンセプト群 (DB/API/画面)
    ├── 05_decisions/         # アーキテクチャ決定記録 (ADR)
    └── 99_others/            # 用語集 (glossary.md)・運用手順
```

---

## 3. Google OKF v0.2 仕様 & 構文規約

### 3.1 予約ファイル
- `index.md`: 各ディレクトリ内の目次（直下の全 Concept ファイルおよびサブディレクトリの一覧と 1 行説明）。
- `log.md`: 変更履歴（`## YYYY-MM-DD` 形式の見出しと Actor 記載）。
- 上記以外の `.md` ファイルはすべて **Concept ドキュメント** とし、**スネークケース英小文字（例: `user_auth.md`, `table_orders.md`）** で命名します。

### 3.2 Actor 表記規約 (Actor Convention)
更新者・生成者・検証者は以下のフォーマットで記録します：
- AI エージェント: `agent:<producer>/<model_or_version>`（例: `agent:antigravity/gemini-3.7-flash`）
- 人間: `human:<username_or_id>`（例: `human:slee`）
- 自動バッチ: `process:<process_id>`（例: `process:daily-sync`）

### 3.3 Concept ドキュメントの Frontmatter 仕様

全 Concept ファイルの先頭には、以下の YAML Frontmatter を付与します。

```yaml
---
type: <Type名>                     # 【必須】概念種別（例: Customer Request, Requirement, Architecture, Database Table, API Endpoint, Decision (ADR), Glossary, Attested Computation）
title: <ドキュメント表示名>          # 【推奨】人間可読な正式名称
description: <1行の説明>           # 【推奨】Progressive Disclosure用要約
tags: [<tag1>, <tag2>]             # 【任意】分類・横断検索用タグ
status: <draft|active|deprecated|tombstone> # 【推奨】ライフサイクル状態 (デフォルト: active)

# ライフサイクル & 生成情報
generated:
  by: agent:antigravity/gemini-3.7-flash # 【推奨】生成 Actor
  at: 2026-08-14T16:00:00Z               # 【推奨】生成日時 (ISO 8601)

# 信頼性 & 検証情報 (Trust Tier)
verified:                                # 【任意】検証済みの場合
  by: human:slee                         # 検証 Actor
  at: 2026-08-14T16:30:00Z               # 検証日時
  method: manual_audit                   # 検証手法 (manual_audit / automated_test / stakeholder_approval)

# 来歴 & 出典情報 (Provenance)
sources:                                 # 【推奨】一次情報または根拠ソース
  - id: hearing-202608                   # 本文中の脚注 [^hearing-202608] と紐づくID
    resource: raw/01_customer_requests/hearing_sheet_202608.md # ファイルパスまたはURL
    title: 顧客ヒアリング議事録 2026年8月
    author: human:client_rep
    last_modified: 2026-08-14

# 世代交代・置換 (Supersession)
supersedes: []                           # 【任意】本ドキュメントが置き換えた旧Concept IDのリスト
superseded_by: null                      # 【任意】本ドキュメントを置き換えた新Concept ID

# セマンティック関連 (Typed Relations)
relations:                               # 【任意】ナレッジグラフ接続
  implements: [01_customer_requests/cr_user_authentication]
  depends_on: [03_basic_designs/arch_auth_system]
  tested_by: []
---
```

---

## 4. Markdown 本文の編纂・記述ルール

### 4.1 出典と主張の紐付け (Claim-level Grounding via Footnotes)
- 単なる末尾の雑多なリンク集ではなく、本文中の具体的な要件・仕様・数値に対し、`sources` の `id` に対応する **Markdown 脚注記法（`[^source_id]`）** を使用して根拠を明記します。
- 本文末尾に自動的に展開される脚注定義を配置します：
  ```markdown
  パスワード誤入力時は 5 回失敗で 15 分間ロックします[^hearing-202608]。

  [^hearing-202608]: raw/01_customer_requests/hearing_sheet_202608.md (顧客ヒアリング議事録)
  ```

### 4.2 相互リンク（Cross-linking）と関係の明示
- 関連する Concept への参照は標準 Markdown リンク（例: `[ユーザーテーブル](../04_detailed_designs/table_users.md)`）または Obsidian 記法（`[[table_users]]`）を用います。
- 単に並べるだけでなく、文脈や Frontmatter の `relations`（`implements`, `depends_on`, `supersedes` 等）で意味的な関係を明確にします。

### 4.3 未確定情報の扱い
- 原本に記載のない仕様や不明点は、AI の推測で補完せず `> [!NOTE]` や `要確認: [不明点]` として明記し、次回の顧客ヒアリングや設計確認事項として可視化します。

### 4.4 結晶化 (Crystallization)
- 複雑な調査、トラブルシューティング、ADR 検討の結論は、一時的なチャットの会話で終わらせず、独立した Concept ドキュメント（`Decision (ADR)` や `Architecture`）として結晶化（Crystallize）して `wiki/` に定着させます。

### 4.5 機密情報のスクラビング (Privacy & Secret Governance)
- Ingest 時に、API キー、秘密鍵、平文パスワード、顧客個人情報（PII）が含まれていないかを自動検査し、マスクまたは環境変数参照（`$ENV_VAR`）に置換して `wiki/` に取り込みます。

---

## 5. ライフサイクル & 変更管理 (Memory Lifecycle)

1. **仕様変更と取り消し線保持**:
   - 変更前の重要記述は即座に削除せず、取り消し線（`~~旧仕様~~`）を残して新仕様および変更理由・更新日を併記します。
2. **世代交代 (Supersession)**:
   - 全体構造の抜本的な刷新時は、旧ドキュメントの `status` を `deprecated` に更新し、`superseded_by: <new_concept_id>` を付与。新ドキュメントには `supersedes: [<old_concept_id>]` を記録します。
3. **履歴追記 (`wiki/log.md`)**:
   - 変更・追加時は必ず `wiki/log.md` の先頭に日付・Actor・操作内容を追記します。
   ```markdown
   ## YYYY-MM-DD
   * **agent:antigravity/gemini-3.7-flash**: [Users Table](04_detailed_designs/table_users.md) のカラム追加（`status: active`）。
   * **human:slee**: [Auth Requirements](02_requirements/req_user_management.md) のレビューおよび承認 (`verified`)。
   ```
