# 有声书生产后台（一期）

将有声书线下 Excel 评估流转迁移至线上，覆盖 TTS 生成 → 片段评估 → 精雕上传 → 章节自动合并完整链路。

## 功能概览

| 角色 | 功能 |
|------|------|
| 管理员 | 导入书籍文本、触发 TTS 批量生成、查看进度与操作日志 |
| 标注员 | 试听音频、判定可用/不可用、填写 badcase 标注、页面内重生成 TTS |
| 精雕老师 | 查看待处理片段、上传精雕后 wav 文件、试听复核 |
| 系统 | 章节内所有片段就绪后自动合并 wav，生成章节成品 |

## 技术栈

- **后端**：Python 3.11 + FastAPI + SQLAlchemy Core + pymysql
- **数据库**：MySQL 8.0+
- **音频处理**：pydub（章节 wav 合并）
- **前端**：单页 HTML + TailwindCSS（无 JS 框架依赖）
- **鉴权**：X-Token 请求头轻鉴权

## 目录结构

```
.
├── backend/
│   ├── main.py                 # FastAPI 入口，提供 /health 和前端静态服务
│   ├── config.py               # 从 .env 读取配置
│   ├── db/
│   │   ├── schema.sql          # MySQL 建表脚本
│   │   └── connection.py       # SQLAlchemy 连接池
│   ├── routers/
│   │   ├── books.py            # 书籍导入与列表接口
│   │   ├── chapters.py         # 章节详情、merge 触发、成品下载
│   │   ├── segments.py         # TTS、音频流、评估、精雕上传
│   │   └── logs.py             # 操作日志查询
│   ├── services/
│   │   ├── book_service.py     # txt/json 文本解析与书籍入库
│   │   ├── chapter_service.py  # 章节查询与完成度计算
│   │   ├── tts_service.py      # TTS Mock（可替换为真实接口）
│   │   ├── evaluation_service.py # 评估状态机
│   │   ├── upload_service.py   # wav 格式校验与版本管理
│   │   └── merge_service.py    # pydub 章节自动合并
│   └── tests/                  # 45 个单元测试（全 mock DB）
├── frontend/
│   └── index.html              # 单页应用，hash routing 切换三视图
├── data/                       # 运行时自动创建
│   ├── audio/{segment_id}/     # 片段音频（各版本）
│   └── output/                 # 章节合并成品
├── requirements.txt
└── .env.example
```

## 快速开始

### 1. 创建虚拟环境并安装依赖

```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

音频处理依赖 ffmpeg（pydub 后端）：

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
apt-get install ffmpeg
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填写 MySQL 连接信息
```

`.env` 字段说明：

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=audiobook_user
DB_PASSWORD=your_password
DB_NAME=audiobook_platform
DATA_DIR=./data          # 音频文件存储目录
TOKEN_SECRET=random_str  # X-Token 鉴权密钥
HOST=0.0.0.0
PORT=8000
```

### 3. 初始化数据库

```bash
mysql -u root -p < backend/db/schema.sql
```

或者使用指定用户：

```bash
mysql -h localhost -u audiobook_user -p audiobook_platform < backend/db/schema.sql
```

### 4. 启动服务

```bash
source venv/bin/activate      # 未激活时先激活
cd backend
uvicorn main:app --reload
```

服务启动后：
- **前端页面**：http://localhost:8000
- **API 文档**：http://localhost:8000/docs
- **健康检查**：http://localhost:8000/health

## 使用流程

```
管理员：导入书籍（txt/json）
    ↓
管理员：触发 TTS 批量生成
    ↓
标注员：逐片段试听 → 可用 / 不可用
    ├── 可用 → 片段通过（passed）
    └── 不可用 → 填写 badcase + 选择返工方式
              ├── 页面内重生成 TTS
              └── 等待精雕老师上传
                      ↓
              精雕老师：上传精雕 wav → 试听复核 → 确认
                      ↓
系统：章节内所有片段就绪 → 自动合并 wav → 章节成品
    ↓
管理员：下载章节成品音频
```

## 书籍导入格式

支持两种格式：

**txt 格式**（章节以"第X章"或"Chapter X"开头行识别，片段以双空行分隔）：

```
第一章 标题

第一个片段的文本内容。

第二个片段的文本内容。

第二章 标题

...
```

**json 格式**：

```json
{
  "title": "书名",
  "chapters": [
    {
      "title": "第一章",
      "segments": ["第一个片段文本", "第二个片段文本"]
    }
  ]
}
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/health` | 健康检查 |
| `GET` | `/api/v1/books` | 书籍列表 |
| `POST` | `/api/v1/books` | 导入书籍（multipart: title + file） |
| `GET` | `/api/v1/books/{id}` | 书籍详情 |
| `GET` | `/api/v1/books/{id}/chapters` | 章节列表（含完成度） |
| `GET` | `/api/v1/chapters/{id}` | 章节详情 + completion_rate |
| `GET` | `/api/v1/chapters/{id}/segments` | 片段列表 |
| `POST` | `/api/v1/chapters/{id}/merge` | 手动触发章节合并 |
| `GET` | `/api/v1/chapters/{id}/output` | 下载章节成品 wav |
| `GET` | `/api/v1/segments/{id}` | 片段详情（含当前版本） |
| `POST` | `/api/v1/segments/{id}/tts` | 触发 TTS 生成 |
| `GET` | `/api/v1/segments/{id}/audio` | 流式返回音频文件 |
| `POST` | `/api/v1/segments/{id}/evaluate` | 提交评估结果 |
| `POST` | `/api/v1/segments/{id}/upload` | 上传精雕 wav |
| `GET` | `/api/v1/logs` | 操作日志查询 |

## 数据库表结构

| 表名 | 说明 |
|------|------|
| `books` | 书籍（status: importing/ready/in_progress/done） |
| `chapters` | 章节（status: pending/in_progress/chapter_done/failed） |
| `segments` | 片段（status: pending_tts/tts_done/passed/needs_polish/polish_uploaded/failed） |
| `segment_versions` | 片段音频版本（source_type: tts_init/tts_regen/polish_upload，is_active 标记当前生效版本） |
| `operation_logs` | 操作日志（全链路可追踪） |

## 运行测试

```bash
source venv/bin/activate
python -m pytest backend/tests/ -v
```

测试全部使用 mock DB，无需真实 MySQL 连接，45 个测试用例覆盖：
- 书籍文本解析（txt/json）
- TTS Mock 服务
- 评估状态机（可用/不可用路径）
- 精雕上传与格式校验
- 章节自动合并
- 端到端完整链路

## 接入真实 TTS

一期 TTS 使用 Mock（生成 1 秒静音 wav）。替换步骤：

1. 编辑 `backend/services/tts_service.py`
2. 将 `MockTTSService.generate()` 替换为真实 HTTP 调用
3. 参考：`/Users/qizhi/work/Code/LP/listenpal-crawler/scripts/rich_txt_tts.py`（tts-t.zuoyebang.com 接口实现）

## 音频格式要求

- 格式：WAV
- 采样率：同一章节内所有片段必须一致（上传时自动校验）
- 声道：单声道或立体声均支持

## 一期不包含

- 自动抽卡链路（二期规划）
- 完整质检工作台（状态字段已预留）
- 上架/下游对接（webhook 预留）
- RBAC 细粒度权限
