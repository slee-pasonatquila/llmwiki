"""
convert_anydoc.py - Automated document conversion & cleanup pipeline for LLM Wiki

Supported Formats:
  - Excel (.xlsx, .xls, .csv)
  - PDF (.pdf)
  - Word (.docx)
  - PowerPoint (.pptx)
  - Text & Markdown (.txt, .md, .sql, .json, .yaml, .yml)

Workflow:
  1. Uses `anydoc` CLI (if installed) or native Python parsers (openpyxl/pandas/pypdf/docx) to extract Markdown.
  2. Applies `table_cleaner.py` to remove empty cells, empty columns, and redundant whitespace.
  3. Outputs clean Markdown ready for Google OKF Ingestion.
"""

import os
import sys
import subprocess
import shutil
import argparse
from pathlib import Path
from table_cleaner import clean_markdown_content


def convert_via_anydoc_cli(input_path: Path) -> str:
    """Attempt conversion using the anydoc CLI if installed."""
    anydoc_bin = shutil.which("anydoc") or shutil.which("npx")
    if not anydoc_bin:
        raise RuntimeError("anydoc CLI / npx not found in PATH.")

    cmd = ["anydoc", str(input_path)] if shutil.which("anydoc") else ["npx", "-y", "anydoc", str(input_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout


def convert_excel_fallback(input_path: Path) -> str:
    """Fallback Excel to Markdown conversion with sheet headers."""
    try:
        import pandas as pd
        excel_file = pd.ExcelFile(input_path)
        markdown_sections = [f"# Document: {input_path.name}\n"]
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            # Drop columns and rows that are completely empty
            df = df.dropna(how="all").dropna(axis=1, how="all")
            if not df.empty:
                markdown_sections.append(f"## Sheet: {sheet_name}\n")
                markdown_sections.append(df.to_markdown(index=False))
                markdown_sections.append("\n")
        return "\n".join(markdown_sections)
    except ImportError:
        # Simple text fallback if pandas not installed
        return f"# Excel Document: {input_path.name}\n\n*(Please install pandas or openpyxl, or anydoc for full Excel extraction)*\n"


def convert_text_file(input_path: Path) -> str:
    """Read plain text, SQL, Markdown files."""
    with open(input_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    if input_path.suffix.lower() == ".sql":
        return f"# SQL Script: {input_path.name}\n\n```sql\n{content}\n```\n"
    return content


def convert_file(input_path: Path) -> str:
    """Dispatch file to best available converter."""
    suffix = input_path.suffix.lower()

    # Try anydoc first for rich binary formats
    if suffix in [".docx", ".pptx", ".pdf", ".xlsx", ".xls"]:
        try:
            raw_md = convert_via_anydoc_cli(input_path)
            if raw_md and len(raw_md.strip()) > 0:
                return clean_markdown_content(raw_md)
        except Exception:
            pass  # Fallback to python parsers

    if suffix in [".xlsx", ".xls", ".csv"]:
        raw_md = convert_excel_fallback(input_path)
    elif suffix in [".txt", ".md", ".sql", ".json", ".yaml", ".yml"]:
        raw_md = convert_text_file(input_path)
    else:
        # Generic text read
        try:
            raw_md = convert_text_file(input_path)
        except Exception as e:
            raw_md = f"# Document: {input_path.name}\n\nError reading file: {e}\n"

    return clean_markdown_content(raw_md)


def main():
    parser = argparse.ArgumentParser(description="Convert documents to cleaned Markdown for LLM Wiki.")
    parser.add_argument("input", help="Path to input file or directory")
    parser.add_argument("-o", "--output", help="Output file or directory path")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} does not exist.")
        sys.exit(1)

    if input_path.is_file():
        cleaned_md = convert_file(input_path)
        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(cleaned_md)
            print(f"Successfully converted and cleaned: {input_path} -> {out_path}")
        else:
            print(cleaned_md)
    elif input_path.is_dir():
        out_dir = Path(args.output) if args.output else input_path.parent / (input_path.name + "_cleaned_md")
        out_dir.mkdir(parents=True, exist_ok=True)
        for root, _, files in os.walk(input_path):
            for file in files:
                if file.startswith("."):
                    continue
                file_path = Path(root) / file
                rel_path = file_path.relative_to(input_path)
                target_md = out_dir / rel_path.with_suffix(".md")
                target_md.parent.mkdir(parents=True, exist_ok=True)
                cleaned_md = convert_file(file_path)
                with open(target_md, "w", encoding="utf-8") as f:
                    f.write(cleaned_md)
                print(f"Converted: {file_path} -> {target_md}")


if __name__ == "__main__":
    main()
