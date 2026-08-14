---
name: llm-wiki-ingest
description: "一次資料 (Office, PDF, SQL, text 等) を自動クレンジング・機密除去して取り込み、Google OKF (Open Knowledge Format v0.2) 準拠の Concept ドキュメント（sources, generated, 脚注 [^id] 完備）として wiki/ 配下に分類・出力し、index.md および log.md を自動更新するスキル。"
---

# LLM Wiki Ingest Skill (OKF v0.2 & LLM Wiki v2 準拠)

このスキルは、ユーザーから「資料をWikiに追加して」と指示された際に、`raw/` 配下に配置された各種書類（顧客要望、要件定義書、概要設計書、詳細設計書、議事録など）を読み込み、**自動クレンジング（空セル・不要空行の削除等）** および **シークレット除去（APIキー・パスワード・個人情報のマスク）** を施した上で、**Google OKF (v0.2)** 仕様に従って構造化された知識ファイル（Concept ドキュメント）として `wiki/` に編纂・配置します。

> **Note**: ユーザーが個別に `index.md` や `log.md` の更新を指示しなくても、本スキル内で必ず自動的に更新します。

---

## 振り分け先ディレクトリ定義

取り込む文書の種類に応じて、`wiki/` 配下の適切なフォルダに Concept ドキュメント（スネークケース `.md`）を出力します。

| カテゴリ | 保存先ディレクトリ | OKF `type` の例 | 扱う内容の例 |
| :--- | :--- | :--- | :--- |
| **顧客要望** | `wiki/01_customer_requests/` | `Customer Request`, `Business Goal` | 顧客ヒアリング結果、RFP、業務課題、要望一覧 |
| **要件定義** | `wiki/02_requirements/` | `Requirement`, `Functional Requirement`, `Non-Functional Requirement` | 機能要件、非機能要件、業務フロー、画面一覧 |
| **概要設計** | `wiki/03_basic_designs/` | `Architecture`, `System Design`, `Infra Design` | システム構成図、全体アーキテクチャ、認証基盤設計 |
| **詳細設計** | `wiki/04_detailed_designs/` | `Database Table`, `API Endpoint`, `Batch Spec`, `Screen Spec` | テーブル定義、SQL/DDL、API 仕様、UI 遷移、ロジック詳細 |
| **設計決定** | `wiki/05_decisions/` | `Decision (ADR)` | アーキテクチャ決定記録 (ADR)、技術選定理由 |
| **その他** | `wiki/99_others/` | `Glossary`, `Meeting Minutes`, `Runbook`, `Attested Computation` | プロジェクト用語集、議事録、運用マニュアル、計算根拠 |

---

## Ingest の作業手順（自動実行パイプライン）

### 1. ドキュメントの変換と自動クレンジング・機密スクラビング
- `scripts/convert_anydoc.py` や `scripts/table_cleaner.py` を実行するか、テキスト/PDF を読み取って、大量の空セル（`| | | |`）や不要な空行、HTML ゴミを自動除去したクリーンな Markdown を生成します。
- **機密情報の保護**: API キー、平文パスワード、顧客個人情報（PII）が含まれている場合は環境変数（`$SECRET`）やマスク（`***`）に置換します。
- **解像度保持**: API パラメータ、カラム型定義、エラーコード等の詳細を要約省略せず完全に保持します。

### 2. 知識の分割 (Concept 分割)
- 1 つの大きな資料をそのまま 1 ファイルにするのではなく、**「1 概念 = 1 ファイル」** の原則で論理的に分割します（例: `authentication.md`, `jwt_token.md`）。

### 3. Google OKF v0.2 フォーマットの適用
生成するすべての Concept ドキュメントに以下の Frontmatter と本文構造を適用します。

```markdown
---
type: Database Table             # 【必須】概念種別
title: Users Table Specification # 【推奨】タイトル
description: ユーザーマスタおよび認証情報のテーブル定義 # 【推奨】一行要約
tags: [auth, user, db]           # 【任意】タグ
status: active                   # 【推奨】draft | active | deprecated | tombstone

generated:
  by: agent:antigravity/gemini-3.7-flash # 【推奨】生成 Actor
  at: 2026-08-14T16:00:00Z               # 【推奨】ISO 8601

sources:                                 # 【推奨】一次情報来歴
  - id: user-schema-v1
    resource: raw/04_detailed_designs/user_schema.xlsx
    title: ユーザーテーブル設計書
    author: human:designer
    last_modified: 2026-08-14

relations:                               # 【任意】セマンティック関連
  implements: [02_requirements/req_user_management]
  depends_on: [03_basic_designs/arch_auth_system]
---

# ユーザーテーブル定義

（構造化された本文：見出し、表、リスト、コードブロック）

パスワードハッシュは argon2id アルゴリズムで生成します[^user-schema-v1]。

# 関連概念
* 認証アーキテクチャ: [Authentication Architecture](../03_basic_designs/arch_auth_system.md)
* ログイン API 仕様: [Login API Specification](../04_detailed_designs/api_auth_login.md)

[^user-schema-v1]: raw/04_detailed_designs/user_schema.xlsx (ユーザーテーブル設計書)
```

### 4. `index.md` と `log.md` の自動更新（必須）
ユーザーからの明示的な指定がなくても、必ず以下を実行します：
- 各カテゴリフォルダの `index.md` に新しい Concept ドキュメントへのリンクと 1 行説明を追加。
- `wiki/index.md`（マスターインデックス）の整合性を確認・更新。
- `wiki/log.md` の先頭に本日の日付と Actor 名で取り込み履歴を追記。
