"""TTS mock service: generates silent wav audio for segments."""

import io
import os
from typing import Optional

from pydub import AudioSegment
from sqlalchemy import text

from db.connection import get_db
from config import settings


class MockTTSService:
    """Mock TTS service that generates silent wav audio."""

    DEFAULT_DURATION_MS = 1000  # 1 second of silence
    SAMPLE_RATE = 22050
    CHANNELS = 1

    def generate(self, text: str) -> bytes:
        """Generate silent wav bytes for given text.

        Args:
            text: Input text (ignored in mock, length scales duration)

        Returns:
            WAV bytes
        """
        # Scale duration by text length (min 500ms, max 5s)
        duration_ms = min(max(len(text) * 50, 500), 5000)
        audio = AudioSegment.silent(
            duration=duration_ms,
            frame_rate=self.SAMPLE_RATE,
        )
        # Convert to mono
        audio = audio.set_channels(self.CHANNELS)

        buf = io.BytesIO()
        audio.export(buf, format="wav")
        return buf.getvalue()


def run_tts_for_segment(segment_id: int, source_type: str = "tts_init") -> Optional[int]:
    """Run TTS for a segment and persist the result.

    Args:
        segment_id: ID of the segment to process
        source_type: One of 'tts_init', 'tts_regen'

    Returns:
        ID of the new segment_versions record, or None on failure
    """
    service = MockTTSService()

    with get_db() as conn:
        # Fetch segment
        segment = conn.execute(
            text("SELECT * FROM tts2mp3_segments WHERE id = :id"),
            {"id": segment_id}
        ).fetchone()

        if segment is None:
            raise ValueError(f"Segment {segment_id} not found")

        seg = dict(segment._mapping)
        text_to_speak = seg.get("modified_text") or seg["original_text"]

        # Get current version count
        count_row = conn.execute(
            text("SELECT COUNT(*) AS cnt FROM tts2mp3_segment_versions WHERE segment_id = :sid"),
            {"sid": segment_id}
        ).fetchone()
        version_no = dict(count_row._mapping)["cnt"] + 1

        # Generate audio
        wav_bytes = service.generate(text_to_speak)

        # Save audio file
        segment_audio_dir = os.path.join(settings.AUDIO_DIR, str(segment_id))
        os.makedirs(segment_audio_dir, exist_ok=True)
        audio_filename = f"v{version_no}.wav"
        audio_path = os.path.join(segment_audio_dir, audio_filename)

        with open(audio_path, "wb") as f:
            f.write(wav_bytes)

        # Parse audio metadata
        import io as _io
        audio_seg = AudioSegment.from_wav(_io.BytesIO(wav_bytes))
        sample_rate = audio_seg.frame_rate
        channels = audio_seg.channels
        duration_ms = len(audio_seg)
        file_size = len(wav_bytes)

        # Deactivate previous active version
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
                "VALUES (:segment_id, :version_no, :source_type, :audio_path, :text_content, "
                ":sample_rate, :channels, :duration_ms, :file_size, TRUE)"
            ),
            {
                "segment_id": segment_id,
                "version_no": version_no,
                "source_type": source_type,
                "audio_path": audio_path,
                "text_content": text_to_speak,
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
                "UPDATE tts2mp3_segments SET status='tts_done', updated_at=NOW() "
                "WHERE id=:id"
            ),
            {"id": segment_id}
        )

    return version_id


def get_active_audio_path(segment_id: int) -> Optional[str]:
    """Get the file path of the active audio version for a segment."""
    with get_db() as conn:
        row = conn.execute(
            text(
                "SELECT audio_path FROM tts2mp3_segment_versions "
                "WHERE segment_id=:sid AND is_active=TRUE "
                "LIMIT 1"
            ),
            {"sid": segment_id}
        ).fetchone()
    if row is None:
        return None
    return dict(row._mapping)["audio_path"]
