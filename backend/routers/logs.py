"""Logs router."""

from typing import Optional

from fastapi import APIRouter, Query
from sqlalchemy import text

from db.connection import get_db

router = APIRouter(tags=["logs"])


@router.get("/logs")
async def list_logs(
    target_type: Optional[str] = Query(None),
    target_id: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=200),
):
    """Return operation logs with optional filters.

    Args:
        target_type: Filter by target type (segment, chapter, book)
        target_id: Filter by target ID
        limit: Number of records to return (default 20)
    """
    conditions = []
    params: dict = {"limit": limit}

    if target_type:
        conditions.append("target_type = :target_type")
        params["target_type"] = target_type

    if target_id is not None:
        conditions.append("target_id = :target_id")
        params["target_id"] = target_id

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    with get_db() as conn:
        rows = conn.execute(
            text(
                f"SELECT id, operator_token, operator_role, action, target_type, "
                f"target_id, before_status, after_status, extra, created_at "
                f"FROM tts2mp3_operation_logs "
                f"{where_clause} "
                f"ORDER BY created_at DESC "
                f"LIMIT :limit"
            ),
            params
        ).fetchall()

    result = []
    for row in rows:
        d = dict(row._mapping)
        d["created_at"] = str(d["created_at"])
        result.append(d)
    return result
