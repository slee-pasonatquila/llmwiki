# Claude Code Workspace Guidelines: LLM Wiki (Google OKF v0.2 & v2 / Multi-User)

本ワークスペースは、**Google OKF (Open Knowledge Format) v0.2** および **LLM Wiki v2** 仕様に準拠した統合ナレッジベースです。
AI エージェント（Claude Code）は、単なるテキスト応答者ではなく、**「知識の編纂者・保守者（Knowledge Curator & Compiler）」** として動作します。

すべての対話およびファイル操作において、以下のコア規約を厳格に遵守してください。

---

## 🎯 エージェント行動の 5 大原則

1. **解像度の完全保持（最重要 / Zero Information Loss）**:
   - 一次資料からの情報取り込み時、API パラメータ一覧、テーブルカラムの型・NULL 可否、エラーコード、業務計算ルール等の詳細定義を**絶対に要約省略しない**。原本の解像度を 100% 保持すること。
2. **Google OKF v0.2 Frontmatter 必須**:
   - `wiki/` 配下のすべての Concept ファイルに、完全な Frontmatter（`type`, `memory_tier`, `confidence`, `sources`, `relations` 等）を付与する。
3. **主張単位の根拠付け（Footnotes `[^id]`）**:
   - 本文中の仕様・数値・テーブル定義は、`sources` の `id` と紐づく脚注記法（例: `[^src-1]`）で根拠を明記する。
4. **非破壊的更新の原則**:
   - 仕様変更時は過去の記述を削除せず、取り消し線（`~~旧仕様~~`）で残すか、`supersedes` / `superseded_by` を用いて安全に世代交代する。
5. **複数人協調・自動同期（Decentralized Sync）**:
   - `index.md` や `log.md` の手動編集はコンフリクトの原因となるため禁止。変更ログは `wiki/.changelogs/` に断片保存し、同期は `python3 scripts/sync_wiki.py` または CI 自動化に委ねる。動的アクセス記録は `metrics.db` で分離管理する。

---

## 💻 Claude Code で実行可能なコマンド一覧

Claude Code 内では、以下のスラッシュコマンド（または Python スクリプト）を用いて各種 Wiki 操作を実行してください。

| スラッシュコマンド | 実行する Python スクリプト / 役割 | 説明 |
| :--- | :--- | :--- |
| `/llmwiki_ingest <file_path>` | `python3 scripts/convert_anydoc.py` + Wiki編纂 | 一次資料を取り込み、クレンジング・機密除去後に OKF Concept ドキュメントとして生成 |
| `/llmwiki_query <question>` | `python3 scripts/hybrid_search.py "<question>"` | ハイブリッド検索（BM25 + グラフ近傍）でナレッジを横断探索し、確信度・根拠付きで回答 |
| `/llmwiki_update <target>` | `python3 scripts/memory_decay.py --reinforce` + 編集 | 仕様変更の適用、忘却曲線の強化、世代交代（supersedes）、ADR起票 |
| `/llmwiki_lint` | `python3 scripts/lint_okf.py wiki/` | OKF v0.2 スキーマ、忘却曲線、リンク切れ、未インデックスファイルの自動整合性検査 |
| `/llmwiki_clean <file_path>` | `python3 scripts/table_cleaner.py <file_path>` | 粗い Markdown・表データの空セル・不要空行の自動削除と機密情報マスク |
| `/llmwiki_sync` | `python3 scripts/sync_wiki.py` | `index.md`, `log.md`, `graph.json` / `mermaid` を一括自動再構築 |

---

## 📁 ディレクトリ構造と保存先

```text
llmwiki/
├── CLAUDE.md              # Claude Code 向けガイドライン（本ファイル）
├── AGENTS.md / GEMINI.md  # Google Antigravity / Gemini 向けガイドライン
├── .claude/commands/      # Claude Code カスタムスラッシュコマンド定義 (llmwiki_*.md)
├── .agents/skills/        # Antigravity Skills 定義 (llmwiki_*/SKILL.md)
├── .agents/rules/         # Antigravity & Claude 共通行動規約
├── raw/                   # 一次資料（Excel, Word, PowerPoint, PDF, SQL, text）
├── scripts/               # 自動化 Python スクリプト群
└── wiki/                  # OKF v0.2 構造化ナレッジ層
    ├── index.md           # 全体インデックス（自動生成）
    ├── log.md             # 統合変更履歴（自動生成）
    ├── graph.json / .mmd  # ナレッジグラフ定義（自動生成）
    ├── .changelogs/       # 分散チェンジログ断片（Git コンフリクト防止）
    ├── 01_customer_requests/ # 顧客要望・ビジネスゴール
    ├── 02_requirements/      # 要件定義・機能要件
    ├── 03_basic_designs/     # 概要設計・アーキテクチャ
    ├── 04_detailed_designs/  # 詳細設計（DB テーブル, API 等）
    ├── 05_decisions/         # 設計決定（ADR）
    └── 99_others/            # 用語集・議事録・Runbook
```

---

## 📝 OKF v0.2 Frontmatter 記述規約 (Claude Code 生成時)

Claude Code が新規ドキュメントを作成または更新する際は、`generated.by` に `agent:claude-code/<model>` を明記してください：

```yaml
---
type: Database Table
title: Users Table Specification
description: ユーザーマスタおよび認証情報のテーブル定義
tags: [auth, user, db]
status: draft

memory_tier: semantic
decay_rate: standard
last_reinforced_at: 2026-08-17T00:00:00Z
access_count: 1

confidence:
  base_score: 0.90
  current_score: 0.90
  factors:
    source_count: 1
    authority: high
    human_verified: false
    has_contradictions: false

generated:
  by: agent:claude-code/claude-3-7-sonnet
  at: 2026-08-17T00:00:00Z

sources:
  - id: src-1
    resource: raw/04_detailed_designs/user_schema.xlsx
    title: ユーザー設計書
    authority: high
    last_modified: 2026-08-17

relations:
  implements: [02_requirements/req_user_management]
  depends_on: [03_basic_designs/arch_auth_system]
  uses: [03_basic_designs/infra_postgresql]
  contradicts: []
---
```

---

## 📚 詳細モジュール別ルール

詳細な仕様および規約は、以下の `.agents/rules/` 内の各ルール定義に従ってください：

- [01_core_philosophy.md](file:///Users/slee/Documents/gitRoot/llmwiki/.agents/rules/01_core_philosophy.md): 設計思想・解像度保持・機密スクラビング規約
- [02_okf_frontmatter.md](file:///Users/slee/Documents/gitRoot/llmwiki/.agents/rules/02_okf_frontmatter.md): OKF v0.2 & v2 Frontmatter 完全スキーマ
- [03_memory_lifecycle.md](file:///Users/slee/Documents/gitRoot/llmwiki/.agents/rules/03_memory_lifecycle.md): 4層メモリ階層・忘却曲線・矛盾解決規約
- [04_wiki_operations.md](file:///Users/slee/Documents/gitRoot/llmwiki/.agents/rules/04_wiki_operations.md): 複数人協調・Wiki編纂・更新・検査オペレーション手順
- [05_git_workflow.md](file:///Users/slee/Documents/gitRoot/llmwiki/.agents/rules/05_git_workflow.md): Git / GitHub 運用フローと CI/CD 自動同期
