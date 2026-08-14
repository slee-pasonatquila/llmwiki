# Rule 04: Wiki Compilation & Multi-User Operations

## 1. 非破壊的編集の徹底 (No Destructive Modification)
仕様変更や廃止が発生した場合、過去の記述を単純削除してはならない。
- **軽微な変更**: 過去の記述を取り消し線（`~~旧仕様~~`）で残し、直後に新仕様を併記する。
  ```markdown
  - パスワード失敗許容回数: ~~3回~~ **5回に改定 (2026-08-14 要件見直しによる)**[^req-auth-v2]
  ```
- **大幅な設計変更 / スキーマ変更**:
  - 新ドキュメントを作成し、`supersedes: [旧ファイルパス]` を指定。
  - 旧ドキュメントの Frontmatter を `status: deprecated`, `superseded_by: 新ファイルパス` に更新。

## 2. 複数人協調・コンフリクト完全排除プロトコル (Decentralized Sync)
複数作業者・エージェントの並行作業による Git コンフリクトを防ぐため、以下のルールを厳守する：

1. **集中ファイル（`index.md`, `log.md`, `graph.*`）の手動編集禁止**:
   - `index.md` や `log.md` はスクリプトにより自動生成されるため、直接手動で書き換えてはならない。
2. **断片変更ログ (Changelog Fragment) の作成**:
   - 仕様を追加・更新した際は、`wiki/.changelogs/YYYYMMDD_<author>_<topic>.json` に変更サマリを保存する（または `python3 scripts/build_changelog.py add <author> <action> <details...>` を実行）。
3. **一括同期ツール (`sync_wiki.py`) の活用**:
   - ローカル検証時は `python3 scripts/sync_wiki.py` を実行して一括自動生成する。
   - `main` ブランチマージ時は GitHub Actions CI が自動生成・同期コミットを行う。

## 3. 複数人並行編集時の競合解決ルール (Concurrency & ADR First)
1. **仕様対立時の両論併記 (`relations.contradicts`)**:
   - 別チームや他者との間で仕様が対立している場合、相手のドキュメントを勝手に上書き・削除してはならない。
   - `relations.contradicts: [対象ファイル]` を付与して両論を併記し、`wiki/05_decisions/` に ADR（アーキテクチャ決定記録）を起票して合意形成を図る。
2. **下書きドキュメント (`status: draft`) の扱い**:
   - 執筆中のドキュメントは `status: draft` を付与する。
   - 他者は原則として `draft` 状態のドキュメントを `depends_on` 等の依存先として指定しない（CI で警告が出力される）。

## 4. 品質検査 (Linting) の実行
作業完了後、エージェントは `python3 scripts/lint_okf.py wiki/` を実行し、以下の項目がすべて PASS することを確認する：
- OKF v0.2 Frontmatter の必須フィールド欠落がないか
- 重複 Concept ID / パスが存在しないか
- リンク切れ（ゴーストリンク）が存在しないか
- `status: draft` ドキュメントへの不正な依存がないか
- `contradicts` に ADR が適切に紐づけられているか
- `sources` と本文中の脚註 `[^id]` の整合性が取れているか
