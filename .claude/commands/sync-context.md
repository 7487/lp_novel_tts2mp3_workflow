# sync-context — 同步外部上下文到本地缓存文件

> **目的**：从 MCP 服务器一次性拉取最新数据，写入本地 Markdown 文件。后续会话直接读文件，避免每轮重复调用 MCP 浪费 token。

**输入**: `$ARGUMENTS`（可选：`db` / `api` / `kb`，留空则全部同步）

---

## 执行步骤

### Step 0：读取项目配置

读取 `CLAUDE.md`，找到 "MCP 工具" 段落中的配置：
- `yapi_project_ids`：需要同步的 YAPI 项目 ID 列表
- 数据库名（来自 settings.json 的 DB_DATABASE 环境变量说明）

记录 `$ARGUMENTS` 指定的同步目标（空则全部执行）。

---

### Step 1：同步数据库 Schema（project-mysql MCP）

**条件**：`$ARGUMENTS` 为空 或 包含 `db`

尝试调用 `project-mysql` MCP 的工具：
1. 列出数据库中所有表
2. 对每张表获取 DDL（`SHOW CREATE TABLE {table_name}` 或等效操作）
3. 覆盖写入 `docs/DB_SCHEMA.md`，格式如下：

```
# 数据库 Schema
> 同步时间：{YYYY-MM-DD HH:MM}
> 数据库：{db_name}

## 表：{table_name}
\`\`\`sql
{建表 DDL}
\`\`\`
> 业务含义：{根据字段名/注释推断，简短说明}

---
```

**如果 project-mysql MCP 不可用**：在报告中标注 ✗，跳过此步骤，**不修改**现有文件。

---

### Step 2：同步 YAPI 接口文档（yapi-mcp MCP）

**条件**：`$ARGUMENTS` 为空 或 包含 `api`

尝试调用 `yapi-mcp` MCP 的工具：
1. 如果 `CLAUDE.md` 中配置了 `yapi_project_ids`，获取这些项目的接口列表
2. 如果未配置，列出所有可用项目，提示用户在 `CLAUDE.md` 中填写 `yapi_project_ids` 后重试
3. 对每个接口获取：URL、Method、描述、请求参数、响应结构
4. 覆盖写入 `docs/API_SPEC.md`，格式如下：

```
# API 接口文档（YAPI 缓存）
> 同步时间：{YYYY-MM-DD HH:MM}
> 来源：{YAPI URL}

## {分类名}

### {接口名}
- **方法**：{GET/POST/PUT/DELETE}
- **路径**：{/api/v1/xxx}
- **描述**：{接口说明}

**请求参数**：
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| xxx  | string | 是 | xxx |

**响应示例**：
\`\`\`json
{
  "code": 0,
  "data": {}
}
\`\`\`

---
```

**如果 yapi-mcp 不可用**：在报告中标注 ✗，跳过此步骤，**不修改**现有文件。

---

### Step 3：同步团队知识库（knowledge-base MCP）

**条件**：`$ARGUMENTS` 为空 或 包含 `kb`

尝试调用 `knowledge-base` MCP 的工具：
1. 搜索与当前项目相关的知识条目（使用 CLAUDE.md 中的项目名或关键词）
2. **追加写入** `docs/KB.md`（不全量覆盖，保留用户手动添加的内容）
3. 去重：按条目标题判断，已有则更新内容，不重复追加

**如果 knowledge-base MCP 不可用**：在报告中标注 ✗，跳过此步骤。

---

### Step 4：输出同步报告

```
## /sync-context 执行报告

| 数据源 | 状态 | 详情 |
|--------|------|------|
| MySQL Schema (project-mysql) | ✓ 成功 | X 张表 |
| YAPI 接口 (yapi-mcp) | ✓ 成功 | X 个接口 |
| 团队知识库 (knowledge-base) | ✗ 跳过 | MCP 未配置 |

**更新文件**：docs/DB_SCHEMA.md, docs/API_SPEC.md

**下次同步时机**：
- DB Schema：数据库表结构变更后
- YAPI 接口：新增或修改接口后
- 知识库：团队有新规范沉淀后

**提示**：本地缓存文件已就绪，后续会话 Claude 直接读取文件，无需重复调用 MCP。
```

---

## 规则

- 任何步骤失败都不影响其他步骤的执行，继续往下走
- 写文件前必须确认 MCP 工具真实可用（有响应），不可凭空生成内容
- `docs/KB.md` 只追加/更新，不全量覆盖
- `docs/DB_SCHEMA.md` 和 `docs/API_SPEC.md` 全量覆盖（以 MCP 返回为准）
- 如果某 MCP 的 token 环境变量明显是占位符（如 `YOUR_YAPI_TOKEN_HERE`），视为未配置，跳过
