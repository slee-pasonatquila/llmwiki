"""
table_cleaner.py - Markdown Table & Document Cleaner for LLM Wiki

Purpose:
  Cleans raw Markdown converted from Office (Excel/Word/PowerPoint), PDF, and text files.
  - Removes empty columns (columns with no content in any row).
  - Removes completely empty rows in tables.
  - Trims unnecessary leading/trailing whitespace inside table cells.
  - Normalizes excessive consecutive blank lines (max 2 consecutive newlines).
  - Cleans up common anydoc / HTML artifact tags (e.g. empty <br>, redundant spans).
"""

import re
import sys
from typing import List, Tuple


def clean_table_block(table_lines: List[str]) -> List[str]:
    """
    Cleans a single Markdown table block.
    Removes empty rows, empty columns, and normalizes cell whitespace.
    """
    if not table_lines:
        return []

    # Parse table rows into cells
    parsed_rows: List[List[str]] = []
    is_delimiter_row = []

    for line in table_lines:
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            # If a line in table block doesn't start/end with |, wrap it or keep
            cells = [c.strip() for c in stripped.split("|")]
            if cells and cells[0] == "":
                cells = cells[1:]
            if cells and cells[-1] == "":
                cells = cells[:-1]
        else:
            # Strip outer '|' and split
            inner = stripped[1:-1]
            cells = [c.strip() for c in inner.split("|")]

        # Check if delimiter row (e.g. :---, ---:, :---:)
        is_delim = all(re.match(r"^:?-+:?$", c) is not None for c in cells) if cells else False
        is_delimiter_row.append(is_delim)
        parsed_rows.append(cells)

    if not parsed_rows:
        return table_lines

    # Normalize row lengths to the maximum column count
    max_cols = max(len(row) for row in parsed_rows)
    for row in parsed_rows:
        while len(row) < max_cols:
            row.append("")

    # Determine which columns have non-empty content in at least one non-delimiter row
    valid_col_indices = []
    for col_idx in range(max_cols):
        has_content = False
        for row_idx, row in enumerate(parsed_rows):
            if not is_delimiter_row[row_idx]:
                cell_val = row[col_idx].strip()
                # If cell has content other than html breaks or whitespace
                clean_val = re.sub(r"<br\s*/?>|&nbsp;|\s+", "", cell_val)
                if clean_val:
                    has_content = True
                    break
        if has_content:
            valid_col_indices.append(col_idx)

    # If all columns are empty, discard table
    if not valid_col_indices:
        return []

    # Filter columns and remove completely empty rows
    cleaned_rows: List[str] = []
    for row_idx, row in enumerate(parsed_rows):
        filtered_cells = [row[c] for c in valid_col_indices]
        
        if is_delimiter_row[row_idx]:
            # Recreate delimiter cells
            delim_cells = []
            for c in filtered_cells:
                if re.match(r"^:?-+:?$", c):
                    delim_cells.append(c)
                else:
                    delim_cells.append("---")
            cleaned_rows.append("| " + " | ".join(delim_cells) + " |")
        else:
            # Check if this row has any content
            has_content = any(re.sub(r"<br\s*/?>|&nbsp;|\s+", "", c) for c in filtered_cells)
            if has_content:
                cleaned_rows.append("| " + " | ".join(filtered_cells) + " |")

    return cleaned_rows


def clean_markdown_content(content: str) -> str:
    """
    Cleans an entire Markdown string:
    - Identifies table blocks and cleans them using clean_table_block
    - Removes HTML trash
    - Collapses excessive blank lines
    """
    lines = content.splitlines()
    output_lines: List[str] = []
    
    in_table = False
    table_buffer: List[str] = []

    for line in lines:
        stripped = line.strip()
        # Check if line looks like a table row (starts and ends with | or has multiple |)
        is_table_row = (stripped.startswith("|") and stripped.endswith("|")) or (stripped.count("|") >= 2 and not stripped.startswith("```"))

        if is_table_row:
            in_table = True
            table_buffer.append(line)
        else:
            if in_table:
                # Process accumulated table
                cleaned_table = clean_table_block(table_buffer)
                output_lines.extend(cleaned_table)
                table_buffer = []
                in_table = False
            output_lines.append(line)

    if in_table and table_buffer:
        cleaned_table = clean_table_block(table_buffer)
        output_lines.extend(cleaned_table)

    text = "\n".join(output_lines)

    # Clean redundant html artifacts
    text = re.sub(r"<br\s*/?>\s*<br\s*/?>", "<br>", text)
    text = re.sub(r"&nbsp;", " ", text)
    
    # Strip trailing whitespace on each line
    text = "\n".join(l.rstrip() for l in text.splitlines())

    # Collapse 3 or more consecutive newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    return text.strip() + "\n"


if __name__ == "__main__":
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        with open(filepath, "r", encoding="utf-8") as f:
            raw_text = f.read()
        cleaned = clean_markdown_content(raw_text)
        if len(sys.argv) > 2:
            outpath = sys.argv[2]
            with open(outpath, "w", encoding="utf-8") as f:
                f.write(cleaned)
            print(f"Cleaned Markdown saved to {outpath}")
        else:
            print(cleaned)
    else:
        print("Usage: python table_cleaner.py <input.md> [output.md]")
