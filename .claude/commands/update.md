# Update Command (`/update <target_concept_or_topic>`)

要件変更や設計見直しが発生した際に、既存の Wiki ドキュメントを更新し、忘却曲線の再強化（Reinforce）、OKF v0.2 の世代交代（`supersedes` / `superseded_by`）、矛盾解決、非破壊的更新（取り消し線保持）、ADR の新規起票を行います。

## 実行手順

1. **更新対象の特定と依存関係調査**:
   - `python3 scripts/hybrid_search.py "$1"` またはグラフ関係性を確認し、影響を受ける Concept ファイル群を特定。

2. **非破壊的更新の適用**:
   - 仕様変更時は過去の記述を削除せず、取り消し線（`~~旧仕様~~`）で残すか、`supersedes` / `superseded_by` を用いて安全に新ドキュメントへ世代交代。
   - Frontmatter の `last_reinforced_at` を現在時刻に更新し、`python3 scripts/memory_decay.py --reinforce <path>` を実行。

3. **ADR 起票（重大な設計決定の場合）**:
   - 設計方針の変更やトレードオフ決定がある場合、`wiki/05_decisions/adr_YYYYMMDD_<title>.md` を作成。

4. **チェンジログ記録と検証**:
   - `wiki/.changelogs/YYYYMMDD_<author>_<topic>.json` に変更内容を記録。
   - `python3 scripts/lint_okf.py wiki/` を実行して整合性を確認。
