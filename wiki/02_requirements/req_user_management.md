---
type: Requirement
title: ユーザー管理・認証機能要件 (REQ-USER-01)
description: ユーザー認証、トークン管理、ロールベースアクセス制御 (RBAC) の機能要件およびセキュリティ要件
tags: [requirement, auth, rbac, security, user]
timestamp: 2026-08-14T15:30:00Z
resource: raw/02_requirements/requirement_spec_v1.0.md
status: Approved
---

# ユーザー管理・認証機能要件 (REQ-USER-01)

## 1. 概要
本機能は、顧客要望 [CR-01](../01_customer_requests/cr_user_authentication.md) に基づき、エンドユーザーおよび管理者のアカウント登録・認証・アクセス認可を安全に提供する。

## 2. 機能要件一覧

| 要件 ID | 項目 | 内容 | 優先度 |
| :--- | :--- | :--- | :---: |
| **REQ-AUTH-01** | メール/パスワードログイン | メールアドレスと暗号化パスワード（Argon2id）でログインする。 | 高 |
| **REQ-AUTH-02** | JWT トークン発行 | 認証成功時にアクセストークン（有効期限 15 分）およびリフレッシュトークン（有効期限 7 日）を発行する。 | 高 |
| **REQ-AUTH-03** | アカウントロック | パスワード誤入力 5 回連続で 15 分間アカウントを一時凍結する。 | 高 |
| **REQ-AUTH-04** | RBAC 権限制御 | 下表のロール定義に従い、各 API エンドポイントおよび画面の表示制御を行う。 | 高 |

### ロール定義 (RBAC Matrix)

| ロール | 一般画面閲覧 | 記事・データ編集 | 管理画面アクセス | ユーザー管理 |
| :--- | :---: | :---: | :---: | :---: |
| `ROLE_USER` | ◯ | ✕ | ✕ | ✕ |
| `ROLE_EDITOR` | ◯ | ◯ | ✕ | ✕ |
| `ROLE_ADMIN` | ◯ | ◯ | ◯ | ◯ |

## 3. 非機能要件
* **認証応答時間**: 95%のログインリクエストを 200ms 以内に処理すること。
* **暗号化**: 通信は TLS 1.3 必須、パスワードハッシュは Argon2id を採用。

# 関連設計
* 概要設計: [認証基盤アーキテクチャ](../03_basic_designs/arch_auth_system.md)
* 詳細設計: [Users テーブル定義](../04_detailed_designs/table_users.md)
* 詳細設計: [ログイン API 仕様](../04_detailed_designs/api_auth_login.md)
* 意思決定: [ADR-001: JWT によるステートレス認証の採用](../05_decisions/adr_001_jwt_auth.md)

# Citations
[1] [システム要件定義書 第1版](raw/02_requirements/requirement_spec_v1.0.md)
