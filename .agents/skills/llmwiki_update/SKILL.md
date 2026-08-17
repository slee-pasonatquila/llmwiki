---
name: llmwiki_update
description: "要件変更や設計見直しが発生した際に、既存の Wiki ドキュメントを更新し、忘却曲線の再強化（Reinforce）、OKF v0.2 の世代交代（supersedes / superseded_by）、矛盾解決、変更履歴（log.md）の Actor 記録、過去記述の取り消し線（~~）保持、ADR の新規起票、ナレッジグラフ再生成を行うスキル。"
---

# LLM Wiki Update Skill (`llmwiki_update`) (OKF v0.2 & LLM Wiki v2 準拠)

このスキルは、プロジェクト進行中に発生する「仕様変更」「追加要望」「設計見直し」を LLM Wiki に反映し、知識の鮮度（忘却曲線の再強化）、世代交代、矛盾解決、変更履歴の透明性を維持します。

---

## 変更運用の規律 (Update Principles)

1. **忘却曲線の再強化 (Memory Reinforce)**:
   - ドキュメントを参照・更新した際は `last_reinforced_at` を更新し、`access_count` を加算して確信度スコアをリフレッシュします（または `python3 scripts/memory_decay.py --reinforce <file>` を実行）。
2. **矛盾解決 (Contradiction Resolution) と世代交代 (Supersession)**:
   - 変更前の記述を単に消し去るのではなく、変更理由が重要な箇所には取り消し線（`~~旧仕様~~`）を残し、直後に新仕様と変更日を記載します。
   - 抜本的刷新時は、旧ドキュメントの Frontmatter を `status: deprecated` および `superseded_by: <new_concept_id>` に更新し、新ドキュメントに `supersedes: [<old_concept_id>]` を設定します。
3. **アーキテクチャ・重要設計の決定記録 (ADR の起票・結晶化)**:
   - データベース変更や認証方式の変更など、大きなアーキテクチャ上の決定は `wiki/05_decisions/` 配下に新規 ADR（例: `adr_002_oauth2_sso.md`）として結晶化（Crystallize）して起票します。
4. **関連ドキュメントの連鎖更新 (Graph Traversal)**:
   - 要件が変わった場合、紐づく「詳細設計」「API 定義」「DB スキーマ」の関連記述および `relations` も漏れなく更新します。
5. **ナレッジグラフ & `log.md` の自動更新**:
   - `python3 scripts/build_graph.py wiki/` でグラフを再構築し、`wiki/log.md` の先頭に Actor（`agent:...` または `human:...`）とともに変更内容を追記します。

---

## 更新作業の流れ

```text
[仕様変更・設計見直しの発生]
       │
       ▼
1. 影響箇所の特定 (python3 scripts/hybrid_search.py または relations / graph.mermaid の探索)
       │
       ▼
2. Concept ドキュメントの編集 
   - 忘却曲線の再強化 (last_reinforced_at, access_count, confidence)
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
5. python3 scripts/build_graph.py wiki/ によるナレッジグラフ再生成
       │
       ▼
6. python3 scripts/lint_okf.py wiki/ による整合性確認
```
