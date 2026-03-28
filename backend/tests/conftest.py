"""Pytest configuration and shared fixtures."""

import os
import sys
import pytest

# Ensure backend is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_txt_content():
    """Sample txt book content with chapters and segments."""
    return """第1章 开始

这是第一段文字。这段文字描述了故事的开头。

这是第二段文字。主角登场了。

这是第三段文字。故事展开。

第2章 发展

这是第二章第一段。情节逐渐发展。

这是第二章第二段。矛盾开始出现。
"""


@pytest.fixture
def sample_json_content():
    """Sample JSON book content."""
    return {
        "title": "测试书籍",
        "chapters": [
            {
                "title": "第一章",
                "segments": [
                    "这是第一段文字。",
                    "这是第二段文字。",
                ]
            },
            {
                "title": "第二章",
                "segments": [
                    "第二章第一段。",
                ]
            }
        ]
    }
