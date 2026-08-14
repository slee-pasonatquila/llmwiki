"""
memory_decay.py - LLM Wiki v2 Memory Lifecycle & Forgetting Curve Simulator (Multi-User SQLite Supported)

Calculates time-decayed confidence scores based on Ebbinghaus forgetting curves.
Formula:
  final_score = base_confidence * exp(-lambda * days_since_last_reinforced) + verification_boost

Decay Rates (lambda):
  - permanent (0.002, half-life ~346 days): Architecture decisions (ADR), Core specs
  - standard  (0.010, half-life ~69 days):  Requirements, DB/API specs, Domain models
  - volatile  (0.050, half-life ~14 days):  Meeting notes, Temporary bugfixes, Working drafts

Multi-User Architecture:
  - Daily access & reinforcement records are saved to `wiki/.cache/metrics.db` by default to avoid Git conflicts.
  - Periodic synchronization to Markdown frontmatter can be executed via `--sync-to-frontmatter`.

Usage:
  python3 scripts/memory_decay.py wiki/                     # View memory decay report (from cache/files)
  python3 scripts/memory_decay.py --reinforce <file_path>   # Record reinforcement to metrics.db
  python3 scripts/memory_decay.py wiki/ --sync-to-frontmatter # Flush DB metrics to Markdown Frontmatters
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

# Import metrics_db
try:
    from metrics_db import record_access, get_metrics, update_decay_scores, get_db
    HAVE_METRICS_DB = True
except ImportError:
    try:
        from scripts.metrics_db import record_access, get_metrics, update_decay_scores, get_db
        HAVE_METRICS_DB = True
    except ImportError:
        HAVE_METRICS_DB = False


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
        try:
            from lint_okf import parse_yaml_subset
            return parse_yaml_subset(fm_text), body, fm_text
        except ImportError:
            return {}, body, fm_text


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

    def calculate_decay(self, fm: dict, now: Optional[datetime] = None, concept_id: str = "") -> Dict[str, Any]:
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
            decay_lambda = DECAY_RATES["standard"]

        # Check metrics_db if available
        db_metric = None
        if HAVE_METRICS_DB and concept_id:
            db_metric = get_metrics(concept_id)

        # Baseline date: verified_at > last_reinforced_at > updated_at > created_at
        ver_data = fm.get("verified")
        ver_date = None
        if isinstance(ver_data, dict):
            ver_date = ver_data.get("date")
        elif isinstance(ver_data, str):
            ver_date = ver_data

        if db_metric and db_metric.get("last_verified_at"):
            ref_date_raw = db_metric.get("last_verified_at")
        else:
            ref_date_raw = ver_date or fm.get("last_reinforced_at") or fm.get("updated_at") or fm.get("created_at")
        ref_dt = self.parse_datetime(ref_date_raw)

        days_passed = max(0.0, (now - ref_dt).total_seconds() / 86400.0)

        decayed_score = base_score * math.exp(-decay_lambda * days_passed)
        decayed_score = max(0.10, min(1.0, decayed_score))

        acc_count = (db_metric.get("access_count", 0) if db_metric else 0) or int(fm.get("access_count", 0))

        return {
            "base_score": round(base_score, 3),
            "current_score": round(decayed_score, 3),
            "decay_rate": decay_key,
            "lambda": decay_lambda,
            "days_passed": round(days_passed, 1),
            "is_stale": decayed_score < STALE_THRESHOLD,
            "access_count": acc_count
        }

    def reinforce(self, file_path: Path, use_db_only: bool = True):
        rel_path = file_path.relative_to(self.wiki_root).as_posix() if self.wiki_root in file_path.parents else file_path.name
        concept_id = strip_md_suffix(rel_path)

        if HAVE_METRICS_DB and use_db_only:
            record_access(concept_id, action_type="reinforce", actor="user/agent")
            print(f"⚡ Reinforced concept in SQLite metrics: {concept_id}")
            print(f"   • Database: wiki/.cache/metrics.db (Zero Git Conflict)")
            return

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        fm, body, _ = extract_frontmatter(content)
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

        print(f"⚡ Reinforced concept in Markdown: {file_path.name}")

    def sync_to_frontmatter(self):
        now = datetime.now(timezone.utc)
        count = 0
        for root, _, files in os.walk(self.wiki_root):
            for file in files:
                if file.endswith(".md") and file not in ("index.md", "log.md"):
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(self.wiki_root).as_posix()
                    cid = strip_md_suffix(rel_path)

                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    fm, body, _ = extract_frontmatter(content)
                    if not fm:
                        continue

                    decay = self.calculate_decay(fm, now, concept_id=cid)
                    if not isinstance(fm.get("confidence"), dict):
                        fm["confidence"] = {}
                    fm["confidence"]["base_score"] = decay["base_score"]
                    fm["confidence"]["current_score"] = decay["current_score"]
                    if decay["access_count"] > 0:
                        fm["access_count"] = decay["access_count"]
                    
                    if decay["is_stale"] and fm.get("status") == "active":
                        fm["status"] = "stale"

                    new_content = self.dump_frontmatter(fm, body)
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    count += 1

        print(f"🔄 Flushed SQLite metrics to {count} Markdown frontmatters.")

    def print_report(self):
        print("\n" + "=" * 70)
        print("🧠 LLM Wiki v2 Memory Decay & Retention Analysis")
        print("=" * 70)
        now = datetime.now(timezone.utc)
        
        items = []
        for root, _, files in os.walk(self.wiki_root):
            for file in files:
                if file.endswith(".md") and file not in ("index.md", "log.md"):
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(self.wiki_root).as_posix()
                    cid = strip_md_suffix(rel_path)

                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    fm, _, _ = extract_frontmatter(content)
                    if not fm:
                        continue

                    decay = self.calculate_decay(fm, now, concept_id=cid)
                    title = fm.get("title", file)
                    tier = fm.get("memory_tier", "semantic")
                    items.append((cid, title, tier, decay))

        # Sort by current_score ascending (most decayed first)
        items.sort(key=lambda x: x[3]["current_score"])

        print(f"{'Concept ID':<35} {'Tier':<10} {'Score':<8} {'Days':<6} {'Status'}")
        print("-" * 70)
        for cid, title, tier, d in items:
            score_str = f"{d['current_score']:.2f}"
            days_str = f"{d['days_passed']:.0f}d"
            status_str = "⚠️ STALE" if d["is_stale"] else "✅ Healthy"
            print(f"{cid:<35} {tier:<10} {score_str:<8} {days_str:<6} {status_str}")

        stale_count = sum(1 for _, _, _, d in items if d["is_stale"])
        print("-" * 70)
        print(f"Summary: {len(items)} concepts analyzed. {stale_count} stale concept(s) detected.\n")

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
            target_path = Path(args[idx + 1])
            use_direct_md = "--force-markdown" in args
            mgr.reinforce(target_path, use_db_only=not use_direct_md)
        else:
            print("Usage: python3 scripts/memory_decay.py --reinforce <file_path> [--force-markdown]")
    elif "--sync-to-frontmatter" in args or "--update" in args:
        target = Path(args[0]) if args and not args[0].startswith("--") else wiki_dir
        mgr = MemoryLifecycleManager(target)
        mgr.sync_to_frontmatter()
        mgr.print_report()
    else:
        target = Path(args[0]) if args and not args[0].startswith("--") else wiki_dir
        mgr = MemoryLifecycleManager(target)
        mgr.print_report()
