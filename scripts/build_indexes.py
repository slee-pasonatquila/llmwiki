#!/usr/bin/env python3
"""
build_indexes.py - LLM Wiki Index Generator

wiki/ 配下の各カテゴリディレクトリおよびマスター index.md を、
各 Markdown ファイルの OKF Frontmatter から自動走査・生成します。
これにより、手動編集による Git コンフリクトを完全に防止します。
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Any

try:
    import yaml
except ImportError:
    print("Warning: PyYAML not found, using basic regex parser.")
    yaml = None

CATEGORY_METADATA = {
    "01_customer_requests": {
        "title": "顧客要望 (Customer Requests)",
        "description": "クライアントからのヒアリング内容、課題、ビジネス目標、RFP、初期要望に関する構造化ナレッジです。"
    },
    "02_requirements": {
        "title": "要件定義 (Requirements)",
        "description": "機能要件、非機能要件、業務フロー、受け入れ基準、制約事項に関する構造化ナレッジです。"
    },
    "03_basic_designs": {
        "title": "概要設計 (Basic / Architecture Designs)",
        "description": "システム全体構成、認証・認可アーキテクチャ、インフラ構成、ドメインモデルに関する構造化ナレッジです。"
    },
    "04_detailed_designs": {
        "title": "詳細設計 (Detailed Designs)",
        "description": "データベーステーブル定義 (DDL/スキーマ)、API エンドポイント仕様、詳細ロジック、UI 仕様に関する構造化ナレッジです。"
    },
    "05_decisions": {
        "title": "設計決定記録 (Architecture Decision Records - ADR)",
        "description": "技術選定、アーキテクチャ決定の背景、トレードオフ検討、決定理由 (ADR) に関する記録です。"
    },
    "99_others": {
        "title": "その他・用語集 (Others & Glossary)",
        "description": "プロジェクト用語集、議事録、運用マニュアル、その他リファレンス情報です。"
    }
}


def parse_frontmatter(file_path: Path) -> Dict[str, Any]:
    content = file_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    fm_str = parts[1]
    if yaml:
        try:
            return yaml.safe_load(fm_str) or {}
        except Exception:
            pass
    # Fallback basic parser
    data = {}
    for line in fm_str.split("\n"):
        if ":" in line and not line.strip().startswith("-") and not line.strip().startswith("#"):
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def generate_category_index(cat_dir: Path, cat_info: Dict[str, str]) -> None:
    docs = []
    for doc in sorted(cat_dir.glob("*.md")):
        if doc.name in ("index.md", "README.md"):
            continue
        fm = parse_frontmatter(doc)
        title = fm.get("title", doc.stem.replace("_", " ").title())
        tier = fm.get("memory_tier", "semantic")
        status = fm.get("status", "active")
        updated_at = fm.get("updated_at", "")
        summary = fm.get("summary", "")
        if not summary:
            content = doc.read_text(encoding="utf-8")
            body = content.split("---", 2)[2] if content.startswith("---") and len(content.split("---", 2)) >= 3 else content
            lines = [l.strip() for l in body.split("\n") if l.strip() and not l.startswith("#")]
            summary = lines[0][:80] + "..." if lines else ""

        docs.append({
            "file": doc.name,
            "title": title,
            "tier": tier,
            "status": status,
            "updated_at": updated_at,
            "summary": summary
        })

    lines = [
        f"# {cat_info['title']}",
        "",
        cat_info["description"],
        "",
        "## コンセプト一覧",
        "",
        "| ドキュメント | メモリ階層 | ステータス | 概要 |",
        "| :--- | :--- | :--- | :--- |"
    ]

    for d in docs:
        status_badge = f"`{d['status']}`" if d['status'] != 'active' else "active"
        lines.append(f"| [{d['title']}]({d['file']}) | `{d['tier']}` | {status_badge} | {d['summary']} |")

    lines.extend([
        "",
        "---",
        "* [戻る: マスターインデックス](../index.md)",
        ""
    ])

    index_path = cat_dir / "index.md"
    index_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [Index] Updated {index_path.name} in {cat_dir.name} ({len(docs)} documents)")


def generate_master_index(wiki_dir: Path) -> None:
    lines = [
        "# LLM Wiki Master Index",
        "",
        "本ドキュメントは、プロジェクト全体の構造化ナレッジ（Google OKF v0.2 準拠）を一覧化したマスターインデックスです。",
        "段階的な知識開示（Progressive Disclosure）を支援し、人間と AI エージェントが目的の設計・仕様に迅速にアクセスできるように自動生成されます。",
        "",
        "---",
        "",
        "## ナレッジカテゴリ一覧",
        ""
    ]

    for dir_name, cat_info in CATEGORY_METADATA.items():
        cat_dir = wiki_dir / dir_name
        if cat_dir.exists():
            doc_count = len([f for f in cat_dir.glob("*.md") if f.name not in ("index.md", "README.md")])
            lines.append(f"* [{cat_info['title']}]({dir_name}/index.md) - {cat_info['description']} *(計 {doc_count} 件)*")

    lines.extend([
        "",
        "---",
        "",
        "## 運用リンク",
        "* [全体更新履歴 (Changelog)](log.md)",
        "* [Wiki 編纂ルール (SCHEMA.md)](../SCHEMA.md)",
        ""
    ])

    master_index_path = wiki_dir / "index.md"
    master_index_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [Master Index] Updated {master_index_path.name}")


def main():
    wiki_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("wiki")
    if not wiki_dir.exists():
        print(f"Error: Directory {wiki_dir} does not exist.")
        sys.exit(1)

    print(f"Generating Wiki Indexes for: {wiki_dir.resolve()}")
    for dir_name, cat_info in CATEGORY_METADATA.items():
        cat_dir = wiki_dir / dir_name
        if cat_dir.exists() and cat_dir.is_dir():
            generate_category_index(cat_dir, cat_info)

    generate_master_index(wiki_dir)
    print("✓ All indexes successfully generated.")


if __name__ == "__main__":
    main()
