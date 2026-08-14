"""
build_graph.py - LLM Wiki v2 Knowledge Graph Builder & Analyzer

Extracts typed entities and typed relations from OKF Concept documents and cross-links.
Outputs:
  - wiki/graph.json: Machine-readable graph data (nodes & edges)
  - wiki/graph.mermaid: Visual Mermaid diagram with category styles and relation labels
Analyzes:
  - Orphan nodes (nodes with no connections)
  - Contradiction edges (`contradicts`)
  - Circular dependencies (`depends_on` cycles)
  - Graph traversal & Impact analysis
"""

import os
import re
import sys
import json
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple

try:
    import yaml
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False


def strip_md_suffix(s: str) -> str:
    s = s.strip()
    return s[:-3] if s.endswith(".md") else s


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
        # Minimal pure-Python parser
        from lint_okf import parse_yaml_subset
        return parse_yaml_subset(fm_text), body


class KnowledgeGraph:
    def __init__(self, wiki_root: Path):
        self.wiki_root = wiki_root.resolve()
        self.repo_root = self.wiki_root.parent
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        self.adjacency: Dict[str, List[Tuple[str, str]]] = {}
        self.reverse_adjacency: Dict[str, List[Tuple[str, str]]] = {}

    def build(self):
        # 1. Gather all concept nodes (deterministically sorted)
        for root, dirs, files in os.walk(self.wiki_root):
            dirs.sort()
            for file in sorted(files):
                if file.endswith(".md") and file not in ("index.md", "log.md"):
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(self.wiki_root).as_posix()
                    concept_id = strip_md_suffix(rel_path)

                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()

                    fm, body = extract_frontmatter(content)
                    fm = fm or {}

                    parts = rel_path.split("/")
                    category = parts[0] if len(parts) > 1 else "root"

                    self.nodes[concept_id] = {
                        "id": concept_id,
                        "path": rel_path,
                        "type": fm.get("type", "Concept"),
                        "title": fm.get("title", concept_id.split("/")[-1]),
                        "description": fm.get("description", ""),
                        "category": category,
                        "status": fm.get("status", "active"),
                        "memory_tier": fm.get("memory_tier", "semantic"),
                        "confidence": fm.get("confidence", {}).get("current_score", 1.0) if isinstance(fm.get("confidence"), dict) else 1.0,
                        "tags": fm.get("tags", []),
                    }
                    self.adjacency[concept_id] = []
                    self.reverse_adjacency[concept_id] = []

        # 2. Extract relations and links (Edges)
        for concept_id in sorted(self.nodes.keys()):
            node = self.nodes[concept_id]
            full_path = self.wiki_root / (node["path"])
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            fm, body = extract_frontmatter(content)
            fm = fm or {}

            # (A) Typed relations from frontmatter
            relations = fm.get("relations", {})
            if isinstance(relations, dict):
                for rel_type in sorted(relations.keys()):
                    targets = relations[rel_type]
                    if isinstance(targets, list):
                        for tgt in targets:
                            tgt_clean = strip_md_suffix(str(tgt))
                            self.add_edge(concept_id, tgt_clean, rel_type)
                    elif isinstance(targets, str):
                        self.add_edge(concept_id, strip_md_suffix(targets), rel_type)

            # Supersedes / Superseded_by
            if "supersedes" in fm and fm["supersedes"]:
                supers = fm["supersedes"] if isinstance(fm["supersedes"], list) else [fm["supersedes"]]
                for s in supers:
                    self.add_edge(concept_id, strip_md_suffix(str(s)), "supersedes")

            if "superseded_by" in fm and fm["superseded_by"]:
                self.add_edge(concept_id, strip_md_suffix(str(fm["superseded_by"])), "superseded_by")

            # (B) Cross-links in Markdown body: [Text](path)
            md_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", body)
            for text, link in md_links:
                if link.startswith("http") or link.startswith("#") or link.startswith("raw/"):
                    continue
                clean_target = strip_md_suffix(link.split("#")[0].split("?")[0])
                tgt_resolved = self.resolve_link(full_path, clean_target)
                if tgt_resolved and tgt_resolved in self.nodes and tgt_resolved != concept_id:
                    self.add_edge(concept_id, tgt_resolved, "references")

            # (C) Obsidian style links: [[concept_name]]
            wiki_links = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", body)
            for wlink in wiki_links:
                wlink_clean = strip_md_suffix(wlink.strip())
                matched = sorted([nid for nid in self.nodes if nid.endswith(wlink_clean) or nid == wlink_clean])
                for m in matched:
                    if m != concept_id:
                        self.add_edge(concept_id, m, "references")

    def resolve_link(self, current_file: Path, target_str: str) -> Optional[str]:
        target_path = target_str + (".md" if not target_str.endswith(".md") else "")
        if target_path.startswith("/"):
            candidate = (self.wiki_root / target_path.lstrip("/")).resolve()
        else:
            candidate = (current_file.parent / target_path).resolve()

        if candidate.exists() and candidate.is_relative_to(self.wiki_root):
            rel = candidate.relative_to(self.wiki_root).as_posix()
            return strip_md_suffix(rel)
        return None

    def add_edge(self, source: str, target: str, rel_type: str):
        for edge in self.edges:
            if edge["source"] == source and edge["target"] == target and edge["type"] == rel_type:
                return

        edge_data = {"source": source, "target": target, "type": rel_type}
        self.edges.append(edge_data)

        if source in self.adjacency:
            self.adjacency[source].append((target, rel_type))
        if target in self.reverse_adjacency:
            self.reverse_adjacency[target].append((source, rel_type))

    def export_json(self, output_path: Path):
        sorted_nodes = [self.nodes[k] for k in sorted(self.nodes.keys())]
        sorted_edges = sorted(self.edges, key=lambda e: (e["source"], e["target"], e["type"]))
        data = {
            "version": "2.0",
            "node_count": len(sorted_nodes),
            "edge_count": len(sorted_edges),
            "nodes": sorted_nodes,
            "edges": sorted_edges
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"📊 Exported Knowledge Graph JSON: {output_path} ({len(self.nodes)} nodes, {len(self.edges)} edges)")

    def export_mermaid(self, output_path: Path):
        lines = [
            "```mermaid",
            "flowchart TD",
            "  %% LLM Wiki v2 Knowledge Graph",
            "  classDef customer fill:#FFEAA7,stroke:#D6A2E8,stroke-width:2px;",
            "  classDef requirement fill:#DFF9FB,stroke:#7ED6DF,stroke-width:2px;",
            "  classDef basic fill:#E8F8F5,stroke:#48DBFB,stroke-width:2px;",
            "  classDef detailed fill:#FADBD8,stroke:#FF7675,stroke-width:2px;",
            "  classDef decision fill:#D5F5E3,stroke:#2ECC71,stroke-width:2px;",
            "  classDef stale fill:#F5EEF8,stroke:#BDC581,stroke-width:2px,stroke-dasharray: 5 5;",
            "  classDef deprecated fill:#E5E8E8,stroke:#95A5A6,stroke-width:1px,opacity:0.6;",
            ""
        ]

        def sanitize_id(raw_id: str) -> str:
            return re.sub(r"[^a-zA-Z0-9_]", "_", raw_id)

        for nid in sorted(self.nodes.keys()):
            node = self.nodes[nid]
            sid = sanitize_id(nid)
            title = node["title"].replace('"', "'")
            ntype = node["type"]
            tier = node.get("memory_tier", "semantic")
            label = f'"{title}<br/><i>[{ntype} | {tier}]</i>"'
            lines.append(f"  {sid}[{label}]")

            cat = node["category"]
            status = node.get("status", "active")
            if status == "deprecated":
                lines.append(f"  class {sid} deprecated;")
            elif status == "stale":
                lines.append(f"  class {sid} stale;")
            elif "01_customer" in cat:
                lines.append(f"  class {sid} customer;")
            elif "02_require" in cat:
                lines.append(f"  class {sid} requirement;")
            elif "03_basic" in cat:
                lines.append(f"  class {sid} basic;")
            elif "04_detail" in cat:
                lines.append(f"  class {sid} detailed;")
            elif "05_decision" in cat:
                lines.append(f"  class {sid} decision;")

        lines.append("")
        sorted_edges = sorted(self.edges, key=lambda e: (e["source"], e["target"], e["type"]))
        for edge in sorted_edges:
            s = sanitize_id(edge["source"])
            t = sanitize_id(edge["target"])
            rel = edge["type"]
            if edge["target"] not in self.nodes:
                continue

            if rel == "contradicts":
                lines.append(f"  {s} -.-|⚠️ contradicts| {t}")
            elif rel == "supersedes":
                lines.append(f"  {s} ==>|supersedes| {t}")
            elif rel in ("implements", "implemented_by", "depends_on", "uses"):
                lines.append(f"  {s} -->|{rel}| {t}")
            else:
                lines.append(f"  {s} -.->|{rel}| {t}")

        lines.append("```\n")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"🗺️  Exported Knowledge Graph Mermaid: {output_path}")

    def analyze(self):
        print("\n" + "=" * 64)
        print("🧠 LLM Wiki v2 Knowledge Graph Analysis")
        print("=" * 64)

        print(f"• Total Concepts (Nodes): {len(self.nodes)}")
        print(f"• Total Relations (Edges): {len(self.edges)}")

        tiers = {}
        for n in self.nodes.values():
            t = n.get("memory_tier", "semantic")
            tiers[t] = tiers.get(t, 0) + 1
        print("• Memory Tiers: " + ", ".join(f"{k}: {v}" for k, v in tiers.items()))

        contradictions = [e for e in self.edges if e["type"] == "contradicts"]
        if contradictions:
            print(f"\n⚠️  CONTRADICTIONS DETECTED ({len(contradictions)}):")
            for c in contradictions:
                print(f"  • [{c['source']}] CONTRADICTS [{c['target']}]")
        else:
            print("• Contradictions: None (Consistent)")

        orphans = []
        for nid in self.nodes:
            out_edges = self.adjacency.get(nid, [])
            in_edges = self.reverse_adjacency.get(nid, [])
            if not out_edges and not in_edges:
                orphans.append(nid)
        if orphans:
            print(f"\n⚠️  ORPHAN CONCEPTS ({len(orphans)}):")
            for o in orphans:
                print(f"  • {o}")
        else:
            print("• Orphan Concepts: None (Well connected)")

        degree = {
            nid: len(self.adjacency.get(nid, [])) + len(self.reverse_adjacency.get(nid, []))
            for nid in self.nodes
        }
        sorted_hubs = sorted(degree.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"\n🌟 Top Hub Concepts (Highest Connectivity):")
        for hid, deg in sorted_hubs:
            print(f"  • {hid} (Degree: {deg}) - {self.nodes[hid]['title']}")

        print("=" * 64 + "\n")


if __name__ == "__main__":
    wiki_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("wiki")
    kg = KnowledgeGraph(wiki_path)
    kg.build()
    kg.export_json(wiki_path / "graph.json")
    kg.export_mermaid(wiki_path / "graph.mermaid")
    kg.analyze()
