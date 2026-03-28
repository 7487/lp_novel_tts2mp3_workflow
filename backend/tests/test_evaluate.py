"""Tests for segment evaluation API state machine.

Initially RED (service not implemented).
"""

import pytest
from unittest.mock import MagicMock, patch


def _make_segment_row(status="tts_done"):
    row = MagicMock()
    row._mapping = {
        "id": 1,
        "chapter_id": 10,
        "status": status,
        "original_text": "测试文字",
        "badcase_tags": None,
        "modified_text": None,
        "annotation": None,
    }
    return row


def _setup_conn(conn, segment_status="tts_done"):
    """Setup mock conn for evaluation tests."""
    segment_row = _make_segment_row(segment_status)
    chapter_row = MagicMock()
    # total=3, completed=0 (not fully complete)
    chapter_row._mapping = {"total": 3, "completed": 0}
    conn.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=segment_row)),  # fetch segment
        MagicMock(),   # update segment
        MagicMock(),   # insert operation_log
        MagicMock(fetchone=MagicMock(return_value=chapter_row)),  # check chapter completion
    ]
    return segment_row


def test_evaluate_available_sets_passed():
    """Test that can_use=True transitions segment to passed status."""
    from services.evaluation_service import evaluate_segment

    with patch("services.evaluation_service.get_db") as mock_get_db:
        conn = MagicMock()
        mock_get_db.return_value.__enter__ = MagicMock(return_value=conn)
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)
        _setup_conn(conn)

        result = evaluate_segment(
            segment_id=1,
            can_use=True,
            badcase_tags=None,
            modified_text=None,
            annotation=None,
            operator_token="test_token",
            operator_role="annotator",
        )

    assert result["status"] == "passed"


def test_evaluate_unavailable_sets_needs_polish():
    """Test that can_use=False transitions segment to needs_polish."""
    from services.evaluation_service import evaluate_segment

    with patch("services.evaluation_service.get_db") as mock_get_db:
        conn = MagicMock()
        mock_get_db.return_value.__enter__ = MagicMock(return_value=conn)
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)
        _setup_conn(conn)

        result = evaluate_segment(
            segment_id=1,
            can_use=False,
            badcase_tags=["发音错误", "语速问题"],
            modified_text="修改后的文字",
            annotation="这里有问题",
            operator_token="test_token",
            operator_role="annotator",
        )

    assert result["status"] == "needs_polish"


def test_evaluate_unavailable_without_tags_raises():
    """Test that can_use=False without badcase_tags raises ValueError."""
    from services.evaluation_service import evaluate_segment

    with patch("services.evaluation_service.get_db") as mock_get_db:
        conn = MagicMock()
        mock_get_db.return_value.__enter__ = MagicMock(return_value=conn)
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)
        _setup_conn(conn)

        with pytest.raises(ValueError, match="badcase_tags"):
            evaluate_segment(
                segment_id=1,
                can_use=False,
                badcase_tags=[],   # empty list → should raise
                modified_text=None,
                annotation=None,
                operator_token="test_token",
                operator_role="annotator",
            )


def test_evaluate_unavailable_without_tags_none_raises():
    """Test that can_use=False with None badcase_tags raises ValueError."""
    from services.evaluation_service import evaluate_segment

    with patch("services.evaluation_service.get_db") as mock_get_db:
        conn = MagicMock()
        mock_get_db.return_value.__enter__ = MagicMock(return_value=conn)
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)
        _setup_conn(conn)

        with pytest.raises(ValueError, match="badcase_tags"):
            evaluate_segment(
                segment_id=1,
                can_use=False,
                badcase_tags=None,
                modified_text=None,
                annotation=None,
                operator_token="test_token",
                operator_role="annotator",
            )


def test_evaluate_writes_operation_log():
    """Test that evaluation writes an operation log entry."""
    from services.evaluation_service import evaluate_segment

    with patch("services.evaluation_service.get_db") as mock_get_db:
        conn = MagicMock()
        mock_get_db.return_value.__enter__ = MagicMock(return_value=conn)
        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)
        _setup_conn(conn)

        evaluate_segment(
            segment_id=1,
            can_use=True,
            badcase_tags=None,
            modified_text=None,
            annotation=None,
            operator_token="tok",
            operator_role="annotator",
        )

    # At least 3 execute calls: fetch segment, update segment, insert log
    assert conn.execute.call_count >= 3
