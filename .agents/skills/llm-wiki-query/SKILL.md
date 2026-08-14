---
name: llm-wiki-query
description: "LLM Wiki 内の編集済み知識層をハイブリッド検索 (BM25 + Semantic + Graph Proximity) および Typed Graph Traversal（implements, depends_on 等）で横断探索し、確信度スコア（減衰考慮）、メモリ階層、Provenance（sources/脚注）を付与して開発者の質問に高精度で回答するスキル。"
---

# LLM Wiki Query Skill (OKF v0.2 & LLM Wiki v2 準拠)

このスキルは、開発プロジェクトにおいて「顧客要望」「要件定義」「概要設計」「詳細設計」「意思決定（ADR）」の間にあるセマンティックな関係性を辿りながら、質問に対して正確な回答を合成・提示します。

---

## 探索パイプライン (Hybrid Search & Graph Traversal)

AI エージェントは以下の手順で高精度に知識を探索します：

1. **ハイブリッド検索の実行 (`scripts/hybrid_search.py`)**:
   - `python3 scripts/hybrid_search.py "<質問キーワード>" --top 5 --json` を実行し、BM25（キーワード一致）、セマンティック（概念類似度）、グラフ近傍スコアを RRF 統合した上位 Concept 群を取得。
2. **マスター / サブインデックス (`index.md`) の参照**:
   - 検索結果のコンテキストを補足するため、関連ディレクトリの `index.md` を確認。
3. **個別 Concept ドキュメントの精読**:
   - Frontmatter（`type`, `memory_tier`, `confidence`, `sources`, `relations`）と本文、脚注を確認。
4. **Graph Traversal（関係性の追跡）**:
   - `relations`（`implements`, `depends_on`, `uses`, `contradicts`, `supersedes` 等）を辿り、影響範囲・依存関係を網羅。
5. **一次資料 (`raw/`) の裏付け（必要時）**:
   - `sources` に記載された原本を参照し、最新性や細部を確認。

---

## 回答フォーマットの規律

ユーザーへの回答には必ず以下の要素を含めます：

1. **直接的な回答 (Clear Answer)**:
   - 要件や設計の結論を簡潔かつ明確に説明。
2. **信頼性 & メモリ階層 (Confidence & Memory Tier)**:
   - 確信度スコア（減衰後の現在スコア、例: `Confidence: 0.88`）
   - メモリ階層（`[Semantic Memory]` や `[Episodic Memory]`）
   - 検証状態（`verified: { by: human:... }` による監査済みかドラフトか）
3. **仕様の根拠とトレース (Traceability & Graph Traversal)**:
   - 「顧客要望 [CR-01](../01_customer_requests/cr_user_authentication.md) に基づき、要件定義 [REQ-USER-01](../02_requirements/req_user_management.md) で定義され、詳細設計 [API Spec](../04_detailed_designs/api_auth_login.md) および [DB Schema](../04_detailed_designs/table_users.md) で実装されています」のように追跡可能なリンクを提示。
4. **Provenance (一次情報)**:
   - 元となった一次資料（`sources` に定義されたファイルや議事録）を明記。
