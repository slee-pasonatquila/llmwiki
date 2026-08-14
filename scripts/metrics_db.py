#!/usr/bin/env python3
"""
metrics_db.py - SQLite Metrics & Access Cache for LLM Wiki

ドキュメントのアクセスログ、検索ヒット履歴、忘却曲線の動的スコアを
Markdown の外部（wiki/.cache/metrics.db）に分離して管理します。
これにより、日常の検索や閲覧で Markdown ファイルに不要な Git 差分・コンフリクトが発生するのを防ぎます。
"""

import sqlite3
import math
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

DB_PATH = Path("wiki/.cache/metrics.db")


def get_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS document_metrics (
                concept_id TEXT PRIMARY KEY,
                base_score REAL DEFAULT 1.0,
                decay_rate TEXT DEFAULT 'standard',
                last_verified_at TEXT,
                last_accessed_at TEXT,
                access_count INTEGER DEFAULT 0,
                search_hit_count INTEGER DEFAULT 0,
                reinforced_count INTEGER DEFAULT 0,
                current_decayed_score REAL DEFAULT 1.0,
                updated_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept_id TEXT,
                action_type TEXT,
                query_text TEXT,
                actor TEXT,
                timestamp TEXT
            )
        """)


def record_access(concept_id: str, action_type: str = "view", query_text: str = "", actor: str = "user", db_path: Path = DB_PATH) -> None:
    conn = get_db(db_path)
    now_iso = datetime.now(timezone.utc).isoformat()
    with conn:
        conn.execute("""
            INSERT INTO access_logs (concept_id, action_type, query_text, actor, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (concept_id, action_type, query_text, actor, now_iso))

        if action_type == "search_hit":
            conn.execute("""
                INSERT INTO document_metrics (concept_id, search_hit_count, last_accessed_at, updated_at)
                VALUES (?, 1, ?, ?)
                ON CONFLICT(concept_id) DO UPDATE SET
                    search_hit_count = search_hit_count + 1,
                    last_accessed_at = excluded.last_accessed_at,
                    updated_at = excluded.updated_at
            """, (concept_id, now_iso, now_iso))
        elif action_type == "reinforce":
            conn.execute("""
                INSERT INTO document_metrics (concept_id, reinforced_count, last_verified_at, last_accessed_at, updated_at)
                VALUES (?, 1, ?, ?, ?)
                ON CONFLICT(concept_id) DO UPDATE SET
                    reinforced_count = reinforced_count + 1,
                    last_verified_at = excluded.last_verified_at,
                    last_accessed_at = excluded.last_accessed_at,
                    updated_at = excluded.updated_at
            """, (concept_id, now_iso, now_iso, now_iso))
        else: # view / read
            conn.execute("""
                INSERT INTO document_metrics (concept_id, access_count, last_accessed_at, updated_at)
                VALUES (?, 1, ?, ?)
                ON CONFLICT(concept_id) DO UPDATE SET
                    access_count = access_count + 1,
                    last_accessed_at = excluded.last_accessed_at,
                    updated_at = excluded.updated_at
            """, (concept_id, now_iso, now_iso))


def get_metrics(concept_id: str, db_path: Path = DB_PATH) -> Optional[Dict[str, Any]]:
    conn = get_db(db_path)
    row = conn.execute("SELECT * FROM document_metrics WHERE concept_id = ?", (concept_id,)).fetchone()
    return dict(row) if row else None


def update_decay_scores(half_life_map: Dict[str, float], default_half_life: float = 69.0, db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    conn = get_db(db_path)
    rows = conn.execute("SELECT * FROM document_metrics").fetchall()
    now = datetime.now(timezone.utc)
    results = []

    with conn:
        for r in rows:
            cid = r["concept_id"]
            base = r["base_score"] or 1.0
            last_date_str = r["last_verified_at"] or r["last_accessed_at"] or r["updated_at"]
            decay_rate = r["decay_rate"] or "standard"

            if decay_rate == "permanent":
                current_score = base
            else:
                half_life = half_life_map.get(decay_rate, default_half_life)
                if last_date_str:
                    try:
                        last_dt = datetime.fromisoformat(last_date_str.replace("Z", "+00:00"))
                        days = max(0.0, (now - last_dt).total_seconds() / 86400.0)
                    except Exception:
                        days = 0.0
                else:
                    days = 0.0

                decay_constant = math.log(2) / half_life
                current_score = max(0.1, round(base * math.exp(-decay_constant * days), 4))

            conn.execute(
                "UPDATE document_metrics SET current_decayed_score = ?, updated_at = ? WHERE concept_id = ?",
                (current_score, now.isoformat(), cid)
            )
            results.append({
                "concept_id": cid,
                "base_score": base,
                "current_decayed_score": current_score,
                "access_count": r["access_count"],
                "search_hit_count": r["search_hit_count"]
            })

    return results


if __name__ == "__main__":
    print(f"Initializing metrics database at: {DB_PATH.resolve()}")
    conn = get_db()
    print("✓ Schema initialized successfully.")
