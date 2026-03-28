"""Tests for chapter auto merge functionality.

Initially RED (service not implemented).
"""

import io
import os
import pytest
from unittest.mock import MagicMock, patch
from pydub import AudioSegment


def _make_wav_bytes(sample_rate=22050, duration_ms=500):
    """Generate real WAV bytes."""
    audio = AudioSegment.silent(duration=duration_ms, frame_rate=sample_rate)
    buf = io.BytesIO()
    audio.export(buf, format="wav")
    return buf.getvalue()


def _make_chapter_row(chapter_id=10, status="in_progress"):
    row = MagicMock()
    row._mapping = {
        "id": chapter_id,
        "book_id": 1,
        "status": status,
        "output_path": None,
    }
    return row


def _make_segment_version_row(segment_id, version_no=1, audio_path=None, sample_rate=22050):
    row = MagicMock()
    row._mapping = {
        "segment_id": segment_id,
        "segment_no": segment_id,  # use id as no for simplicity
        "audio_path": audio_path or f"/tmp/audio/{segment_id}/v{version_no}.wav",
        "sample_rate": sample_rate,
        "channels": 1,
    }
    return row


def test_merge_all_passed_triggers_chapter_done(tmp_path):
    """Test: all segments passed/polish_uploaded → merge → chapter_done."""
    from services.merge_service import merge_chapter

    # Create real wav files
    seg1_dir = tmp_path / "1"
    seg2_dir = tmp_path / "2"
    seg1_dir.mkdir()
    seg2_dir.mkdir()
    wav1 = seg1_dir / "v1.wav"
    wav2 = seg2_dir / "v1.wav"
    wav1.write_bytes(_make_wav_bytes())
    wav2.write_bytes(_make_wav_bytes())

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    with patch("services.merge_service.get_db") as mock_get_db:
        conn = MagicMock()
        mock_get_db.return_value.__enter__ = MagicMock(return_value=conn)
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

        chapter_row = _make_chapter_row(10)
        sv1 = _make_segment_version_row(1, audio_path=str(wav1))
        sv2 = _make_segment_version_row(2, audio_path=str(wav2))
        sv1._mapping["segment_no"] = 1
        sv2._mapping["segment_no"] = 2

        conn.execute.side_effect = [
            MagicMock(fetchone=MagicMock(return_value=chapter_row)),
            MagicMock(fetchall=MagicMock(return_value=[sv1, sv2])),
            MagicMock(),  # update chapter status
            MagicMock(),  # insert log
        ]

        with patch("services.merge_service.settings") as mock_settings:
            mock_settings.OUTPUT_DIR = str(output_dir)
            result = merge_chapter(10)

    assert result["status"] == "chapter_done"
    assert result["output_path"] is not None


def test_merge_missing_audio_file_fails(tmp_path):
    """Test: segment with missing audio file → merge fails → chapter status = failed."""
    from services.merge_service import merge_chapter

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    with patch("services.merge_service.get_db") as mock_get_db:
        conn = MagicMock()
        mock_get_db.return_value.__enter__ = MagicMock(return_value=conn)
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

        chapter_row = _make_chapter_row(11)
        sv1 = _make_segment_version_row(1, audio_path="/nonexistent/path/v1.wav")
        sv1._mapping["segment_no"] = 1

        conn.execute.side_effect = [
            MagicMock(fetchone=MagicMock(return_value=chapter_row)),
            MagicMock(fetchall=MagicMock(return_value=[sv1])),
            MagicMock(),  # update chapter status = failed
            MagicMock(),  # insert log
        ]

        with patch("services.merge_service.settings") as mock_settings:
            mock_settings.OUTPUT_DIR = str(output_dir)
            result = merge_chapter(11)

    assert result["status"] == "failed"


def test_merge_manual_trigger(tmp_path):
    """Test: manual trigger POST /api/v1/chapters/{id}/merge."""
    from services.merge_service import merge_chapter

    seg1_dir = tmp_path / "3"
    seg1_dir.mkdir()
    wav1 = seg1_dir / "v1.wav"
    wav1.write_bytes(_make_wav_bytes())
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    with patch("services.merge_service.get_db") as mock_get_db:
        conn = MagicMock()
        mock_get_db.return_value.__enter__ = MagicMock(return_value=conn)
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

        chapter_row = _make_chapter_row(12)
        sv1 = _make_segment_version_row(3, audio_path=str(wav1))
        sv1._mapping["segment_no"] = 1

        conn.execute.side_effect = [
            MagicMock(fetchone=MagicMock(return_value=chapter_row)),
            MagicMock(fetchall=MagicMock(return_value=[sv1])),
            MagicMock(),
            MagicMock(),
        ]

        with patch("services.merge_service.settings") as mock_settings:
            mock_settings.OUTPUT_DIR = str(output_dir)
            result = merge_chapter(12)

    assert result["status"] == "chapter_done"


def test_merge_output_file_exists(tmp_path):
    """Test that merge creates the output WAV file."""
    from services.merge_service import merge_chapter

    seg1_dir = tmp_path / "4"
    seg1_dir.mkdir()
    wav1 = seg1_dir / "v1.wav"
    wav1.write_bytes(_make_wav_bytes())
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    with patch("services.merge_service.get_db") as mock_get_db:
        conn = MagicMock()
        mock_get_db.return_value.__enter__ = MagicMock(return_value=conn)
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

        chapter_row = _make_chapter_row(13)
        sv1 = _make_segment_version_row(4, audio_path=str(wav1))
        sv1._mapping["segment_no"] = 1

        conn.execute.side_effect = [
            MagicMock(fetchone=MagicMock(return_value=chapter_row)),
            MagicMock(fetchall=MagicMock(return_value=[sv1])),
            MagicMock(),
            MagicMock(),
        ]

        with patch("services.merge_service.settings") as mock_settings:
            mock_settings.OUTPUT_DIR = str(output_dir)
            result = merge_chapter(13)

    output_file = output_dir / "13.wav"
    assert output_file.exists()
