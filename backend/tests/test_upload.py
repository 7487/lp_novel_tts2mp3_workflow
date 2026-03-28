"""Tests for polish upload and WAV format validation.

Initially RED (service not yet implemented).
"""

import io
import pytest
from unittest.mock import MagicMock, patch
from pydub import AudioSegment


def _make_wav_bytes(sample_rate=22050, channels=1, duration_ms=1000):
    """Generate valid WAV bytes for testing."""
    audio = AudioSegment.silent(duration=duration_ms, frame_rate=sample_rate)
    audio = audio.set_channels(channels)
    buf = io.BytesIO()
    audio.export(buf, format="wav")
    return buf.getvalue()


def _make_mp3_bytes():
    """Create some bytes that look like mp3 (not wav)."""
    return b"ID3\x03\x00\x00\x00\x00\x00\x00" + b"\x00" * 100


def _make_segment_row(segment_id=1, chapter_id=10):
    row = MagicMock()
    row._mapping = {
        "id": segment_id,
        "chapter_id": chapter_id,
        "status": "needs_polish",
        "original_text": "test",
    }
    return row


def _make_version_count_row(cnt=0):
    row = MagicMock()
    row._mapping = {"cnt": cnt}
    return row


def _make_active_version_row(sample_rate=22050):
    row = MagicMock()
    row._mapping = {"sample_rate": sample_rate, "version_no": 1}
    return row


def _setup_conn_no_existing(conn, segment_id=1):
    """No existing active version."""
    insert_result = MagicMock()
    insert_result.lastrowid = 20
    chapter_row = MagicMock()
    chapter_row._mapping = {"total": 2, "completed": 1}
    conn.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=_make_segment_row(segment_id))),
        MagicMock(fetchone=MagicMock(return_value=None)),       # no active version
        MagicMock(fetchone=MagicMock(return_value=_make_version_count_row(0))),  # cnt=0
        MagicMock(),    # deactivate old
        insert_result,  # insert new version
        MagicMock(),    # update segment status
        MagicMock(),    # insert operation_log
        MagicMock(fetchone=MagicMock(return_value=chapter_row)),  # check completion
    ]
    return insert_result


def _setup_conn_with_existing(conn, existing_sample_rate=22050, segment_id=1):
    """Has existing active version with given sample_rate."""
    insert_result = MagicMock()
    insert_result.lastrowid = 21
    chapter_row = MagicMock()
    chapter_row._mapping = {"total": 2, "completed": 1}
    conn.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=_make_segment_row(segment_id))),
        MagicMock(fetchone=MagicMock(return_value=_make_active_version_row(existing_sample_rate))),
        MagicMock(fetchone=MagicMock(return_value=_make_version_count_row(1))),
        MagicMock(),    # deactivate old
        insert_result,  # insert new version
        MagicMock(),    # update segment status
        MagicMock(),    # insert operation_log
        MagicMock(fetchone=MagicMock(return_value=chapter_row)),  # check completion
    ]


def test_upload_valid_wav_creates_version(tmp_path):
    """Test that valid WAV upload creates a new version with is_active=True."""
    from services.upload_service import upload_polish

    wav_bytes = _make_wav_bytes()

    with patch("services.upload_service.get_db") as mock_get_db:
        conn = MagicMock()
        mock_get_db.return_value.__enter__ = MagicMock(return_value=conn)
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)
        insert_result = _setup_conn_no_existing(conn, segment_id=1)
        insert_result.lastrowid = 20

        with patch("services.upload_service.settings") as mock_settings:
            mock_settings.AUDIO_DIR = str(tmp_path)
            result = upload_polish(
                segment_id=1,
                file_bytes=wav_bytes,
                filename="test.wav",
                operator_token="polisher_tok",
                operator_role="polisher",
            )

    assert result["version_id"] == 20
    assert result["status"] == "polish_uploaded"


def test_upload_non_wav_raises(tmp_path):
    """Test that non-WAV file raises ValueError."""
    from services.upload_service import upload_polish

    non_wav = _make_mp3_bytes()

    with patch("services.upload_service.get_db") as mock_get_db:
        conn = MagicMock()
        mock_get_db.return_value.__enter__ = MagicMock(return_value=conn)
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

        with patch("services.upload_service.settings") as mock_settings:
            mock_settings.AUDIO_DIR = str(tmp_path)
            with pytest.raises(ValueError, match="wav"):
                upload_polish(
                    segment_id=1,
                    file_bytes=non_wav,
                    filename="test.mp3",
                    operator_token="polisher_tok",
                    operator_role="polisher",
                )


def test_upload_mismatched_sample_rate_raises(tmp_path):
    """Test that WAV with mismatched sample rate raises ValueError.

    Note: First upload always passes. This only applies when existing version exists.
    """
    from services.upload_service import upload_polish

    wav_bytes = _make_wav_bytes(sample_rate=44100)  # Different from existing 22050

    with patch("services.upload_service.get_db") as mock_get_db:
        conn = MagicMock()
        mock_get_db.return_value.__enter__ = MagicMock(return_value=conn)
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)
        _setup_conn_with_existing(conn, existing_sample_rate=22050, segment_id=1)

        with patch("services.upload_service.settings") as mock_settings:
            mock_settings.AUDIO_DIR = str(tmp_path)
            with pytest.raises(ValueError, match="sample_rate"):
                upload_polish(
                    segment_id=1,
                    file_bytes=wav_bytes,
                    filename="test.wav",
                    operator_token="polisher_tok",
                    operator_role="polisher",
                )


def test_upload_first_wav_always_passes(tmp_path):
    """Test that first WAV upload passes regardless of sample rate."""
    from services.upload_service import upload_polish

    wav_bytes = _make_wav_bytes(sample_rate=44100)

    with patch("services.upload_service.get_db") as mock_get_db:
        conn = MagicMock()
        mock_get_db.return_value.__enter__ = MagicMock(return_value=conn)
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)
        insert_result = _setup_conn_no_existing(conn, segment_id=5)
        insert_result.lastrowid = 30

        with patch("services.upload_service.settings") as mock_settings:
            mock_settings.AUDIO_DIR = str(tmp_path)
            result = upload_polish(
                segment_id=5,
                file_bytes=wav_bytes,
                filename="test.wav",
                operator_token="polisher_tok",
                operator_role="polisher",
            )

    assert result["status"] == "polish_uploaded"
