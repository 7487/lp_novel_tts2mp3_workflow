# /brainstorm — 头脑风暴与 PRD 生成

> 从模糊想法到结构化 PRD 草稿。

**输入**: `$ARGUMENTS`（一句话需求描述）

---

## 执行步骤

### Step 1：理解上下文

读取以下文件，理解项目现状：
- `CLAUDE.md` — 项目目标、技术栈、编码规范
- `docs/STATE.md` — 当前进度和阶段
- `docs/TODO.md` — 已有任务（避免重复）
- `docs/MEMORY.md` — 历史经验

**按需读取输入型文档**（如目录存在，执行以下步骤）：
1. 列出 `docs/specs/`、`docs/meetings/`、`docs/research/` 目录内容
2. 跳过 `_template.md` 和 `_archive/` 目录下的文件
3. 对剩余文件，读取文件头的 `status` 字段（只读前 5 行）：
   - `status: done` → 先将该文件移入同目录 `_archive/`，然后跳过
   - `status: reference` → 跳过（除非文件名与当前需求高度相关）
   - `status: active` → 判断文件名 / tags 是否与 `$ARGUMENTS` 相关，相关则读取
4. 最多读取 1-3 个相关文件，不贪多

### Step 2：澄清需求

根据 `$ARGUMENTS`，向用户提出 3-5 个澄清问题，覆盖：
- **目标用户**：谁会使用这个功能？
- **核心场景**：最关键的使用场景是什么？
- **边界**：明确不做什么？
- **约束**：技术限制、时间限制、兼容性要求？
- **成功标准**：怎样算做完了？

等待用户回答后再继续。

### Step 3：探索方案

提出 2-3 个候选方案，每个方案包含：
- **方案名称**
- **一句话描述**
- **优点**（2-3 条）
- **缺点**（2-3 条）
- **工作量估算**：S（1-3 个 TODO）/ M（4-8 个 TODO）/ L（9+ 个 TODO）
- **推荐理由或不推荐理由**

明确给出推荐方案，等待用户确认。

### Step 4：生成 PRD

用户确认方案后，按 `docs/specs/PRD_{{feature_name}}.md` 模板生成完整 PRD，包含：
1. **审批状态** — 设为 `draft`
2. **问题定义** — What & Why
3. **用户故事** — 至少 2 个场景
4. **设计方案** — 展开选定方案的细节
5. **接口设计 / 数据结构** — 如适用
6. **验收标准** — 可验证的 AC 列表
7. **风险与约束**
8. **里程碑与拆分** — 初步 TODO 规划

### Step 5：写入文件

将生成的 PRD 写入 `docs/specs/PRD_{{feature_name}}.md`。

如果 `docs/specs/PRD_{{feature_name}}.md` 已有内容（非模板），提示用户：
- 覆盖当前 PRD
- 写入 `docs/PRD_{{feature_name}}.md` 作为独立文件

### Step 6：提示下一步

输出提示：

```
PRD 已生成 → docs/specs/PRD_{{feature_name}}.md（status: draft）

下一步：
1. 审核 PRD 内容，确认无误
2. 将审批状态改为 approved
3. 运行 /plan 生成 TODO 清单
```

---

## 规则

- 不要跳过澄清问题步骤，即使需求看起来很清晰
- 方案探索至少 2 个，不要只给一个
- PRD 状态必须设为 `draft`，不可直接设为 `approved`
- 如果 `$ARGUMENTS` 为空，提示用户输入需求描述
- 生成的 PRD 必须严格遵循 `docs/PRD.md` 模板结构
