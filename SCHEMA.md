# LLM Wiki Schema & Compilation Rules (Google OKF v0.2 & LLM Wiki v2 準拠)

本ファイルは、AI エージェント（知識編纂者）および開発者が本リポジトリのドキュメントを読み込み、編纂・更新・検証・探索する際に厳格に従うべきスキーマおよび運用ルールを定義します。

---

## 1. 基本方針と役割 (Core Philosophy & Agent Role)

### 1.1 コア原則: "Stop Re-deriving, Start Compiling" (LLM Wiki v2)
- 従来の RAG（検索拡張生成）のように毎回未構造化ドキュメントを断片的に読み直して要約するのではなく、**AI エージェント自身が継続的に整理・統合・相互リンク・検証・減衰管理した構造化ナレッジ層（Compiled Knowledge Layer）** を Git 上で蓄積・成長させます。
- **ドキュメントの解像度保持（最重要）**: API パラメータ一覧、テーブルカラムの型・NULL 可否、エラーコード、業務計算ルール等の詳細定義を「箇条書き 3 行に丸める」などの要約省略を絶対に行いません。原本の解像度を 100% 保持します。

### 1.2 エージェントの役割 (Knowledge Curator & Compiler)
- `raw/` に配置された一次資料（原本）から情報を抽出し、不要な空行・空セル等のノイズをクレンジングした上で、`wiki/` 配下に **Google OKF (Open Knowledge Format v0.2)** および **LLM Wiki v2** 準拠の Concept ドキュメントを作成・保守します。
- 記憶のライフサイクル（4層メモリ階層、忘却曲線、確信度スコア、型付きナレッジグラフ、矛盾解決、ハイブリッド検索）を能動的に管理します。

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
└── wiki/                     # 【Google OKF v0.2 & LLM Wiki v2 編集済み知識層】
    ├── index.md              # 全体マスターインデックス (Progressive Disclosure)
    ├── log.md                # 全体更新履歴 (Changelog with Actor Attribution)
    ├── graph.json            # ナレッジグラフデータ (JSON)
    ├── graph.mermaid         # ナレッジグラフ可視化 (Mermaid)
    ├── 01_customer_requests/ # 顧客要望コンセプト群 (index.md 完備)
    ├── 02_requirements/      # 要件定義コンセプト群 (index.md 完備)
    ├── 03_basic_designs/     # 概要設計コンセプト群 (index.md 完備)
    ├── 04_detailed_designs/  # 詳細設計コンセプト群 (DB/API/画面)
    ├── 05_decisions/         # アーキテクチャ決定記録 (ADR)
    └── 99_others/            # 用語集 (glossary.md)・運用手順
```

---

## 3. LLM Wiki v2 コアアーキテクチャ仕様

### 3.1 Memory Lifecycle (4層メモリ階層 & 忘却曲線)

知識を 4 つのメモリ階層に分類し、時間の経過とともに圧縮・抽象化・長期固定化します。

| メモリ階層 (`memory_tier`) | 役割と対象ドキュメント | 寿命 / 減衰率 (`decay_rate`) |
| :--- | :--- | :--- |
| **Working Memory** (`working`) | 未処理の観察、ドラフトメモ、一時的なセッション記録 | 短期（`volatile`: $\lambda=0.05$, 半減期約14日） |
| **Episodic Memory** (`episodic`) | セッション要約、顧客ヒアリング議事録、ミーティング記録 | 中期（`standard`: $\lambda=0.01$, 半減期約69日） |
| **Semantic Memory** (`semantic`) | 要件定義、アーキテクチャ、DBスキーマ、API仕様、ADR | 長期〜永続（`standard` / `permanent`: $\lambda=0.002$） |
| **Procedural Memory** (`procedural`) | ワークフロー、運用手順書 (Runbook)、SOP、スキル定義 | 永続（`permanent`: $\lambda=0.002$, 半減期約346日） |

#### エビングハウス忘却曲線 (Forgetting Curve) による確信度減衰
知識は放置されると時間経過で確信度スコアが減衰します：
$$\text{Score}(t) = \text{BaseScore} \times e^{-\lambda \times \Delta t} + \text{VerificationBoost}$$
- 参照・更新・検証（`last_reinforced_at`）によってタイマーがリセットされ、記憶が再強化（Reinforce）されます。
- スコアが 0.50 未満に落ちたドキュメントは `status: stale`（要再確認）として検知されます。

---

### 3.2 Confidence Scoring (確信度スコア & 矛盾解決)

すべての Concept に確信度スコア（0.0 〜 1.0）を付与し、知識の信頼性を数学的に管理します。

```yaml
confidence:
  base_score: 0.90               # 初期確信度 (0.0〜1.0)
  current_score: 0.88            # 忘却曲線減衰後の現在スコア
  factors:
    source_count: 2              # 裏付け一次資料数
    authority: high              # high (原本/公式仕様) | medium (議事録) | low (推論)
    human_verified: true         # 人間による監査有無 (+0.05〜0.10 ブースト)
    has_contradictions: false    # 矛盾フラグ
```

#### 矛盾解決 (Contradiction Resolution)
新旧の記述や異資料間で矛盾が生じた場合：
1. `relations.contradicts: [対象Concept]` を明記。
2. ソース権威性（原本 > 議事録 > AIドラフト）、新しさ、裏付け数に基づき、新しい仕様を優先。
3. 旧仕様は `status: deprecated` および `superseded_by` で置換し、変更経緯を保持。

---

### 3.3 Knowledge Graphs (型付きエンティティ & 型付き関係)

単なるフラットなリンクではなく、セマンティックな関係性を Frontmatter で明示します。

#### 型付きリレーション一覧 (`relations`)
- `implements`: 要件や顧客要望を具体的に実現・実装している関係。
- `depends_on`: 他の設計やインフラ、前提条件に依存している関係。
- `uses`: 外部ライブラリ、共通サービス、共通テーブルを利用している関係。
- `contradicts`: 主張や仕様が矛盾・対立している関係（要解消）。
- `supersedes` / `superseded_by`: ドキュメント・仕様の世代交代。
- `fixes` / `tested_by`: 不具合修正やテストによる検証関係。

---

### 3.4 Hybrid Search (ハイブリッド検索エンジン)

Wiki の規模拡大に対応するため、3 種類の手法を **Reciprocal Rank Fusion (RRF)** で統合します：
1. **BM25Okapi**: 語彙・コード識別子・日本語 N-gram の厳密キーワード検索。
2. **Semantic Similarity**: 概念、タイトル、説明、タグの意味的類似度。
3. **Graph Proximity**: クエリ関連ノードからナレッジグラフのエッジ（`implements`, `depends_on` 等）を辿った構造的近傍スコアリング。

$$\text{RRF}(d) = \sum_{m \in \{\text{BM25, Semantic, Graph}\}} \frac{w_m}{k + \text{rank}_m(d)} \times (0.6 + 0.4 \times \text{Confidence}(d))$$

---

## 4. Concept ドキュメントの Frontmatter 仕様

```yaml
---
type: Database Table             # 【必須】概念種別
title: Users Table Specification # 【推奨】ドキュメント表示名
description: ユーザーマスタおよび認証情報のテーブル定義 # 【推奨】1行要約
tags: [auth, user, database]    # 【任意】分類タグ
status: active                   # 【推奨】draft | active | stale | deprecated | tombstone

# 1. Memory Lifecycle
memory_tier: semantic            # 【推奨】working | episodic | semantic | procedural
decay_rate: standard             # 【推奨】permanent | standard | volatile
last_reinforced_at: 2026-08-14T16:00:00Z # 最終確認・強化日時
access_count: 12                 # 参照・強化回数

# 2. Confidence Scoring
confidence:
  base_score: 0.90               # 初期確信度 (0.0〜1.0)
  current_score: 0.90            # 減衰適用後スコア
  factors:
    source_count: 2
    authority: high
    human_verified: true
    has_contradictions: false

# 3. 生成・検証情報
generated:
  by: agent:antigravity/gemini-3.7-flash
  at: 2026-08-14T16:00:00Z

verified:
  by: human:slee
  at: 2026-08-14T16:30:00Z
  method: manual_audit

# 4. 来歴 (Provenance)
sources:
  - id: user-schema-v1
    resource: raw/04_detailed_designs/user_schema.xlsx
    title: ユーザー設計書
    authority: high
    last_modified: 2026-08-14

# 5. 世代交代 & ナレッジグラフ (Typed Relations)
supersedes: []
superseded_by: null
relations:
  implements: [02_requirements/req_user_management]
  depends_on: [03_basic_designs/arch_auth_system]
  uses: [03_basic_designs/infra_postgresql]
  contradicts: []
---
```

---

## 5. 運用ルールと品質規約 (Rules & Guidelines)

1. **要約による情報欠落の禁止（最重要）**:
   - カラム型、NULL可否、パラメータ一覧、エラーコード、業務計算ルール等の詳細定義を**絶対に要約省略しない**。
2. **主張単位の根拠付け（Footnotes `[^source_id]`）**:
   - 本文中の仕様や数値は `sources` の `id` と紐づく脚注記法で根拠を明記。
3. **グラフ関係の明示と相互リンク**:
   - 関連 Concept 間は Markdown リンクで接続し、Frontmatter の `relations` にセマンティックな関係を記録。
4. **忘却曲線の保守と再強化**:
   - 定期的に `python3 scripts/memory_decay.py wiki/` を実行し、減衰した知識を再監査・強化。
5. **破壊的削除の禁止（取り消し線・世代交代の活用）**:
   - 仕様変更時は取り消し線（`~~旧仕様~~`）または `supersedes` / `superseded_by` を使用。
6. **機密情報の保護 (Privacy Governance)**:
   - API キーやパスワード、個人情報は自動検知してマスク（`$SECRET`）化。
