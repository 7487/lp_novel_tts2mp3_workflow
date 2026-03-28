# TODO

> 唯一任务源。每轮只允许处理一个任务。
> PRD: docs/PRD.md（有声书生产后台一期）
> 生成时间: 2026-03-28

---

## Phase A — 基础设施（数据库 + 后端骨架）

- [x] T101: 数据库建表脚本
  - 文件: `backend/db/schema.sql`
  - 验收: SQL 脚本可执行，生成 books / chapters / segments / segment_versions / operation_logs 五张表，字段与 PRD 4.1 一致
  - 依赖: 无

- [x] T102: 后端项目骨架
  - 文件: `backend/main.py`, `backend/config.py`, `backend/db/connection.py`, `requirements.txt`, `.env.example`
  - 验收: `uvicorn main:app` 可启动；`GET /health` 返回 `{"status":"ok"}`；MySQL 连接从 .env 读取；项目结构清晰（routers/services/models 分层）
  - 依赖: T101

---

## Phase B — 书籍导入 + TTS Mock

- [x] T103: 写测试 — 书籍文本解析
  - 文件: `backend/tests/test_book_parser.py`
  - 验收: 测试覆盖 txt 解析（按空行切段）和 json 解析（{chapters:[{title,segments:[text]}]}）；测试初始为红灯
  - 依赖: T102

- [x] T104: 实现 — 书籍导入接口
  - 文件: `backend/routers/books.py`, `backend/services/book_service.py`
  - 验收: `POST /api/v1/books` 接收 title + 文件；解析后 books/chapters/segments 写入 DB；T103 测试绿灯；`GET /api/v1/books` 返回书籍列表
  - 依赖: T103

- [x] T105: 写测试 — TTS Mock 服务
  - 文件: `backend/tests/test_tts_service.py`
  - 验收: 测试 Mock TTS 返回固定 wav 字节、写入 segment_versions、片段状态更新为 tts_done；测试初始为红灯
  - 依赖: T102

- [x] T106: 实现 — TTS Mock 接口 + 音频查询
  - 文件: `backend/routers/segments.py`, `backend/services/tts_service.py`
  - 验收: `POST /api/v1/segments/{id}/tts` 调用 Mock TTS，生成 wav 写入本地 `data/audio/`，segment_versions 有记录，is_active=true；T105 测试绿灯；`GET /api/v1/segments/{id}/audio` 可流式返回 wav 文件
  - 依赖: T105

- [x] T107: 实现 — 查询接口全套
  - 文件: `backend/routers/books.py`, `backend/routers/chapters.py`, `backend/routers/segments.py`
  - 验收: `GET /api/v1/books/{id}` / `GET /api/v1/books/{id}/chapters` / `GET /api/v1/chapters/{id}` / `GET /api/v1/chapters/{id}/segments` / `GET /api/v1/segments/{id}` 均返回正确数据；章节接口包含 completion_rate 字段（已完成片段数/总片段数）
  - 依赖: T104

---

## Phase C — 前端

- [x] T108: 前端骨架 + Hash Routing
  - 文件: `frontend/index.html`
  - 验收: TailwindCSS CDN 引入；页面有三个视图区块（admin / annotator / polisher）；URL hash 切换（#admin / #annotator / #polisher）；默认显示 admin 视图；无 JS 框架依赖
  - 依赖: T107

- [x] T109: 管理员视图
  - 文件: `frontend/index.html`（管理员视图部分）
  - 验收: 书籍列表展示（书名、状态、章节数）；"导入书籍"按钮（弹窗：填书名 + 上传文件）；章节列表（带完成度进度条）；每章节行有"触发 TTS"按钮（调用后端批量触发当前章节所有 pending_tts 片段）；AC-1/AC-2 通过
  - 依赖: T108

- [x] T110: 标注员评估工作台
  - 文件: `frontend/index.html`（标注员视图部分）
  - 验收: 左侧片段列表（章节选择器 + 片段状态色块）；右侧作答区：音频播放器（播放/暂停/进度条/1x-2x 倍速）；可用/不可用单选按钮；选"不可用"时展开扩展表单（badcase 多选下拉、修改后文本输入框默认带入原始文本、备注）；提交按钮；AC-3/AC-4/AC-5 通过
  - 依赖: T108

---

## Phase D — 评估接口 + 精雕上传 + 章节 Merge

- [x] T111: 写测试 — 评估接口状态机
  - 文件: `backend/tests/test_evaluate.py`
  - 验收: 测试"可用"路径（passed 状态）、"不可用"路径（needs_polish 状态）、必填校验（不可用时 badcase_tags 为空报错）；测试初始为红灯
  - 依赖: T106

- [x] T112: 实现 — 片段评估接口
  - 文件: `backend/routers/segments.py`, `backend/services/evaluation_service.py`
  - 验收: `POST /api/v1/segments/{id}/evaluate` 接收 can_use/badcase_tags/modified_text/annotation；状态机流转正确；不可用时 badcase_tags 必填；T111 测试绿灯；写入 operation_logs
  - 依赖: T111

- [x] T113: 写测试 — 精雕上传 + 格式校验
  - 文件: `backend/tests/test_upload.py`
  - 验收: 测试正常上传（wav 正确格式）→ 新版本 is_active=true；测试采样率不一致 → 返回 400；测试文件类型非 wav → 返回 400；测试初始为红灯
  - 依赖: T106

- [x] T114: 实现 — 精雕上传接口
  - 文件: `backend/routers/segments.py`, `backend/services/upload_service.py`
  - 验收: `POST /api/v1/segments/{id}/upload` 接收 wav 文件；校验格式（pydub 读取采样率/声道/时长）；生成 segment_versions 记录，is_active=true；片段状态变 polish_uploaded；写入 operation_logs；T113 测试绿灯
  - 依赖: T113

- [x] T115: 写测试 — 章节自动 merge
  - 文件: `backend/tests/test_merge.py`
  - 验收: 测试全部片段就绪时自动触发 merge → chapters.output_path 有值、状态变 chapter_done；测试采样率不一致时 merge 失败 → 状态变 failed、error 写入 operation_logs；测试初始为红灯
  - 依赖: T114

- [x] T116: 实现 — 章节自动 merge
  - 文件: `backend/services/merge_service.py`, `backend/routers/chapters.py`
  - 验收: 精雕上传/评估通过后检查章节完成度；完成度 100% 时自动调用 pydub 按 segment_no 排序拼接；merge 结果写入 `data/output/{chapter_id}.wav`；T115 测试绿灯；`POST /api/v1/chapters/{id}/merge` 可手动触发；`GET /api/v1/chapters/{id}/output` 下载成品
  - 依赖: T115

---

## Phase E — 精雕前端视图 + 日志 + 集成验收

- [x] T117: 精雕老师视图
  - 文件: `frontend/index.html`（精雕视图部分）
  - 验收: 待处理片段列表（状态 needs_polish）；点击片段查看原始文本 + 标注员 badcase 备注；上传 wav 区域（拖拽/点击）；上传成功后 Mini 播放器试听；确认提交按钮；AC-6/AC-7 通过
  - 依赖: T110, T114

- [x] T118: 操作日志接口 + 管理员日志面板
  - 文件: `backend/routers/logs.py`, `frontend/index.html`（日志面板）
  - 验收: `GET /api/v1/logs?target_type=&target_id=&limit=` 返回操作日志列表；管理员视图有简单日志查看面板（最近 20 条）；AC-10 通过
  - 依赖: T112, T116

- [x] T119: 端到端集成验收
  - 文件: `backend/tests/test_e2e.py`（或手动测试 checklist）
  - 验收: 按顺序执行：导入书籍 → 触发 TTS → 标注员评估（可用 + 不可用两条路径）→ 精雕上传 → 章节自动 merge → 管理员下载成品；AC-1 到 AC-11 全部通过
  - 依赖: T117, T118
