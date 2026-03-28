"""Segments router."""

import os
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Header, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel

from services.tts_service import run_tts_for_segment, get_active_audio_path
from services.chapter_service import get_segments_for_chapter, get_segment
from services.evaluation_service import evaluate_segment
from services.upload_service import upload_polish

router = APIRouter(tags=["segments"])


class EvaluateRequest(BaseModel):
    can_use: bool
    badcase_tags: Optional[List[str]] = None
    modified_text: Optional[str] = None
    annotation: Optional[str] = None


@router.get("/chapters/{chapter_id}/segments")
async def list_segments(chapter_id: int):
    """Return segments for a chapter."""
    return get_segments_for_chapter(chapter_id)


@router.get("/segments/{segment_id}")
async def get_segment_detail(segment_id: int):
    """Return segment detail with active version info."""
    segment = get_segment(segment_id)
    if segment is None:
        raise HTTPException(status_code=404, detail="Segment not found")
    return segment


@router.post("/segments/{segment_id}/tts")
async def trigger_tts(
    segment_id: int,
    x_token: Optional[str] = Header(None),
):
    """Trigger mock TTS for a segment."""
    try:
        version_id = run_tts_for_segment(segment_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"TTS failed: {exc}")

    return {"segment_id": segment_id, "version_id": version_id, "status": "tts_done"}


@router.get("/segments/{segment_id}/audio")
async def stream_audio(segment_id: int):
    """Stream the active audio file for a segment."""
    audio_path = get_active_audio_path(segment_id)
    if audio_path is None or not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio not found")
    return FileResponse(audio_path, media_type="audio/wav")


@router.post("/segments/{segment_id}/evaluate")
async def evaluate(
    segment_id: int,
    body: EvaluateRequest,
    x_token: Optional[str] = Header(None),
    x_role: Optional[str] = Header(default="annotator"),
):
    """Evaluate a segment (mark as passed or needs_polish)."""
    try:
        result = evaluate_segment(
            segment_id=segment_id,
            can_use=body.can_use,
            badcase_tags=body.badcase_tags,
            modified_text=body.modified_text,
            annotation=body.annotation,
            operator_token=x_token,
            operator_role=x_role or "annotator",
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return result


@router.post("/segments/{segment_id}/upload")
async def upload_audio(
    segment_id: int,
    file: UploadFile = File(...),
    x_token: Optional[str] = Header(None),
    x_role: Optional[str] = Header(default="polisher"),
):
    """Upload a polished WAV file for a segment."""
    file_bytes = await file.read()
    try:
        result = upload_polish(
            segment_id=segment_id,
            file_bytes=file_bytes,
            filename=file.filename or "",
            operator_token=x_token,
            operator_role=x_role or "polisher",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return result
