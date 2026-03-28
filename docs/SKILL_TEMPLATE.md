# Skill 编写模板

> 本文件是 Claude Code Skill（slash command）的编写模板。
> 复制本模板创建新的 `.md` 文件，放在 `.claude/commands/` 目录下即可注册为 slash command。

---

## 模板结构

一个 Skill 文件由以下部分组成：

### 1. YAML Front Matter（必须）

```yaml
---
name: skill-name
description: 一句话描述 skill 的功能
version: "1.0"
metadata:
  author: your-name
  tags: [category1, category2]
  triggers:
    - "关键词 1"
    - "关键词 2"
---
```

**字段说明**:

| 字段 | 必须 | 说明 |
|------|------|------|
| `name` | 是 | Skill 唯一标识，用于 `/skill-name` 调用 |
| `description` | 是 | 功能简述，显示在帮助列表中 |
| `version` | 否 | 版本号 |
| `metadata.author` | 否 | 作者 |
| `metadata.tags` | 否 | 分类标签 |
| `metadata.triggers` | 否 | 自动触发关键词（Claude 根据上下文自动判断是否触发） |

### 2. 环境初始化（可选）

```markdown
## 环境初始化

执行前确认以下条件：
- [ ] 依赖已安装：`npm install` / `pip install -r requirements.txt`
- [ ] 环境变量已配置：`API_KEY`, `DB_URL`
- [ ] 工作目录正确：项目根目录
```

### 3. 命令列表（核心）

```markdown
## 命令

### /skill-name [arg1] [arg2]

**描述**: 主命令功能说明

**参数**:
- `arg1` (必须): 参数说明
- `arg2` (可选): 参数说明，默认值 = xxx

**执行步骤**:
1. 步骤 1
2. 步骤 2
3. 步骤 3

**输出格式**:
[描述输出格式]

**示例**:
```
/skill-name my-feature --flag
```
```

### 4. 规则（可选）

```markdown
## 规则

- 规则 1：[约束条件]
- 规则 2：[约束条件]
- 规则 3：[约束条件]
```

---

## 完整示例：代码审查 Skill

```markdown
---
name: review
description: 对指定文件或目录进行代码审查
version: "1.0"
metadata:
  author: team
  tags: [code-quality, review]
---

## 命令

### /review [path]

**描述**: 对指定路径的代码进行审查，输出问题清单和改进建议。

**参数**:
- `path` (可选): 要审查的文件或目录，默认为当前暂存区变更

**执行步骤**:
1. 如未指定 path，运行 `git diff --cached --name-only` 获取变更文件
2. 逐文件阅读代码
3. 按以下维度审查：
   - 正确性：逻辑错误、边界条件
   - 安全性：参照 CLAUDE.md 安全守则
   - 性能：参照 CLAUDE.md 性能意识
   - 可读性：命名、结构、注释
4. 输出审查报告

**输出格式**:

## 审查报告

### [文件名]

| 行号 | 级别 | 问题 | 建议 |
|------|------|------|------|
| L42 | ERROR | SQL 注入风险 | 使用参数化查询 |
| L87 | WARN | N+1 查询 | 使用 JOIN 或预加载 |
| L123 | INFO | 可提取为函数 | 提取 `calculate_total()` |

### 总结

- 错误: N 个
- 警告: N 个
- 建议: N 个

## 规则

- 只报告真正的问题，不吹毛求疵
- ERROR 级别必须修复才能合并
- WARN 级别建议修复
- INFO 级别供参考
```

---

## 文件放置

将编写好的 Skill 文件放在项目的 `.claude/commands/` 目录下：

```
.claude/
└── commands/
    ├── review.md
    ├── brainstorm.md
    └── deploy-check.md
```

在 Claude Code 中使用 `/review`、`/brainstorm`、`/deploy-check` 即可调用。

---

## 编写建议

1. **单一职责**: 每个 Skill 只做一件事
2. **幂等性**: 多次执行结果一致
3. **明确输出**: 定义清晰的输出格式
4. **错误处理**: 说明异常情况如何处理
5. **文档即代码**: Skill 文件本身就是最好的文档
