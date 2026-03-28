"""Polish upload service: WAV validation and version management."""

import io
import json
import os
from typing import Optional, Dict, Any

from pydub import AudioSegment
from sqlalchemy import text

from db.connection import get_db
from config import settings


def _validate_wav(file_bytes: bytes) -> AudioSegment:
    """Validate that bytes are valid WAV and return parsed AudioSegment.

    Raises:
        ValueError: If file is not a valid WAV
    """
    try:
        buf = io.BytesIO(file_bytes)
        audio = AudioSegment.from_wav(buf)
        return audio
    except Exception as exc:
        raise ValueError(f"File is not a valid wav: {exc}")


def upload_polish(
    segment_id: int,
    file_bytes: bytes,
    filename: str,
    operator_token: Optional[str] = None,
    operator_role: Optional[str] = None,
) -> Dict[str, Any]:
    """Process a polish WAV upload for a segment.

    Steps:
    1. Validate WAV format
    2. Fetch segment and existing active version
    3. Check sample_rate matches if existing version present
    4. Save file, create new version record, deactivate old
    5. Update segment status to polish_uploaded
    6. Write operation log

    Returns:
        Dict with version_id and new status

    Raises:
        ValueError: If file is not wav, or sample_rate mismatch
    """
    # Validate WAV
    audio = _validate_wav(file_bytes)
    sample_rate = audio.frame_rate
    channels = audio.channels
    duration_ms = len(audio)
    file_size = len(file_bytes)

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

        # Check existing active version for sample_rate compatibility
        active_version = conn.execute(
            text(
                "SELECT sample_rate, version_no FROM tts2mp3_segment_versions "
                "WHERE segment_id=:sid AND is_active=TRUE LIMIT 1"
            ),
            {"sid": segment_id}
        ).fetchone()

        if active_version is not None:
            av = dict(active_version._mapping)
            existing_sr = av.get("sample_rate")
            if existing_sr and existing_sr != sample_rate:
                raise ValueError(
                    f"sample_rate mismatch: existing={existing_sr}, uploaded={sample_rate}"
                )

        # Get version count for new version_no
        count_row = conn.execute(
            text("SELECT COUNT(*) AS cnt FROM tts2mp3_segment_versions WHERE segment_id=:sid"),
            {"sid": segment_id}
        ).fetchone()
        version_no = (dict(count_row._mapping)["cnt"] or 0) + 1

        # Save file to disk
        segment_audio_dir = os.path.join(settings.AUDIO_DIR, str(segment_id))
        os.makedirs(segment_audio_dir, exist_ok=True)
        audio_path = os.path.join(segment_audio_dir, f"v{version_no}.wav")
        with open(audio_path, "wb") as f:
            f.write(file_bytes)

        # Deactivate existing active version
        conn.execute(
            text(
                "UPDATE tts2mp3_segment_versions SET is_active=FALSE "
                "WHERE segment_id=:sid AND is_active=TRUE"
            ),
            {"sid": segment_id}
        )

        # Insert new version
        result = conn.execute(
            text(
                "INSERT INTO tts2mp3_segment_versions "
                "(segment_id, version_no, source_type, audio_path, text_content, "
                "sample_rate, channels, duration_ms, file_size, is_active) "
                "VALUES (:segment_id, :version_no, 'polish_upload', :audio_path, NULL, "
                ":sample_rate, :channels, :duration_ms, :file_size, TRUE)"
            ),
            {
                "segment_id": segment_id,
                "version_no": version_no,
                "audio_path": audio_path,
                "sample_rate": sample_rate,
                "channels": channels,
                "duration_ms": duration_ms,
                "file_size": file_size,
            }
        )
        version_id = result.lastrowid

        # Update segment status
        conn.execute(
            text(
                "UPDATE tts2mp3_segments SET status='polish_uploaded', updated_at=NOW() "
                "WHERE id=:id"
            ),
            {"id": segment_id}
        )

        # Write operation log
        conn.execute(
            text(
                "INSERT INTO tts2mp3_operation_logs "
                "(operator_token, operator_role, action, target_type, target_id, "
                "before_status, after_status, extra) "
                "VALUES (:token, :role, 'upload_polish', 'segment', :target_id, "
                ":before, 'polish_uploaded', :extra)"
            ),
            {
                "token": operator_token,
                "role": operator_role,
                "target_id": segment_id,
                "before": before_status,
                "extra": json.dumps({"filename": filename, "version_no": version_no}),
            }
        )

        # Check chapter completion → trigger merge if ready
        chapter_id = seg["chapter_id"]
        row = conn.execute(
            text(
                "SELECT COUNT(*) AS total, "
                "SUM(CASE WHEN status IN ('passed','polish_uploaded') THEN 1 ELSE 0 END) AS completed "
                "FROM tts2mp3_segments WHERE chapter_id = :chapter_id"
            ),
            {"chapter_id": chapter_id}
        ).fetchone()

        if row is not None:
            d = dict(row._mapping)
            total = d.get("total") or 0
            completed = d.get("completed") or 0
            if total > 0 and total == completed:
                try:
                    from services.merge_service import merge_chapter
                    merge_chapter(chapter_id)
                except Exception:
                    pass

    return {"segment_id": segment_id, "version_id": version_id, "status": "polish_uploaded"}
