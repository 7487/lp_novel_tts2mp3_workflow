# 数据库 Schema

> **维护方式**：运行 `/sync-context db` 从 MySQL MCP 自动同步，或手动维护。
> **最后同步**：2026-03-28（手动）

## 命名规范

**所有表名必须以 `tts2mp3_` 前缀开头**，详见 `CLAUDE.md` § 编码规范 § 0. 数据库命名规范。

## 何时更新

- 新增/删除/修改表结构后，重新运行 `/sync-context db` 或手动更新本文件
- 保持此文件与 `backend/db/schema.sql` 同步，Claude 会优先读此文件而非直接查库

---

<!-- /sync-context 写入的内容从此处开始 -->

## 数据库：`audiobook_platform`

字符集：`utf8mb4`，排序规则：`utf8mb4_unicode_ci`

---

### tts2mp3_books

书籍主表。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | |
| title | VARCHAR(512) | NOT NULL | 书名 |
| status | ENUM | NOT NULL, DEFAULT 'importing' | `importing` / `ready` / `in_progress` / `done` |
| created_at | DATETIME | NOT NULL, DEFAULT NOW() | |
| updated_at | DATETIME | NOT NULL, ON UPDATE NOW() | |

索引：`idx_tts2mp3_books_status(status)`

---

### tts2mp3_chapters

章节表，属于某本书。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | |
| book_id | INT | NOT NULL, FK → tts2mp3_books(id) CASCADE | |
| chapter_no | INT | NOT NULL | 章节顺序号 |
| title | VARCHAR(512) | NOT NULL DEFAULT '' | 章节标题 |
| status | ENUM | NOT NULL, DEFAULT 'pending' | `pending` / `in_progress` / `chapter_done` / `failed` |
| output_path | VARCHAR(512) | NULL | 合成后章节音频路径 |
| created_at | DATETIME | NOT NULL, DEFAULT NOW() | |
| updated_at | DATETIME | NOT NULL, ON UPDATE NOW() | |

索引：`idx_tts2mp3_chapters_book_id(book_id)`、`idx_tts2mp3_chapters_status(status)`

---

### tts2mp3_segments

片段表，属于某章节。每段对应一段待 TTS 的文本。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | |
| chapter_id | INT | NOT NULL, FK → tts2mp3_chapters(id) CASCADE | |
| segment_no | INT | NOT NULL | 片段顺序号 |
| original_text | TEXT | NOT NULL | 原始文本 |
| status | ENUM | NOT NULL, DEFAULT 'pending_tts' | `pending_tts` / `tts_done` / `passed` / `needs_polish` / `polish_uploaded` / `failed` |
| badcase_tags | JSON | NULL | 不可用时的 badcase 分类标签 |
| modified_text | TEXT | NULL | 标注员修改后的文本 |
| annotation | TEXT | NULL | 标注备注 |
| created_at | DATETIME | NOT NULL, DEFAULT NOW() | |
| updated_at | DATETIME | NOT NULL, ON UPDATE NOW() | |

索引：`idx_tts2mp3_segments_chapter_id(chapter_id)`、`idx_tts2mp3_segments_status(status)`

---

### tts2mp3_segment_versions

片段音频版本表。每个片段可以有多个版本，`is_active=TRUE` 为当前生效版本。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | |
| segment_id | INT | NOT NULL, FK → tts2mp3_segments(id) CASCADE | |
| version_no | INT | NOT NULL | 版本号（从 1 开始递增） |
| source_type | ENUM | NOT NULL | `tts_init` / `tts_regen` / `polish_upload` |
| audio_path | VARCHAR(512) | NULL | 音频文件本地路径 |
| text_content | TEXT | NULL | 生成音频时使用的文本 |
| sample_rate | INT | NULL | 采样率（Hz） |
| channels | INT | NULL | 声道数 |
| duration_ms | INT | NULL | 时长（毫秒） |
| file_size | INT | NULL | 文件大小（字节） |
| is_active | BOOLEAN | NOT NULL, DEFAULT FALSE | 是否为当前生效版本 |
| created_at | DATETIME | NOT NULL, DEFAULT NOW() | |

索引：`idx_tts2mp3_seg_versions_segment_id(segment_id)`、`idx_tts2mp3_seg_versions_is_active(is_active)`

---

### tts2mp3_operation_logs

操作日志表，记录所有状态变更操作。

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INT | PK, AUTO_INCREMENT | |
| operator_token | VARCHAR(64) | NULL | 操作者 token |
| operator_role | ENUM | NULL | `admin` / `annotator` / `polisher` / `qc` |
| action | VARCHAR(64) | NOT NULL | 操作类型（如 `evaluate`、`upload_polish`、`merge_done`） |
| target_type | VARCHAR(32) | NOT NULL | 操作对象类型（`segment` / `chapter` / `book`） |
| target_id | INT | NOT NULL | 操作对象 ID |
| before_status | VARCHAR(32) | NULL | 操作前状态 |
| after_status | VARCHAR(32) | NULL | 操作后状态 |
| extra | JSON | NULL | 附加信息 |
| created_at | DATETIME | NOT NULL, DEFAULT NOW() | |

索引：`idx_tts2mp3_op_logs_target(target_type, target_id)`、`idx_tts2mp3_op_logs_created_at(created_at)`
