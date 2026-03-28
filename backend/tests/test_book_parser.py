"""Tests for book text parsing functionality.

These tests are initially RED (service not yet implemented).
"""

import pytest
import json


def test_parse_txt_returns_chapters(sample_txt_content):
    """Test that txt parsing returns correct chapter count."""
    from services.book_service import parse_txt

    result = parse_txt(sample_txt_content)
    assert len(result) == 2


def test_parse_txt_chapter_titles(sample_txt_content):
    """Test that txt parsing extracts chapter titles."""
    from services.book_service import parse_txt

    result = parse_txt(sample_txt_content)
    assert result[0]["title"] == "第1章 开始"
    assert result[1]["title"] == "第2章 发展"


def test_parse_txt_chapter_segments(sample_txt_content):
    """Test that txt parsing splits segments by blank lines."""
    from services.book_service import parse_txt

    result = parse_txt(sample_txt_content)
    # First chapter has 3 segments
    assert len(result[0]["segments"]) == 3
    # Second chapter has 2 segments
    assert len(result[1]["segments"]) == 2


def test_parse_txt_segment_content(sample_txt_content):
    """Test that segment text content is preserved."""
    from services.book_service import parse_txt

    result = parse_txt(sample_txt_content)
    assert "这是第一段文字" in result[0]["segments"][0]


def test_parse_txt_no_empty_segments(sample_txt_content):
    """Test that empty segments are filtered out."""
    from services.book_service import parse_txt

    result = parse_txt(sample_txt_content)
    for chapter in result:
        for segment in chapter["segments"]:
            assert segment.strip() != ""


def test_parse_json_returns_chapters(sample_json_content):
    """Test that JSON parsing returns correct chapter count."""
    from services.book_service import parse_json

    result = parse_json(sample_json_content)
    assert len(result) == 2


def test_parse_json_chapter_titles(sample_json_content):
    """Test that JSON parsing extracts chapter titles."""
    from services.book_service import parse_json

    result = parse_json(sample_json_content)
    assert result[0]["title"] == "第一章"
    assert result[1]["title"] == "第二章"


def test_parse_json_segments(sample_json_content):
    """Test that JSON parsing returns correct segments."""
    from services.book_service import parse_json

    result = parse_json(sample_json_content)
    assert len(result[0]["segments"]) == 2
    assert len(result[1]["segments"]) == 1
    assert result[0]["segments"][0] == "这是第一段文字。"


def test_parse_json_string_input(sample_json_content):
    """Test that JSON parsing accepts string input."""
    from services.book_service import parse_json

    json_str = json.dumps(sample_json_content)
    result = parse_json(json_str)
    assert len(result) == 2


def test_parse_txt_chapter_marker_variants():
    """Test various chapter marker formats."""
    from services.book_service import parse_txt

    content = """Chapter 1 The Beginning

First segment here.

Chapter 2 The End

Second chapter segment.
"""
    result = parse_txt(content)
    assert len(result) == 2
    assert "Chapter 1" in result[0]["title"]


def test_parse_txt_single_chapter():
    """Test parsing txt with single chapter."""
    from services.book_service import parse_txt

    content = """第1章 唯一章节

这是唯一的段落。
"""
    result = parse_txt(content)
    assert len(result) == 1
    assert len(result[0]["segments"]) == 1
