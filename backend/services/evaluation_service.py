"""Segment evaluation service: state machine logic."""

import json
from typing import List, Optional, Dict, Any

from sqlalchemy import text

from db.connection import get_db


def evaluate_segment(
    segment_id: int,
    can_use: bool,
    badcase_tags: Optional[List[str]],
    modified_text: Optional[str],
    annotation: Optional[str],
    operator_token: Optional[str] = None,
    operator_role: Optional[str] = None,
) -> Dict[str, Any]:
    """Evaluate a segment and update its status.

    Args:
        segment_id: Target segment ID
        can_use: True → passed, False → needs_polish
        badcase_tags: Required when can_use is False
        modified_text: Annotator's corrected text
        annotation: Annotator's notes
        operator_token: Auth token of submitter
        operator_role: Role of submitter

    Returns:
        Dict with new status

    Raises:
        ValueError: If can_use=False but badcase_tags is empty/None
        ValueError: If segment not found
    """
    if not can_use and not badcase_tags:
        raise ValueError("badcase_tags is required when can_use is False")

    new_status = "passed" if can_use else "needs_polish"

    with get_db() as conn:
        # Fetch segment
        segment = conn.execute(
            text("SELECT * FROM tts2mp3_segments WHERE id = :id"),
            {"id": segment_id}
        ).fetchone()

        if segment is None:
            raise ValueError(f"Segment {segment_id} not found")

        seg = dict(segment._mapping)
        before_status = seg["status"]

        # Build update params
        update_params: Dict[str, Any] = {
            "id": segment_id,
            "new_status": new_status,
        }

        if not can_use:
            tags_json = json.dumps(badcase_tags, ensure_ascii=False)
            conn.execute(
                text(
                    "UPDATE tts2mp3_segments SET status=:new_status, "
                    "badcase_tags=:tags, modified_text=:modified_text, "
                    "annotation=:annotation, updated_at=NOW() "
                    "WHERE id=:id"
                ),
                {
                    "id": segment_id,
                    "new_status": new_status,
                    "tags": tags_json,
                    "modified_text": modified_text,
                    "annotation": annotation,
                }
            )
        else:
            conn.execute(
                text(
                    "UPDATE tts2mp3_segments SET status=:new_status, updated_at=NOW() "
                    "WHERE id=:id"
                ),
                {"id": segment_id, "new_status": new_status}
            )

        # Write operation log
        conn.execute(
            text(
                "INSERT INTO tts2mp3_operation_logs "
                "(operator_token, operator_role, action, target_type, target_id, "
                "before_status, after_status, extra) "
                "VALUES (:token, :role, 'evaluate', 'segment', :target_id, "
                ":before, :after, :extra)"
            ),
            {
                "token": operator_token,
                "role": operator_role,
                "target_id": segment_id,
                "before": before_status,
                "after": new_status,
                "extra": json.dumps({"can_use": can_use}, ensure_ascii=False),
            }
        )

        # Check chapter completion and trigger merge if ready
        chapter_id = seg["chapter_id"]
        _check_and_trigger_merge(conn, chapter_id)

    return {"segment_id": segment_id, "status": new_status}


def _check_and_trigger_merge(conn, chapter_id: int) -> None:
    """Check if chapter is fully complete and trigger merge."""
    row = conn.execute(
        text(
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN status IN ('passed','polish_uploaded') THEN 1 ELSE 0 END) AS completed "
            "FROM tts2mp3_segments WHERE chapter_id = :chapter_id"
        ),
        {"chapter_id": chapter_id}
    ).fetchone()

    if row is None:
        return

    d = dict(row._mapping)
    total = d.get("total") or 0
    completed = d.get("completed") or 0

    if total > 0 and total == completed:
        # Trigger merge asynchronously by importing merge service
        # We do this in a separate connection to avoid nested transaction issues
        try:
            from services.merge_service import merge_chapter
            merge_chapter(chapter_id)
        except Exception:
            pass  # Merge failure is non-blocking for evaluation
