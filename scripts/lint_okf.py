"""
lint_okf.py - Google OKF (Open Knowledge Format v0.1) Linter & Validator

Validates:
  1. YAML Frontmatter presence & non-empty `type:` key in all non-reserved `.md` files.
  2. Reserved files structure (`index.md`, `log.md`).
  3. Internal Cross-link integrity (detects ghost/broken links).
  4. Citations formatting and presence (`# Citations`).
  5. Missing concepts in `index.md` (Progressive disclosure coverage).
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Set

try:
    import yaml
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False


class OKFLinter:
    def __init__(self, wiki_root: Path):
        self.wiki_root = wiki_root
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.all_concept_paths: Set[str] = set()

    def run(self) -> bool:
        if not self.wiki_root.exists():
            self.errors.append(f"Wiki directory does not exist: {self.wiki_root}")
            return False

        # Gather all concept paths
        for root, _, files in os.walk(self.wiki_root):
            for file in files:
                if file.endswith(".md"):
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(self.wiki_root).as_posix()
                    self.all_concept_paths.add(rel_path)

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
            self.errors.append(f"[{rel_path}] Missing YAML Frontmatter (must start and end with '---').")
            return

        # 2. Check required `type` field
        if "type" not in frontmatter or not str(frontmatter.get("type", "")).strip():
            self.errors.append(f"[{rel_path}] OKF Conformance Error: Required frontmatter key 'type' is missing or empty.")

        # 3. Check recommended fields
        if "title" not in frontmatter:
            self.warnings.append(f"[{rel_path}] Recommended frontmatter key 'title' is missing.")
        if "description" not in frontmatter:
            self.warnings.append(f"[{rel_path}] Recommended frontmatter key 'description' is missing.")

        # 4. Check links in body
        self.check_links(full_path, rel_path, body)

        # 5. Check Citations section
        if "# Citations" not in body and "## Citations" not in body:
            self.warnings.append(f"[{rel_path}] Missing '# Citations' section (recommended for grounding assertions in raw documents).")

    def lint_index_file(self, full_path: Path, rel_path: str, content: str):
        # index.md should have links to concepts in its directory
        parent_dir = full_path.parent
        dir_files = [f.name for f in parent_dir.iterdir() if f.is_file() and f.name.endswith(".md") and f.name != "index.md" and f.name != "log.md"]
        sub_dirs = [d.name for d in parent_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]

        for doc in dir_files:
            if doc not in content:
                self.warnings.append(f"[{rel_path}] Concept '{doc}' is not indexed in {rel_path}.")

        for sdir in sub_dirs:
            if sdir not in content:
                self.warnings.append(f"[{rel_path}] Subdirectory '{sdir}' is not referenced in {rel_path}.")

    def lint_log_file(self, full_path: Path, rel_path: str, content: str):
        if not re.search(r"##\s+\d{4}-\d{2}-\d{2}", content):
            self.warnings.append(f"[{rel_path}] log.md does not contain ISO date headings (e.g. '## YYYY-MM-DD').")

    def extract_frontmatter(self, content: str) -> Tuple[dict, str]:
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
            # Lightweight standard library parser for key: value
            parsed = {}
            for line in fm_text.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    k, v = line.split(":", 1)
                    k = k.strip()
                    v = v.strip()
                    if v.startswith("[") and v.endswith("]"):
                        items = [item.strip() for item in v[1:-1].split(",") if item.strip()]
                        parsed[k] = items
                    else:
                        # Strip quotes
                        v = v.strip("'\"")
                        parsed[k] = v
            return parsed, body

    def check_links(self, full_path: Path, rel_path: str, body: str):
        repo_root = self.wiki_root.parent
        # Markdown standard links: [Text](path.md)
        md_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", body)
        for text, link in md_links:
            if link.startswith("http://") or link.startswith("https://") or link.startswith("#") or link.startswith("mailto:"):
                continue

            # Strip query or anchor
            clean_target = link.split("#")[0]
            if not clean_target:
                continue

            # Resolve relative link
            if clean_target.startswith("/"):
                # Bundle-absolute link
                target_full = self.wiki_root / clean_target.lstrip("/")
            elif clean_target.startswith("raw/"):
                # Repo-relative link into raw directory
                target_full = repo_root / clean_target
            else:
                target_full = (full_path.parent / clean_target).resolve()

            if not target_full.exists():
                # Check if it exists relative to repo root
                alt_target = repo_root / clean_target
                if not alt_target.exists():
                    self.warnings.append(f"[{rel_path}] Ghost / Unresolved Link: '{link}' (target does not exist on disk).")

        # Obsidian style links: [[concept_name]]
        wiki_links = re.findall(r"\[\[([^\]]+)\]\]", body)
        for wlink in wiki_links:
            # Check if matching file exists anywhere
            found = any(p.endswith(f"{wlink}.md") or p.endswith(f"{wlink}") for p in self.all_concept_paths)
            if not found:
                self.warnings.append(f"[{rel_path}] Ghost Wiki Link: '[[{wlink}]]' (no matching .md file found).")

    def print_report(self):
        print("\n" + "=" * 60)
        print("🔍 Google OKF (Open Knowledge Format v0.1) Lint Report")
        print("=" * 60)

        if not self.errors and not self.warnings:
            print("✅ All Wiki documents are fully conformant with OKF v0.1! No issues found.")
            return

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for err in self.errors:
                print(f"  • {err}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warn in self.warnings:
                print(f"  • {warn}")

        print("\n" + "-" * 60)
        if self.errors:
            print(f"Result: FAILED (Errors must be resolved for OKF strict conformance).")
        else:
            print(f"Result: PASSED with warnings.")
        print("-" * 60 + "\n")


if __name__ == "__main__":
    target_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("wiki")
    linter = OKFLinter(target_dir)
    success = linter.run()
    sys.exit(0 if success else 1)
