# Rule 03: Memory Lifecycle, Confidence Decay & Conflict Resolution

## 1. 4層メモリ階層 (Memory Tiers)
知識は寿命と抽象度に応じて 4 階層に分類する：

| メモリ階層 (`memory_tier`) | 対象ドキュメント | 推奨 `decay_rate` | 典型的な配置先 |
| :--- | :--- | :--- | :--- |
| **Working Memory** (`working`) | 未処理の作業メモ、一時的な観察、セッションメモ | `volatile` ($\lambda=0.05$, 半減期約14日) | `wiki/99_others/drafts/` |
| **Episodic Memory** (`episodic`) | 顧客ヒアリング記録、ミーティング議事録、セッション要約 | `standard` ($\lambda=0.01$, 半減期約69日) | `wiki/01_customer_requests/`, `wiki/99_others/` |
| **Semantic Memory** (`semantic`) | 要件定義、アーキテクチャ設計、DBスキーマ、API仕様、ADR | `standard` または `permanent` ($\lambda=0.002$, 半減期約346日) | `wiki/02_requirements/` 〜 `wiki/05_decisions/` |
| **Procedural Memory** (`procedural`) | ワークフロー、運用手順書 (Runbook)、SOP、スキル定義 | `permanent` ($\lambda=0.002$, 半減期約346日) | `wiki/99_others/runbooks/` |

## 2. 忘却曲線 (Forgetting Curve) と再強化 (Reinforcement)
- **減衰計算**: $\text{Score}(t) = \text{BaseScore} \times e^{-\lambda \times \Delta t} + \text{VerificationBoost}$
- **再強化ルール**:
  - ドキュメントが参照・検証・更新された場合、エージェントは `last_reinforced_at` を現在日時に更新し、`access_count` をインクリメントして減衰タイマーをリセットする。
  - スコアが 0.50 未満に減衰したドキュメントは `status: stale`（要再確認）として検知され、優先的に再監査・更新する。

## 3. 矛盾解決 (Contradiction Resolution)
新旧のドキュメントや異資料間で矛盾が生じた場合：
1. 発見した矛盾を Frontmatter の `relations.contradicts` に記録する。
2. 以下の基準で正当性を判定する：
   - **ソース権威性**: 一次設計書原本 (`high`) > 議事録 (`medium`) > 推論・ドラフト (`low`)
   - **更新日時**: より新しい決定を優先
   - **裏付け数 (`source_count`)**: より多くの資料で言及されている方を優先
3. 判定結果に基づき：
   - 正しい側に更新を反映し、`relations.contradicts` を解消。
   - 変更理由がアーキテクチャ・重要仕様に関わる場合は `wiki/05_decisions/` に ADR を起票。
   - 旧ドキュメントは `status: deprecated` とし、`superseded_by` を設定する。
