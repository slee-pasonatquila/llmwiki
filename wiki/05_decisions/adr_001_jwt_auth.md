---
type: Decision (ADR)
title: "ADR-001: セッション管理における JWT ステートレス認証の採用"
description: マイクロサービス化および水平スケーリングを見据え、ステートフルセッションからJWTステートレス認証への移行を決定
tags: [adr, decision, architecture, auth, jwt]
status: active

# Memory Lifecycle
memory_tier: semantic
decay_rate: permanent
last_reinforced_at: 2026-08-14T16:00:00Z
access_count: 7

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
  - id: tech-meeting-202608
    resource: raw/99_others/meeting_notes_202608.md
    title: 技術選定検討ミーティング議事録 2026年8月
    author: human:tech_lead
    last_modified: 2026-08-14

relations:
  implements: [02_requirements/req_user_management]
  implemented_by: [03_basic_designs/arch_auth_system]
---

# ADR-001: セッション管理における JWT ステートレス認証の採用

## 1. コンテキスト (Context)
要件定義 [REQ-USER-01](../02_requirements/req_user_management.md) において、ピーク時の急激なアクセス増に耐えうる高スケーラビリティな認証基盤が求められた[^tech-meeting-202608]。
従来型の RDBMS セッション管理では、API リクエストごとに DB 問い合わせが発生し、ボトルネックとなる懸念があった[^tech-meeting-202608]。

## 2. 検討した選択肢 (Options Considered)

| 選択肢 | メリット | デメリット | 判定 |
| :--- | :--- | :--- | :---: |
| **A. RDBMS セッション** | 即時失効が容易、実装がシンプル | 毎リクエストで DB 負荷、スケールしにくい | ✕ 却下 |
| **B. Redis セッション** | 高速、即時無効化が可能 | Redis 障害時の単一障害点 (SPOF)、運用コスト増 | △ 保留 |
| **C. JWT ステートレス認証 + Refresh Token** | API 側で DB 問い合わせ不要、水平スケール容易 | 即時失効の制御に工夫が必要 | **◯ 採用** |

## 3. 決定内容 (Decision)
**選択肢 C (JWT + Refresh Token 方式)** を採用する[^tech-meeting-202608]。
* Access Token は 15 分の短い有効期限とし、API ゲートウェイが公開鍵で自律検証する。
* 即時失効・ログアウト制御が必要な Refresh Token のみ Redis で最小限管理する。

## 4. 影響と結果 (Consequences)
* API サーバーのスケールアウトが容易となり、DB 負荷を約 70% 削減できる。
* 一方で、クライアント側でのトークン安全保持（HttpOnly Cookie）の実装規約が必要となる。

# 関連設計
* 概要設計: [認証基盤アーキテクチャ](../03_basic_designs/arch_auth_system.md)
* 詳細設計: [ログイン API 仕様](../04_detailed_designs/api_auth_login.md)

[^tech-meeting-202608]: raw/99_others/meeting_notes_202608.md (技術選定検討ミーティング議事録 2026年8月)
