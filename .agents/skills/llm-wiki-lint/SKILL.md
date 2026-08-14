---
name: llm-wiki-lint
description: "Google OKF (v0.2) および LLM Wiki v2 仕様への適合性、忘却曲線（stale ドキュメント検知）、ゴーストリンク、未インデックスファイル、ナレッジグラフの矛盾（contradicts）や孤立ノード、sources/脚注（Provenance）の欠落、supersedes 参照整合性を機械的に検査・自動修復するスキル。"
---

# LLM Wiki Lint Skill (OKF v0.2 & LLM Wiki v2 準拠)

このスキルは、Wiki 全体の健全性、OKF v0.2 適合性、LLM Wiki v2 のナレッジグラフ整合性、および忘却曲線（減衰した stale 知識）を機械的に検査し、不整合を修復します。

---

## 検査・修復パイプライン

### 1. OKF v0.2 & v2 バリデータの実行
```bash
python3 scripts/lint_okf.py wiki/
```
- **検査項目**:
  - 必須 `type`、推奨 `title`, `description`, `status`
  - メモリ階層 `memory_tier`、減衰率 `decay_rate`
  - 確信度スコア `confidence` (0.0〜1.0)
  - `sources` 定義と本文中脚注（`[^source_id]`）の 1 対 1 対応
  - `relations`（`implements`, `depends_on`, `uses`, `contradicts` 等）の参照先実在チェック
  - 矛盾（`contradicts`）フラグの警告
  - 世代交代（`supersedes`, `superseded_by`）の整合性
  - 内部リンク・Wiki リンクのリンク切れ（ゴーストリンク）
  - `index.md` のファイル・サブディレクトリ網羅性
  - `log.md` の日付フォーマット

### 2. ナレッジグラフ分析 & 矛盾・孤立ノード検査
```bash
python3 scripts/build_graph.py wiki/
```
- 孤立ノード（誰からも参照されず参照もしていない Concept）を検出し、適切な相互リンクや `relations` を追加。
- 矛盾関係（`contradicts`）を可視化し、解決が必要な箇所をレポート。
- `wiki/graph.json` および `wiki/graph.mermaid` を最新化。

### 3. 忘却曲線減衰チェック & リフレッシュ推奨
```bash
python3 scripts/memory_decay.py wiki/
```
- 確信度スコアが 0.50 未満に減衰した `stale` ドキュメントを検知。
- 必要に応じて最新ソースや人間への確認を促し、再強化（`--reinforce`）または `status: stale` の付与を実行。
