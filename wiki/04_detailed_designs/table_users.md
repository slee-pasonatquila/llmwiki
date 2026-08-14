---
type: Database Table
title: Users テーブル定義
description: PostgreSQLにおけるユーザーマスタ、認証情報、権限ロール管理テーブルの物理設計
tags: [database, table, schema, postgres, users, auth]
status: active

generated:
  by: agent:antigravity/gemini-3.7-flash
  at: 2026-08-14T15:30:00Z

verified:
  by: human:slee
  at: 2026-08-14T16:00:00Z
  method: manual_audit

sources:
  - id: db-schema-v1-2
    resource: raw/04_detailed_designs/db_schema_v1.2.sql
    title: データベース定義書 (SQL)
    author: human:dba
    last_modified: 2026-08-14

relations:
  implements: [02_requirements/req_user_management]
  depends_on: [03_basic_designs/arch_auth_system]
---

# Users テーブル定義 (`users`)

## 1. テーブル概要
本テーブルは、システムの登録ユーザー基本情報、認証用ハッシュ、アカウントロック状態を保持する[^db-schema-v1-2]。

## 2. カラム物理定義一覧

| カラム名 | 物理名 | 型 | NULL | 初期値 | 説明 |
| :--- | :--- | :--- | :---: | :--- | :--- |
| ユーザー ID | `id` | UUID | NO | `gen_random_uuid()` | 主キー (UUID v4) |
| メールアドレス | `email` | VARCHAR(255) | NO | - | ログイン ID (一意制約) |
| パスワードハッシュ | `password_hash` | VARCHAR(255) | NO | - | Argon2id で暗号化されたハッシュ値 |
| 表示名 | `display_name` | VARCHAR(100) | NO | - | ユーザーの画面表示名 |
| ロール | `role` | VARCHAR(32) | NO | `'ROLE_USER'` | `ROLE_USER` / `ROLE_EDITOR` / `ROLE_ADMIN` |
| 失敗回数 | `failed_attempts` | INT | NO | `0` | 連続パスワード失敗回数 |
| ロック期限 | `locked_until` | TIMESTAMP WITH TIME ZONE | YES | NULL | アカウント一時凍結解除日時 |
| 作成日時 | `created_at` | TIMESTAMP WITH TIME ZONE | NO | `CURRENT_TIMESTAMP` | レコード作成日時 |
| 更新日時 | `updated_at` | TIMESTAMP WITH TIME ZONE | NO | `CURRENT_TIMESTAMP` | レコード最終更新日時 |

## 3. インデックス定義
* `pk_users`: PRIMARY KEY (`id`)[^db-schema-v1-2]
* `uk_users_email`: UNIQUE (`email`)[^db-schema-v1-2]
* `idx_users_locked`: INDEX (`locked_until`) WHERE `locked_until IS NOT NULL`[^db-schema-v1-2]

## 4. DDL スクリプト
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'ROLE_USER',
    failed_attempts INT NOT NULL DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

# 関連ドキュメント
* 要件定義: [ユーザー管理要件](../02_requirements/req_user_management.md)
* 概要設計: [認証基盤アーキテクチャ](../03_basic_designs/arch_auth_system.md)
* API 仕様: [ログイン API 仕様](api_auth_login.md)

[^db-schema-v1-2]: raw/04_detailed_designs/db_schema_v1.2.sql (データベース定義書 SQL)
