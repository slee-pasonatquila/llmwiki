"""
consolidate_memory.py - LLM Wiki v2 Memory Consolidation & Tier Promotion Tool

Manages transitions across the 4 memory tiers:
  1. Working Memory    (working):    Raw, unprocessed observations and session scratchpads.
  2. Episodic Memory   (episodic):   Session summaries, meeting notes, hearing records.
  3. Semantic Memory   (semantic):   Cross-session integrated facts, specs, ADRs, schemas.
  4. Procedural Memory (procedural): Workflows, runbooks, SOPs, repeatable execution skills.

Usage:
  python3 scripts/consolidate_memory.py wiki/              # View memory tier distribution
  python3 scripts/consolidate_memory.py --promote <file> <new_tier> # Promote a document's tier
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import memory_decay

VALID_TIERS = ["working", "episodic", "semantic", "procedural"]

TIER_DESCRIPTIONS = {
    "working": "Working Memory: Raw temporary observations, drafts, session notes.",
    "episodic": "Episodic Memory: Time-bounded session summaries, meeting minutes, interview logs.",
    "semantic": "Semantic Memory: Integrated concepts, requirements, architecture, schemas, ADRs.",
    "procedural": "Procedural Memory: Workflows, playbooks, runbooks, and repeatable skills."
}


class MemoryConsolidator:
    def __init__(self, wiki_root: Path):
        self.wiki_root = wiki_root.resolve()

    def print_distribution(self):
        docs_by_tier: Dict[str, List[Dict[str, str]]] = {t: [] for t in VALID_TIERS}

        for root, _, files in os.walk(self.wiki_root):
            for file in files:
                if file.endswith(".md") and file not in ("index.md", "log.md"):
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(self.wiki_root).as_posix()

                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()

                    fm, _, _ = memory_decay.extract_frontmatter(content)
                    if not fm:
                        continue

                    tier = fm.get("memory_tier", "semantic")
                    if tier not in docs_by_tier:
                        tier = "semantic"

                    docs_by_tier[tier].append({
                        "id": rel_path[:-3],
                        "title": fm.get("title", file),
                        "type": fm.get("type", "Concept")
                    })

        print("\n" + "=" * 70)
        print("🧠 LLM Wiki v2 Memory Tier Consolidation Status")
        print("=" * 70)

        for tier in VALID_TIERS:
            docs = docs_by_tier[tier]
            print(f"\n📂 [{tier.upper()}] ({len(docs)} items)")
            print(f"   💡 {TIER_DESCRIPTIONS[tier]}")
            if docs:
                for d in docs[:8]:
                    print(f"   • [{d['type']}] {d['title']} ({d['id']})")
                if len(docs) > 8:
                    print(f"   • ... and {len(docs) - 8} more.")
            else:
                print("   • (empty)")

        print("\n" + "=" * 70 + "\n")

    def promote(self, file_path: Path, new_tier: str):
        if new_tier not in VALID_TIERS:
            print(f"❌ Invalid tier: '{new_tier}'. Valid tiers: {', '.join(VALID_TIERS)}")
            return

        if not file_path.exists():
            print(f"❌ Target file not found: {file_path}")
            return

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        fm, body, _ = memory_decay.extract_frontmatter(content)
        if not fm:
            print(f"❌ No frontmatter found in {file_path}")
            return

        old_tier = fm.get("memory_tier", "semantic")
        fm["memory_tier"] = new_tier

        # Adjust decay rate if promoting/demoting
        if new_tier == "working":
            fm["decay_rate"] = "volatile"
        elif new_tier in ("semantic", "procedural"):
            if fm.get("decay_rate") == "volatile":
                fm["decay_rate"] = "standard"

        mgr = memory_decay.MemoryLifecycleManager(self.wiki_root)
        new_content = mgr.dump_frontmatter(fm, body)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"✨ Successfully promoted [{file_path.name}]:")
        print(f"   • Tier: {old_tier} ➡️  {new_tier}")
        print(f"   • Decay Rate: {fm.get('decay_rate', 'standard')}")


if __name__ == "__main__":
    args = sys.argv[1:]
    wiki_path = Path("wiki")

    if "--promote" in args:
        idx = args.index("--promote")
        if idx + 2 < len(args):
            fpath = Path(args[idx + 1])
            tier = args[idx + 2].lower()
            con = MemoryConsolidator(wiki_path)
            con.promote(fpath, tier)
        else:
            print("Usage: python3 scripts/consolidate_memory.py --promote <file_path> <new_tier>")
    else:
        con = MemoryConsolidator(wiki_path)
        con.print_distribution()
