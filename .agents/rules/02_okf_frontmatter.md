# Rule 02: Google OKF v0.2 & LLM Wiki v2 Frontmatter Specification

`wiki/` 配下に配置されるすべての Markdown ファイル（Concept ドキュメント）は、先頭に以下の完全な YAML Frontmatter を持たなければならない。

```yaml
---
type: Database Table             # 【必須】概念種別 (Database Table, API Endpoint, Requirement, Architecture, Decision (ADR), Glossary など)
title: Users Table Specification # 【推奨】ドキュメント表示名
description: ユーザーマスタおよび認証情報のテーブル定義 # 【推奨】1行要約 (50〜200文字)
tags: [auth, user, database]    # 【任意】分類・検索用タグ配列
status: active                   # 【必須】draft | active | stale | deprecated | tombstone

# 1. Memory Lifecycle
memory_tier: semantic            # 【必須】working | episodic | semantic | procedural
decay_rate: standard             # 【必須】permanent | standard | volatile
last_reinforced_at: 2026-08-14T16:00:00Z # 【必須】最終確認・強化日時 (ISO 8601)
access_count: 1                 # 【必須】参照・強化回数 (整数)

# 2. Confidence Scoring
confidence:
  base_score: 0.90               # 【必須】初期確信度 (0.0〜1.0)
  current_score: 0.90            # 【必須】減衰適用後スコア (0.0〜1.0)
  factors:
    source_count: 2              # 【必須】裏付け一次資料数
    authority: high              # 【必須】high (原本/公式仕様) | medium (議事録) | low (推論)
    human_verified: true         # 【必須】人間による監査有無 (boolean)
    has_contradictions: false    # 【必須】矛盾フラグ (boolean)

# 3. 生成・検証情報
generated:
  by: agent:antigravity/gemini-3.7-flash # 【必須】生成エージェント名
  at: 2026-08-14T16:00:00Z       # 【必須】生成日時 (ISO 8601)

verified:                        # 【任意/推奨】人間による監査情報
  by: human:slee
  at: 2026-08-14T16:30:00Z
  method: manual_audit

# 4. 来歴 (Provenance)
sources:                         # 【必須】裏付け一次資料リスト (1件以上)
  - id: user-schema-v1           # 本文中の脚注 [^user-schema-v1] で参照されるID
    resource: raw/04_detailed_designs/user_schema.xlsx # 相対ファイルパス
    title: ユーザー設計書
    authority: high
    last_modified: 2026-08-14

# 5. 世代交代 & ナレッジグラフ (Typed Relations)
supersedes: []                   # 【必須】旧ドキュメントの相対パス配列
superseded_by: null              # 【必須】新ドキュメントの相対パス (置換された場合のみ)
relations:
  implements: [02_requirements/req_user_management] # 要件の実現
  depends_on: [03_basic_designs/arch_auth_system]   # 前提・依存関係
  uses: [03_basic_designs/infra_postgresql]         # 利用・参照関係
  contradicts: []                                   # 矛盾・対立関係
---
```

## 本文中の脚注 (Footnotes) 規約
- すべての重要仕様、型定義、計算ルール、ビジネス制約には、`sources` の `id` を参照する脚注記法を使用する。
  ```markdown
  ユーザーパスワードは bcrypt でハッシュ化して保存する[^user-schema-v1]。
  パスワード失敗上限は 5 回とする[^user-schema-v1]。

  [^user-schema-v1]: raw/04_detailed_designs/user_schema.xlsx「認証仕様シート」より引用
  ```
