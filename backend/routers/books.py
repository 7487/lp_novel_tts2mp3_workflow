"""Books router."""

import json
from typing import List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from services.book_service import parse_txt, parse_json, import_book, get_books, get_book
from services.archive_service import parse_archive_as_book

router = APIRouter(tags=["books"])


@router.post("/books")
async def create_book(
    title: str = Form(...),
    file: UploadFile = File(...),
):
    """Import a book from a txt or json file.

    Args:
        title: Book title
        file: Text file (.txt or .json) with chapter content
    """
    content_bytes = await file.read()
    content_str = content_bytes.decode("utf-8", errors="replace")
    filename = file.filename or ""

    if filename.lower().endswith(".json"):
        try:
            chapters = parse_json(content_str)
        except (json.JSONDecodeError, KeyError) as exc:
            raise HTTPException(status_code=400, detail=f"Invalid JSON format: {exc}")
    else:
        # Default: treat as txt
        chapters = parse_txt(content_str)

    if not chapters:
        raise HTTPException(status_code=400, detail="No chapters found in file")

    book_id = import_book(title, chapters)
    return {"id": book_id, "title": title, "status": "ready"}


@router.get("/books")
async def list_books():
    """Return list of all books."""
    books = get_books()
    # Serialize datetime objects
    result = []
    for book in books:
        result.append({
            "id": book["id"],
            "title": book["title"],
            "status": book["status"],
            "chapter_count": book["chapter_count"],
            "created_at": str(book["created_at"]),
            "updated_at": str(book["updated_at"]),
        })
    return result


@router.get("/books/{book_id}")
async def get_book_detail(book_id: int):
    """Return a single book by ID."""
    book = get_book(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return {
        "id": book["id"],
        "title": book["title"],
        "status": book["status"],
        "chapter_count": book["chapter_count"],
        "created_at": str(book["created_at"]),
        "updated_at": str(book["updated_at"]),
    }


_MAX_BATCH_FILES = 20
_MAX_FILE_BYTES = 50 * 1024 * 1024  # 50 MB


@router.post("/books/batch-archive")
async def batch_import_archives(
    files: List[UploadFile] = File(...),
):
    """Batch import books from zip/tar archives.

    Each archive becomes one book. Book title is extracted from filename.
    Returns succeeded and failed lists.
    Max 20 files per request. Max 50MB per file.
    """
    if len(files) > _MAX_BATCH_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files: max {_MAX_BATCH_FILES} per request, got {len(files)}",
        )

    succeeded = []
    failed = []

    for upload in files:
        filename = upload.filename or "unknown"
        try:
            archive_bytes = await upload.read()

            if len(archive_bytes) > _MAX_FILE_BYTES:
                failed.append({"filename": filename, "error": "文件过大（超过 50MB）"})
                continue

            book_data = parse_archive_as_book(archive_bytes, filename)
            book_id = import_book(book_data["title"], book_data["chapters"])

            succeeded.append({
                "filename": filename,
                "book_id": book_id,
                "book_title": book_data["title"],
                "chapter_count": len(book_data["chapters"]),
            })

        except ValueError as exc:
            failed.append({"filename": filename, "error": str(exc)})
        except Exception as exc:
            failed.append({"filename": filename, "error": f"导入失败: {exc}"})

    return {"succeeded": succeeded, "failed": failed}
