---
name: llm-wiki-query
description: "LLM Wiki 内の編集済み知識層（顧客要望、要件定義、概要設計、詳細設計、ADR）を横断検索・統合し、正確な根拠（Citations）とファイルリンクを付与して開発者の質問に回答するスキル。"
---

# LLM Wiki Query Skill

このスキルは、開発プロジェクトにおいて「顧客要望」「要件定義」「概要設計」「詳細設計」「意思決定（ADR）」の間にある整合性を辿りながら、質問に対して正確な回答を合成・提示します。

---

## 探索の原則 (Progressive Disclosure)

AI エージェントは大量の全ファイルを無差別に読み込むのではなく、以下の順序で効率的に探索します。

1. **マスターインデックス (`wiki/index.md`) の参照**:
   - 関連するカテゴリ（要件か設計かなど）を特定。
2. **サブインデックス (`wiki/<category>/index.md`) の参照**:
   - 該当フォルダ内の関連 Concept をピックアップ。
3. **個別 Concept ドキュメントの精読**:
   - YAML Frontmatter と本文、相互リンク（Cross-links）を辿って関連仕様を把握。
4. **一次資料 (`raw/`) の裏付け（必要時）**:
   - `# Citations` に記載された原本を参照し、最新性や細部を確認。

---

## 回答フォーマットの規律

ユーザーへの回答には必ず以下の要素を含めます：

1. **直接的な回答 (Clear Answer)**:
   - 要件や設計の結論を簡潔に説明。
2. **仕様の根拠とトレース (Traceability)**:
   - 「顧客要望 [CR-01](../01_customer_requests/cr_auth.md) に基づき、要件定義 [REQ-03](../02_requirements/auth_requirements.md) で定義され、詳細設計 [API Spec](../04_detailed_designs/api_auth_login.md) で実装されています」のように追跡可能なリンクを提示。
3. **Citations (一次資料)**:
   - 元となった資料（`raw/` 配下のファイル名など）を明記。
