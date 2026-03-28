"""Chapter query service."""

from typing import List, Dict, Any, Optional

from sqlalchemy import text

from db.connection import get_db

COMPLETED_STATUSES = ("passed", "polish_uploaded")


def get_chapters_for_book(book_id: int) -> List[Dict[str, Any]]:
    """Return chapters for a book with completion_rate."""
    with get_db() as conn:
        rows = conn.execute(
            text(
                "SELECT c.id, c.book_id, c.chapter_no, c.title, c.status, "
                "c.output_path, c.created_at, c.updated_at, "
                "COUNT(s.id) AS total_segments, "
                "SUM(CASE WHEN s.status IN ('passed','polish_uploaded') THEN 1 ELSE 0 END) "
                "   AS completed_segments "
                "FROM tts2mp3_chapters c "
                "LEFT JOIN tts2mp3_segments s ON s.chapter_id = c.id "
                "WHERE c.book_id = :book_id "
                "GROUP BY c.id "
                "ORDER BY c.chapter_no"
            ),
            {"book_id": book_id}
        ).fetchall()

    result = []
    for row in rows:
        d = dict(row._mapping)
        total = d.get("total_segments") or 0
        completed = d.get("completed_segments") or 0
        d["completion_rate"] = (completed / total) if total > 0 else 0.0
        d["created_at"] = str(d["created_at"])
        d["updated_at"] = str(d["updated_at"])
        result.append(d)
    return result


def get_chapter(chapter_id: int) -> Optional[Dict[str, Any]]:
    """Return chapter detail with completion_rate."""
    with get_db() as conn:
        row = conn.execute(
            text(
                "SELECT c.id, c.book_id, c.chapter_no, c.title, c.status, "
                "c.output_path, c.created_at, c.updated_at, "
                "COUNT(s.id) AS total_segments, "
                "SUM(CASE WHEN s.status IN ('passed','polish_uploaded') THEN 1 ELSE 0 END) "
                "   AS completed_segments "
                "FROM tts2mp3_chapters c "
                "LEFT JOIN tts2mp3_segments s ON s.chapter_id = c.id "
                "WHERE c.id = :chapter_id "
                "GROUP BY c.id"
            ),
            {"chapter_id": chapter_id}
        ).fetchone()

    if row is None:
        return None
    d = dict(row._mapping)
    total = d.get("total_segments") or 0
    completed = d.get("completed_segments") or 0
    d["completion_rate"] = (completed / total) if total > 0 else 0.0
    d["created_at"] = str(d["created_at"])
    d["updated_at"] = str(d["updated_at"])
    return d


def get_segments_for_chapter(chapter_id: int) -> List[Dict[str, Any]]:
    """Return segments for a chapter."""
    with get_db() as conn:
        rows = conn.execute(
            text(
                "SELECT s.*, "
                "sv.audio_path AS active_audio_path, "
                "sv.version_no AS active_version_no, "
                "sv.duration_ms, sv.sample_rate "
                "FROM tts2mp3_segments s "
                "LEFT JOIN tts2mp3_segment_versions sv "
                "   ON sv.segment_id = s.id AND sv.is_active = TRUE "
                "WHERE s.chapter_id = :chapter_id "
                "ORDER BY s.segment_no"
            ),
            {"chapter_id": chapter_id}
        ).fetchall()

    result = []
    for row in rows:
        d = dict(row._mapping)
        d["created_at"] = str(d["created_at"])
        d["updated_at"] = str(d["updated_at"])
        result.append(d)
    return result


def get_segment(segment_id: int) -> Optional[Dict[str, Any]]:
    """Return segment detail with active version info."""
    with get_db() as conn:
        row = conn.execute(
            text(
                "SELECT s.*, "
                "sv.id AS version_id, "
                "sv.version_no AS active_version_no, "
                "sv.audio_path AS active_audio_path, "
                "sv.source_type, sv.duration_ms, sv.sample_rate, sv.channels "
                "FROM tts2mp3_segments s "
                "LEFT JOIN tts2mp3_segment_versions sv "
                "   ON sv.segment_id = s.id AND sv.is_active = TRUE "
                "WHERE s.id = :segment_id"
            ),
            {"segment_id": segment_id}
        ).fetchone()

    if row is None:
        return None
    d = dict(row._mapping)
    d["created_at"] = str(d["created_at"])
    d["updated_at"] = str(d["updated_at"])
    return d
