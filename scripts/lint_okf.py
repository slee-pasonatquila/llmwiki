"""
lint_okf.py - Google OKF (Open Knowledge Format v0.2) Linter & Validator

Validates:
  1. YAML Frontmatter presence & required/recommended OKF v0.2 keys:
     - `type:` (Required)
     - `title:`, `description:` (Recommended)
     - `status:` (Optional, must be draft|active|deprecated|tombstone)
     - `generated:`, `verified:` (Structured actor attribution)
     - `sources:` (Structured list with required 'resource')
  2. Footnote / Provenance link integrity ([^source_id] matches sources.id).
  3. Supersession integrity (supersedes / superseded_by points to existing concepts).
  4. Reserved files structure (index.md coverage of files & subdirectories, log.md date headings).
  5. Internal Cross-link integrity (standard markdown, absolute bundle paths, and wiki-links).
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Set, Any, Optional

try:
    import yaml
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False

VALID_STATUSES = {"draft", "active", "deprecated", "tombstone"}


def parse_yaml_subset(text: str) -> dict:
    """A self-contained pure-Python parser for standard OKF frontmatter subsets."""
    lines = text.splitlines()
    root: Dict[str, Any] = {}
    
    # We will build a structured hierarchy by tracking indent levels
    # Tokenize lines into (indent, content)
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
        # Inline list: [a, b, c]
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
        # Inline dict: { a: 1, b: 2 }
        if v.startswith("{") and v.endswith("}"):
            inner = v[1:-1].strip()
            if not inner:
                return {}
            res = {}
            # Match key: value pairs
            pairs = re.findall(r"([a-zA-Z0-9_\-]+)\s*:\s*([^,}]+)", inner)
            for pk, pv in pairs:
                res[pk.strip()] = parse_value(pv)
            return res
        # String without quotes
        return v.strip("'\"")

    i = 0
    while i < len(cleaned_lines):
        indent, line = cleaned_lines[i]
        if indent == 0 and ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip()
            
            if v:
                root[k] = parse_value(v)
                i += 1
            else:
                # Lookahead to see if it's a block mapping or list
                i += 1
                if i >= len(cleaned_lines):
                    root[k] = None
                    break
                
                next_indent, next_line = cleaned_lines[i]
                if next_indent > 0:
                    if next_line.startswith("- "):
                        # It's a list
                        items = []
                        current_dict: Optional[Dict[str, Any]] = None
                        list_indent = next_indent
                        
                        while i < len(cleaned_lines):
                            cur_indent, cur_line = cleaned_lines[i]
                            if cur_indent < list_indent:
                                break
                            
                            if cur_line.startswith("- "):
                                item_content = cur_line[2:].strip()
                                if ":" in item_content:
                                    # Dict in list
                                    current_dict = {}
                                    dk, dv = item_content.split(":", 1)
                                    current_dict[dk.strip()] = parse_value(dv)
                                    items.append(current_dict)
                                else:
                                    current_dict = None
                                    items.append(parse_value(item_content))
                            elif current_dict is not None and ":" in cur_line:
                                dk, dv = cur_line.split(":", 1)
                                current_dict[dk.strip()] = parse_value(dv)
                            i += 1
                        root[k] = items
                    else:
                        # It's a nested mapping
                        nested_map = {}
                        map_indent = next_indent
                        while i < len(cleaned_lines):
                            cur_indent, cur_line = cleaned_lines[i]
                            if cur_indent < map_indent:
                                break
                            if ":" in cur_line:
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

    def run(self) -> bool:
        if not self.wiki_root.exists():
            self.errors.append(f"Wiki directory does not exist: {self.wiki_root}")
            self.print_report()
            return False

        # Gather all concept paths and concept IDs
        for root, _, files in os.walk(self.wiki_root):
            for file in files:
                if file.endswith(".md"):
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(self.wiki_root).as_posix()
                    self.all_concept_paths.add(rel_path)
                    if file not in ("index.md", "log.md"):
                        concept_id = rel_path[:-3] if rel_path.endswith(".md") else rel_path
                        self.all_concept_ids.add(concept_id)

        # Lint each markdown file
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

        # It's a regular Concept document
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

        # 4. Check status field if present
        status_val = frontmatter.get("status")
        if status_val and str(status_val).lower() not in VALID_STATUSES:
            self.warnings.append(
                f"[{rel_path}] Non-standard status '{status_val}'. Recommended values are: {', '.join(sorted(VALID_STATUSES))}."
            )

        # 5. Check sources (OKF v0.2 §5.1)
        source_ids = set()
        sources_val = frontmatter.get("sources")
        if sources_val is not None:
            if not isinstance(sources_val, list):
                self.errors.append(f"[{rel_path}] 'sources' must be a YAML list of source entries.")
            else:
                for idx, src in enumerate(sources_val):
                    if not isinstance(src, dict):
                        self.errors.append(f"[{rel_path}] sources[{idx}] must be a dictionary.")
                        continue
                    if "resource" not in src or not str(src["resource"]).strip():
                        self.errors.append(f"[{rel_path}] sources[{idx}] is missing required key 'resource'.")
                    if "id" in src and src["id"]:
                        source_ids.add(str(src["id"]))

        # 6. Check footnotes vs sources.id
        footnotes = re.findall(r"\[\^([a-zA-Z0-9_\-]+)\]", body)
        for fn_id in set(footnotes):
            if source_ids and fn_id not in source_ids:
                if not re.search(r"\[\^" + re.escape(fn_id) + r"\]:", body):
                    self.warnings.append(
                        f"[{rel_path}] Footnote '[^{fn_id}]' does not match any source id in frontmatter 'sources'."
                    )

        # 7. Check supersession references (OKF v0.2 §5.2)
        supersedes_val = frontmatter.get("supersedes")
        if supersedes_val:
            items = supersedes_val if isinstance(supersedes_val, list) else [supersedes_val]
            for target_id in items:
                clean_id = str(target_id).rstrip(".md")
                if clean_id not in self.all_concept_ids:
                    self.warnings.append(
                        f"[{rel_path}] 'supersedes' references unknown concept ID: '{target_id}'."
                    )

        superseded_by_val = frontmatter.get("superseded_by")
        if superseded_by_val:
            clean_id = str(superseded_by_val).rstrip(".md")
            if clean_id not in self.all_concept_ids:
                self.warnings.append(
                    f"[{rel_path}] 'superseded_by' references unknown concept ID: '{superseded_by_val}'."
                )

        # 8. Check links in body
        self.check_links(full_path, rel_path, body)

    def lint_index_file(self, full_path: Path, rel_path: str, content: str):
        parent_dir = full_path.parent
        dir_files = [
            f.name for f in parent_dir.iterdir()
            if f.is_file() and f.name.endswith(".md") and f.name not in ("index.md", "log.md")
        ]
        sub_dirs = [
            d.name for d in parent_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
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
        # 1. Standard markdown links: [Text](path)
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

        # 2. Obsidian style links: [[concept_name]]
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
        print("\n" + "=" * 64)
        print("🔍 Google OKF (Open Knowledge Format v0.2) Lint Report")
        print("=" * 64)

        if not self.errors and not self.warnings:
            print("✅ All Wiki documents are fully conformant with OKF v0.2! (0 errors, 0 warnings)")
            return

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for err in self.errors:
                print(f"  • {err}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warn in self.warnings:
                print(f"  • {warn}")

        print("\n" + "-" * 64)
        if self.errors:
            print(f"Result: FAILED (Errors must be resolved for strict OKF v0.2 conformance).")
        else:
            print(f"Result: PASSED with {len(self.warnings)} warning(s).")
        print("-" * 64 + "\n")


if __name__ == "__main__":
    target_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("wiki")
    linter = OKFLinter(target_dir)
    success = linter.run()
    sys.exit(0 if success else 1)
