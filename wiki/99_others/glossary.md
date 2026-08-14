---
type: Glossary
title: プロジェクト共通用語集 (Glossary)
description: 本プロジェクトで使用される業務用語、システム略称、ロール定義、ドメイン概念の辞書
tags: [glossary, domain, terms, definition]
status: active

# Memory Lifecycle
memory_tier: procedural
decay_rate: permanent
last_reinforced_at: 2026-08-14T16:00:00Z
access_count: 20

# Confidence Scoring
confidence:
  base_score: 0.98
  current_score: 0.98
  factors:
    source_count: 1
    authority: high
    human_verified: true
    has_contradictions: false

generated:
  by: agent:antigravity/gemini-3.7-flash
  at: 2026-08-14T15:30:00Z

verified:
  by: human:slee
  at: 2026-08-14T16:00:00Z
  method: manual_audit

sources:
  - id: dev-guidelines-v1
    resource: raw/99_others/dev_guidelines.md
    title: システム開発ガイドライン 2026
    author: human:architect
    last_modified: 2026-08-14
---

# プロジェクト共通用語集 (Glossary)

本ドキュメントは、プロジェクト関係者および AI エージェントが共通の認識を持ち、用語の揺らぎやハルシネーションを防ぐための辞書です[^dev-guidelines-v1]。

---

## 1. 認証・セキュリティ関連用語

| 用語 | 英語表記 / 略称 | 定義・説明 |
| :--- | :--- | :--- |
| **JWT** | JSON Web Token | 属性情報（クレーム）を JSON 形式で安全に送受信するためのオープン標準規格 (RFC 7519)。 |
| **RBAC** | Role-Based Access Control | ユーザーに付与された役割（ロール）に基づいてシステム機能のアクセス権限を制御する方式。 |
| **Argon2id** | Argon2id Password Hash | パスワードハッシュ化アルゴリズム。GPU による総当たり攻撃に強い耐性を持つ。 |
| **Opaque Token** | - | トークン文字列自体に意味を持たせず、サーバー側でのみ検証可能な識別子文字列。 |

## 2. 権限ロール定義

| ロールコード | 表示名 | 権限範囲 |
| :--- | :--- | :--- |
| `ROLE_USER` | 一般ユーザー | 公開画面の閲覧および自己プロフィールの変更のみ可能。 |
| `ROLE_EDITOR` | 編集者 | 一般画面閲覧に加え、記事・マスターデータの登録・更新が可能。 |
| `ROLE_ADMIN` | システム管理者 | 全機能へのアクセス、ユーザー管理、セキュリティ監査権限を持つ。 |

## 3. ドキュメント・アーキテクチャ用語

| 用語 | 英語表記 / 略称 | 定義・説明 |
| :--- | :--- | :--- |
| **OKF** | Open Knowledge Format | Google Cloud が策定した、Markdown + YAML frontmatter で知識を構造化するオープン仕様。 |
| **ADR** | Architecture Decision Record | 設計上の重要な決定理由、代替案との比較、結果を短く記録した文書。 |
| **LLM Wiki** | Large Language Model Wiki | AI エージェントが自律的に編集・保守・検索する、Git 管理された構造化知識ベース。 |

[^dev-guidelines-v1]: raw/99_others/dev_guidelines.md (システム開発ガイドライン 2026)
