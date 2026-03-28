-- Audiobook Production Platform Database Schema
-- MySQL 8.0+

CREATE DATABASE IF NOT EXISTS audiobook_platform DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE audiobook_platform;

-- Books table
CREATE TABLE IF NOT EXISTS tts2mp3_books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(512) NOT NULL,
    status ENUM('importing', 'ready', 'in_progress', 'done') NOT NULL DEFAULT 'importing',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_tts2mp3_books_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Chapters table
CREATE TABLE IF NOT EXISTS tts2mp3_chapters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    chapter_no INT NOT NULL,
    title VARCHAR(512) NOT NULL DEFAULT '',
    status ENUM('pending', 'in_progress', 'chapter_done', 'failed') NOT NULL DEFAULT 'pending',
    output_path VARCHAR(512) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES tts2mp3_books(id) ON DELETE CASCADE,
    INDEX idx_tts2mp3_chapters_book_id (book_id),
    INDEX idx_tts2mp3_chapters_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Segments table
CREATE TABLE IF NOT EXISTS tts2mp3_segments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    chapter_id INT NOT NULL,
    segment_no INT NOT NULL,
    original_text TEXT NOT NULL,
    status ENUM('pending_tts', 'tts_done', 'passed', 'needs_polish', 'polish_uploaded', 'failed') NOT NULL DEFAULT 'pending_tts',
    badcase_tags JSON DEFAULT NULL,
    modified_text TEXT DEFAULT NULL,
    annotation TEXT DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (chapter_id) REFERENCES tts2mp3_chapters(id) ON DELETE CASCADE,
    INDEX idx_tts2mp3_segments_chapter_id (chapter_id),
    INDEX idx_tts2mp3_segments_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Segment versions table
CREATE TABLE IF NOT EXISTS tts2mp3_segment_versions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    segment_id INT NOT NULL,
    version_no INT NOT NULL,
    source_type ENUM('tts_init', 'tts_regen', 'polish_upload') NOT NULL,
    audio_path VARCHAR(512) DEFAULT NULL,
    text_content TEXT DEFAULT NULL,
    sample_rate INT DEFAULT NULL,
    channels INT DEFAULT NULL,
    duration_ms INT DEFAULT NULL,
    file_size INT DEFAULT NULL,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (segment_id) REFERENCES tts2mp3_segments(id) ON DELETE CASCADE,
    INDEX idx_tts2mp3_seg_versions_segment_id (segment_id),
    INDEX idx_tts2mp3_seg_versions_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Operation logs table
CREATE TABLE IF NOT EXISTS tts2mp3_operation_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    operator_token VARCHAR(64) DEFAULT NULL,
    operator_role ENUM('admin', 'annotator', 'polisher', 'qc') DEFAULT NULL,
    action VARCHAR(64) NOT NULL,
    target_type VARCHAR(32) NOT NULL,
    target_id INT NOT NULL,
    before_status VARCHAR(32) DEFAULT NULL,
    after_status VARCHAR(32) DEFAULT NULL,
    extra JSON DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tts2mp3_op_logs_target (target_type, target_id),
    INDEX idx_tts2mp3_op_logs_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
