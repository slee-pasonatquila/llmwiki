---
name: llm-wiki-query
description: "LLM Wiki 内の編集済み知識層を Progressive Disclosure および Typed Graph Traversal（implements, depends_on 等）で横断探索し、Trust Tier（検証状態）と Provenance（sources/脚注）を付与して開発者の質問に高精度で回答するスキル。"
---

# LLM Wiki Query Skill (OKF v0.2 & LLM Wiki v2 準拠)

このスキルは、開発プロジェクトにおいて「顧客要望」「要件定義」「概要設計」「詳細設計」「意思決定（ADR）」の間にあるセマンティックな関係性を辿りながら、質問に対して正確な回答を合成・提示します。

---

## 探索の原則 (Progressive Disclosure & Graph Traversal)

AI エージェントは全ファイルを無差別に読み込むのではなく、以下の階層的かつ関係駆動の探索を行います。

1. **マスターインデックス (`wiki/index.md`) の参照**:
   - 関連するカテゴリ（要件か設計かなど）を特定。
2. **サブインデックス (`wiki/<category>/index.md`) の参照**:
   - 該当フォルダ内の関連 Concept をピックアップ。
3. **個別 Concept ドキュメントの精読**:
   - YAML Frontmatter（`type`, `status`, `verified`, `sources`, `relations`）と本文、脚注を確認。
4. **Graph Traversal（関係性の追跡）**:
   - `relations`（`implements`, `depends_on`, `supersedes` 等）や Markdown リンクを辿り、影響範囲・依存関係を網羅。
5. **一次資料 (`raw/`) の裏付け（必要時）**:
   - `sources` に記載された原本を参照し、最新性や細部を確認。

---

## 回答フォーマットの規律

ユーザーへの回答には必ず以下の要素を含めます：

1. **直接的な回答 (Clear Answer)**:
   - 要件や設計の結論を簡潔かつ明確に説明。
2. **仕様の根拠とトレース (Traceability & Graph Traversal)**:
   - 「顧客要望 [CR-01](../01_customer_requests/cr_user_authentication.md) に基づき、要件定義 [REQ-USER-01](../02_requirements/req_user_management.md) で定義され、詳細設計 [API Spec](../04_detailed_designs/api_auth_login.md) および [DB Schema](../04_detailed_designs/table_users.md) で実装されています」のように追跡可能なリンクを提示。
3. **信頼性 & 検証状態 (Trust Tier)**:
   - レビュー済み（`verified: { by: human:... }`）か、機械生成ドラフト（`status: draft`）かを明示。
4. **Provenance (一次情報)**:
   - 元となった一次資料（`sources` に定義されたファイルや議事録）を明記。
