---
name: llm-wiki-lint
description: "Google OKF (v0.1) 仕様への適合性、ゴーストリンク（未作成ドキュメントへのリンク）、未インデックスファイル、Citations（根拠）の欠落を機械的に検査・自動修復するスキル。"
---

# LLM Wiki Lint & Repair Skill

このスキルは、Wiki が巨大化・継続更新される過程で発生する「知識の腐敗（リンク切れ、フロントマター破損、目次への未反映）」を機械的に検知し、修復します。

---

## 検査項目 (Lint Checklist)

1. **OKF 適合性 (Conformance)**:
   - 全ての非予約 `.md` ファイルに YAML Frontmatter が存在すること。
   - `type` フィールドが空でなく定義されていること。
   - 推奨フィールド（`title`, `description`）が存在すること。
2. **リンク整合性 (Link Integrity)**:
   - 相対リンク `[タイトル](path.md)` の宛先ファイルが存在すること。
   - Obsidian 記法 `[[concept_name]]` の宛先が存在すること（存在しない場合はゴーストリンクとして検出）。
3. **インデックス網羅性 (Index Coverage)**:
   - 各フォルダ内の Concept ドキュメントが、同フォルダの `index.md` にすべて掲載されていること。
4. **Citations 存在性 (Grounding)**:
   - 文書末尾に `# Citations` が存在し、一次資料や外部 URL が明記されていること。

---

## 実行手順

### 1. スクリプトによる自動 Lint 実行
```bash
python scripts/lint_okf.py wiki/
```

### 2. 修復（Repair）の適用ルール
- **ゴーストリンクの修復**:
  - もしリンク先がまだ作成されていない重要概念である場合、空のテンプレートドキュメント（スタブ）を生成するか、リンク表記をプレーンテキストに修正します。
- **インデックスへの追加**:
  - `index.md` に記載が漏れている Concept ドキュメントがあれば、タイトルと一行要約を読み取って `index.md` に追記します。
- **YAML Frontmatter の補完**:
  - `type` や `title` が欠落しているドキュメントに対し、本文を解析して適切な Frontmatter を付与します。
- **注意点**:
  - **Repair 処理ではドメイン知識（仕様そのもの）を勝手に改変してはいけません。** フォーマットの正常化とリンク補正のみを行います。
