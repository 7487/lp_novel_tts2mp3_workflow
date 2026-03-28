"""Chapters router."""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from services.chapter_service import get_chapters_for_book, get_chapter
from services.merge_service import merge_chapter

router = APIRouter(tags=["chapters"])


@router.get("/books/{book_id}/chapters")
async def list_chapters(book_id: int):
    """Return chapters for a book with completion_rate."""
    return get_chapters_for_book(book_id)


@router.get("/chapters/{chapter_id}")
async def get_chapter_detail(chapter_id: int):
    """Return chapter detail with completion_rate."""
    chapter = get_chapter(chapter_id)
    if chapter is None:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter


@router.post("/chapters/{chapter_id}/merge")
async def trigger_merge(chapter_id: int):
    """Manually trigger chapter merge."""
    try:
        result = merge_chapter(chapter_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return result


@router.get("/chapters/{chapter_id}/output")
async def download_output(chapter_id: int):
    """Download the merged output WAV file for a chapter."""
    chapter = get_chapter(chapter_id)
    if chapter is None:
        raise HTTPException(status_code=404, detail="Chapter not found")

    output_path = chapter.get("output_path")
    if not output_path or not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Output file not found")

    return FileResponse(
        output_path,
        media_type="audio/wav",
        filename=f"chapter_{chapter_id}.wav",
    )
