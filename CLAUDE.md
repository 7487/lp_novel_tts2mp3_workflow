# CLAUDE.md — {{PROJECT_NAME}}

> 本文件是项目的唯一规范源。Claude Code 交互模式自动加载，`claude -p` 循环模式同样自动加载。
> 如果你是通过 Codex 执行，请同时参阅 `agent.md`（Codex 兼容垫片）。

---

## 项目目标

<!-- TODO: 替换为你的项目目标 -->

[一句话描述项目目标]

核心方向：
- [方向 1]
- [方向 2]
- [方向 3]

## 项目概况

<!-- TODO: 替换为你的项目技术栈和关键信息 -->
- 当前核心输入文档：
  - docs/specs/LLM平台Audiobook生成评估需求 (1).md
  - docs/design/一期-任务流转+TTS.md
- [技术栈 Python 3.11 后端，FastAPI + MySql]
- [前端，tailwind css frontend/index.html 单页应用]
- [依赖文件位置]
- [外部 API / 服务]
- 持续执行闭环：`scripts/claude_loop.sh` + `prompts/claude_loop_prompt.txt`
- 状态追踪：`docs/TODO.md` + `docs/STATE.md` + `docs/FEEDBACK.md`
- 设计与测试：`docs/PRD.md`（需求模板）+ `docs/TDD.md`（测试规范）
- 规则参考：`docs/RULES.md`（语言特定规则）+ `docs/SKILL_TEMPLATE.md`（Skill 编写模板）
- 外部上下文缓存：`docs/DB_SCHEMA.md`（DB schema）+ `docs/API_SPEC.md`（YAPI 接口）+ `docs/KB.md`（团队知识库）

---

## 输入型文档生命周期管理

`docs/meetings/`、`docs/design/`、`docs/research/`、`docs/specs/` 下的文档遵循以下规范。

### 文件命名

```
YYYYMMDD_主题关键词.md        # 标准格式，如 20260327_kickoff.md
_template.md                  # 模板文件，永远跳过，不读取
```

### 文件头状态标记

每个文档第一个 HTML 注释块为生命周期标记：

```html
<!--
status: active      # 活跃：当前相关，按需读取
date: YYYY-MM-DD
tags: [feature-x, auth]
-->
```

| status 值 | 含义 | AI 行为 |
|-----------|------|---------|
| `active` | 当前相关，仍在使用 | 按需读取（filename / tags 匹配时） |
| `reference` | 已完成但保留参考 | 仅在被明确提及时才读取 |
| `done` | 已过期，可归档 | **自动移入 `_archive/`**，不再读取 |

### 自主归档规则

在执行任何 slash command 的 Step 1 扫描阶段，遇到 `status: done` 的文件时：
1. 将该文件移动到同目录下的 `_archive/` 子目录（`mv` 操作，不删除）
2. 在输出中简要说明已归档的文件名
3. 继续正常执行，不打断主流程

`_archive/` 目录下的文件永远不自动读取，除非用户明确要求。

### 何时更新 status

| 触发场景 | 建议操作 |
|----------|----------|
| 会议行动项全部完成 | `active` → `done` |
| 需求规格已转化为 PRD | `active` → `reference` |
| 技术设计已实现完毕 | `active` → `reference` |
| 调研结论已纳入方案 | `active` → `done` |

---

## MCP 工具与上下文管理

<!-- TODO: 按项目实际情况填写 MCP 配置 -->

本项目集成三个 MCP 服务器，用于访问数据库、API 文档和团队知识库。
**配置**：复制 `.claude/settings.json.example` 为 `.claude/settings.json` 并填写实际参数（此文件含密钥，不提交 Git）。

### 已集成 MCP

| MCP 名称 | 用途 | 工具示例 |
|----------|------|---------|
| `project-mysql` | 查询数据库结构与执行 SQL | list_tables, execute_query |
| `yapi-mcp` | 获取 YAPI 接口文档 | list_projects, get_interface |
| `knowledge-base` | 读写团队知识库 | search, add_entry |

### Token 节省：静态优先原则

> MCP 工具调用结果往往很大（schema dump、接口列表等），消耗大量 token。
> **优先读取本地缓存文件**，只在文件不存在或数据明显过期时才重新调用 MCP。

| 需求 | 优先方式（省 token） | 何时才调用 MCP |
|------|---------------------|---------------|
| 了解表结构 | 读 `docs/DB_SCHEMA.md` | 文件不存在 / 有 DDL 变更 |
| 查看 API 接口 | 读 `docs/API_SPEC.md` | 文件不存在 / 接口有更新 |
| 查阅团队规范 | 读 `docs/KB.md` | 需要搜索特定知识条目 |
| 执行实际 SQL 查询 | 直接调用 project-mysql MCP | 始终（静态文件无法替代） |

**初始化本地缓存**（项目开始时运行一次）：
```
/sync-context       # 同步全部
/sync-context db    # 仅同步 DB schema
/sync-context api   # 仅同步 YAPI 接口
/sync-context kb    # 仅同步知识库
```

### YAPI 项目 ID 配置

<!-- TODO: 填写你的 YAPI 项目 ID，/sync-context api 使用此配置过滤接口 -->

```
yapi_project_ids: []
```

---

## 编码规范

### 0. 数据库命名规范（强制）

**所有数据库表名必须以 `tts2mp3_` 作为前缀。**

- 新建任何表时，表名格式为 `tts2mp3_<业务名>`，例如：`tts2mp3_books`、`tts2mp3_chapters`
- 对应的索引名也需带前缀，格式：`idx_tts2mp3_<表简称>_<字段>`
- 外键约束中的 `REFERENCES` 目标表名同样须带前缀
- 代码中所有 SQL（`FROM`、`INSERT INTO`、`UPDATE`、`JOIN`、`REFERENCES`）里的表名必须带前缀
- 违反此规则的表名在 code review 和 AI 执行阶段均应立即修正
- 当前已有表（均已带前缀）：
  - `tts2mp3_books`
  - `tts2mp3_chapters`
  - `tts2mp3_segments`
  - `tts2mp3_segment_versions`
  - `tts2mp3_operation_logs`

### 1. 依赖管理

<!-- TODO: 根据你的项目调整依赖文件位置和规则 -->

- 位置：`[依赖文件路径，如 requirements.txt / package.json]`
- 每次新增第三方库的 import 时，必须同步更新依赖文件
- 每次删除依赖使用时，也要从依赖文件中移除

### 2. 文档同步

以下文档需要随代码变化同步更新：

- **README.md**：项目结构、API、启动方式变化时更新
- **docs/SOP.md**（可选）：工作流变化时更新
- **docs/MEMORY.md**：每次会话结束前或完成重要变更后，主动更新
  - 记录内容：本次做了什么、关键设计决策、踩过的坑、经验教训
  - 目的：跨会话保留项目级知识，避免重复踩坑

### 3. 代码风格（通用规则）

<!-- TODO: 语言特定规则请参考 docs/RULES.md，选择适用的章节复制到此处 -->

- [代码风格要求，如：Google 风格 docstring / JSDoc / 等]
- [命名规范]
- [其他约定]

**通用编码原则**（语言无关）：

- **不可变性优先**：新建对象 > 修改对象，减少副作用
- **文件组织**：按功能/领域组织代码，单文件 200-400 行为宜，上限 800 行
- **函数粒度**：单个函数不超过 50 行，嵌套不超过 4 层
- **显式错误处理**：不吞异常、不忽略错误返回值
- **输入验证**：在系统边界（用户输入、外部 API 响应）进行验证，内部调用信任参数
- **无硬编码值**：配置项、魔法数字、URL 等提取为常量或配置文件
- **DRY 但不过度**：三次以上重复再提取，不要过早抽象

### 4. 安全守则

- **禁止硬编码密钥**：API key、password、token、secret 不得出现在代码中
- **环境变量管理密钥**：使用 `.env` 文件 + 环境变量，或 secret manager
- **`.env` 文件必须在 `.gitignore` 中**：永远不要提交 `.env` 文件
- **所有用户输入必须验证**：长度、类型、范围、格式
- **SQL 注入防护**：使用参数化查询 / ORM，禁止字符串拼接 SQL
- **XSS 防护**：输出到 HTML 时进行转义
- **错误信息不泄露内部细节**：面向用户的错误信息不包含堆栈、路径、SQL 等敏感数据
- **最小权限原则**：服务账号、数据库用户只授予必要权限

### 5. 性能意识

- **避免 N+1 查询**：使用 JOIN / 预加载 / 批量查询替代循环内逐条查询
- **大数据集分页/流式处理**：不要一次加载全部数据到内存
- **合理使用缓存**：对频繁读取且不常变化的数据使用缓存，注意缓存失效策略
- **异步 I/O 优先**：网络请求、文件操作等 I/O 密集型任务使用异步（适用时）
- **数据库索引意识**：WHERE / JOIN / ORDER BY 涉及的字段考虑添加索引
- **避免不必要的计算**：循环外可完成的计算不放在循环内

### 6. Git 工作流

- **Commit 格式**: `<type>: <description>`
  - `feat`: 新功能
  - `fix`: Bug 修复
  - `refactor`: 重构（不改变行为）
  - `docs`: 文档变更
  - `test`: 测试相关
  - `chore`: 构建、配置等杂务
  - `perf`: 性能优化
  - `ci`: CI/CD 变更
- **Commit 粒度**: 一个逻辑变更一个 commit，不混合无关修改
- **PR 包含**: Summary（做了什么、为什么）+ Test plan（如何验证）

### 7. PRD 与 TDD 流程

- **新功能**: 必须先写 PRD（`docs/PRD.md`）→ 审批 → 拆分 TODO → TDD 实现
- **Bug 修复**: 可跳过 PRD，但仍需先写测试复现 → 修复 → 验证
- **TDD 规范**: 详见 `docs/TDD.md`
- **PRD 模板**: 详见 `docs/PRD.md`
- **审批门**: PRD 状态为 `approved` 后方可开始编码

### 8. 执行后总结与经验沉淀

每次执行完用户命令后，必须在回复末尾附上**执行后总结**，包含：

1. **本次操作摘要**：做了什么、改了哪些文件
2. **分类归档**：判断是否产生需要归档的内容：
   - **BUG**：发现或修复的 bug → 记录到 `docs/FEEDBACK.md` 或 `bug_fix/`
   - **FEEDBACK**：流程改进、编码规范补充 → 记录到 `docs/FEEDBACK.md`
   - **规则沉淀**：反复出现的模式 → 更新 `docs/MEMORY.md`
3. **无产出也要说明**：明确标注"无需归档"

---

## 反馈与 Bug 修复闭环

本项目有两个问题输入通道，Agent 每轮执行前必须同时检查：

### 通道 1：`docs/FEEDBACK.md`（结构化反馈）

- 用户记录编码规范、流程改进、文档缺失等**持续性约束**
- 每轮执行前，阅读所有 `status: open` 条目
- Open 条目中的 `action` 字段是**强制约束**，本轮及后续所有轮次都必须遵守
- 如果当前任务涉及 open feedback 相关的代码/文件，必须在本轮一并修正
- 当某条 feedback 被完全解决后，移到 "Resolved" 段落并填写 `resolved-by`

### 通道 2：`bug_fix/`（热修收件箱）

- 用户遇到具体 bug 时，在 `bug_fix/` 下放一个 `.md` 文件
- **优先级高于常规 TODO**：`bug_fix/` 下存在未解决的文件时，Agent 必须先处理
- 处理流程：
  1. 读取 `bug_fix/` 下每个 `.md` 文件，理解问题和修复建议
  2. 执行修复，如文件中包含验证方法则按其验证
  3. 在 `docs/FEEDBACK.md` 的 Resolved 段落追加一条记录（留痕）
  4. 将该 `.md` 文件移动到 `bug_fix/resolved/`（归档）
- 如果无法修复，在 `docs/FEEDBACK.md` Open 段落登记，并在输出 `blockers` 中注明

---

## 思考层 Skills（Slash Commands）

模板内置 4 个 slash command，覆盖从想法到执行的完整工作流：

```
/brainstorm "需求描述"  →  /plan  →  /execute  →  /status
    想法 → PRD 草稿    PRD → TODO   逐个 TDD 执行   查看进度
```

| 命令 | 触发时机 | 输入 | 输出 |
|------|----------|------|------|
| `/brainstorm` | 有模糊想法时 | 一句话需求 | `docs/PRD.md`（status=draft） |
| `/plan` | PRD 审批通过后 | `docs/PRD.md`（approved） | `docs/TODO.md` + `docs/STATE.md` |
| `/execute` | TODO 已就绪 | `docs/TODO.md` | 逐个 TDD 执行 TODO |
| `/status` | 随时 | 无 | 项目进度概览 |

**完整工作流**：

1. `/brainstorm 我想做一个 XX 功能` — 交互式澄清需求 → 探索方案 → 生成 PRD 草稿
2. 用户审核 PRD → 将状态改为 `approved`
3. `/plan` — 读取 PRD → 按 TDD 原则拆分 TODO → 写入 TODO.md + STATE.md
4. `/execute` — 交互模式逐个执行，或提示启动 `bash scripts/claude_loop.sh` 自动循环
5. `/status` — 随时查看进度、待处理 Bug、open Feedback

Skill 文件位于 `.claude/commands/` 目录，Claude Code 自动注册为 slash command。

---

## 循环执行规则（claude_loop.sh 上下文）

> 以下规则在 `claude -p` 循环模式中生效。交互模式下作为参考。

### 全局规则

1. 每一轮只允许处理一个 `ACTIVE_TODO`
2. 执行前必须先阅读：
   - `docs/TODO.md`
   - `docs/STATE.md`
   - `docs/FEEDBACK.md`
   - `docs/MEMORY.md`
   - （按需）当前 TODO 涉及数据库操作时，读 `docs/DB_SCHEMA.md`
   - （按需）当前 TODO 涉及 API 接口时，读 `docs/API_SPEC.md`
   - （按需）需要查阅团队规范时，读 `docs/KB.md`
   - （按需）当前 TODO 涉及特定模块时，检查 `docs/design/` 下是否有对应设计文档
3. 只做完成当前 TODO 必需的最小修改，不顺手处理下一个 TODO
4. 只有在任务真实闭环后，才允许勾选 `docs/TODO.md`
5. 每轮结束必须更新 `docs/STATE.md`
6. 修改时优先复用现有目录结构，不做无关重构

### 实现原则

1. **先骨架，后细节**：先落数据结构与接口，再丰富体验
2. **先持久化，后编排**：先让状态能落盘，再引入复杂调度
3. **保持兼容**：已有接口短期内尽量保留，通过新增接口渐进演进
4. **最小可运行增量**：每个 TODO 都应产出能被验证的文件、接口或页面

### 修改边界

<!-- TODO: 根据你的项目调整 -->

允许修改：
- [列出可自由修改的目录/文件]

谨慎修改：
- [列出需要谨慎修改的领域]

禁止行为：
- 不经说明删除可运行的现有主流程
- 把多个 TODO 合并一轮一起做
- 未确认闭环就勾选 TODO
- 引入重型基础设施依赖作为第一步前置

### 实现优先级

<!-- TODO: 根据你的项目规划调整 -->

按下面顺序推进，不跳步：
1. [Phase A 目标]
2. [Phase B 目标]
3. [Phase C 目标]

### 输出 JSON

每轮最终必须只输出一个 JSON 对象，不要输出 markdown、代码块或额外解释。

```json
{
  "run_status": "success | blocked | failed",
  "active_todo": "Txxx",
  "completed": true | false,
  "summary": "short summary",
  "bugs_fixed": ["filename.md", ...],
  "files_changed": ["file1", "file2"],
  "state_updated": true | false,
  "todo_updated": true | false,
  "next_todo": "Txxx or empty string",
  "blockers": ["..."]
}
```

**completed=true 条件**（必须同时满足）：
- 当前 TODO 所需的代码/文档/脚本已实际修改完成
- `docs/STATE.md` 已写回本轮进度
- 没有阻塞当前 TODO 闭环的关键缺失

**completed=false 条件**（满足任一）：
- 只改了一半 / 仍需额外依赖才能判断完成 / 尚未补齐状态文件 / 结果不可验证
