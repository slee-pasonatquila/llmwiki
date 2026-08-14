"""
memory_decay.py - LLM Wiki v2 Memory Lifecycle & Forgetting Curve Simulator

Calculates time-decayed confidence scores based on Ebbinghaus forgetting curves.
Formula:
  final_score = base_confidence * exp(-lambda * days_since_last_reinforced) + verification_boost

Decay Rates (lambda):
  - permanent (0.002, half-life ~346 days): Architecture decisions (ADR), Core specs
  - standard  (0.010, half-life ~69 days):  Requirements, DB/API specs, Domain models
  - volatile  (0.050, half-life ~14 days):  Meeting notes, Temporary bugfixes, Working drafts

Usage:
  python3 scripts/memory_decay.py wiki/                  # View memory decay report
  python3 scripts/memory_decay.py wiki/ --update         # Update frontmatters with decayed scores
  python3 scripts/memory_decay.py --reinforce wiki/04_detailed_designs/table_users.md # Reinforce concept
"""

import os
import re
import sys
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

try:
    import yaml
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False


DECAY_RATES = {
    "permanent": 0.002,
    "standard": 0.010,
    "volatile": 0.050,
}

STALE_THRESHOLD = 0.50


def strip_md_suffix(s: str) -> str:
    s = s.strip()
    return s[:-3] if s.endswith(".md") else s


def extract_frontmatter(content: str) -> Tuple[Optional[dict], str, Optional[str]]:
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)
    if not match:
        return None, content, None
    fm_text, body = match.groups()
    if HAVE_YAML:
        try:
            parsed = yaml.safe_load(fm_text)
            return (parsed if isinstance(parsed, dict) else {}), body, fm_text
        except Exception:
            return None, body, fm_text
    else:
        from lint_okf import parse_yaml_subset
        return parse_yaml_subset(fm_text), body, fm_text


class MemoryLifecycleManager:
    def __init__(self, wiki_root: Path):
        self.wiki_root = wiki_root.resolve()

    def parse_datetime(self, dt_val: Any) -> datetime:
        if isinstance(dt_val, datetime):
            return dt_val.replace(tzinfo=timezone.utc) if dt_val.tzinfo is None else dt_val
        if isinstance(dt_val, str):
            dt_clean = dt_val.strip().replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(dt_clean)
                return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
            except Exception:
                pass
            try:
                dt = datetime.strptime(dt_clean[:10], "%Y-%m-%d")
                return dt.replace(tzinfo=timezone.utc)
            except Exception:
                pass
        return datetime.now(timezone.utc)

    def calculate_decay(self, fm: dict, now: Optional[datetime] = None) -> Dict[str, Any]:
        now = now or datetime.now(timezone.utc)
        
        conf_data = fm.get("confidence", {})
        if isinstance(conf_data, dict):
            base_score = float(conf_data.get("base_score", 0.90))
        elif isinstance(conf_data, (int, float)):
            base_score = float(conf_data)
        else:
            base_score = 0.90

        decay_key = fm.get("decay_rate", "standard")
        if isinstance(decay_key, str) and decay_key.lower() in DECAY_RATES:
            decay_lambda = DECAY_RATES[decay_key.lower()]
        else:
            tier = fm.get("memory_tier", "semantic")
            if tier == "working":
                decay_lambda = DECAY_RATES["volatile"]
                decay_key = "volatile"
            elif fm.get("type") in ("Decision (ADR)", "Architecture"):
                decay_lambda = DECAY_RATES["permanent"]
                decay_key = "permanent"
            else:
                decay_lambda = DECAY_RATES["standard"]
                decay_key = "standard"

        last_dt = fm.get("last_reinforced_at")
        if not last_dt:
            gen = fm.get("generated", {})
            last_dt = gen.get("at") if isinstance(gen, dict) else None

        reinforced_time = self.parse_datetime(last_dt)
        elapsed_days = max(0.0, (now - reinforced_time).total_seconds() / 86400.0)

        raw_score = base_score * math.exp(-decay_lambda * elapsed_days)

        verified = fm.get("verified")
        boost = 0.05 if (verified and isinstance(verified, dict) and verified.get("by")) else 0.0

        current_score = min(1.0, max(0.0, raw_score + boost))
        is_stale = current_score < STALE_THRESHOLD

        return {
            "base_score": round(base_score, 3),
            "current_score": round(current_score, 3),
            "decay_rate": decay_key,
            "lambda": decay_lambda,
            "elapsed_days": round(elapsed_days, 1),
            "last_reinforced": reinforced_time.isoformat(),
            "is_stale": is_stale,
            "has_verification": bool(boost > 0)
        }

    def generate_report(self) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        results = []

        for root, _, files in os.walk(self.wiki_root):
            for file in files:
                if file.endswith(".md") and file not in ("index.md", "log.md"):
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(self.wiki_root).as_posix()

                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()

                    fm, _, _ = extract_frontmatter(content)
                    if not fm:
                        continue

                    decay_info = self.calculate_decay(fm, now)
                    decay_info["path"] = rel_path
                    decay_info["title"] = fm.get("title", file)
                    decay_info["type"] = fm.get("type", "Concept")
                    decay_info["tier"] = fm.get("memory_tier", "semantic")
                    decay_info["status"] = fm.get("status", "active")
                    results.append(decay_info)

        return results

    def print_report(self):
        results = self.generate_report()
        print("\n" + "=" * 72)
        print("⏳ LLM Wiki v2 Memory Lifecycle & Confidence Decay Report")
        print("=" * 72)
        print(f"{'Doc / Title':<34} | {'Tier':<10} | {'Days':<6} | {'Base':<5} | {'Current':<7} | {'Status'}")
        print("-" * 72)

        stale_docs = []
        for r in sorted(results, key=lambda x: x["current_score"]):
            status_tag = "🔴 STALE" if r["is_stale"] else ("🟢 FRESH" if r["current_score"] >= 0.8 else "🟡 DECAYING")
            title_short = (r["title"][:31] + "...") if len(r["title"]) > 34 else r["title"]
            print(f"{title_short:<34} | {r['tier']:<10} | {r['elapsed_days']:<6} | {r['base_score']:<5} | {r['current_score']:<7} | {status_tag}")
            if r["is_stale"]:
                stale_docs.append(r)

        print("-" * 72)
        if stale_docs:
            print(f"\n⚠️  {len(stale_docs)} Concept(s) have decayed below threshold ({STALE_THRESHOLD}):")
            for sd in stale_docs:
                print(f"  • [{sd['path']}] {sd['title']} (Score: {sd['current_score']}) -> Recommend Review & Reinforce!")
        else:
            print("✅ All Concepts maintain active confidence levels!")
        print("=" * 72 + "\n")

    def reinforce(self, file_path: Path):
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            return

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        fm, body, raw_fm = extract_frontmatter(content)
        if not fm:
            print(f"❌ No frontmatter found in {file_path}")
            return

        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        acc = int(fm.get("access_count", 0)) + 1
        
        conf = fm.get("confidence", {})
        base_score = float(conf.get("base_score", 0.90)) if isinstance(conf, dict) else 0.90
        
        if acc > 3 and base_score < 0.95:
            base_score = min(0.98, base_score + 0.02)

        fm["last_reinforced_at"] = now_iso
        fm["access_count"] = acc
        if not isinstance(fm.get("confidence"), dict):
            fm["confidence"] = {}
        fm["confidence"]["base_score"] = round(base_score, 3)
        fm["confidence"]["current_score"] = round(base_score, 3)

        if fm.get("status") == "stale":
            fm["status"] = "active"

        new_content = self.dump_frontmatter(fm, body)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"⚡ Reinforced concept: {file_path.name}")
        print(f"   • Last Reinforced At: {now_iso}")
        print(f"   • Access Count: {acc}")
        print(f"   • Current Confidence: {base_score}")

    def update_all_decay(self):
        now = datetime.now(timezone.utc)
        count = 0
        for root, _, files in os.walk(self.wiki_root):
            for file in files:
                if file.endswith(".md") and file not in ("index.md", "log.md"):
                    full_path = Path(root) / file
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    fm, body, _ = extract_frontmatter(content)
                    if not fm:
                        continue

                    decay = self.calculate_decay(fm, now)
                    if not isinstance(fm.get("confidence"), dict):
                        fm["confidence"] = {}
                    fm["confidence"]["base_score"] = decay["base_score"]
                    fm["confidence"]["current_score"] = decay["current_score"]
                    
                    if decay["is_stale"] and fm.get("status") == "active":
                        fm["status"] = "stale"

                    new_content = self.dump_frontmatter(fm, body)
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    count += 1

        print(f"🔄 Updated decayed confidence scores across {count} concept documents.")

    def dump_frontmatter(self, fm: dict, body: str) -> str:
        if HAVE_YAML:
            fm_str = yaml.dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False)
            return f"---\n{fm_str}---\n{body}"
        else:
            lines = ["---"]
            for k, v in fm.items():
                if isinstance(v, dict):
                    lines.append(f"{k}:")
                    for subk, subv in v.items():
                        if isinstance(subv, dict):
                            lines.append(f"  {subk}:")
                            for ssk, ssv in subv.items():
                                lines.append(f"    {ssk}: {ssv}")
                        elif isinstance(subv, list):
                            lines.append(f"  {subk}: [{', '.join(str(x) for x in subv)}]")
                        else:
                            lines.append(f"  {subk}: {subv}")
                elif isinstance(v, list):
                    if all(isinstance(item, dict) for item in v):
                        lines.append(f"{k}:")
                        for item in v:
                            first = True
                            for ik, iv in item.items():
                                prefix = "  - " if first else "    "
                                lines.append(f"{prefix}{ik}: {iv}")
                                first = False
                    else:
                        lines.append(f"{k}: [{', '.join(str(x) for x in v)}]")
                else:
                    lines.append(f"{k}: {v}")
            lines.append("---\n")
            return "\n".join(lines) + body


if __name__ == "__main__":
    args = sys.argv[1:]
    wiki_dir = Path("wiki")

    if "--reinforce" in args:
        idx = args.index("--reinforce")
        if idx + 1 < len(args):
            mgr = MemoryLifecycleManager(wiki_dir)
            mgr.reinforce(Path(args[idx + 1]))
        else:
            print("Usage: python3 scripts/memory_decay.py --reinforce <file_path>")
    elif "--update" in args:
        target = Path(args[0]) if args and not args[0].startswith("--") else wiki_dir
        mgr = MemoryLifecycleManager(target)
        mgr.update_all_decay()
        mgr.print_report()
    else:
        target = Path(args[0]) if args and not args[0].startswith("--") else wiki_dir
        mgr = MemoryLifecycleManager(target)
        mgr.print_report()
