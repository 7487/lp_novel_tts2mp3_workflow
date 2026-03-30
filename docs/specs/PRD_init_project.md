# PRD — 有声书生产后台（一期）

> 产品需求文档。覆盖任务流转 + TTS 生成 + 片段评估返工 + 精雕结果上传 + 章节自动重组完整链路。

---

## 审批状态

<!-- 审批门：设计未审批前不得开始编码 -->

- **状态**: `approved`
- **审批人**: 齐郅
- **审批日期**: 2026-03-28
- **关联 TODO**: T101 起

---

## 1. 问题定义（What & Why）

### 1.1 问题描述

有声书生产流程当前依赖 Excel 线下流转：标注员手动核对文本、播放音频、填写修改意见、粘贴新音频链接，精雕老师线下完成后人工整理文件并替换，章节合并需要手动拼接。存在以下问题：

1. 评估与返工信息结构化程度低，无法强约束必填逻辑，漏填、错填频繁。
2. 精雕结果回传后，仍需人工下载、整理、改名、替换，造成明显人力瓶颈。
3. 各阶段依赖钉钉沟通，状态不透明、不可追踪、不可审计。
4. 缺乏片段级版本管理，无法知道某章节当前生效的是哪一版音频。

### 1.2 目标

- 目标 1：将 Excel 标注流程迁移至线上，标注员全量切换到系统内操作
- 目标 2：实现"任务导入 → TTS 批量生成 → 片段评估/返工 → 精雕上传 → 章节自动重组"完整闭环
- 目标 3：建立统一任务状态机和操作日志，所有操作可追踪

### 1.3 非目标

- 一期不做自动抽卡链路（后续二期加入）
- 一期不做完整质检工作台（质检状态字段预留，UI 不实现）
- 一期不对接上架/运营系统（webhook 预留但不接入）
- 一期不做 RBAC 细粒度权限（token 轻鉴权即可）
- 一期 TTS 接口先 Mock，预留真实接入扩展点

---

## 2. 用户故事 / 使用场景

### 场景 1：标注员评估片段音频

> 作为标注员，我希望在线上工作台试听音频并提交评估结果，以便替换 Excel 标注，减少漏填和错填。

**前置条件**: 管理员已导入书籍章节任务，TTS 已为每个片段生成初始音频。

**操作流程**:
1. 进入评估工作台，左侧列出当前章节所有片段任务
2. 点击某片段，加载原始文本和初始音频（支持播放/暂停/倍速）
3. 判定：选择【可用】→ 直接提交，片段状态变更为 `passed`
4. 判定：选择【不可用】→ 展开扩展表单，填写 badcase 分类（多选）、修改后文本（默认带入原始文本）、备注
5. 选择返工方式：① 页面内一键 TTS 重生成（调用 Mock/真实 TTS 接口）；② 等待精雕老师上传
6. 提交后片段状态变更为 `needs_polish` 或 `pending_tts`

**预期结果**: 片段评估结果结构化存储，无法跳过必填项。

---

### 场景 2：精雕老师上传精雕结果

> 作为精雕老师，我希望按片段任务上传精雕后的 wav 文件，以便系统自动绑定版本并触发章节重组，不再需要人工整理和替换。

**前置条件**: 片段处于 `needs_polish` 状态，标注员已填写 badcase 和修改文本。

**操作流程**:
1. 进入精雕上传页，查看待处理片段列表
2. 选择具体片段任务，查看原始文本和标注员备注
3. 上传精雕后的 wav 文件，系统校验格式（采样率、编码、声道、文件大小）
4. 上传成功后，页面内显示 Mini 播放器供复核试听
5. 确认后提交，系统生成新的片段版本并标记为当前生效版本（is_active=true）

**预期结果**: 片段状态变更为 `polish_uploaded`，触发章节完成度检查，若章节所有片段已就绪则自动触发 merge。

---

### 场景 3：管理员导入书籍并触发 TTS

> 作为管理员，我希望通过后台页面导入一本书的章节文本，以便系统自动切分片段并批量触发 TTS 生成，不再依赖脚本手动操作。

**前置条件**: 已有书籍的纯文本文件（按章节和片段结构化）。

**操作流程**:
1. 进入管理后台，点击"导入书籍"
2. 填写书名、上传文本文件（支持 txt/json 格式）
3. 系统自动切分章节和片段，初始化片段任务（stage=tts）
4. 管理员点击"批量触发 TTS"，系统按片段调用 TTS 接口（Mock 或真实）
5. TTS 完成后，片段状态变更为 `tts_done`，进入评估队列

**预期结果**: 书籍所有片段均有初始音频，评估工作台可正常展示。

---

### 场景 4：章节自动重组

> 作为系统，当章节内所有片段均达到可用状态时，自动按顺序拼接 wav 文件生成章节成品，不再需要人工 merge。

**前置条件**: 章节内所有片段状态为 `passed` 或 `polish_uploaded`，且均有生效版本音频。

**操作流程**:
1. 系统检测到章节完成度 = 100%
2. 自动读取所有片段的 active version 音频文件，按 segment_order 排序
3. 使用 pydub 拼接 wav（复用 merge_wav / merge_audio 逻辑）
4. 格式校验（采样率一致性等）
5. 生成章节成品音频，记录到 chapter_outputs 表
6. 章节状态变更为 `chapter_done`，可供下游复核

**预期结果**: 章节成品可在管理后台下载，操作日志记录 merge 触发时间和结果。

---

## 3. 设计方案

### 方案 A：一体化生产后台（选定方案）

**描述**: 统一后台覆盖四个角色（管理员、标注员、精雕老师、质检员），前端单 HTML 页面（TailwindCSS），后端 Python FastAPI + MySQL，章节 merge 由后端 pydub/ffmpeg 执行。

**优点**:
- 业务闭环完整，一期结束即可显著降低线下沟通和人工 merge 成本
- 数据模型统一，为二期自动抽卡和精雕 API 接入提供底座
- 复用现有 TTS 脚本和 merge 脚本逻辑，降低实现风险

**缺点**:
- 前端单页多模块，需要合理组织视图切换逻辑
- MySQL + 状态机设计要求较高，需一次设计清楚

**工作量**: L（12-16 个 TODO）

### 推荐方案

**推荐**: 方案 A（一体化生产后台）
**理由**: 与一期设计文档（一期-任务流转+TTS.md）完全对齐；成功标准要求标注员全量切换，必须覆盖完整链路。

---

## 4. 接口设计 / 数据结构

### 4.1 数据库表设计（MySQL）

```sql
-- 书籍
books
  id            INT AUTO_INCREMENT PK
  title         VARCHAR(255) NOT NULL
  status        ENUM('importing','ready','in_progress','done') DEFAULT 'importing'
  created_at    DATETIME
  updated_at    DATETIME

-- 章节
chapters
  id            INT AUTO_INCREMENT PK
  book_id       INT FK books.id
  chapter_no    INT          -- 章节序号
  title         VARCHAR(255)
  status        ENUM('pending','in_progress','chapter_done','failed') DEFAULT 'pending'
  output_path   VARCHAR(512) -- merge 后成品路径
  created_at    DATETIME
  updated_at    DATETIME

-- 片段
segments
  id            INT AUTO_INCREMENT PK
  chapter_id    INT FK chapters.id
  segment_no    INT          -- 片段序号（决定 merge 顺序）
  original_text TEXT
  status        ENUM('pending_tts','tts_done','passed','needs_polish','polish_uploaded','failed') DEFAULT 'pending_tts'
  badcase_tags  JSON         -- 不可用时的 badcase 分类
  modified_text TEXT         -- 标注员修改后文本
  annotation    TEXT         -- 备注
  created_at    DATETIME
  updated_at    DATETIME

-- 片段版本（每次生成/上传产生一个版本）
segment_versions
  id            INT AUTO_INCREMENT PK
  segment_id    INT FK segments.id
  version_no    INT
  source_type   ENUM('tts_init','tts_regen','polish_upload')
  audio_path    VARCHAR(512) -- 本地文件路径（一期）
  text_content  TEXT
  sample_rate   INT
  channels      INT
  duration_ms   INT
  file_size     INT
  is_active     BOOLEAN DEFAULT FALSE
  created_at    DATETIME

-- 操作日志
operation_logs
  id            INT AUTO_INCREMENT PK
  operator_token VARCHAR(64)
  operator_role  ENUM('admin','annotator','polisher','qc')
  action         VARCHAR(64)  -- e.g. tts_triggered, evaluated, polish_uploaded, chapter_merged
  target_type    VARCHAR(32)  -- segment / chapter / book
  target_id      INT
  before_status  VARCHAR(32)
  after_status   VARCHAR(32)
  extra          JSON         -- 额外上下文
  created_at     DATETIME
```

### 4.2 核心 API 接口

```
# 书籍管理
GET  /api/v1/books                      # 书籍列表
POST /api/v1/books                      # 导入书籍（title + text file）
GET  /api/v1/books/{book_id}            # 书籍详情

# 章节
GET  /api/v1/books/{book_id}/chapters   # 章节列表
GET  /api/v1/chapters/{chapter_id}      # 章节详情 + 完成度

# 片段
GET  /api/v1/chapters/{chapter_id}/segments          # 片段列表
GET  /api/v1/segments/{segment_id}                   # 片段详情（含当前版本）
POST /api/v1/segments/{segment_id}/tts               # 触发 TTS（Mock/真实）
POST /api/v1/segments/{segment_id}/evaluate          # 提交评估（can_use: bool, badcase_tags, modified_text, annotation）
POST /api/v1/segments/{segment_id}/upload            # 上传精雕音频（multipart/form-data）
GET  /api/v1/segments/{segment_id}/audio             # 流式返回音频文件

# 章节 merge
POST /api/v1/chapters/{chapter_id}/merge             # 手动触发 merge（自动触发无需调用）
GET  /api/v1/chapters/{chapter_id}/output            # 下载章节成品

# 日志
GET  /api/v1/logs?target_type=&target_id=            # 操作日志查询
```

### 4.3 前端页面模块（单 HTML + TailwindCSS）

```
index.html
├── [管理员视图]
│   ├── 书籍列表 + 导入入口
│   ├── 章节列表 + 完成度进度条
│   └── 触发 TTS / 查看日志
├── [标注员视图]
│   ├── 片段评估工作台（左侧列表 + 右侧作答区）
│   ├── 音频播放器（播放/暂停/进度/倍速）
│   ├── 可用/不可用分支表单（条件联动展示）
│   └── 页面内一键 TTS 重生成
└── [精雕老师视图]
    ├── 待处理片段列表
    ├── 上传音频 + Mini 播放器复核
    └── 提交确认
```

---

## 5. 验收标准

- [ ] AC-1: 管理员可通过页面导入书籍文本文件，系统自动切分章节和片段
- [ ] AC-2: 系统可为每个片段触发 TTS（Mock 返回固定音频），生成初始版本
- [ ] AC-3: 标注员可在评估工作台试听音频、选择可用/不可用并提交
- [ ] AC-4: 选择"不可用"时，badcase 分类和新音频为必填，选"可用"时跳过校验
- [ ] AC-5: 修改后文本输入框默认带入原始文本
- [ ] AC-6: 精雕老师可按片段任务上传 wav，系统校验格式并生成新版本
- [ ] AC-7: 上传成功后页面内 Mini 播放器可试听复核
- [ ] AC-8: 章节内所有片段就绪后，系统自动触发 pydub merge 生成章节成品
- [ ] AC-9: merge 失败时（格式不一致/文件缺失）记录错误并打回待处理
- [ ] AC-10: 所有关键操作记录到 operation_logs 表，可查询
- [ ] AC-11: 一个片段可保留多个版本，当前生效版本 is_active=true

---

## 6. 风险与约束

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| TTS 接口待定，Mock 可能不准确 | 中 | Mock 接口预留 source_type=tts_init，真实接入时只替换实现层 |
| pydub merge 对采样率有要求 | 高 | 上传时强制校验采样率/声道，不一致时拒绝并提示 |
| 精雕老师上传规范不清晰 | 高 | 在上传页明确展示格式要求，校验失败时给出具体错误信息 |
| 前端单页多视图，切换逻辑复杂 | 中 | 用简单 hash routing + 状态变量管理视图切换 |
| MySQL 连接配置 | 低 | 使用 .env 管理，不硬编码 |

**约束**:
- 技术栈：Python 3.11 + FastAPI + MySQL + TailwindCSS（单 HTML）
- 音频格式：一期仅支持 wav，merge 使用 pydub
- 文件存储：一期使用本地文件系统（预留 OSS 扩展点）
- 鉴权：token 轻鉴权（请求头 X-Token），不做 RBAC

---

## 7. 里程碑与拆分

| 阶段 | TODO | 描述 | 验收 |
|------|------|------|------|
| Phase A | T101 | 数据库初始化：建表脚本（books/chapters/segments/segment_versions/operation_logs） | 脚本可执行，表结构与 PRD 一致 |
| Phase A | T102 | 后端项目骨架：FastAPI 项目结构 + MySQL 连接 + .env 配置 + 健康检查接口 | GET /health 返回 200 |
| Phase A | T103 | 书籍导入接口：POST /api/v1/books（解析文本 → 切分章节/片段 → 写入 DB） | 导入后 DB 有对应记录 |
| Phase B | T104 | TTS Mock 接口：POST /api/v1/segments/{id}/tts，生成 Mock 音频并写入 segment_versions | 调用后片段状态变 tts_done |
| Phase B | T105 | 书籍/章节/片段查询接口：GET 系列接口 + 章节完成度计算 | 接口返回正确数据 |
| Phase B | T106 | 片段音频流式返回接口：GET /api/v1/segments/{id}/audio | 浏览器可直接播放 |
| Phase C | T107 | 前端骨架：index.html + TailwindCSS + hash routing（管理员/标注员/精雕视图切换） | 三个视图可切换 |
| Phase C | T108 | 管理员视图：书籍列表、章节列表、完成度进度条、触发 TTS 按钮 | 完整展示 + 触发功能 |
| Phase C | T109 | 标注员评估工作台：片段列表 + 音频播放器 + 可用/不可用分支表单 + 提交接口对接 | AC-3/4/5 通过 |
| Phase D | T110 | 片段评估后端接口：POST /api/v1/segments/{id}/evaluate（状态机流转 + 日志） | 状态正确流转 |
| Phase D | T111 | 精雕上传接口 + 前端：POST /api/v1/segments/{id}/upload + 格式校验 + Mini 播放器 | AC-6/7 通过 |
| Phase D | T112 | 章节自动 merge：所有片段就绪后触发 pydub merge，结果写入 chapters.output_path | AC-8/9 通过 |
| Phase E | T113 | 操作日志：所有关键操作写入 operation_logs，GET /api/v1/logs 查询接口 | AC-10 通过 |
| Phase E | T114 | 集成验收：端到端跑通完整链路（导入→TTS→评估→上传→merge） | AC-1 到 AC-11 全部通过 |
| Phase E | T115 | 章节成品下载接口 + 管理员视图展示 | 管理员可下载 merge 后的 wav |

---

## 附录

### 参考资料

- `docs/specs/LLM平台Audiobook生成评估需求 (1).md` — 评估工作台 UI 设计和字段映射
- `docs/design/一期-任务流转+TTS.md` — 一期范围、流程图、数据对象、上线步骤
- `/Users/qizhi/work/Code/LP/listenpal-crawler/scripts/merge_wav.py` — pydub merge 参考实现
- `/Users/qizhi/work/Code/LP/listenpal-crawler/scripts/merge_audio.py` — 章节级 merge 参考实现
- `/Users/qizhi/work/Code/LP/listenpal-crawler/scripts/rich_txt_tts.py` — TTS 接口参考实现（tts-t.zuoyebang.com）

### 变更记录

| 日期 | 作者 | 变更内容 |
|------|------|----------|
| 2026-03-28 | 齐郅 | 初稿（/brainstorm 生成） |
