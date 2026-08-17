# Query Command (`/llmwiki_query <question>`)

LLM Wiki 内の編纂済みナレッジ層を横断探索（BM25 + Semantic + Graph Proximity + Typed Graph Traversal）し、確信度スコア（忘却曲線の減衰考慮）、メモリ階層、Provenance（一次資料根拠・脚注）を付与して回答します。

## 実行手順

1. **ハイブリッド検索の実行**:
   - `python3 scripts/hybrid_search.py "$1"` を実行して関連ドキュメントを特定。
   - 関連する上位・下位概念（`implements`, `depends_on`, `uses`, `contradicts`）をグラフ探索。

2. **回答の合成**:
   - 一次資料の解像度（テーブル定義、API パラメータ、エラーコード等）を崩さずに回答を構成。
   - 出典・根拠（Sources）と確信度スコア（Confidence Score）を明記。
   - 矛盾（`contradicts`）や未解決の ADR がある場合は注意喚起を明記。

3. **アクセス記録の更新**:
   - `python3 scripts/metrics_db.py record_access <accessed_path>` を呼び出してアクセス頻度を記録。
