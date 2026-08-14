# Rule 04: Wiki Compilation & Update Operations

## 1. 非破壊的編集の徹底 (No Destructive Modification)
仕様変更や廃止が発生した場合、過去の記述を単純削除してはならない。
- **軽微な変更**: 過去の記述を取り消し線（`~~旧仕様~~`）で残し、直後に新仕様を併記する。
  ```markdown
  - パスワード失敗許容回数: ~~3回~~ **5回に改定 (2026-08-14 要件見直しによる)**[^req-auth-v2]
  ```
- **大幅な設計変更 / スキーマ変更**:
  - 新ドキュメントを作成し、`supersedes: [旧ファイルパス]` を指定。
  - 旧ドキュメントの Frontmatter を `status: deprecated`, `superseded_by: 新ファイルパス` に更新。

## 2. 必須の同期更新トリガー (Atomic Update Requirement)
`wiki/` 配下のファイルを新規作成または更新した場合、エージェントは必ず同一作業内で以下の 3 点を実行しなければならない：

1. **ディレクトリインデックス (`index.md`) の更新**:
   - 当該フォルダ（例: `wiki/04_detailed_designs/index.md`）の一覧テーブルに新ドキュメントのリンク、概要、更新日、ステータスを反映。
2. **全体更新ログ (`wiki/log.md`) の追記**:
   - `wiki/log.md` の先頭（または最新日付ブロック）に、実施日時、担当エージェント、対象ファイル、変更サマリを追記。
3. **ナレッジグラフの再構築**:
   - `python3 scripts/build_graph.py wiki/` を実行し、`wiki/graph.json` および `wiki/graph.mermaid` を最新状態に再生成する。

## 3. 品質検査 (Linting) の実行
編集完了後、エージェントは `python3 scripts/lint_okf.py wiki/` を実行し、以下の項目がすべて PASS することを確認する：
- OKF v0.2 Frontmatter の必須フィールド欠落がないか
- リンク切れ（ゴーストリンク）が存在しないか
- 孤立ノードや矛盾（`contradicts`）が放置されていないか
- `sources` と本文中の脚註 `[^id]` の整合性が取れているか
