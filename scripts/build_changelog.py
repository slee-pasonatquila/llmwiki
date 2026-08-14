#!/usr/bin/env python3
"""
build_changelog.py - LLM Wiki Distributed Changelog Aggregator

wiki/.changelogs/ 配下に保存された個別の JSON 断片ログを収集・ソートし、
単一の wiki/log.md を自動集約・再生成します。
これにより、複数人による log.md への同時書き込みコンフリクトを完全に排除します。
"""

import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


def load_changelog_fragments(changelogs_dir: Path) -> List[Dict[str, Any]]:
    entries = []
    if not changelogs_dir.exists():
        return entries

    for f in changelogs_dir.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(data, list):
                entries.extend(data)
            elif isinstance(data, dict):
                entries.append(data)
        except Exception as e:
            print(f"Warning: Failed to parse {f.name}: {e}")

    # Sort entries by date desc, then timestamp desc
    def sort_key(item):
        date_str = item.get("date", "1970-01-01")
        timestamp = item.get("timestamp", date_str)
        return (date_str, timestamp)

    entries.sort(key=sort_key, reverse=True)
    return entries


def render_log_md(entries: List[Dict[str, Any]]) -> str:
    lines = [
        "# Wiki Update Log",
        "",
        "本ファイルは、ナレッジベース全体の更新履歴を時系列（最新が上）で集約した自動生成ログです。",
        "個別エントリは `wiki/.changelogs/` 配下に分散管理されており、CI または `scripts/build_changelog.py` により自動統合されます。",
        "",
        "---",
        ""
    ]

    # Group by date
    grouped = {}
    for entry in entries:
        date_str = entry.get("date", "Unknown Date")
        if date_str not in grouped:
            grouped[date_str] = []
        grouped[date_str].append(entry)

    for date_str, items in grouped.items():
        lines.append(f"## {date_str}")
        for item in items:
            author = item.get("author", "unknown")
            action = item.get("action", "")
            details = item.get("details", [])
            lines.append(f"* **{author}**: {action}")
            for detail in details:
                lines.append(f"  - {detail}")
        lines.append("")

    return "\n".join(lines)


def add_fragment(changelogs_dir: Path, author: str, action: str, details: List[str]) -> Path:
    changelogs_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    safe_author = re.sub(r'[^a-zA-Z0-9_\-]', '_', author)
    filename = f"{timestamp}_{safe_author}.json"
    target = changelogs_dir / filename

    entry = {
        "date": date_str,
        "timestamp": now.isoformat(),
        "author": author,
        "action": action,
        "details": details
    }

    target.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Created changelog fragment: {target}")
    return target


def main():
    wiki_dir = Path("wiki")
    changelogs_dir = wiki_dir / ".changelogs"
    log_md_path = wiki_dir / "log.md"

    if len(sys.argv) > 1 and sys.argv[1] == "add":
        # Interactive / CLI add fragment
        # Usage: build_changelog.py add <author> <action> [details...]
        if len(sys.argv) < 4:
            print("Usage: build_changelog.py add <author> <action> [detail1 detail2...]")
            sys.exit(1)
        author = sys.argv[2]
        action = sys.argv[3]
        details = sys.argv[4:]
        add_fragment(changelogs_dir, author, action, details)
        return

    # Build / Aggregate mode
    entries = load_changelog_fragments(changelogs_dir)
    rendered = render_log_md(entries)
    log_md_path.write_text(rendered, encoding="utf-8")
    print(f"✓ Aggregated {len(entries)} changelog entries into {log_md_path.resolve()}")


if __name__ == "__main__":
    main()
