## 概要 (Overview)
<!-- 変更の目的、追加/修正した仕様の要約を記述してください -->

## 変更種別 (Type of Change)
- [ ] 📄 新規仕様・資料取り込み (`wiki/01_customer_requests`, `02_requirements` 等)
- [ ] 📐 アーキテクチャ・設計更新 (`wiki/03_basic_designs`, `04_detailed_designs`)
- [ ] 🏛️ ADR (アーキテクチャ決定記録) の起票 (`wiki/05_decisions`)
- [ ] ⚠️ 既存仕様の非推奨化 / 世代交代 (`supersedes` / `superseded_by`)
- [ ] 🔧 スクリプト・ルール・CI の修正

## OKF v0.2 チェックリスト (OKF & Multi-User Checklist)
- [ ] **Frontmatter 完備**: `type`, `memory_tier`, `confidence`, `sources`, `relations` を定義している。
- [ ] **解像度 100% 保持**: パラメータ型、エラーコード、NULL可否等の一次情報を省略要約していない。
- [ ] **来歴 & 脚注**: 本文の仕様記述に `sources` と対応する脚注 `[^id]` を付与している。
- [ ] **非破壊的更新**: 仕様変更時、過去記述を取り消し線（`~~`）で残すか、`supersedes` を用いている。
- [ ] **コンフリクトフリー**: `wiki/log.md` や `index.md` を直接手動編集せず、`wiki/.changelogs/` に断片ログを追加した（またはコミットメッセージに明記）。
- [ ] **CI Lint PASS**: `python3 scripts/lint_okf.py wiki/` がローカルで正常終了している。

## 関連 Issue / ADR
- Resolves #
- Related ADR: `wiki/05_decisions/adr_XXX.md`
