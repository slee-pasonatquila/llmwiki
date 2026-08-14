---
type: API Endpoint
title: ログイン API 仕様 (POST /api/v1/auth/login)
description: ユーザー認証を実行し、アクセストークンとリフレッシュトークンを発行するエンドポイント仕様
tags: [api, auth, endpoint, rest, jwt]
status: active

generated:
  by: agent:antigravity/gemini-3.7-flash
  at: 2026-08-14T15:30:00Z

verified:
  by: human:slee
  at: 2026-08-14T16:00:00Z
  method: manual_audit

sources:
  - id: api-spec-auth-v1
    resource: raw/04_detailed_designs/api_spec_auth.yaml
    title: OpenAPI 認証定義書 (YAML)
    author: human:api_designer
    last_modified: 2026-08-14

relations:
  implements: [02_requirements/req_user_management]
  depends_on: [03_basic_designs/arch_auth_system, 04_detailed_designs/table_users]
---

# ログイン API 仕様 (`POST /api/v1/auth/login`)

## 1. エンドポイント概要
* **URL**: `/api/v1/auth/login`[^api-spec-auth-v1]
* **Method**: `POST`[^api-spec-auth-v1]
* **認証**: 不要 (Public)[^api-spec-auth-v1]
* **概要**: メールアドレスとパスワードによる認証を行い、JWT アクセストークンを返却する。

## 2. リクエスト仕様

### ヘッダー (Request Headers)
| ヘッダー名 | 必須 | 設定値 | 説明 |
| :--- | :---: | :--- | :--- |
| `Content-Type` | ◯ | `application/json` | リクエスト形式 |

### リクエストボディ (Request Body)
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

| フィールド名 | 型 | 必須 | バリデーション | 説明 |
| :--- | :--- | :---: | :--- | :--- |
| `email` | String | ◯ | メールアドレス形式、最大 255 文字 | ログイン用メールアドレス |
| `password` | String | ◯ | 8〜64文字、英数字記号混在 | ユーザーの生パスワード |

## 3. レスポンス仕様

### 3.1 成功時 (200 OK)
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJSUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 900,
    "user": {
      "id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
      "email": "user@example.com",
      "display_name": "Yamada Taro",
      "role": "ROLE_USER"
    }
  }
}
```
* **Set-Cookie**: `refresh_token=xxx; Path=/api/v1/auth; HttpOnly; Secure; SameSite=Strict; Max-Age=604800`

### 3.2 エラーレスポンス
| HTTP コード | エラーコード | 説明 |
| :---: | :--- | :--- |
| `400` | `INVALID_INPUT` | パラメータのバリデーションエラー |
| `401` | `AUTH_FAILED` | メールアドレスまたはパスワードが不一致 |
| `423` | `ACCOUNT_LOCKED` | 5 回失敗によるアカウント一時ロック中 |

# 関連ドキュメント
* 要件定義: [ユーザー管理要件](../02_requirements/req_user_management.md)
* 概要設計: [認証基盤アーキテクチャ](../03_basic_designs/arch_auth_system.md)
* DB 設計: [Users テーブル定義](table_users.md)

[^api-spec-auth-v1]: raw/04_detailed_designs/api_spec_auth.yaml (OpenAPI 認証定義書 YAML)
