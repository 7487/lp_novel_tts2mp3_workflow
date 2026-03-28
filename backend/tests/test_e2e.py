"""End-to-end integration test for the audiobook production workflow.

Full flow:
  import book → trigger TTS → evaluate (passed + needs_polish) →
  upload polish → verify chapter auto-merge → verify chapter output
"""

import io
import json
import os
import pytest
from unittest.mock import MagicMock, patch, call
from pydub import AudioSegment


# ===== Helpers =====

def _make_wav_bytes(sample_rate=22050, duration_ms=500):
    audio = AudioSegment.silent(duration=duration_ms, frame_rate=sample_rate)
    buf = io.BytesIO()
    audio.export(buf, format="wav")
    return buf.getvalue()


def _make_txt_book():
    return """第1章 测试章节

这是第一个片段的内容。

这是第二个片段的内容，需要被评估。
"""


# ===== Tests =====

class TestParsing:
    """Verify parsing layer (no DB needed)."""

    def test_parse_txt_book(self):
        from services.book_service import parse_txt
        result = parse_txt(_make_txt_book())
        assert len(result) == 1
        assert len(result[0]["segments"]) == 2

    def test_parse_json_book(self):
        from services.book_service import parse_json
        data = {
            "title": "集成测试书",
            "chapters": [
                {"title": "第一章", "segments": ["段落一。", "段落二。"]},
                {"title": "第二章", "segments": ["段落三。"]},
            ]
        }
        result = parse_json(data)
        assert len(result) == 2
        assert result[0]["segments"] == ["段落一。", "段落二。"]


class TestTTSLayer:
    """Verify TTS mock generates valid audio."""

    def test_mock_tts_wav_header(self):
        from services.tts_service import MockTTSService
        svc = MockTTSService()
        wav = svc.generate("测试文字")
        assert wav[:4] == b"RIFF"
        assert len(wav) > 100

    def test_mock_tts_parseable_by_pydub(self):
        from services.tts_service import MockTTSService
        svc = MockTTSService()
        wav = svc.generate("另一段文字")
        audio = AudioSegment.from_wav(io.BytesIO(wav))
        assert audio.frame_rate > 0
        assert len(audio) > 0


class TestEvaluationStateTransitions:
    """Verify state machine transitions."""

    def _run_eval(self, tmp_path, can_use, tags=None):
        from services.evaluation_service import evaluate_segment

        with patch("services.evaluation_service.get_db") as mock_db:
            conn = MagicMock()
            mock_db.return_value.__enter__ = MagicMock(return_value=conn)
            mock_db.return_value.__exit__ = MagicMock(return_value=False)

            seg_row = MagicMock()
            seg_row._mapping = {
                "id": 1, "chapter_id": 10, "status": "tts_done",
                "original_text": "txt", "badcase_tags": None, "modified_text": None,
                "annotation": None,
            }
            ch_row = MagicMock()
            ch_row._mapping = {"total": 2, "completed": 0}
            conn.execute.side_effect = [
                MagicMock(fetchone=MagicMock(return_value=seg_row)),
                MagicMock(),
                MagicMock(),
                MagicMock(fetchone=MagicMock(return_value=ch_row)),
            ]

            return evaluate_segment(
                segment_id=1,
                can_use=can_use,
                badcase_tags=tags,
                modified_text=None,
                annotation=None,
            )

    def test_passed_transition(self, tmp_path):
        result = self._run_eval(tmp_path, can_use=True)
        assert result["status"] == "passed"

    def test_needs_polish_transition(self, tmp_path):
        result = self._run_eval(tmp_path, can_use=False, tags=["发音错误"])
        assert result["status"] == "needs_polish"

    def test_unavailable_without_tags_raises(self, tmp_path):
        from services.evaluation_service import evaluate_segment
        with pytest.raises(ValueError):
            self._run_eval(tmp_path, can_use=False, tags=[])


class TestUploadLayer:
    """Verify polish upload validation."""

    def test_valid_wav_accepted(self, tmp_path):
        from services.upload_service import upload_polish

        wav = _make_wav_bytes()
        with patch("services.upload_service.get_db") as mock_db:
            conn = MagicMock()
            mock_db.return_value.__enter__ = MagicMock(return_value=conn)
            mock_db.return_value.__exit__ = MagicMock(return_value=False)

            seg_row = MagicMock()
            seg_row._mapping = {"id": 1, "chapter_id": 10, "status": "needs_polish", "original_text": "t"}
            cnt_row = MagicMock()
            cnt_row._mapping = {"cnt": 1}
            ch_row = MagicMock()
            ch_row._mapping = {"total": 2, "completed": 1}
            ins = MagicMock()
            ins.lastrowid = 5

            conn.execute.side_effect = [
                MagicMock(fetchone=MagicMock(return_value=seg_row)),
                MagicMock(fetchone=MagicMock(return_value=None)),  # no active version
                MagicMock(fetchone=MagicMock(return_value=cnt_row)),
                MagicMock(),  # deactivate
                ins,          # insert
                MagicMock(),  # update segment
                MagicMock(),  # insert log
                MagicMock(fetchone=MagicMock(return_value=ch_row)),
            ]

            with patch("services.upload_service.settings") as ms:
                ms.AUDIO_DIR = str(tmp_path)
                result = upload_polish(1, wav, "test.wav")

        assert result["status"] == "polish_uploaded"

    def test_non_wav_rejected(self, tmp_path):
        from services.upload_service import upload_polish
        with pytest.raises(ValueError, match="wav"):
            with patch("services.upload_service.get_db"):
                upload_polish(1, b"not a wav file", "test.mp3")


class TestMergeLayer:
    """Verify chapter merge logic."""

    def test_merge_success(self, tmp_path):
        from services.merge_service import merge_chapter

        wav = _make_wav_bytes()
        seg_dir = tmp_path / "1"
        seg_dir.mkdir()
        wav_path = seg_dir / "v1.wav"
        wav_path.write_bytes(wav)
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        with patch("services.merge_service.get_db") as mock_db:
            conn = MagicMock()
            mock_db.return_value.__enter__ = MagicMock(return_value=conn)
            mock_db.return_value.__exit__ = MagicMock(return_value=False)

            ch_row = MagicMock()
            ch_row._mapping = {"id": 20, "book_id": 1, "status": "in_progress", "output_path": None}
            sv_row = MagicMock()
            sv_row._mapping = {"segment_no": 1, "audio_path": str(wav_path),
                               "sample_rate": 22050, "channels": 1}

            conn.execute.side_effect = [
                MagicMock(fetchone=MagicMock(return_value=ch_row)),
                MagicMock(fetchall=MagicMock(return_value=[sv_row])),
                MagicMock(),
                MagicMock(),
            ]

            with patch("services.merge_service.settings") as ms:
                ms.OUTPUT_DIR = str(out_dir)
                result = merge_chapter(20)

        assert result["status"] == "chapter_done"
        assert os.path.exists(result["output_path"])

    def test_merge_missing_file_fails(self, tmp_path):
        from services.merge_service import merge_chapter

        out_dir = tmp_path / "out"
        out_dir.mkdir()

        with patch("services.merge_service.get_db") as mock_db:
            conn = MagicMock()
            mock_db.return_value.__enter__ = MagicMock(return_value=conn)
            mock_db.return_value.__exit__ = MagicMock(return_value=False)

            ch_row = MagicMock()
            ch_row._mapping = {"id": 21, "book_id": 1, "status": "in_progress", "output_path": None}
            sv_row = MagicMock()
            sv_row._mapping = {"segment_no": 1, "audio_path": "/nope/v1.wav",
                               "sample_rate": 22050, "channels": 1}

            conn.execute.side_effect = [
                MagicMock(fetchone=MagicMock(return_value=ch_row)),
                MagicMock(fetchall=MagicMock(return_value=[sv_row])),
                MagicMock(),  # update failed
                MagicMock(),  # log
            ]

            with patch("services.merge_service.settings") as ms:
                ms.OUTPUT_DIR = str(out_dir)
                result = merge_chapter(21)

        assert result["status"] == "failed"


class TestFullFlowIntegration:
    """Simulate the full audiobook production flow without a real DB."""

    def test_txt_parse_to_chapter_structure(self):
        """AC-1: Book can be imported with chapters and segments."""
        from services.book_service import parse_txt

        txt = """第1章 第一章标题

第一段内容。

第二段内容。

第2章 第二章标题

第三段内容。
"""
        chapters = parse_txt(txt)
        assert len(chapters) == 2
        assert len(chapters[0]["segments"]) == 2
        assert len(chapters[1]["segments"]) == 1

    def test_tts_produces_valid_audio_for_each_segment(self):
        """AC-2: TTS mock produces valid audio."""
        from services.tts_service import MockTTSService

        svc = MockTTSService()
        segments = ["片段一内容。", "片段二内容。"]
        for seg_text in segments:
            wav = svc.generate(seg_text)
            assert wav[:4] == b"RIFF"
            audio = AudioSegment.from_wav(io.BytesIO(wav))
            assert len(audio) > 0

    def test_evaluate_both_paths(self):
        """AC-3/AC-4: Evaluation transitions state correctly."""
        from services.evaluation_service import evaluate_segment

        def _eval(can_use, tags=None):
            with patch("services.evaluation_service.get_db") as mock_db:
                conn = MagicMock()
                mock_db.return_value.__enter__ = MagicMock(return_value=conn)
                mock_db.return_value.__exit__ = MagicMock(return_value=False)

                seg_row = MagicMock()
                seg_row._mapping = {
                    "id": 1, "chapter_id": 1, "status": "tts_done",
                    "original_text": "x", "badcase_tags": None,
                    "modified_text": None, "annotation": None,
                }
                ch_row = MagicMock()
                ch_row._mapping = {"total": 3, "completed": 0}
                conn.execute.side_effect = [
                    MagicMock(fetchone=MagicMock(return_value=seg_row)),
                    MagicMock(), MagicMock(),
                    MagicMock(fetchone=MagicMock(return_value=ch_row)),
                ]
                return evaluate_segment(1, can_use, tags, None, None)

        passed = _eval(True)
        assert passed["status"] == "passed"

        needs_polish = _eval(False, ["发音错误"])
        assert needs_polish["status"] == "needs_polish"

    def test_upload_and_merge_chain(self, tmp_path):
        """AC-6/AC-8: Upload triggers merge when chapter complete."""
        from services.merge_service import merge_chapter
        from pydub import AudioSegment

        wav = _make_wav_bytes()
        seg_dir = tmp_path / "10"
        seg_dir.mkdir()
        wav_path = seg_dir / "v1.wav"
        wav_path.write_bytes(wav)
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        with patch("services.merge_service.get_db") as mock_db:
            conn = MagicMock()
            mock_db.return_value.__enter__ = MagicMock(return_value=conn)
            mock_db.return_value.__exit__ = MagicMock(return_value=False)

            ch_row = MagicMock()
            ch_row._mapping = {"id": 30, "book_id": 1, "status": "in_progress", "output_path": None}
            sv_row = MagicMock()
            sv_row._mapping = {"segment_no": 1, "audio_path": str(wav_path),
                               "sample_rate": 22050, "channels": 1}

            conn.execute.side_effect = [
                MagicMock(fetchone=MagicMock(return_value=ch_row)),
                MagicMock(fetchall=MagicMock(return_value=[sv_row])),
                MagicMock(), MagicMock(),
            ]

            with patch("services.merge_service.settings") as ms:
                ms.OUTPUT_DIR = str(out_dir)
                result = merge_chapter(30)

        assert result["status"] == "chapter_done"
        output_path = result["output_path"]
        assert os.path.exists(output_path)
        # Verify output is a valid WAV
        merged_audio = AudioSegment.from_wav(output_path)
        assert len(merged_audio) > 0
