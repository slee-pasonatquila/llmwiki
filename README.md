# LLM Wiki for Development Projects (Google OKF v0.2 & LLM Wiki v2 準拠)

本リポジトリは、開発プロジェクトにおける各種ドキュメント（顧客要望、要件定義書、概要設計書、詳細設計書、ADR、議事録等）を、**LLM Wiki v2 概念** および **Google OKF (Open Knowledge Format) v0.2** 仕様に基づいて一元管理・運用するための統合ナレッジベースです。

一次情報（Office / PDF / SQL / テキスト）を自動クレンジング・機密スクラビングして取り込み、人間と AI エージェント（Antigravity）が協調して高精度に閲覧・更新・検索・検査できる環境を提供します。

---

## 📚 目次
1. [LLM Wiki v2 & Google OKF v0.2 のコア概念](#-llm-wiki-v2--google-okf-v0-2-のコア概念)
2. [リポジトリ構成とフォルダの役割](#-リポジトリ構成とフォルダの役割)
3. [OKF v0.2 Frontmatter 仕様](#-okf-v02-frontmatter-仕様)
4. [Antigravity Skills の使い方](#-antigravity-skills-の使い方)
5. [運用ルールと品質規約 (Rules & Guidelines)](#-運用ルールと品質規約-rules--guidelines)
6. [CLI 支援ツールの使い方](#-cli-支援ツールの使い方)
7. [Git & GitHub 運用フロー](#-git--github-運用フロー)

---

## 💡 LLM Wiki v2 & Google OKF v0.2 のコア概念

### 1. "Stop Re-deriving, Start Compiling" (LLM Wiki v2)
従来の RAG（検索拡張生成）のように散在するドキュメントを毎回その場で切り貼りして要約し直すのではなく、**AI エージェント自身が継続的に編集・統合・相互リンク（Cross-linking）・信頼性検証を施した構造化知識層（Compiled Knowledge Layer）** を Git リポジトリ上で育てます。

- **Memory Lifecycle & Confidence**: 知識の鮮度・信頼度を管理し、陳腐化や世代交代（Supersession）を追跡。
- **Typed Knowledge Graph**: `implements`, `depends_on`, `supersedes` などのセマンティックな関係性を付与し、Graph Traversal による確実な影響調査が可能。
- **Crystallization（結晶化）**: 調査やデバッグ、ADR の結論を即座に再利用可能な一級の知識ドキュメントとして Wiki に定着。

### 2. Google OKF (Open Knowledge Format) v0.2 仕様
Google Cloud が提唱するオープンなナレッジ表現仕様です。
- **Knowledge Bundle**: ディレクトリツリー全体が自己完結した知識の集合体。
- **Concept Document**: 1 ファイル = 1 知識単位。ファイル先頭に YAML Frontmatter（`type:` 必須）、本文は構造的 Markdown。
- **Provenance（来歴）**: `sources` リストと Markdown 脚注（`[^source_id]`）による主張単位の明確な根拠付け。
- **Trust & Verification**: `verified: { by, at, method }` と Actor 規約（`agent:...`, `human:...`, `process:...`）による信頼性の可視化。
- **Progressive Disclosure**: 各階層の `index.md` により、AI や人間が全ファイルを読まずとも目次から必要な知識へ最短でアクセス可能。
- **Changelog**: `log.md` による時系列・Actor 別の更新管理。

---

## 📁 リポジトリ構成とフォルダの役割

```text
llmwiki/
├── README.md                      # 本ドキュメント
├── SCHEMA.md                      # AI エージェント用 Wiki 編纂ルール (OKF v0.2 準拠)
├── .gemini/
│   └── skills/                    # Antigravity 専用スキル群
│       ├── llm-wiki-clean/        # Markdown 不要空欄・Excel空セル削除・構造整形・シークレット除去
│       ├── llm-wiki-ingest/       # 一次資料取り込み・OKF v0.2 知識化・脚注付与
│       ├── llm-wiki-lint/         # OKF v0.2 整合性・ゴーストリンク・脚注検査
│       ├── llm-wiki-query/        # Wiki 横断検索・Graph Traversal・仕様回答
│       └── llm-wiki-update/       # 仕様変更・ADR 起票・世代交代 (Supersession)
├── scripts/                       # 運用スクリプト
│   ├── convert_anydoc.py          # anydoc 変換 ＋ ルールベース前処理
│   ├── table_cleaner.py           # 表の空セル・空列・空行自動削除モジュール
│   └── lint_okf.py                # OKF v0.2 適合性自動検査・バリデータ
├── raw/                           # 【一次資料保管庫】（人間が受領・配置した原本）
│   ├── 01_customer_requests/      # 顧客ヒアリングシート、RFP、要望一覧
│   ├── 02_requirements/           # システム要件定義書、業務フロー図
│   ├── 03_basic_designs/          # 基本設計書、システム構成図、外部IF仕様書
│   ├── 04_detailed_designs/       # 詳細設計書、DB定義 (Excel/DDL)、API仕様書
│   ├── 05_decisions/              # 意思決定の背景資料・比較検討資料
│   └── 99_others/                 # 参考技術資料、開発ガイドライン、議事録
└── wiki/                          # 【Google OKF v0.2 準拠 編集済み知識層】
    ├── index.md                   # 全体マスターインデックス
    ├── log.md                     # 全体更新履歴 (Changelog)
    ├── 01_customer_requests/      # 顧客要望コンセプト群 (index.md 完備)
    ├── 02_requirements/           # 要件定義コンセプト群 (index.md 完備)
    ├── 03_basic_designs/          # 概要・基本設計コンセプト群 (index.md 完備)
    ├── 04_detailed_designs/       # 詳細設計コンセプト群 (DB/API/画面)
    ├── 05_decisions/              # アーキテクチャ決定記録 (ADR)
    └── 99_others/                 # プロジェクト共通用語集 (glossary.md) 等
```

---

## 🏷️ OKF v0.2 Frontmatter 仕様

```yaml
---
type: Database Table             # 【必須】概念種別
title: Users Table Specification # 【推奨】ドキュメント表示名
description: ユーザーマスタおよび認証情報のテーブル定義 # 【推奨】1行要約
tags: [auth, user, database]    # 【任意】分類・検索用タグ
status: active                   # 【推奨】draft | active | deprecated | tombstone

generated:
  by: agent:antigravity/gemini-3.7-flash # 生成 Actor
  at: 2026-08-14T16:00:00Z               # 生成日時 (ISO 8601)

verified:                                # 検証情報 (Trust Tier)
  by: human:slee
  at: 2026-08-14T16:30:00Z
  method: manual_audit

sources:                                 # 一次情報来歴 (Provenance)
  - id: user-schema-v1
    resource: raw/04_detailed_designs/user_schema.xlsx
    title: ユーザー設計書
    last_modified: 2026-08-14

relations:                               # セマンティック関連 (Typed Relations)
  implements: [02_requirements/req_user_management]
  depends_on: [03_basic_designs/arch_auth_system]
---
```

---

## 🚀 Antigravity Skills の使い方

Antigravity IDE のチャット画面から、自然な指示を出すだけで、AI エージェントが OKF v0.2 に準拠した知識操作を自律的に実行します。

### 1. 資料の追加・Wiki 化（自動クレンジング ＋ Ingest）
一次資料（Excel, PDF, Word, SQL 等）を指定するだけで、不要な空セルや空行を自動クレンジングし、シークレットを除去した上で OKF v0.2 形式（`sources` ＋ 脚注）で取り込みます。
> **プロンプト例:**
> 「`raw/04_detailed_designs/db_schema.xlsx` を Wiki に追加してください。」

### 2. 質問・横断検索（Query）
Progressive Disclosure および Graph Traversal（`implements`, `depends_on` 等）を辿り、根拠（Footnotes / Sources）と信頼度（Trust Tier）付きで回答します。
> **プロンプト例:**
> 「ユーザー認証機能について、要件定義から DB 設計、API 仕様までどうなっているか教えてください。」

### 3. 仕様変更・世代交代（Update）
仕様変更時に過去の記述を取り消し線（`~~`）で残しつつ更新し、必要に応じて ADR 起票や旧ドキュメントの世代交代（`supersedes` / `superseded_by`）を行います。
> **プロンプト例:**
> 「パスワード失敗時のロック時間を15分から30分に変更してください。」

### 4. Wiki の整合性検査・修復（Lint）
OKF v0.2 適合性、リンク切れ、脚注対応、フロントマター欠落などを検査・修復します。
> **プロンプト例:**
> 「Wiki 全体のリンク切れや OKF v0.2 整合性をチェックして修正してください。」

---

## 📋 運用ルールと品質規約 (Rules & Guidelines)

1. **要約による情報欠落の禁止（最重要）**:
   - API パラメータ一覧、テーブルカラムの型・NULL 可否、エラーコード表、業務計算ルール等の詳細定義を**「箇条書き 3 行に丸める」などの要約省略を絶対に行わない**。原本の解像度を 100% 保持すること。
2. **OKF v0.2 構文の厳守**:
   - 全 Concept ファイルに `type`（必須）、`generated`、`sources`、`status` を記載。
3. **主張単位の根拠付け（Footnotes `[^source_id]`）**:
   - 仕様や数値の根拠は `sources` の `id` と紐づく脚注記法で本文中に明記する。
4. **相互リンク（Cross-linking）とセマンティック関係の明示**:
   - 関連する Concept 間は標準 Markdown リンクで接続し、Frontmatter の `relations` で関係性（`implements`, `depends_on` 等）を定義する。
5. **破壊的削除の禁止（取り消し線・世代交代の活用）**:
   - 仕様変更時は、変更前の重要な記述を削除せず取り消し線（`~~旧仕様~~`）で残すか、`supersedes` / `superseded_by` で世代を管理する。
6. **未確定情報の扱い**:
   - 原本から確認できない情報は AI の推測で勝手に埋めず、`要確認: [不明点]` として明記する。
7. **機密情報の保護 (Privacy Governance)**:
   - API キーやパスワード、個人情報（PII）は Ingest 時に自動検知してマスクする。

---

## 🛠️ CLI 支援ツールの使い方

### 1. OKF v0.2 整合性・バリデータ (`lint_okf.py`)
```bash
# Wiki 全体の適合性を検査
python3 scripts/lint_okf.py wiki/
```

### 2. ドキュメント変換と自動クレンジング (`convert_anydoc.py`)
```bash
# 単一ファイルの変換と空セル削除
python3 scripts/convert_anydoc.py raw/04_detailed_designs/schema.xlsx -o temp_cleaned.md

# ディレクトリ一括変換
python3 scripts/convert_anydoc.py raw/01_customer_requests/ -o temp_requests/
```

### 3. Markdown 表クレンジング単体実行 (`table_cleaner.py`)
```bash
python3 scripts/table_cleaner.py messy_table.md clean_table.md
```

---

## 🐙 Git & GitHub 運用フロー

1. **ブランチ運用**:
   - 新規資料の取り込みや仕様更新はトピックブランチ（例: `feature/ingest-auth-spec`）で作業。
2. **コミット規約**:
   - 一次資料の追加: `docs(raw): add auth_spec_v2.pdf`
   - Wiki の更新: `docs(wiki): ingest auth requirements into 02_requirements`
3. **CI / CD (GitHub Actions)**:
   - Pull Request 時に `python3 scripts/lint_okf.py wiki/` を実行し、OKF v0.2 適合性およびリンク・脚注の整合性が保たれていることを自動検証します。
