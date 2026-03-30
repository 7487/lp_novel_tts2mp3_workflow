"""Tests for archive_service: zip/tar extraction, encoding detection, book title extraction.

These tests are initially RED (service doesn't exist yet).
"""

import io
import tarfile
import zipfile

import pytest


def _make_zip(files: dict) -> bytes:
    """Create an in-memory zip archive. files = {name: bytes_content}."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


def _make_tar(files: dict, mode: str = "w") -> bytes:
    """Create an in-memory tar archive. files = {name: bytes_content}.
    mode: 'w' for plain tar, 'w:gz' for tar.gz, 'w:bz2' for tar.bz2.
    """
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode=mode) as tf:
        for name, content in files.items():
            data = content if isinstance(content, bytes) else content.encode("utf-8")
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


# ---------------------------------------------------------------------------
# T1: zip returns sorted txt files
# ---------------------------------------------------------------------------

def test_extract_zip_returns_sorted_txt_files():
    from services.archive_service import extract_txt_files

    zip_bytes = _make_zip({
        "chapter_b.txt": b"content b",
        "chapter_a.txt": b"content a",
    })
    result = extract_txt_files(zip_bytes, "mybook.zip")
    names = [r[0] for r in result]
    assert names == sorted(names)
    assert len(result) == 2
    assert all(name.endswith(".txt") for name in names)


# ---------------------------------------------------------------------------
# T2: tar returns sorted txt files
# ---------------------------------------------------------------------------

def test_extract_tar_returns_sorted_txt_files():
    from services.archive_service import extract_txt_files

    tar_bytes = _make_tar({
        "chapter_b.txt": b"content b",
        "chapter_a.txt": b"content a",
    }, mode="w")
    result = extract_txt_files(tar_bytes, "mybook.tar")
    names = [r[0] for r in result]
    assert names == sorted(names)
    assert len(result) == 2


# ---------------------------------------------------------------------------
# T3: tar.gz returns sorted txt files
# ---------------------------------------------------------------------------

def test_extract_tar_gz_returns_sorted_txt_files():
    from services.archive_service import extract_txt_files

    tar_bytes = _make_tar({
        "z_last.txt": b"content z",
        "a_first.txt": b"content a",
    }, mode="w:gz")
    result = extract_txt_files(tar_bytes, "mybook.tar.gz")
    names = [r[0] for r in result]
    assert names == sorted(names)
    assert len(result) == 2


# ---------------------------------------------------------------------------
# T4: GBK encoding detected and decoded
# ---------------------------------------------------------------------------

def test_gbk_encoding_detected_and_decoded():
    from services.archive_service import decode_txt

    chinese = "这是一段中文内容，用于测试GBK编码检测。"
    gbk_bytes = chinese.encode("gbk")
    result = decode_txt(gbk_bytes)
    assert result == chinese


# ---------------------------------------------------------------------------
# T5: subdirectory txt files ignored (only root-level)
# ---------------------------------------------------------------------------

def test_subdirectory_txt_ignored():
    from services.archive_service import extract_txt_files

    zip_bytes = _make_zip({
        "root.txt": b"root content",
        "subdir/nested.txt": b"nested content",
    })
    result = extract_txt_files(zip_bytes, "mybook.zip")
    names = [r[0] for r in result]
    assert "root.txt" in names
    assert not any("subdir" in n or "/" in n for n in names)
    assert len(result) == 1


# ---------------------------------------------------------------------------
# T6: no txt files raises ValueError
# ---------------------------------------------------------------------------

def test_no_txt_raises_value_error():
    from services.archive_service import extract_txt_files

    zip_bytes = _make_zip({
        "image.jpg": b"\xff\xd8\xff",
        "doc.pdf": b"%PDF",
    })
    with pytest.raises(ValueError, match="No .txt"):
        extract_txt_files(zip_bytes, "mybook.zip")


# ---------------------------------------------------------------------------
# T7: unsupported format raises ValueError
# ---------------------------------------------------------------------------

def test_unsupported_format_raises_value_error():
    from services.archive_service import extract_txt_files

    with pytest.raises(ValueError, match="[Uu]nsupported"):
        extract_txt_files(b"%PDF-1.4 fake data", "document.pdf")


# ---------------------------------------------------------------------------
# T8: book title extracted from filename
# ---------------------------------------------------------------------------

def test_book_title_extracted_from_filename():
    from services.archive_service import _strip_archive_ext

    assert _strip_archive_ext("三体.zip") == "三体"
    assert _strip_archive_ext("novel.tar.gz") == "novel"
    assert _strip_archive_ext("book.tar.bz2") == "book"
    assert _strip_archive_ext("story.tar") == "story"
    assert _strip_archive_ext("work.tgz") == "work"


# ---------------------------------------------------------------------------
# T9: path traversal entries filtered out
# ---------------------------------------------------------------------------

def test_path_traversal_filtered():
    from services.archive_service import extract_txt_files

    # Build a tar with a path-traversal entry
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        # Legitimate file
        data = b"safe content"
        info = tarfile.TarInfo(name="safe.txt")
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))

        # Malicious path-traversal entry
        evil_data = b"evil content"
        evil_info = tarfile.TarInfo(name="../etc/passwd")
        evil_info.size = len(evil_data)
        tf.addfile(evil_info, io.BytesIO(evil_data))

    tar_bytes = buf.getvalue()
    result = extract_txt_files(tar_bytes, "archive.tar")
    names = [r[0] for r in result]
    assert "safe.txt" in names
    assert "../etc/passwd" not in names
    assert not any(".." in n for n in names)


# ---------------------------------------------------------------------------
# T10: parse_archive_as_book returns correct structure
# ---------------------------------------------------------------------------

def test_parse_archive_as_book_structure():
    from services.archive_service import parse_archive_as_book

    txt1 = "第1章 开始\n\n这是第一段。\n\n这是第二段。\n"
    txt2 = "第2章 结束\n\n这是结尾。\n"
    zip_bytes = _make_zip({
        "a_chapter.txt": txt1.encode("utf-8"),
        "b_chapter.txt": txt2.encode("utf-8"),
    })

    result = parse_archive_as_book(zip_bytes, "三体.zip")
    assert result["title"] == "三体"
    assert isinstance(result["chapters"], list)
    assert len(result["chapters"]) >= 1
    # Each chapter must have title and segments
    for chapter in result["chapters"]:
        assert "title" in chapter
        assert "segments" in chapter
        assert isinstance(chapter["segments"], list)
