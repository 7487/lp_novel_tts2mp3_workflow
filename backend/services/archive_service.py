"""Archive service: extract txt files from zip/tar archives, detect encoding, parse as book."""

import io
import tarfile
import zipfile
from pathlib import PurePosixPath
from typing import List, Tuple

import chardet

from services.book_service import parse_txt


def _strip_archive_ext(filename: str) -> str:
    """Remove archive extension(s) to get book title."""
    name = filename
    for ext in (".tar.bz2", ".tar.gz", ".tgz", ".tar", ".zip"):
        if name.lower().endswith(ext):
            name = name[: len(name) - len(ext)]
            break
    return name


def _is_safe_root_txt(entry_name: str) -> bool:
    """Return True if entry is a root-level .txt file with no path traversal."""
    p = PurePosixPath(entry_name)
    # Must end with .txt (case-insensitive)
    if p.suffix.lower() != ".txt":
        return False
    # No parent directory parts (root-level only)
    parts = p.parts
    if len(parts) != 1:
        return False
    # No path traversal components
    if ".." in parts:
        return False
    return True


def extract_txt_files(archive_bytes: bytes, filename: str) -> List[Tuple[str, bytes]]:
    """Extract root-level .txt files from zip or tar archive, sorted by filename.

    Security: filters out entries with path traversal (..) or subdirectory paths.

    Args:
        archive_bytes: Raw bytes of the archive file.
        filename: Original filename (used to determine archive format).

    Returns:
        List of (filename, raw_bytes) tuples, sorted by filename.

    Raises:
        ValueError: If format is not supported or no .txt files found.
    """
    lower = filename.lower()

    if lower.endswith(".zip"):
        results = _extract_from_zip(archive_bytes)
    elif (
        lower.endswith(".tar.gz")
        or lower.endswith(".tgz")
        or lower.endswith(".tar.bz2")
        or lower.endswith(".tar")
    ):
        results = _extract_from_tar(archive_bytes)
    else:
        raise ValueError(f"Unsupported archive format: {filename}")

    if not results:
        raise ValueError(f"No .txt files found in archive: {filename}")

    return sorted(results, key=lambda x: x[0])


def _extract_from_zip(archive_bytes: bytes) -> List[Tuple[str, bytes]]:
    """Extract root-level txt files from a zip archive."""
    results = []
    with zipfile.ZipFile(io.BytesIO(archive_bytes), "r") as zf:
        for entry in zf.infolist():
            name = entry.filename
            if _is_safe_root_txt(name):
                raw = zf.read(name)
                results.append((name, raw))
    return results


def _extract_from_tar(archive_bytes: bytes) -> List[Tuple[str, bytes]]:
    """Extract root-level txt files from a tar archive (plain, gz, bz2)."""
    results = []
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:*") as tf:
        for member in tf.getmembers():
            if not member.isfile():
                continue
            name = member.name
            # Filter path traversal and subdirectories
            if not _is_safe_root_txt(name):
                continue
            f = tf.extractfile(member)
            if f is None:
                continue
            raw = f.read()
            results.append((name, raw))
    return results


def decode_txt(raw_bytes: bytes) -> str:
    """Auto-detect encoding with chardet, fallback to UTF-8 if confidence < 0.7.

    Args:
        raw_bytes: Raw bytes of a text file.

    Returns:
        Decoded string.
    """
    detection = chardet.detect(raw_bytes)
    encoding = detection.get("encoding") or "utf-8"
    confidence = detection.get("confidence") or 0.0

    if confidence < 0.7:
        encoding = "utf-8"

    try:
        return raw_bytes.decode(encoding, errors="replace")
    except (LookupError, UnicodeDecodeError):
        return raw_bytes.decode("utf-8", errors="replace")


def parse_archive_as_book(archive_bytes: bytes, filename: str) -> dict:
    """Parse archive into book structure.

    Each txt file in the archive is parsed as a set of chapters using parse_txt.
    All chapters from all txt files are merged in filename-sorted order.

    Args:
        archive_bytes: Raw bytes of the archive file.
        filename: Original archive filename (used for title extraction and format detection).

    Returns:
        {"title": str, "chapters": [{"title": str, "segments": [str]}]}

    Raises:
        ValueError: If no txt files found or format unsupported.
    """
    title = _strip_archive_ext(filename)
    txt_files = extract_txt_files(archive_bytes, filename)

    all_chapters = []
    for txt_name, raw_bytes in txt_files:
        content = decode_txt(raw_bytes)
        chapters = parse_txt(content)
        all_chapters.extend(chapters)

    return {"title": title, "chapters": all_chapters}
