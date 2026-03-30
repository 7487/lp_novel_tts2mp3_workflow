# STATE

> 项目进度追踪。每轮任务结束后由 Agent 更新。

---

## Overview

| 字段            | 值                                          |
| --------------- | ------------------------------------------- |
| Current Phase   | ALL PHASES COMPLETE (including Phase F)     |
| Last Completed  | T123                                        |
| Active Task     | —                                           |
| Next Task       | —                                           |
| Total Completed | 23 / 23                                     |

---

## Repository Baseline

> 仅在仓库结构发生重大变更时更新。

- 技术栈：Python 3.11 + FastAPI + MySQL + TailwindCSS（单 HTML）
- 后端目录：`backend/`（routers / services / db / tests）
- 前端：`frontend/index.html`（单页，TailwindCSS）
- 音频存储：`data/audio/{segment_id}/v{version_no}.wav`（本地，一期）
- 章节成品：`data/output/{chapter_id}.wav`
- 配置：`.env`（MySQL DSN、数据目录、TTS 配置）

---

## Blockers

> 当前无阻塞项。

---

## Active Task

> 当前无活跃任务。运行 /execute 开始执行 T120。

---

## Phase Progress

### Phase A — 基础设施（数据库 + 后端骨架）

| TODO | 描述                    | 状态      |
| ---- | ----------------------- | --------- |
| T101 | 数据库建表脚本          | completed |
| T102 | 后端项目骨架            | completed |

### Phase B — 书籍导入 + TTS Mock

| TODO | 描述                         | 状态      |
| ---- | ---------------------------- | --------- |
| T103 | 写测试 — 书籍文本解析        | completed |
| T104 | 实现 — 书籍导入接口          | completed |
| T105 | 写测试 — TTS Mock 服务       | completed |
| T106 | 实现 — TTS Mock 接口 + 音频查询 | completed |
| T107 | 实现 — 查询接口全套          | completed |

### Phase C — 前端

| TODO | 描述                         | 状态      |
| ---- | ---------------------------- | --------- |
| T108 | 前端骨架 + Hash Routing      | completed |
| T109 | 管理员视图                   | completed |
| T110 | 标注员评估工作台             | completed |

### Phase D — 评估接口 + 精雕上传 + 章节 Merge

| TODO | 描述                         | 状态      |
| ---- | ---------------------------- | --------- |
| T111 | 写测试 — 评估接口状态机      | completed |
| T112 | 实现 — 片段评估接口          | completed |
| T113 | 写测试 — 精雕上传 + 格式校验 | completed |
| T114 | 实现 — 精雕上传接口          | completed |
| T115 | 写测试 — 章节自动 merge      | completed |
| T116 | 实现 — 章节自动 merge        | completed |

### Phase E — 精雕前端视图 + 日志 + 集成验收

| TODO | 描述                          | 状态      |
| ---- | ----------------------------- | --------- |
| T117 | 精雕老师视图                  | completed |
| T118 | 操作日志接口 + 管理员日志面板 | completed |
| T119 | 端到端集成验收                | completed |

### Phase F — 批量压缩包书籍导入

| TODO | 描述                                      | 状态    |
| ---- | ----------------------------------------- | ------- |
| T120 | 写测试 — archive_service                  | completed |
| T121 | 实现 — archive_service.py                 | completed |
| T122 | 实现 — POST /api/v1/books/batch-archive   | completed |
| T123 | 前端 — 管理员视图批量导入压缩包入口       | completed |

---

## Completed Task Log

> 逆序记录。

| Task | 描述 | 完成时间 |
|------|------|---------|
| T123 | 前端管理员视图批量导入压缩包入口（modal + JS） | 2026-03-28 |
| T122 | POST /api/v1/books/batch-archive 接口（max 20 files, 50MB/file） | 2026-03-28 |
| T121 | archive_service.py（extract_txt_files/decode_txt/parse_archive_as_book + chardet） | 2026-03-28 |
| T120 | 写测试 — archive_service（10 tests, 初始红灯） | 2026-03-28 |
| T119 | 端到端集成验收（45 tests 全部通过） | 2026-03-28 |
| T118 | 操作日志接口 + 管理员日志面板 | 2026-03-28 |
| T117 | 精雕老师视图（集成在 frontend/index.html） | 2026-03-28 |
| T116 | 章节自动 merge（merge_service.py + chapters router） | 2026-03-28 |
| T115 | 写测试 — 章节自动 merge | 2026-03-28 |
| T114 | 精雕上传接口（upload_service.py） | 2026-03-28 |
| T113 | 写测试 — 精雕上传格式校验 | 2026-03-28 |
| T112 | 片段评估接口（evaluation_service.py） | 2026-03-28 |
| T111 | 写测试 — 评估接口状态机 | 2026-03-28 |
| T110 | 标注员评估工作台（frontend/index.html） | 2026-03-28 |
| T109 | 管理员视图（frontend/index.html） | 2026-03-28 |
| T108 | 前端骨架 + Hash Routing | 2026-03-28 |
| T107 | 查询接口全套（chapter_service.py） | 2026-03-28 |
| T106 | TTS Mock 接口 + 音频流（tts_service.py） | 2026-03-28 |
| T105 | 写测试 — TTS Mock 服务 | 2026-03-28 |
| T104 | 书籍导入接口（book_service.py + books router） | 2026-03-28 |
| T103 | 写测试 — 书籍文本解析 | 2026-03-28 |
| T102 | 后端项目骨架（main.py, config.py, db/connection.py） | 2026-03-28 |
| T101 | 数据库建表脚本（schema.sql） | 2026-03-28 |

---

## Architecture Decisions

> 关键技术决策记录。

- **2026-03-28**: 采用方案二一体化后台，MySQL 替代 SQLite（用户确认）
- **2026-03-28**: 前端维护单一 index.html，TailwindCSS CDN，无 JS 框架
- **2026-03-28**: 音频 merge 用 pydub 在后端执行，一期本地文件系统存储
- **2026-03-28**: TTS 一期 Mock，真实接口参考 listenpal-crawler/scripts/rich_txt_tts.py（tts-t.zuoyebang.com）
- **2026-03-28**: Token 轻鉴权（X-Token 请求头），不做 RBAC
- **2026-03-28**: 测试层全部使用 mock DB（patch get_db），不依赖真实 MySQL，CI 无需数据库
- **2026-03-28**: evaluation_service 和 upload_service 中章节完成度检查触发 merge 采用 try/except 包裹（非阻塞）
- **2026-03-28**: SQLAlchemy Core + pymysql（非 ORM），sync 模式，FastAPI 路由层 async 包装
