# 詳細設計 (Detailed Designs)

データベーステーブル定義 (DDL/スキーマ)、API エンドポイント仕様、詳細ロジック、UI 仕様に関する構造化ナレッジです。

## コンセプト一覧

| ドキュメント | メモリ階層 | ステータス | 概要 |
| :--- | :--- | :--- | :--- |
| [OpenAPI 認証定義書 (YAML)](api_auth_login.md) | `semantic` | active | * **URL**: `/api/v1/auth/login`[^api-spec-auth-v1]... |
| [データベース定義書 (SQL)](table_users.md) | `semantic` | active | 本テーブルは、システムの登録ユーザー基本情報、認証用ハッシュ、アカウントロック状態を保持する[^db-schema-v1-2]。... |

---
* [戻る: マスターインデックス](../index.md)
