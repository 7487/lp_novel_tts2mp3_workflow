"""Book import service: parsing and DB insertion."""

import json
import re
from typing import List, Dict, Any, Union

from sqlalchemy import text
from db.connection import get_db


# Chapter header patterns
CHAPTER_PATTERNS = [
    re.compile(r'^第\s*\d+\s*章', re.MULTILINE),
    re.compile(r'^Chapter\s+\d+', re.MULTILINE | re.IGNORECASE),
    re.compile(r'^第[一二三四五六七八九十百千]+章', re.MULTILINE),
]


def _detect_chapter_starts(lines: List[str]) -> List[int]:
    """Return indices of lines that are chapter headers."""
    header_indices = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        for pattern in CHAPTER_PATTERNS:
            if pattern.match(stripped):
                header_indices.append(i)
                break
    return header_indices


def parse_txt(content: str) -> List[Dict[str, Any]]:
    """Parse txt book content into chapters and segments.

    Chapter markers: lines starting with '第X章' or 'Chapter X'.
    Segments within a chapter are separated by blank lines.

    Returns:
        List of dicts with keys: title, segments (list of str)
    """
    lines = content.splitlines()
    header_indices = _detect_chapter_starts(lines)

    if not header_indices:
        # No chapter markers found: treat entire content as one chapter
        segments = _split_into_segments("\n".join(lines))
        return [{"title": "正文", "segments": segments}]

    chapters = []
    for i, start_idx in enumerate(header_indices):
        end_idx = header_indices[i + 1] if i + 1 < len(header_indices) else len(lines)
        chapter_title = lines[start_idx].strip()
        body_lines = lines[start_idx + 1:end_idx]
        body = "\n".join(body_lines)
        segments = _split_into_segments(body)
        chapters.append({"title": chapter_title, "segments": segments})

    return chapters


def _split_into_segments(text: str) -> List[str]:
    """Split text into segments using blank lines as delimiters."""
    # Split on one or more blank lines
    raw_segments = re.split(r'\n\s*\n', text)
    segments = []
    for seg in raw_segments:
        cleaned = seg.strip()
        if cleaned:
            segments.append(cleaned)
    return segments


def parse_json(content: Union[str, Dict]) -> List[Dict[str, Any]]:
    """Parse JSON book content into chapters and segments.

    Expected format:
        {"title": "...", "chapters": [{"title": "...", "segments": ["text1", ...]}]}
    Or accepts a dict directly.

    Returns:
        List of dicts with keys: title, segments (list of str)
    """
    if isinstance(content, str):
        data = json.loads(content)
    else:
        data = content

    chapters = []
    for chapter in data.get("chapters", []):
        title = chapter.get("title", "")
        segments = [str(s) for s in chapter.get("segments", []) if str(s).strip()]
        chapters.append({"title": title, "segments": segments})

    return chapters


def import_book(title: str, chapters: List[Dict[str, Any]]) -> int:
    """Insert book, chapters, and segments into the database.

    Args:
        title: Book title
        chapters: List of chapter dicts with title and segments

    Returns:
        The new book ID
    """
    with get_db() as conn:
        # Insert book
        result = conn.execute(
            text("INSERT INTO tts2mp3_books (title, status) VALUES (:title, 'importing')"),
            {"title": title}
        )
        book_id = result.lastrowid

        # Insert chapters and segments
        for chapter_no, chapter in enumerate(chapters, start=1):
            chapter_result = conn.execute(
                text(
                    "INSERT INTO tts2mp3_chapters (book_id, chapter_no, title, status) "
                    "VALUES (:book_id, :chapter_no, :title, 'pending')"
                ),
                {
                    "book_id": book_id,
                    "chapter_no": chapter_no,
                    "title": chapter["title"],
                }
            )
            chapter_id = chapter_result.lastrowid

            for segment_no, seg_text in enumerate(chapter["segments"], start=1):
                conn.execute(
                    text(
                        "INSERT INTO tts2mp3_segments "
                        "(chapter_id, segment_no, original_text, status) "
                        "VALUES (:chapter_id, :segment_no, :original_text, 'pending_tts')"
                    ),
                    {
                        "chapter_id": chapter_id,
                        "segment_no": segment_no,
                        "original_text": seg_text,
                    }
                )

        # Update book status to ready
        conn.execute(
            text("UPDATE tts2mp3_books SET status='ready' WHERE id=:book_id"),
            {"book_id": book_id}
        )

    return book_id


def get_books() -> List[Dict[str, Any]]:
    """Retrieve all books with chapter count."""
    with get_db() as conn:
        rows = conn.execute(
            text(
                "SELECT b.id, b.title, b.status, b.created_at, b.updated_at, "
                "COUNT(c.id) AS chapter_count "
                "FROM tts2mp3_books b "
                "LEFT JOIN tts2mp3_chapters c ON c.book_id = b.id "
                "GROUP BY b.id "
                "ORDER BY b.created_at DESC"
            )
        ).fetchall()
    return [dict(row._mapping) for row in rows]


def get_book(book_id: int) -> Dict[str, Any]:
    """Retrieve a single book by ID."""
    with get_db() as conn:
        row = conn.execute(
            text(
                "SELECT b.id, b.title, b.status, b.created_at, b.updated_at, "
                "COUNT(c.id) AS chapter_count "
                "FROM tts2mp3_books b "
                "LEFT JOIN tts2mp3_chapters c ON c.book_id = b.id "
                "WHERE b.id = :book_id "
                "GROUP BY b.id"
            ),
            {"book_id": book_id}
        ).fetchone()
    if row is None:
        return None
    return dict(row._mapping)
