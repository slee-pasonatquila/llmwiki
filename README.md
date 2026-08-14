# LLM Wiki for Development Projects (Google OKF 準拠)

本リポジトリは、開発プロジェクトにおける各種書類（顧客要望、要件定義書、概要設計書、詳細設計書、ADR、議事録等）を、**LLM Wiki 概念**および **Google OKF (Open Knowledge Format v0.1)** 仕様に基づいて一元管理・運用するための統合ナレッジベースです。

一次情報（Office / PDF / SQL / テキスト）を自動クレンジングして取り込み、人間と AI エージェント（Antigravity）が協調して高精度に閲覧・更新・検索・検査できる環境を提供します。

---

## 📚 目次
1. [LLM Wiki & Google OKF とは](#-llm-wiki--google-okf-とは)
2. [リポジトリ構成とフォルダの役割](#-リポジトリ構成とフォルダの役割)
3. [Antigravity Skills の使い方](#-antigravity-skills-の使い方)
4. [運用ルールと品質規約 (Rules & Guidelines)](#-運用ルールと品質規約-rules--guidelines)
5. [CLI 支援ツールの使い方](#-cli-支援ツールの使い方)
6. [Git & GitHub 運用フロー](#-git--github-運用フロー)

---

## 💡 LLM Wiki & Google OKF とは

### 1. LLM Wiki 概念
従来の RAG（検索拡張生成）のように散在するドキュメントを毎回その場で検索・切り貼りするのではなく、**AI エージェント自身が継続的に編集・統合・相互リンク（Cross-linking）を施した構造化 Markdown 群（編集済み知識層）** を Git リポジトリ上で育てるアーキテクチャです。

### 2. Google OKF (Open Knowledge Format v0.1) 仕様
Google Cloud が公開したナレッジ記述のオープン標準仕様です。
* **Knowledge Bundle**: ディレクトリツリー全体が自己完結した知識の集合体。
* **Concept Document**: 1 ファイル = 1 知識単位。ファイル先頭に YAML Frontmatter（`type:` 必須）、本文は構造的 Markdown。
* **Progressive Disclosure**: 各階層の `index.md` により、AI や人間が全ファイルを読まずとも目次から必要な知識へ最短でアクセス可能。
* **Grounding (Citations)**: 文末に `# Citations` を設け、一次情報（`raw/`）への根拠を明示。
* **Changelog**: `log.md` による時系列の更新管理。

---

## 📁 リポジトリ構成とフォルダの役割

```text
llmwiki/
├── README.md                      # 本ドキュメント
├── SCHEMA.md                      # AI エージェント用 Wiki 編纂ルール
├── .gemini/
│   └── skills/                    # Antigravity 専用スキル群
│       ├── llm-wiki-clean/        # Markdown 不要空欄・Excel空セル削除・構造整形
│       ├── llm-wiki-ingest/       # 一次資料取り込み・OKF 知識化
│       ├── llm-wiki-lint/         # OKF 整合性・ゴーストリンク検査
│       ├── llm-wiki-query/        # Wiki 横断検索・仕様回答
│       └── llm-wiki-update/       # 仕様変更・ADR 起票・差分管理
├── scripts/                       # 運用スクリプト
│   ├── convert_anydoc.py          # anydoc 変換 ＋ ルールベース前処理
│   ├── table_cleaner.py           # 表の空セル・空列・空行自動削除モジュール
│   └── lint_okf.py                # OKF 適合性自動検査スクリプト
├── raw/                           # 【一次資料保管庫】（人間が受領・配置した原本）
│   ├── 01_customer_requests/      # 顧客ヒアリングシート、RFP、要望一覧
│   ├── 02_requirements/           # システム要件定義書、業務フロー図
│   ├── 03_basic_designs/          # 基本設計書、システム構成図、外部IF仕様書
│   ├── 04_detailed_designs/       # 詳細設計書、DB定義 (Excel/DDL)、API仕様書
│   └── 99_others/                 # 参考技術資料、開発ガイドライン、議事録
└── wiki/                          # 【Google OKF 準拠 編集済み知識層】
    ├── index.md                   # 全体マスターインデックス
    ├── log.md                     # 全体更新履歴 (Changelog)
    ├── 01_customer_requests/      # 顧客要望コンセプト群 (index.md 完備)
    ├── 02_requirements/           # 要件定義コンセプト群 (index.md 完備)
    ├── 03_basic_designs/          # 概要・基本設計コンセプト群 (index.md 完備)
    ├── 04_detailed_designs/       # 詳細設計コンセプト群 (DB/API/画面)
    ├── 05_decisions/              # 【提案】アーキテクチャ決定記録 (ADR)
    └── 99_others/                 # 【提案】プロジェクト共通用語集 (glossary.md)
```

---

## 🚀 Antigravity Skills の使い方

Antigravity IDE のチャット画面から、日常的な言葉で自然に指示を出すだけで、AI エージェントが必要なクレンジングやファイル更新を自律的に行います。  
*(※ `index.md` や `log.md` などの内部管理ファイルは、作業時にエージェントが自動的に更新するため、ユーザーが指定する必要はありません)*

### 1. 資料の追加・Wiki 化（自動クレンジング ＋ Ingest）
一次資料（Excel, PDF, Word, SQL 等）を指定するだけで、不要な空セルや空行を自動クレンジングし、適切な `wiki/` フォルダへ OKF 形式で取り込みます。
> **プロンプト例:**
> 「`raw/04_detailed_designs/db_schema.xlsx` を Wiki に追加してください。」

### 2. 質問・横断検索（Query）
顧客要望から要件、詳細設計、ADR に至るトレーサビリティを辿り、根拠リンク（Citations）付きで回答します。
> **プロンプト例:**
> 「ユーザー認証機能について、要件定義から DB 設計、API 仕様までどうなっているか教えてください。」

### 3. 仕様変更の反映（Update）
仕様変更時に過去の記述を取り消し線（`~~`）で残しつつ更新し、必要に応じて ADR を作成・関連ドキュメントを連鎖更新します。
> **プロンプト例:**
> 「パスワード失敗時のロック時間を15分から30分に変更してください。」

### 4. Wiki の整合性検査・修復（Lint）
リンク切れやフロントマターの欠落などを検査・修復します。
> **プロンプト例:**
> 「Wiki 全体のリンク切れや整合性をチェックして修正してください。」

---

## 📋 運用ルールと品質規約 (Rules & Guidelines)

1. **要約による情報欠落の禁止（最重要）**:
   - API パラメータ一覧、テーブルカラムの型・NULL 可否、エラーコード表、業務計算ルール等の詳細定義を**「箇条書き 3 行に丸める」などの要約省略を絶対に行わない**。原本の解像度を完全に保つこと。
2. **OKF 構文の厳守**:
   - 全 Concept ファイルに `type`（必須）、`title`、`description`、`tags`、`timestamp`、`resource` を記載。
3. **出典の明記 (# Citations)**:
   - 全 Concept ファイルの末尾に `# Citations` を配置し、一次情報ファイルへの参照リンク（例: `[1] [原本名](raw/path/to/file)`）を必ず残す。
4. **相互リンク（Cross-linking）の義務化**:
   - 関連する Concept 間は標準 Markdown リンク（例: `[Users Table](../04_detailed_designs/table_users.md)`）で相互に接続する。
5. **破壊的削除の禁止（取り消し線保持）**:
   - 仕様変更時は、変更前の重要な記述を削除せず取り消し線（`~~旧仕様~~`）で残し、直後に新仕様を追記する。
6. **未確定情報の扱い**:
   - 原本から確認できない情報は AI の推測で勝手に埋めず、`要確認: [不明点]` として明記する。

---

## 🛠️ CLI 支援ツールの使い方

### 1. OKF 整合性・リンク自動検査 (`lint_okf.py`)
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
   - Pull Request 時に `python3 scripts/lint_okf.py wiki/` を実行し、OKF 適合性およびリンク切れがないことを自動検証することを推奨します。
