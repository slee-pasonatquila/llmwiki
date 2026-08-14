"""
hybrid_search.py - LLM Wiki v2 Hybrid Search Engine (Multi-User SQLite Supported)

Combines 3 search paradigms into a unified, high-accuracy ranking:
  1. BM25 Keyword Search (Exact term matching, code identifiers, Japanese n-grams)
  2. Semantic Similarity (Concept, title, description, tags vector similarity)
  3. Knowledge Graph Proximity (Traversal along implements, depends_on, uses edges)
  
Integrated via Reciprocal Rank Fusion (RRF) with memory confidence weighting.
Search queries and hit metrics are recorded in `wiki/.cache/metrics.db`.

Usage:
  python3 scripts/hybrid_search.py "ユーザー認証 パスワードロック"
  python3 scripts/hybrid_search.py "table_users" --top 3
  python3 scripts/hybrid_search.py "ADR SSO" --json
"""

import os
import re
import sys
import json
import math
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any

try:
    import yaml
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False

# Import metrics_db
try:
    from metrics_db import record_access, get_metrics
    HAVE_METRICS_DB = True
except ImportError:
    try:
        from scripts.metrics_db import record_access, get_metrics
        HAVE_METRICS_DB = True
    except ImportError:
        HAVE_METRICS_DB = False


def strip_md_suffix(s: str) -> str:
    s = s.strip()
    return s[:-3] if s.endswith(".md") else s


def tokenize(text: str) -> List[str]:
    """Tokenizes mixed Japanese, English, and code text into words & 2-grams."""
    if not text:
        return []
    text_lower = text.lower()
    words = re.findall(r"[a-z0-9_\-]+", text_lower)
    
    cjk_chars = re.findall(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]", text_lower)
    ngrams = []
    for i in range(len(cjk_chars)):
        ngrams.append(cjk_chars[i])
        if i + 1 < len(cjk_chars):
            ngrams.append(cjk_chars[i] + cjk_chars[i + 1])

    cjk_blocks = re.findall(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]+", text_lower)
    return words + ngrams + cjk_blocks


def extract_frontmatter(content: str) -> Tuple[Optional[dict], str]:
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)
    if not match:
        return None, content
    fm_text, body = match.groups()
    if HAVE_YAML:
        try:
            parsed = yaml.safe_load(fm_text)
            return (parsed if isinstance(parsed, dict) else {}), body
        except Exception:
            return None, body
    else:
        try:
            from lint_okf import parse_yaml_subset
            return parse_yaml_subset(fm_text), body
        except ImportError:
            return {}, body


class BM25Okapi:
    def __init__(self, corpus_tokens: Dict[str, List[str]], k1: float = 1.5, b: float = 0.75):
        self.corpus_tokens = corpus_tokens
        self.k1 = k1
        self.b = b
        self.doc_lengths = {doc_id: len(tokens) for doc_id, tokens in corpus_tokens.items()}
        self.avgdl = sum(self.doc_lengths.values()) / max(1, len(self.doc_lengths))
        self.doc_count = len(corpus_tokens)
        
        self.df: Dict[str, int] = {}
        for tokens in corpus_tokens.values():
            seen = set(tokens)
            for t in seen:
                self.df[t] = self.df.get(t, 0) + 1

        self.idf: Dict[str, float] = {}
        for term, freq in self.df.items():
            self.idf[term] = math.log(1 + (self.doc_count - freq + 0.5) / (freq + 0.5))

    def score(self, query_tokens: List[str]) -> Dict[str, float]:
        scores = {doc_id: 0.0 for doc_id in self.corpus_tokens}
        for q in query_tokens:
            if q not in self.idf:
                continue
            idf_val = self.idf[q]
            for doc_id, tokens in self.corpus_tokens.items():
                freq = tokens.count(q)
                if freq == 0:
                    continue
                dl = self.doc_lengths[doc_id]
                numerator = freq * (self.k1 + 1)
                denominator = freq + self.k1 * (1 - self.b + self.b * (dl / self.avgdl))
                scores[doc_id] += idf_val * (numerator / denominator)
        return scores


class HybridSearchEngine:
    def __init__(self, wiki_root: Path):
        self.wiki_root = wiki_root.resolve()
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.corpus_tokens: Dict[str, List[str]] = {}
        self.graph_adj: Dict[str, Set[str]] = {}
        self._load_corpus()
        self.bm25 = BM25Okapi(self.corpus_tokens)

    def _load_corpus(self):
        for root, _, files in os.walk(self.wiki_root):
            for file in files:
                if file.endswith(".md") and file not in ("index.md", "log.md"):
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(self.wiki_root).as_posix()
                    concept_id = strip_md_suffix(rel_path)

                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()

                    fm, body = extract_frontmatter(content)
                    if not fm:
                        continue

                    # Confidence calculation (prefer SQLite cached score if available)
                    conf_raw = fm.get("confidence", 0.9)
                    if isinstance(conf_raw, dict):
                        conf_val = float(conf_raw.get("current_score", conf_raw.get("base_score", 0.9)))
                    else:
                        try:
                            conf_val = float(conf_raw)
                        except (ValueError, TypeError):
                            conf_val = 0.9

                    if HAVE_METRICS_DB:
                        m = get_metrics(concept_id)
                        if m and m.get("current_decayed_score"):
                            conf_val = float(m["current_decayed_score"])

                    title = fm.get("title", file)
                    desc = fm.get("description", "")
                    tags = fm.get("tags", [])
                    tier = fm.get("memory_tier", "semantic")
                    doc_type = fm.get("type", "spec")

                    text_for_search = f"{title}\n{desc}\n{' '.join(tags)}\n{body}"
                    tokens = tokenize(text_for_search)

                    self.documents[concept_id] = {
                        "id": concept_id,
                        "path": rel_path,
                        "title": title,
                        "description": desc,
                        "type": doc_type,
                        "memory_tier": tier,
                        "confidence": conf_val,
                        "body": body,
                        "tokens": tokens,
                        "relations": fm.get("relations", {})
                    }
                    self.corpus_tokens[concept_id] = tokens

                    if concept_id not in self.graph_adj:
                        self.graph_adj[concept_id] = set()

                    rels = fm.get("relations", {})
                    if isinstance(rels, dict):
                        for _, targets in rels.items():
                            if targets:
                                target_list = targets if isinstance(targets, list) else [targets]
                                for t in target_list:
                                    t_clean = strip_md_suffix(str(t))
                                    self.graph_adj[concept_id].add(t_clean)

    def search(self, query: str, top_k: int = 5, k_rrf: int = 60) -> List[Dict[str, Any]]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        # 1. BM25 Scoring
        bm25_scores = self.bm25.score(query_tokens)

        # 2. Semantic Similarity Score
        semantic_scores = {}
        for cid, doc in self.documents.items():
            sem_text = f"{doc['title']} {doc['description']} {' '.join(doc.get('tags', []))}".lower()
            sem_tokens = tokenize(sem_text)
            overlap = set(query_tokens).intersection(set(sem_tokens))
            score = len(overlap) / (math.sqrt(len(query_tokens)) * math.sqrt(max(1, len(sem_tokens))))
            semantic_scores[cid] = score

        # 3. Knowledge Graph Proximity
        graph_scores = {cid: 0.0 for cid in self.documents}
        top_lexical_seeds = sorted(bm25_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        for seed_id, seed_score in top_lexical_seeds:
            if seed_score > 0 and seed_id in self.graph_adj:
                for neighbor in self.graph_adj[seed_id]:
                    if neighbor in graph_scores:
                        graph_scores[neighbor] += 0.5 * seed_score

        # Reciprocal Rank Fusion (RRF)
        bm25_ranked = sorted(bm25_scores.items(), key=lambda x: x[1], reverse=True)
        semantic_ranked = sorted(semantic_scores.items(), key=lambda x: x[1], reverse=True)
        graph_ranked = sorted(graph_scores.items(), key=lambda x: x[1], reverse=True)

        bm25_rank_map = {doc_id: rank + 1 for rank, (doc_id, _) in enumerate(bm25_ranked)}
        sem_rank_map = {doc_id: rank + 1 for rank, (doc_id, _) in enumerate(semantic_ranked)}
        graph_rank_map = {doc_id: rank + 1 for rank, (doc_id, _) in enumerate(graph_ranked)}

        fused_scores = {}
        for cid, doc in self.documents.items():
            r_bm25 = bm25_rank_map.get(cid, 999)
            r_sem = sem_rank_map.get(cid, 999)
            r_graph = graph_rank_map.get(cid, 999)

            rrf_base = (1.0 / (k_rrf + r_bm25)) + (0.8 / (k_rrf + r_sem)) + (0.6 / (k_rrf + r_graph))
            conf = doc["confidence"]
            conf_weight = 0.6 + 0.4 * conf

            final_rrf = rrf_base * conf_weight
            fused_scores[cid] = {
                "rrf_score": final_rrf,
                "bm25_score": bm25_scores[cid],
                "sem_score": semantic_scores[cid],
                "graph_score": graph_scores[cid],
                "bm25_rank": r_bm25,
                "sem_rank": r_sem,
                "graph_rank": r_graph,
            }

        sorted_results = sorted(fused_scores.items(), key=lambda x: x[1]["rrf_score"], reverse=True)

        output = []
        for cid, score_detail in sorted_results[:top_k]:
            doc = self.documents[cid]
            snippet = self._generate_snippet(doc["body"], query_tokens)

            # Record access log in metrics_db (Zero Git Conflict)
            if HAVE_METRICS_DB:
                try:
                    record_access(cid, action_type="search_hit", query_text=query)
                except Exception:
                    pass

            output.append({
                "id": cid,
                "path": doc["path"],
                "title": doc["title"],
                "type": doc["type"],
                "memory_tier": doc["memory_tier"],
                "confidence": doc["confidence"],
                "rrf_score": round(score_detail["rrf_score"] * 1000, 3),
                "details": {
                    "bm25_rank": score_detail["bm25_rank"],
                    "sem_rank": score_detail["sem_rank"],
                    "graph_rank": score_detail["graph_rank"]
                },
                "snippet": snippet,
                "neighbors": list(self.graph_adj.get(cid, []))
            })

        return output

    def _generate_snippet(self, body: str, query_tokens: List[str]) -> str:
        lines = [line.strip() for line in body.splitlines() if line.strip() and not line.startswith("#")]
        for line in lines:
            for q in query_tokens:
                if len(q) > 1 and q in line.lower():
                    return (line[:120] + "...") if len(line) > 120 else line
        return (lines[0][:120] + "...") if lines else ""


def main():
    import argparse
    parser = argparse.ArgumentParser(description="LLM Wiki v2 Hybrid Search Engine")
    parser.add_argument("query", type=str, help="Search query string")
    parser.add_argument("--wiki", type=str, default="wiki", help="Path to wiki directory")
    parser.add_argument("--top", type=int, default=5, help="Number of top results to return")
    parser.add_argument("--json", action="store_true", help="Output raw JSON format")

    args = parser.parse_args()

    engine = HybridSearchEngine(Path(args.wiki))
    results = engine.search(args.query, top_k=args.top)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    print("\n" + "=" * 76)
    print(f"🔎 LLM Wiki v2 Hybrid Search Results for: '{args.query}'")
    print("=" * 76)

    if not results:
        print("No matching concept documents found.")
        print("=" * 76 + "\n")
        return

    for rank, res in enumerate(results, 1):
        print(f"\n#{rank} [{res['rrf_score']:.1f} pts] {res['title']} ({res['id']})")
        print(f"   📂 Type: {res['type']} | Tier: {res['memory_tier']} | Conf: {res['confidence']:.2f}")
        print(f"   📊 Ranks: BM25=#{res['details']['bm25_rank']} | Sem=#{res['details']['sem_rank']} | Graph=#{res['details']['graph_rank']}")
        if res["neighbors"]:
            print(f"   🔗 Connected: {', '.join(res['neighbors'][:4])}")
        if res["snippet"]:
            print(f"   📝 \"{res['snippet']}\"")

    print("\n" + "=" * 76 + "\n")


if __name__ == "__main__":
    main()
