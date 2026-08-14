"""
hybrid_search.py - LLM Wiki v2 Hybrid Search Engine

Combines 3 search paradigms into a unified, high-accuracy ranking:
  1. BM25 Keyword Search (Exact term matching, code identifiers, Japanese n-grams)
  2. Semantic Similarity (Concept, title, description, tags vector similarity)
  3. Knowledge Graph Proximity (Traversal along implements, depends_on, uses edges)
  
Integrated via Reciprocal Rank Fusion (RRF) with memory confidence weighting.

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
        from lint_okf import parse_yaml_subset
        return parse_yaml_subset(fm_text), body


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
                num = freq * (self.k1 + 1)
                den = freq + self.k1 * (1 - self.b + self.b * (self.doc_lengths[doc_id] / max(1e-5, self.avgdl)))
                scores[doc_id] += idf_val * (num / den)
        return scores


class HybridSearchEngine:
    def __init__(self, wiki_root: Path):
        self.wiki_root = wiki_root.resolve()
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.corpus_tokens: Dict[str, List[str]] = {}
        self.graph_adj: Dict[str, List[str]] = {}
        self._load_corpus()

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
                    fm = fm or {}

                    title = fm.get("title", file)
                    desc = fm.get("description", "")
                    tags = fm.get("tags", [])
                    ntype = fm.get("type", "Concept")
                    tier = fm.get("memory_tier", "semantic")
                    conf = fm.get("confidence", {}).get("current_score", 1.0) if isinstance(fm.get("confidence"), dict) else 1.0

                    self.documents[concept_id] = {
                        "id": concept_id,
                        "path": rel_path,
                        "title": title,
                        "description": desc,
                        "tags": tags,
                        "type": ntype,
                        "memory_tier": tier,
                        "confidence": conf,
                        "body": body,
                        "relations": fm.get("relations", {}) if isinstance(fm.get("relations"), dict) else {},
                    }

                    weighted_text = f"{title} {title} {desc} {desc} {' '.join(tags)} {ntype} {concept_id} {body[:1500]}"
                    self.corpus_tokens[concept_id] = tokenize(weighted_text)

        # Build local graph adjacency
        for cid, doc in self.documents.items():
            self.graph_adj[cid] = []
            rels = doc.get("relations", {})
            for rtype, targets in rels.items():
                if isinstance(targets, list):
                    for t in targets:
                        clean_t = strip_md_suffix(str(t))
                        if clean_t in self.documents:
                            self.graph_adj[cid].append(clean_t)
                elif isinstance(targets, str):
                    clean_t = strip_md_suffix(targets)
                    if clean_t in self.documents:
                        self.graph_adj[cid].append(clean_t)

    def search(self, query: str, top_k: int = 5, k_rrf: int = 60) -> List[Dict[str, Any]]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        # 1. BM25 Search
        bm25 = BM25Okapi(self.corpus_tokens)
        bm25_scores = bm25.score(query_tokens)
        bm25_ranked = sorted(bm25_scores.items(), key=lambda x: x[1], reverse=True)

        # 2. Semantic Concept Matching
        semantic_scores = {}
        for cid, doc in self.documents.items():
            concept_text = f"{doc['title']} {doc['description']} {' '.join(doc['tags'])} {doc['type']}"
            c_tokens = set(tokenize(concept_text))
            q_set = set(query_tokens)
            intersection = q_set.intersection(c_tokens)
            score = (len(intersection) / max(1, math.sqrt(len(q_set) * len(c_tokens)))) if c_tokens else 0.0
            semantic_scores[cid] = score
        semantic_ranked = sorted(semantic_scores.items(), key=lambda x: x[1], reverse=True)

        # 3. Knowledge Graph Proximity Search
        graph_scores = {cid: 0.0 for cid in self.documents}
        seeds = [doc_id for doc_id, s in bm25_ranked[:3] if s > 0] + [doc_id for doc_id, s in semantic_ranked[:3] if s > 0]
        for seed in set(seeds):
            graph_scores[seed] += 1.0
            for neighbor in self.graph_adj.get(seed, []):
                graph_scores[neighbor] += 0.5

        graph_ranked = sorted(graph_scores.items(), key=lambda x: x[1], reverse=True)

        # 4. Reciprocal Rank Fusion (RRF)
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
                "neighbors": self.graph_adj.get(cid, [])
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
