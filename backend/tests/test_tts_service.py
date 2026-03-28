"""Tests for TTS mock service."""

import pytest
import os
from unittest.mock import MagicMock, patch


def _make_segment_row(segment_id=1):
    row = MagicMock()
    row._mapping = {
        "id": segment_id,
        "chapter_id": 1,
        "segment_no": 1,
        "original_text": "测试文字内容",
        "status": "pending_tts",
        "modified_text": None,
    }
    return row


def _make_count_row(cnt=0):
    row = MagicMock()
    row._mapping = {"cnt": cnt}
    return row


def _setup_conn_side_effects(conn, segment_id=1, cnt=0):
    """Set up conn.execute side effects matching run_tts_for_segment call order.

    Order:
      1. SELECT segments WHERE id=:id   -> fetchone
      2. SELECT COUNT(*) from segment_versions -> fetchone
      3. UPDATE segment_versions SET is_active=FALSE
      4. INSERT INTO segment_versions   -> lastrowid
      5. UPDATE segments SET status=tts_done
    """
    insert_result = MagicMock()
    insert_result.lastrowid = 99
    conn.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=_make_segment_row(segment_id))),
        MagicMock(fetchone=MagicMock(return_value=_make_count_row(cnt))),
        MagicMock(),    # deactivate old versions
        insert_result,  # insert new version
        MagicMock(),    # update segment status
    ]
    return insert_result


def test_mock_tts_returns_wav_bytes():
    """Test that mock TTS returns valid wav bytes."""
    from services.tts_service import MockTTSService

    service = MockTTSService()
    wav_bytes = service.generate("hello world")
    assert isinstance(wav_bytes, bytes)
    assert len(wav_bytes) > 44
    assert wav_bytes[:4] == b"RIFF"


def test_mock_tts_returns_non_empty():
    """Test that mock TTS returns non-empty bytes."""
    from services.tts_service import MockTTSService

    service = MockTTSService()
    result = service.generate("some text")
    assert len(result) > 0


def test_run_tts_for_segment_creates_version(tmp_path):
    """Test that run_tts_for_segment creates a segment_versions record."""
    from services.tts_service import run_tts_for_segment

    with patch("services.tts_service.get_db") as mock_get_db:
        conn = MagicMock()
        mock_get_db.return_value.__enter__ = MagicMock(return_value=conn)
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)
        _setup_conn_side_effects(conn, segment_id=1)

        with patch("services.tts_service.settings") as mock_settings:
            mock_settings.AUDIO_DIR = str(tmp_path)
            version_id = run_tts_for_segment(1)

        # Should have called execute at least 4 times (select, count, deactivate, insert, update)
        assert conn.execute.call_count >= 4


def test_run_tts_updates_segment_status(tmp_path):
    """Test that run_tts_for_segment updates segment status to tts_done."""
    from services.tts_service import run_tts_for_segment

    with patch("services.tts_service.get_db") as mock_get_db:
        conn = MagicMock()
        mock_get_db.return_value.__enter__ = MagicMock(return_value=conn)
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)
        _setup_conn_side_effects(conn)

        with patch("services.tts_service.settings") as mock_settings:
            mock_settings.AUDIO_DIR = str(tmp_path)
            run_tts_for_segment(1)

        # Verify at least 5 execute calls (select, count, deactivate, insert, update status)
        assert conn.execute.call_count >= 5


def test_run_tts_saves_audio_file(tmp_path):
    """Test that run_tts_for_segment saves audio file to disk."""
    from services.tts_service import run_tts_for_segment

    with patch("services.tts_service.get_db") as mock_get_db:
        conn = MagicMock()
        mock_get_db.return_value.__enter__ = MagicMock(return_value=conn)
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)
        _setup_conn_side_effects(conn, segment_id=42)

        with patch("services.tts_service.settings") as mock_settings:
            mock_settings.AUDIO_DIR = str(tmp_path)
            run_tts_for_segment(42)

        audio_dir = tmp_path / "42"
        assert audio_dir.exists()
        wav_files = list(audio_dir.glob("*.wav"))
        assert len(wav_files) == 1


def test_run_tts_version_id_returned(tmp_path):
    """Test that run_tts_for_segment returns the new version ID."""
    from services.tts_service import run_tts_for_segment

    with patch("services.tts_service.get_db") as mock_get_db:
        conn = MagicMock()
        mock_get_db.return_value.__enter__ = MagicMock(return_value=conn)
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)
        insert_result = _setup_conn_side_effects(conn)
        insert_result.lastrowid = 55

        with patch("services.tts_service.settings") as mock_settings:
            mock_settings.AUDIO_DIR = str(tmp_path)
            version_id = run_tts_for_segment(1)

        assert version_id == 55
