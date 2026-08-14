#!/usr/bin/env python3
"""
sync_wiki.py - LLM Wiki Synchronizer

LLM Wiki 内の派生成果物（Index, Changelog, Knowledge Graph）を
ワンコマンドで一括生成・最新状態に同期します。
ローカル開発時の同期および CI/CD パイプラインでの自動更新で使用されます。
"""

import sys
import subprocess
from pathlib import Path


def run_step(title: str, script_name: str, args: list = None):
    print(f"\n▶ [{title}] Running {script_name}...")
    script_path = Path(__file__).parent / script_name
    cmd = [sys.executable, str(script_path)] + (args or [])
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print(f"❌ Error during {title} (exit code: {res.returncode})")
        return False
    return True


def main():
    wiki_dir = "wiki"
    print("==================================================")
    print(" 🚀 LLM Wiki Synchronization Pipeline")
    print("==================================================")

    # Step 1: Build Indexes
    if not run_step("1/3 Build Category & Master Indexes", "build_indexes.py", [wiki_dir]):
        sys.exit(1)

    # Step 2: Aggregate Changelogs
    if not run_step("2/3 Aggregate Changelogs", "build_changelog.py"):
        sys.exit(1)

    # Step 3: Build Knowledge Graph
    if not run_step("3/3 Build Knowledge Graph (JSON & Mermaid)", "build_graph.py", [wiki_dir]):
        sys.exit(1)

    print("\n==================================================")
    print(" ✅ All Wiki artifacts successfully synchronized!")
    print("==================================================")


if __name__ == "__main__":
    main()
