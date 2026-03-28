"""Chapter merge service: concatenate segment audio files using pydub."""

import json
import os
from typing import Dict, Any

from pydub import AudioSegment
from sqlalchemy import text

from db.connection import get_db
from config import settings


def merge_chapter(chapter_id: int) -> Dict[str, Any]:
    """Merge all segment audio files for a chapter into one WAV.

    Steps:
    1. Fetch chapter record
    2. Fetch segments with active audio paths, ordered by segment_no
    3. Load and concatenate with pydub
    4. Save to data/output/{chapter_id}.wav
    5. Update chapter status

    Returns:
        Dict with status and output_path (or error detail)
    """
    with get_db() as conn:
        # Fetch chapter
        chapter = conn.execute(
            text("SELECT * FROM tts2mp3_chapters WHERE id = :id"),
            {"id": chapter_id}
        ).fetchone()

        if chapter is None:
            raise ValueError(f"Chapter {chapter_id} not found")

        # Fetch segments with their active audio versions ordered by segment_no
        rows = conn.execute(
            text(
                "SELECT s.segment_no, sv.audio_path, sv.sample_rate, sv.channels "
                "FROM tts2mp3_segments s "
                "JOIN tts2mp3_segment_versions sv ON sv.segment_id = s.id AND sv.is_active = TRUE "
                "WHERE s.chapter_id = :chapter_id "
                "ORDER BY s.segment_no"
            ),
            {"chapter_id": chapter_id}
        ).fetchall()

        if not rows:
            _update_chapter_failed(conn, chapter_id, "No segments with active audio")
            return {"status": "failed", "output_path": None, "error": "No segments with active audio"}

        # Attempt merge
        try:
            output_path = _do_merge(chapter_id, rows)
        except Exception as exc:
            error_msg = str(exc)
            _update_chapter_failed(conn, chapter_id, error_msg)
            return {"status": "failed", "output_path": None, "error": error_msg}

        # Success: update chapter
        conn.execute(
            text(
                "UPDATE tts2mp3_chapters SET status='chapter_done', output_path=:output_path, "
                "updated_at=NOW() WHERE id=:id"
            ),
            {"id": chapter_id, "output_path": output_path}
        )
        _write_log(conn, chapter_id, "merge_done", output_path)

    return {"status": "chapter_done", "output_path": output_path}


def _do_merge(chapter_id: int, rows) -> str:
    """Load audio files and concatenate them.

    Args:
        chapter_id: Used for output filename
        rows: SQLAlchemy rows with audio_path, segment_no

    Returns:
        Absolute path to merged output file

    Raises:
        FileNotFoundError: If any audio file is missing
        Exception: If pydub merge fails
    """
    combined = None
    for row in rows:
        d = dict(row._mapping)
        audio_path = d["audio_path"]

        if not audio_path or not os.path.exists(audio_path):
            raise FileNotFoundError(
                f"Audio file missing for segment_no={d['segment_no']}: {audio_path}"
            )

        segment_audio = AudioSegment.from_wav(audio_path)
        if combined is None:
            combined = segment_audio
        else:
            combined = combined + segment_audio

    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(settings.OUTPUT_DIR, f"{chapter_id}.wav")
    combined.export(output_path, format="wav")
    return output_path


def _update_chapter_failed(conn, chapter_id: int, reason: str) -> None:
    conn.execute(
        text(
            "UPDATE tts2mp3_chapters SET status='failed', updated_at=NOW() WHERE id=:id"
        ),
        {"id": chapter_id}
    )
    _write_log(conn, chapter_id, "merge_failed", reason)


def _write_log(conn, chapter_id: int, action: str, detail: str) -> None:
    conn.execute(
        text(
            "INSERT INTO tts2mp3_operation_logs "
            "(action, target_type, target_id, extra) "
            "VALUES (:action, 'chapter', :target_id, :extra)"
        ),
        {
            "action": action,
            "target_id": chapter_id,
            "extra": json.dumps({"detail": detail}),
        }
    )
