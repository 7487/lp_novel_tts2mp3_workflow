"""Books router."""

import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from services.book_service import parse_txt, parse_json, import_book, get_books, get_book

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
