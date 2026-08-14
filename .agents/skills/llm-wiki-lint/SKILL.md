---
name: llm-wiki-lint
description: "Google OKF (v0.2) 仕様への適合性、ゴーストリンク、未インデックスファイル、sources/脚注（Provenance）の欠落、supersedes 参照整合性を機械的に検査・自動修復するスキル。"
---

# LLM Wiki Lint & Repair Skill (OKF v0.2 & LLM Wiki v2 準拠)

このスキルは、Wiki が大規模化・継続更新される過程で発生する「知識の腐敗（リンク切れ、フロントマター破損、目次への未反映、脚注不一致）」を機械的に検知し、自動修復します。

---

## 検査項目 (OKF v0.2 Lint Checklist)

1. **OKF v0.2 適合性 (Conformance)**:
   - 全ての非予約 `.md` ファイルに YAML Frontmatter が存在すること。
   - `type` フィールドが必須で定義されていること。
   - 推奨フィールド（`title`, `description`, `status`, `generated`）が存在すること。
   - `status` が規定値（`draft`, `active`, `deprecated`, `tombstone`）のいずれかであること。
2. **Provenance & 脚注整合性 (Footnotes & Sources Integrity)**:
   - `sources` がリスト形式であり、各要素に `resource` が存在すること。
   - 本文中の脚注 `[^id]` が `sources` 内の `id` に正しくマッピングされていること。
3. **世代交代整合性 (Supersession Integrity)**:
   - `supersedes` または `superseded_by` に指定された Concept ID が実在すること。
4. **リンク整合性 (Link Integrity)**:
   - 相対リンク `[タイトル](path.md)` の宛先ファイルが存在すること。
   - Obsidian 記法 `[[concept_name]]` の宛先が存在すること。
5. **インデックス網羅性 (Index Coverage)**:
   - 各フォルダ内の Concept ファイルおよびサブディレクトリが、同フォルダの `index.md` にすべて掲載されていること。

---

## 実行手順

### 1. スクリプトによる自動 Lint 実行
```bash
python3 scripts/lint_okf.py wiki/
```

### 2. 修復（Self-Healing / Repair）の適用ルール
- **ゴーストリンクの修復**:
  - もしリンク先がまだ作成されていない重要概念である場合、OKF v0.2 テンプレート（スタブ）を生成するか、リンク表記を修正します。
- **インデックスへの追加**:
  - `index.md` に記載が漏れている Concept があれば、タイトルと 1 行要約を読み取って `index.md` に追記します。
- **YAML Frontmatter の補完**:
  - `type` や `sources`, `generated` が欠落しているドキュメントに対し、本文を解析して適切な Frontmatter を付与します。
- **注意点**:
  - **Repair 処理ではドメイン知識（仕様そのもの）を勝手に改変してはいけません。** フォーマットの正常化とリンク補正のみを行います。
