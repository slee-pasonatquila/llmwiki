---
name: llm-wiki-update
description: "要件変更や設計見直しが発生した際に、既存の Wiki ドキュメントを更新し、OKF v0.2 の世代交代（supersedes / superseded_by）、変更履歴（log.md）の Actor 記録、過去記述の取り消し線（~~）保持、ADR の新規起票を行うスキル。"
---

# LLM Wiki Update Skill (OKF v0.2 & LLM Wiki v2 準拠)

このスキルは、プロジェクト進行中に発生する「仕様変更」「追加要望」「設計見直し」を LLM Wiki に反映し、知識の鮮度・世代交代・変更履歴の透明性を維持します。

---

## 変更運用の規律 (Update Principles)

1. **破壊的削除の禁止（過去経緯の保持）**:
   - 変更前の記述を単に消し去るのではなく、変更理由が重要な箇所には取り消し線（`~~旧仕様~~`）を残し、直後に新仕様と変更日を記載します。
2. **世代交代 (Supersession) の管理**:
   - 仕様やドキュメントを抜本的に置き換える場合、旧ドキュメントの Frontmatter を `status: deprecated` および `superseded_by: <new_concept_id>` に更新し、新ドキュメントに `supersedes: [<old_concept_id>]` を設定します。
3. **アーキテクチャ・重要設計の決定記録 (ADR の起票・結晶化)**:
   - データベース変更や認証方式の変更など、大きなアーキテクチャ上の決定は `wiki/05_decisions/` 配下に新規 ADR（例: `adr_002_oauth2_sso.md`）として結晶化（Crystallize）して起票します。
4. **関連ドキュメントの連鎖更新 (Graph Traversal)**:
   - 要件が変わった場合、紐づく「詳細設計」「API 定義」「DB スキーマ」の関連記述および `relations` も漏れなく更新します。
5. **`log.md` の記録（Actor 明記）**:
   - `wiki/log.md` の先頭に、更新を行った Actor（`agent:...` または `human:...`）とともに、変更内容と影響を受けたドキュメントへのリンクを追記します。

---

## 更新作業の流れ

```text
[仕様変更・設計見直しの発生]
       │
       ▼
1. 影響箇所の特定 (wiki/index.md および relations / cross-link の探索)
       │
       ▼
2. Concept ドキュメントの編集 
   - 取り消し線 + 新仕様の追記
   - sources / generated の更新
   - 抜本的置換の場合は supersedes / superseded_by / status の更新
       │
       ▼
3. 必要に応じて ADR の新規作成 (wiki/05_decisions/adr_xxx.md)
       │
       ▼
4. wiki/log.md および index.md の更新 (Actor 表記付き)
       │
       ▼
5. python scripts/lint_okf.py による整合性確認
```
