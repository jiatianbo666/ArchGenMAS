"""SQLite 历史记录持久化"""
import aiosqlite
from pathlib import Path
from datetime import datetime
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "data" / "history.db"


async def get_db() -> aiosqlite.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    await db.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            project_id   TEXT PRIMARY KEY,
            project_name TEXT DEFAULT '',
            filename     TEXT DEFAULT '',
            content_preview TEXT DEFAULT '',
            architecture_style TEXT DEFAULT '',
            review_score REAL,
            risk_level   TEXT DEFAULT '',
            iteration    INTEGER DEFAULT 0,
            stage        TEXT DEFAULT 'running',
            created_at   TEXT DEFAULT '',
            updated_at   TEXT DEFAULT ''
        )
    """)
    await db.commit()
    return db


async def save_project(
    project_id: str,
    project_name: str = "",
    filename: str = "",
    content_preview: str = "",
    architecture_style: str = "",
    review_score: Optional[float] = None,
    risk_level: str = "",
    iteration: int = 0,
    stage: str = "running",
) -> None:
    now = datetime.now().isoformat()
    db = await get_db()
    await db.execute("""
        INSERT INTO projects (project_id, project_name, filename, content_preview,
            architecture_style, review_score, risk_level, iteration, stage, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(project_id) DO UPDATE SET
            project_name = COALESCE(NULLIF(?, ''), project_name),
            architecture_style = COALESCE(NULLIF(?, ''), architecture_style),
            review_score = COALESCE(?, review_score),
            risk_level = COALESCE(NULLIF(?, ''), risk_level),
            iteration = COALESCE(?, iteration),
            stage = ?,
            updated_at = ?
    """, (
        project_id, project_name, filename, content_preview,
        architecture_style, review_score, risk_level, iteration, stage, now, now,
        # ON CONFLICT update values
        project_name, architecture_style, review_score, risk_level, iteration, stage, now,
    ))
    await db.commit()
    await db.close()


async def update_project(project_id: str, **kwargs) -> None:
    if not kwargs:
        return
    sets = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [datetime.now().isoformat(), project_id]
    db = await get_db()
    await db.execute(f"UPDATE projects SET {sets}, updated_at = ? WHERE project_id = ?", values)
    await db.commit()
    await db.close()


async def list_projects(page: int = 1, size: int = 20) -> list[dict]:
    db = await get_db()
    offset = (page - 1) * size
    cursor = await db.execute(
        "SELECT * FROM projects ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (size, offset),
    )
    rows = await cursor.fetchall()
    await db.close()
    return [dict(r) for r in rows]


async def count_projects() -> int:
    db = await get_db()
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM projects")
    row = await cursor.fetchone()
    await db.close()
    return row["cnt"] if row else 0


async def get_project(project_id: str) -> Optional[dict]:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,))
    row = await cursor.fetchone()
    await db.close()
    return dict(row) if row else None


async def delete_project(project_id: str) -> bool:
    db = await get_db()
    cursor = await db.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
    await db.commit()
    deleted = cursor.rowcount > 0
    await db.close()
    return deleted
