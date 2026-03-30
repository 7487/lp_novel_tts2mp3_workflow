# PRD — 批量压缩包书籍导入

> 在现有单文件导入基础上，新增对 zip/tar 压缩包的批量导入支持。

---

## 审批状态

- **状态**: `approved`
- **审批人**: 齐郅
- **审批日期**: 2026-03-28
- **关联 TODO**: T120 起

---

## 1. 问题定义（What & Why）

### 1.1 问题描述

现有书籍导入接口（`POST /api/v1/books`）每次只能上传一个 txt 或 json 文件，且需要手动填写书名。实际使用中，书籍通常以压缩包形式交付（每本书一个 zip/tar 包，包内为多个按章节命名的 txt 文件），需要逐个解压再逐个上传，效率低下。

### 1.2 目标

- 目标 1：支持一次上传多个 zip/tar 压缩包，每个压缩包自动导入为一本书
- 目标 2：书名自动从压缩包文件名提取（去掉扩展名），无需手动填写
- 目标 3：压缩包内多个 txt 文件按文件名字母序排列，每个 txt 视为一个章节
- 目标 4：编码自动检测（chardet），兼容 UTF-8 和 GBK 等常见中文编码
- 目标 5：批量导入时部分成功也返回详细结果（成功列表 + 失败列表）

### 1.3 非目标

- 不改动现有 `POST /api/v1/books` 接口（向后兼容）
- 不支持嵌套目录结构（只支持一层：压缩包直接包含 txt）
- 不支持压缩包内 json 格式（仅支持 txt）
- 不做异步队列处理（同步导入，响应前完成）

---

## 2. 用户故事 / 使用场景

### 场景 1：管理员批量导入多本书

> 作为管理员，我希望一次上传多个压缩包，系统自动解析书名和章节，以便快速导入整批有声书任务。

**前置条件**: 已有多本书的 zip/tar 压缩包，每个包内有一个或多个按章节命名的 txt 文件。

**操作流程**:
1. 进入管理员视图，点击"批量导入压缩包"按钮
2. 文件选择框支持多选，选择多个 zip/tar 文件
3. 点击上传，接口返回导入结果：各书名、成功/失败、失败原因
4. 成功导入的书籍立即出现在书籍列表中

**预期结果**:
```json
{
  "succeeded": [
    {"filename": "三体.zip", "book_id": 5, "book_title": "三体", "chapter_count": 30}
  ],
  "failed": [
    {"filename": "broken.zip", "error": "压缩包内未找到 txt 文件"}
  ]
}
```

---

### 场景 2：压缩包内多 txt 文件自动识别章节顺序

> 作为系统，当压缩包内有多个 txt 文件时，按文件名字母序排列，每个 txt 作为独立章节，txt 内部按现有逻辑拆分片段。

**前置条件**: `小说A.zip` 内有 `ch01_第一章.txt` / `ch02_第二章.txt` / `ch03_第三章.txt`。

**操作流程**:
1. 解压后列出 txt 文件：`['ch01_第一章.txt', 'ch02_第二章.txt', 'ch03_第三章.txt']`
2. 按文件名字母序排序（已有序）
3. 每个 txt 作为一章，txt 文件名（去扩展名）作为章节标题
4. 每个 txt 内容按现有 `parse_txt()` 片段切分逻辑处理

**预期结果**: 书《小说A》有 3 章，章节标题为文件名。

---

## 3. 设计方案

### 方案 A：新增批量导入接口（选定方案）

**描述**: 新增 `POST /api/v1/books/batch-archive` 接口接受多个压缩包，新增 `archive_service.py` 处理解压和编码检测逻辑，原有接口完全不变。

**优点**:
- 不碰现有接口，无回归风险
- 逻辑独立，测试边界清晰

**缺点**:
- API 表面积增加一个端点

**工作量**: S（4 个 TODO）

### 推荐方案

**推荐**: 方案 A
**理由**: 现有接口已稳定并有测试覆盖，新增接口风险最低，语义最清晰。

---

## 4. 接口设计 / 数据结构

### 4.1 新增 API 接口

```
POST /api/v1/books/batch-archive

Content-Type: multipart/form-data
Body: files[] = [archive1.zip, archive2.tar, archive3.tar.gz, ...]

Response 200:
{
  "succeeded": [
    {
      "filename": "三体.zip",
      "book_id": 5,
      "book_title": "三体",
      "chapter_count": 30
    }
  ],
  "failed": [
    {
      "filename": "broken.zip",
      "error": "压缩包内未找到 txt 文件"
    }
  ]
}
```

### 4.2 新增服务层函数

```python
# backend/services/archive_service.py

def extract_txt_files(archive_bytes: bytes, filename: str) -> list[tuple[str, bytes]]:
    """
    解压 zip 或 tar（含 .tar.gz / .tgz）包，返回一层 txt 文件列表。
    filename: 原始文件名，用于判断格式（zip/tar）。
    返回: [(txt_filename, raw_bytes), ...] 按文件名排序
    """

def decode_txt(raw_bytes: bytes) -> str:
    """
    自动检测编码（chardet），fallback UTF-8。
    返回解码后字符串。
    """

def parse_archive_as_book(archive_bytes: bytes, filename: str) -> dict:
    """
    将压缩包解析为书籍结构。
    书名 = filename 去掉扩展名（.zip / .tar / .tar.gz / .tgz）
    章节 = 每个 txt 文件（按文件名排序），章节标题 = txt 文件名去扩展名
    片段 = 每章 txt 内容经 parse_txt() 切分
    返回: {"title": str, "chapters": [{"title": str, "segments": [str]}]}
    异常: ValueError（无 txt 文件、格式不支持等）
    """
```

### 4.3 支持的压缩格式

| 格式 | 扩展名 | 解析方式 |
|------|--------|---------|
| ZIP | `.zip` | `zipfile.ZipFile` |
| TAR | `.tar` | `tarfile.open` |
| TAR+GZ | `.tar.gz` / `.tgz` | `tarfile.open(mode='r:gz')` |
| TAR+BZ2 | `.tar.bz2` | `tarfile.open(mode='r:bz2')` |

---

## 5. 验收标准

- [ ] AC-1: 上传单个 zip 包 → 正确解析书名（文件名去扩展名）、章节（每个 txt 一章，按文件名排序）、片段
- [ ] AC-2: 上传单个 tar/tar.gz 包 → 同上
- [ ] AC-3: 一次上传 3 个压缩包 → 返回 3 条成功记录，书籍列表新增 3 本
- [ ] AC-4: 压缩包内 txt 编码为 GBK → 自动检测并正确解码，不出现乱码
- [ ] AC-5: 其中一个压缩包损坏或无 txt 文件 → 该包进入 failed 列表，其余正常导入
- [ ] AC-6: 压缩包内有子目录（不符合规范）→ 只处理根层 txt 文件，子目录内的 txt 忽略
- [ ] AC-7: 上传非压缩包文件（如 .pdf）→ 该文件进入 failed 列表，提示格式不支持
- [ ] AC-8: 管理员视图新增"批量导入压缩包"入口，上传后展示导入结果摘要

---

## 6. 风险与约束

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| chardet 检测不准确 | 中 | 检测置信度 < 0.7 时 fallback UTF-8，并在失败详情中提示 |
| 压缩包过大占用内存 | 中 | 单个压缩包大小限制 50MB（FastAPI 层校验） |
| tar 包路径穿越（Path Traversal）| 高 | 解压时过滤含 `..` 的路径，只处理纯文件名 |

**约束**:
- 新增依赖：`chardet`（加入 requirements.txt）
- 压缩解压使用 Python 标准库（zipfile / tarfile），无额外依赖
- 单次请求最多支持 20 个压缩包（防止超时）

---

## 7. 里程碑与拆分

| 阶段 | TODO | 描述 | 验收 |
|------|------|------|------|
| Phase F | T120 | 写测试 — archive_service（zip/tar 解压、编码检测、书名提取） | 测试覆盖 AC-1/2/4/6/7，初始红灯 |
| Phase F | T121 | 实现 — archive_service.py | T120 测试绿灯 |
| Phase F | T122 | 实现 — POST /api/v1/books/batch-archive 接口 | AC-3/5 通过 |
| Phase F | T123 | 前端 — 管理员视图新增批量导入压缩包入口 + 结果展示 | AC-8 通过 |

---

## 附录

### 参考资料

- `backend/services/book_service.py` — 现有 parse_txt / import_book 逻辑（复用）
- `backend/routers/books.py` — 现有书籍路由（不改动）
- Python 标准库：`zipfile`、`tarfile`

### 变更记录

| 日期 | 作者 | 变更内容 |
|------|------|----------|
| 2026-03-28 | 齐郅 | 初稿（/brainstorm 生成） |
