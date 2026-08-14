---
type: Customer Request
title: ユーザー認証・権限管理の顧客要望
description: セキュアなシングルサインオン対応と、一般ユーザー・管理者間の厳格なアクセス制御に関する顧客ヒアリング要望
tags: [customer-request, auth, rbac, security]
status: active

generated:
  by: agent:antigravity/gemini-3.7-flash
  at: 2026-08-14T15:30:00Z

verified:
  by: human:slee
  at: 2026-08-14T16:00:00Z
  method: stakeholder_interview

sources:
  - id: hearing-202608
    resource: raw/01_customer_requests/hearing_sheet_202608.md
    title: 顧客ヒアリング議事録 2026年8月
    author: human:client_rep
    last_modified: 2026-08-14

relations:
  implemented_by: [02_requirements/req_user_management]
---

# ユーザー認証・権限管理の顧客要望 (CR-01)

## 1. 背景と課題
現在運用中のレガシーシステムではパスワード認証のみが利用されており、セキュリティリスクおよびパスワード失念による問い合わせ負荷が高い[^hearing-202608]。また、管理者権限が全担当者に付与されており、内部統制上の懸念が存在する[^hearing-202608]。

## 2. 顧客からの具体的要望

### 2.1 認証機能
* メールアドレス＋パスワードによる標準ログインに加え、将来的な OAuth2.0 / SSO 連携を容易にする構成にしたい[^hearing-202608]。
* パスワードの誤入力によるロック機能（5 回失敗で 15 分間アカウントロック）を必須としたい[^hearing-202608]。

### 2.2 権限管理 (RBAC)
* システム利用者を「一般ユーザー」「編集者」「システム管理者」の 3 つのロールに明確に分離したい[^hearing-202608]。
* 個人情報および機密設定画面へのアクセスは「システム管理者」のみに限定したい[^hearing-202608]。

## 3. 実現するビジネスゴール
* アカウント乗っ取りリスクの 90% 削減
* 権限誤付与によるデータ漏洩事故ゼロの達成

# 関連要件
* 要件定義: [ユーザー管理要件 (REQ-USER-01)](../02_requirements/req_user_management.md)
* アーキテクチャ設計: [認証基盤アーキテクチャ](../03_basic_designs/arch_auth_system.md)

[^hearing-202608]: raw/01_customer_requests/hearing_sheet_202608.md (顧客ヒアリング議事録 2026年8月)
