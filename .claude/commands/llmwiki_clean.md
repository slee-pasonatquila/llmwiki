# Clean Command (`/llmwiki_clean <file_path>`)

Office (Excel, Word, PowerPoint) や PDF から変換された粗い Markdown に対し、不要な空欄・空行・大量の空セル（`| | | |`）を削除し、機密情報をマスクした上で、表構造や見出しを美しく再構成します。

## 実行手順

1. **Table Cleaner の実行**:
   ```bash
   python3 scripts/table_cleaner.py "$1"
   ```

2. **手動・対話的な微調整（必要な場合）**:
   - 複雑なネスト表やヘッダ結合のある表を論理的な表構造に整形。
   - 解像度（データ型、NULL可否、デフォルト値等）が欠落していないことを確認。
   - 個人情報（氏名、電話番号、メール等）や認証情報（パスワード、APIキー）が確実にマスクされていることを確認。
