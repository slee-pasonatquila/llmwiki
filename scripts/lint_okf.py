"""
lint_okf.py - Google OKF (Open Knowledge Format v0.2) & LLM Wiki v2 Linter & Validator

Validates:
  1. YAML Frontmatter presence & OKF v0.2 / LLM Wiki v2 schema:
     - `type:` (Required OKF entity type)
     - `title:`, `description:` (Recommended metadata)
     - `status:` (draft | active | stale | deprecated | tombstone)
     - `memory_tier:` (working | episodic | semantic | procedural)
     - `decay_rate:` (permanent | standard | volatile)
     - `confidence:` (base_score, current_score between 0.0 and 1.0)
     - `generated:`, `verified:` (Structured actor attribution)
     - `sources:` (Structured provenance list with required 'resource')
  2. Footnote / Provenance link integrity ([^source_id] matches sources.id).
  3. Knowledge Graph Relations integrity (implements, implemented_by, depends_on, uses, contradicts, etc.).
  4. Supersession integrity (supersedes / superseded_by points to existing concepts).
  5. Multi-User & Concurrency Validation:
     - Concept ID & Title uniqueness check.
     - Dependency on `draft` documents warning.
     - Unresolved contradiction (`contradicts` without ADR link) warning.
  6. Reserved files structure (index.md coverage of files & subdirectories, log.md date headings).
  7. Internal Cross-link integrity (standard markdown, absolute bundle paths, and wiki-links).
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Set, Any, Optional
from collections import defaultdict

try:
    import yaml
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False

VALID_STATUSES = {"draft", "active", "stale", "deprecated", "tombstone"}
VALID_MEMORY_TIERS = {"working", "episodic", "semantic", "procedural"}
VALID_DECAY_RATES = {"permanent", "standard", "volatile"}
KNOWN_RELATION_KEYS = {
    "implements", "implemented_by", "depends_on", "uses", "caused_by",
    "contradicts", "supersedes", "superseded_by", "fixes", "tested_by",
    "part_of", "references"
}


def strip_md_suffix(s: str) -> str:
    s = s.strip()
    return s[:-3] if s.endswith(".md") else s


def parse_yaml_subset(text: str) -> dict:
    """A self-contained pure-Python parser for standard OKF frontmatter subsets."""
    lines = text.splitlines()
    root: Dict[str, Any] = {}
    
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        cleaned_lines.append((indent, stripped))

    def parse_value(val_str: str) -> Any:
        v = val_str.strip()
        if not v or v == "null" or v == "~":
            return None
        if v.lower() == "true":
            return True
        if v.lower() == "false":
            return False
        try:
            if "." in v:
                return float(v)
            return int(v)
        except ValueError:
            pass
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            if not inner:
                return []
            items = []
            for item in inner.split(","):
                item_clean = item.strip().strip("'\"")
                if item_clean:
                    items.append(item_clean)
            return items
        if v.startswith("{") and v.endswith("}"):
            inner = v[1:-1].strip()
            if not inner:
                return {}
            res = {}
            pairs = re.findall(r"([a-zA-Z0-9_\-]+)\s*:\s*([^,}]+)", inner)
            for pk, pv in pairs:
                res[pk.strip()] = parse_value(pv)
            return res
        return v.strip("'\"")

    i = 0
    while i < len(cleaned_lines):
        indent, line = cleaned_lines[i]
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip()
            if v:
                root[k] = parse_value(v)
                i += 1
            else:
                # Nested list or dict
                i += 1
                if i < len(cleaned_lines) and cleaned_lines[i][0] > indent:
                    nested_indent = cleaned_lines[i][0]
                    if cleaned_lines[i][1].startswith("-"):
                        # List items
                        items = []
                        while i < len(cleaned_lines) and cleaned_lines[i][0] >= nested_indent:
                            item_line = cleaned_lines[i][1]
                            if item_line.startswith("-"):
                                item_val = item_line[1:].strip()
                                if ":" in item_val:
                                    # Dict in list
                                    sub_dict = {}
                                    sk, sv = item_val.split(":", 1)
                                    sub_dict[sk.strip()] = parse_value(sv)
                                    # Check for further indented keys
                                    i += 1
                                    while i < len(cleaned_lines) and cleaned_lines[i][0] > nested_indent:
                                        if ":" in cleaned_lines[i][1] and not cleaned_lines[i][1].startswith("-"):
                                            ssk, ssv = cleaned_lines[i][1].split(":", 1)
                                            sub_dict[ssk.strip()] = parse_value(ssv)
                                        i += 1
                                    items.append(sub_dict)
                                    continue
                                else:
                                    items.append(parse_value(item_val))
                            i += 1
                        root[k] = items
                    else:
                        # Nested dict
                        nested_map = {}
                        while i < len(cleaned_lines) and cleaned_lines[i][0] >= nested_indent:
                            cur_line = cleaned_lines[i][1]
                            if ":" in cur_line and not cur_line.startswith("-"):
                                nk, nv = cur_line.split(":", 1)
                                nested_map[nk.strip()] = parse_value(nv)
                            i += 1
                        root[k] = nested_map
                else:
                    root[k] = None
        else:
            i += 1

    return root


class OKFLinter:
    def __init__(self, wiki_root: Path):
        self.wiki_root = wiki_root.resolve()
        self.repo_root = self.wiki_root.parent
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.all_concept_paths: Set[str] = set()
        self.all_concept_ids: Set[str] = set()
        self.concept_metadata: Dict[str, Dict[str, Any]] = {}
        self.title_to_paths: Dict[str, List[str]] = defaultdict(list)

    def run(self) -> bool:
        if not self.wiki_root.exists():
            self.errors.append(f"Wiki directory does not exist: {self.wiki_root}")
            self.print_report()
            return False

        # Phase 1: Gather all concept paths and read frontmatter
        for root, _, files in os.walk(self.wiki_root):
            for file in files:
                if file.endswith(".md"):
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(self.wiki_root).as_posix()
                    self.all_concept_paths.add(rel_path)
                    if file not in ("index.md", "log.md"):
                        concept_id = strip_md_suffix(rel_path)
                        self.all_concept_ids.add(concept_id)

                        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                            content = f.read()
                        fm, _ = self.extract_frontmatter(content)
                        if fm:
                            self.concept_metadata[concept_id] = fm
                            title = fm.get("title")
                            if title:
                                self.title_to_paths[title.strip()].append(rel_path)

        # Multi-user check: Duplicate Titles across different files
        for title, paths in self.title_to_paths.items():
            if len(paths) > 1:
                self.warnings.append(
                    f"Duplicate Concept Title detected: '{title}' is used in multiple files: {', '.join(paths)}"
                )

        # Phase 2: Lint each markdown file
        for rel_path_str in sorted(self.all_concept_paths):
            full_path = self.wiki_root / rel_path_str
            self.lint_file(full_path, rel_path_str)

        self.print_report()
        return len(self.errors) == 0

    def lint_file(self, full_path: Path, rel_path: str):
        filename = full_path.name

        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        if filename == "index.md":
            self.lint_index_file(full_path, rel_path, content)
            return

        if filename == "log.md":
            self.lint_log_file(full_path, rel_path, content)
            return

        self.lint_concept_document(full_path, rel_path, content)

    def lint_concept_document(self, full_path: Path, rel_path: str, content: str):
        # 1. Check YAML Frontmatter
        frontmatter, body = self.extract_frontmatter(content)
        if frontmatter is None:
            self.errors.append(f"[{rel_path}] Missing or invalid YAML Frontmatter (must start and end with '---').")
            return

        # 2. Check required `type` field (OKF v0.2 §4.1)
        type_val = frontmatter.get("type")
        if not type_val or not str(type_val).strip():
            self.errors.append(f"[{rel_path}] OKF Conformance Error: Required frontmatter key 'type' is missing or empty.")

        # 3. Check recommended fields
        if "title" not in frontmatter:
            self.warnings.append(f"[{rel_path}] Recommended frontmatter key 'title' is missing.")
        if "description" not in frontmatter:
            self.warnings.append(f"[{rel_path}] Recommended frontmatter key 'description' is missing.")

        # 4. Check status & memory tier
        status_val = frontmatter.get("status")
        if status_val and str(status_val).lower() not in VALID_STATUSES:
            self.warnings.append(
                f"[{rel_path}] Non-standard status '{status_val}'. Valid values: {', '.join(sorted(VALID_STATUSES))}."
            )

        tier_val = frontmatter.get("memory_tier")
        if tier_val and str(tier_val).lower() not in VALID_MEMORY_TIERS:
            self.warnings.append(
                f"[{rel_path}] Non-standard memory_tier '{tier_val}'. Valid tiers: {', '.join(sorted(VALID_MEMORY_TIERS))}."
            )

        decay_val = frontmatter.get("decay_rate")
        if decay_val and str(decay_val).lower() not in VALID_DECAY_RATES:
            self.warnings.append(
                f"[{rel_path}] Non-standard decay_rate '{decay_val}'. Valid values: {', '.join(sorted(VALID_DECAY_RATES))}."
            )

        # 5. Check Confidence Scoring
        conf_val = frontmatter.get("confidence")
        if conf_val is not None:
            if isinstance(conf_val, dict):
                base_s = conf_val.get("base_score")
                curr_s = conf_val.get("current_score")
                if base_s is not None:
                    try:
                        b_val = float(base_s)
                        if not (0.0 <= b_val <= 1.0):
                            self.errors.append(f"[{rel_path}] confidence.base_score ({b_val}) must be between 0.0 and 1.0.")
                    except ValueError:
                        self.errors.append(f"[{rel_path}] confidence.base_score is not a valid float: {base_s}")
                if curr_s is not None:
                    try:
                        c_val = float(curr_s)
                        if not (0.0 <= c_val <= 1.0):
                            self.errors.append(f"[{rel_path}] confidence.current_score ({c_val}) must be between 0.0 and 1.0.")
                    except ValueError:
                        self.errors.append(f"[{rel_path}] confidence.current_score is not a valid float: {curr_s}")
            else:
                try:
                    c_val = float(conf_val)
                    if not (0.0 <= c_val <= 1.0):
                        self.errors.append(f"[{rel_path}] confidence ({c_val}) must be between 0.0 and 1.0.")
                except ValueError:
                    self.errors.append(f"[{rel_path}] confidence is not a valid float: {conf_val}")

        # 6. Check Provenance (sources)
        sources_val = frontmatter.get("sources")
        source_ids: Set[str] = set()
        if sources_val:
            if isinstance(sources_val, list):
                for idx, src in enumerate(sources_val):
                    if isinstance(src, dict):
                        sid = src.get("id")
                        if sid:
                            source_ids.add(str(sid))
                        else:
                            self.warnings.append(f"[{rel_path}] sources[{idx}] is missing an 'id' field.")
                        if "resource" not in src:
                            self.warnings.append(f"[{rel_path}] sources[{idx}] is missing the required 'resource' field (OKF v0.2 §4.2).")
                    elif isinstance(src, str):
                        source_ids.add(str(idx + 1))
            else:
                self.warnings.append(f"[{rel_path}] 'sources' must be a list of provenance mappings.")

        # 7. Check Footnotes in Body
        footnotes_in_body = set(re.findall(r"\[\^([a-zA-Z0-9_\-]+)\]", body))
        for fn in footnotes_in_body:
            if fn.startswith("note-"):
                continue
            if source_ids and fn not in source_ids:
                self.warnings.append(
                    f"[{rel_path}] Footnote '[^{fn}]' in body has no matching source ID in frontmatter sources: {list(source_ids)}."
                )

        # 8. Check Graph Relations
        relations_val = frontmatter.get("relations")
        if relations_val and isinstance(relations_val, dict):
            for rkey, targets in relations_val.items():
                if rkey not in KNOWN_RELATION_KEYS:
                    self.warnings.append(
                        f"[{rel_path}] Unknown relation type '{rkey}'. Standard: {', '.join(sorted(KNOWN_RELATION_KEYS))}."
                    )
                if targets is None:
                    continue
                target_list = targets if isinstance(targets, list) else [targets]
                for tgt in target_list:
                    clean_tgt = strip_md_suffix(str(tgt))
                    if clean_tgt not in self.all_concept_ids:
                        self.warnings.append(
                            f"[{rel_path}] relation '{rkey}' references unknown concept ID: '{tgt}'."
                        )
                    else:
                        # Multi-user concurrency checks
                        target_fm = self.concept_metadata.get(clean_tgt, {})
                        target_status = target_fm.get("status", "active")
                        
                        # Warning if depending on a draft document
                        if rkey in ("depends_on", "implements") and target_status == "draft":
                            self.warnings.append(
                                f"[{rel_path}] relation '{rkey}' points to a DRAFT document: '{tgt}'. Drafts may change abruptly."
                            )

                if rkey == "contradicts" and targets:
                    self.warnings.append(
                        f"[{rel_path}] ⚠️ Contradiction flagged with: {', '.join(str(t) for t in target_list)}."
                    )
                    # Check if an ADR is linked in relations or body
                    has_adr = any("05_decisions" in str(tgt) or "adr" in str(tgt).lower() for tgt in target_list)
                    if not has_adr and "05_decisions" not in body and "adr" not in body.lower():
                        self.warnings.append(
                            f"[{rel_path}] Contradiction with {target_list} has no associated ADR referenced. Please file an ADR in wiki/05_decisions/."
                        )

        # 9. Check supersession references (OKF v0.2 §5.2)
        supersedes_val = frontmatter.get("supersedes")
        if supersedes_val:
            items = supersedes_val if isinstance(supersedes_val, list) else [supersedes_val]
            for target_id in items:
                clean_id = strip_md_suffix(str(target_id))
                if clean_id not in self.all_concept_ids:
                    self.warnings.append(
                        f"[{rel_path}] 'supersedes' references unknown concept ID: '{target_id}'."
                    )

        superseded_by_val = frontmatter.get("superseded_by")
        if superseded_by_val:
            clean_id = strip_md_suffix(str(superseded_by_val))
            if clean_id not in self.all_concept_ids:
                self.warnings.append(
                    f"[{rel_path}] 'superseded_by' references unknown concept ID: '{superseded_by_val}'."
                )

        # 10. Check links in body
        self.check_links(full_path, rel_path, body)

    def lint_index_file(self, full_path: Path, rel_path: str, content: str):
        parent_dir = full_path.parent
        dir_files = [
            f.name for f in parent_dir.iterdir()
            if f.is_file() and f.name.endswith(".md") and f.name not in ("index.md", "log.md")
        ]
        sub_dirs = [
            d.name for d in parent_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".") and d.name != ".changelogs"
        ]

        for doc in dir_files:
            if doc not in content and doc[:-3] not in content:
                self.warnings.append(f"[{rel_path}] Concept file '{doc}' is not indexed in {rel_path}.")

        for sdir in sub_dirs:
            if sdir not in content:
                self.warnings.append(f"[{rel_path}] Subdirectory '{sdir}' is not referenced in {rel_path}.")

    def lint_log_file(self, full_path: Path, rel_path: str, content: str):
        if not re.search(r"##\s+\d{4}-\d{2}-\d{2}", content):
            self.warnings.append(f"[{rel_path}] log.md does not contain ISO date headings (e.g. '## YYYY-MM-DD').")

    def extract_frontmatter(self, content: str) -> Tuple[Optional[dict], str]:
        pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(pattern, content, re.DOTALL)
        if not match:
            return None, content
        fm_text, body = match.groups()
        if HAVE_YAML:
            try:
                parsed = yaml.safe_load(fm_text)
                return (parsed if isinstance(parsed, dict) else {}), body
            except Exception as e:
                self.errors.append(f"YAML parsing error: {e}")
                return None, body
        else:
            parsed = parse_yaml_subset(fm_text)
            return parsed, body

    def check_links(self, full_path: Path, rel_path: str, body: str):
        md_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", body)
        for text, link in md_links:
            if (
                link.startswith("http://")
                or link.startswith("https://")
                or link.startswith("#")
                or link.startswith("mailto:")
            ):
                continue

            clean_target = link.split("#")[0].split("?")[0]
            if not clean_target:
                continue

            if clean_target.startswith("/"):
                target_full = self.wiki_root / clean_target.lstrip("/")
            elif clean_target.startswith("raw/"):
                target_full = self.repo_root / clean_target
            else:
                target_full = (full_path.parent / clean_target).resolve()

            if not target_full.exists():
                alt_target = self.repo_root / clean_target
                if not alt_target.exists():
                    self.warnings.append(
                        f"[{rel_path}] Ghost / Unresolved Link: '{link}' (target file not found)."
                    )

        wiki_links = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", body)
        for wlink in wiki_links:
            wlink_clean = wlink.strip()
            found = any(
                p.endswith(f"{wlink_clean}.md")
                or p.endswith(f"{wlink_clean}")
                or p == f"{wlink_clean}.md"
                for p in self.all_concept_paths
            )
            if not found:
                self.warnings.append(
                    f"[{rel_path}] Ghost Wiki Link: '[[{wlink}]]' (no matching concept found)."
                )

    def print_report(self):
        print("\n" + "=" * 68)
        print("🔍 Google OKF v0.2 & LLM Wiki v2 Lint Report")
        print("=" * 68)

        if not self.errors and not self.warnings:
            print("✅ All Wiki documents are fully conformant with OKF v0.2 & LLM Wiki v2! (0 errors, 0 warnings)")
            return

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for err in self.errors:
                print(f"  • {err}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warn in self.warnings:
                print(f"  • {warn}")

        print("\n" + "-" * 68)
        if self.errors:
            print(f"Result: FAILED (Errors must be resolved for strict OKF v0.2 conformance).")
        else:
            print(f"Result: PASSED with {len(self.warnings)} warning(s).")
        print("-" * 68 + "\n")


if __name__ == "__main__":
    target_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("wiki")
    linter = OKFLinter(target_dir)
    success = linter.run()
    sys.exit(0 if success else 1)
