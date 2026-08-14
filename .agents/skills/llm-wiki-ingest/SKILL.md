---
name: llm-wiki-ingest
description: "一次資料 (Office, PDF, SQL, text 等) を自動クレンジング・機密除去して取り込み、Google OKF (Open Knowledge Format v0.2) & LLM Wiki v2 準拠の Concept ドキュメント（sources, confidence, memory_tier, 脚注 [^id], relations 完備）として wiki/ 配下に分類・出力し、index.md, log.md, graph.json/mermaid を自動更新するスキル。"
---

# LLM Wiki Ingest Skill (OKF v0.2 & LLM Wiki v2 準拠)

このスキルは、ユーザーから「資料をWikiに追加して」と指示された際に、`raw/` 配下に配置された各種書類（顧客要望、要件定義書、概要設計書、詳細設計書、議事録など）を読み込み、**自動クレンジング（空セル・不要空行の削除等）** および **シークレット除去（APIキー・パスワード・個人情報のマスク）** を施した上で、**Google OKF (v0.2)** および **LLM Wiki v2** 仕様に従って構造化された知識ファイル（Concept ドキュメント）として `wiki/` に編纂・配置します。

---

## 振り分け先ディレクトリ & メモリ階層定義

| カテゴリ | 保存先ディレクトリ | OKF `type` の例 | デフォルト `memory_tier` | デフォルト `decay_rate` |
| :--- | :--- | :--- | :--- | :--- |
| **顧客要望** | `wiki/01_customer_requests/` | `Customer Request`, `Business Goal` | `episodic` / `semantic` | `standard` |
| **要件定義** | `wiki/02_requirements/` | `Requirement`, `Functional Spec` | `semantic` | `standard` |
| **概要設計** | `wiki/03_basic_designs/` | `Architecture`, `System Design` | `semantic` | `permanent` |
| **詳細設計** | `wiki/04_detailed_designs/` | `Database Table`, `API Endpoint` | `semantic` | `standard` |
| **設計決定** | `wiki/05_decisions/` | `Decision (ADR)` | `semantic` | `permanent` |
| **その他** | `wiki/99_others/` | `Glossary`, `Meeting Minutes`, `Runbook` | `procedural` / `episodic` | `permanent` / `standard` |

---

## Ingest の作業手順（自動実行パイプライン）

### 1. ドキュメントの変換と自動クレンジング・機密スクラビング
- `scripts/convert_anydoc.py` や `scripts/table_cleaner.py` を実行するか、テキスト/PDF を読み取って、大量の空セル（`| | | |`）や不要な空行、HTML ゴミを自動除去したクリーンな Markdown を生成します。
- **機密情報の保護**: API キー、平文パスワード、顧客個人情報（PII）が含まれている場合は環境変数（`$SECRET`）やマスク（`***`）に置換します。
- **解像度保持**: API パラメータ、カラム型定義、エラーコード等の詳細を要約省略せず完全に保持します。

### 2. 知識の分割 (Concept 分割)
- 1 つの大きな資料をそのまま 1 ファイルにするのではなく、**「1 概念 = 1 ファイル」** の原則で論理的に分割します。

### 3. OKF v0.2 & LLM Wiki v2 フォーマットの適用
生成するすべての Concept ドキュメントに以下の Frontmatter を適用します：

```yaml
---
type: Database Table
title: Users Table Specification
description: ユーザーマスタおよび認証情報のテーブル定義
tags: [auth, user, db]
status: active

# Memory Lifecycle
memory_tier: semantic
decay_rate: standard
last_reinforced_at: 2026-08-14T16:00:00Z
access_count: 1

# Confidence Scoring
confidence:
  base_score: 0.90
  current_score: 0.90
  factors:
    source_count: 1
    authority: high
    human_verified: false
    has_contradictions: false

generated:
  by: agent:antigravity/gemini-3.7-flash
  at: 2026-08-14T16:00:00Z

sources:
  - id: user-schema-v1
    resource: raw/04_detailed_designs/user_schema.xlsx
    title: ユーザー設計書
    authority: high
    last_modified: 2026-08-14

relations:
  implements: [02_requirements/req_user_management]
  depends_on: [03_basic_designs/arch_auth_system]
---
```

### 4. インデックス・更新履歴・ナレッジグラフの自動更新（必須）
- 各カテゴリフォルダの `index.md` に新しい Concept へのリンクと説明を追加。
- `wiki/log.md` の先頭に取り込み履歴を追記。
- `python3 scripts/build_graph.py wiki/` を実行し、`graph.json` および `graph.mermaid` を自動更新。
