# /plan — PRD 拆分为可执行 TODO

> 将已审批的 PRD 拆分为细粒度 TODO 清单，写入 TODO.md 和 STATE.md。

---

## 执行步骤

### Step 1：读取并校验 PRD

读取 `docs/spec/PRD_{{feature_name}}.md`（或用户指定的 PRD 文件）。

校验审批状态：
- 如果状态为 `approved` → 继续
- 如果状态为 `draft` 或 `review` → 停止，提示用户先审批
- 如果状态为 `rejected` → 停止，提示用户修改后重新审批

### Step 2：读取现有状态

读取以下文件：
- `docs/TODO.md` — 确定现有 TODO 编号，计算新编号起点
- `docs/STATE.md` — 了解当前阶段
- `docs/TDD.md` — 了解测试规范
- `CLAUDE.md` — 确认编码规范和实现原则

**按需读取输入型文档**（如目录存在，执行以下步骤）：
1. 列出 `docs/design/`、`docs/specs/` 目录内容（`docs/design/`下可能包含对应需求的一些现成设计实现，以供参考）
2. 跳过 `_template.md` 和 `_archive/` 目录下的文件
3. 读取文件头 `status` 字段（只读前 5 行）：
   - `status: done` → 移入 `_archive/`，跳过
   - `status: reference` 或 `active` → 判断是否与当前 PRD 主题相关，相关则读取
4. 最多读取 2 个相关文件

### Step 3：拆分 TODO

将 PRD 方案拆分为细粒度 TODO，遵循以下原则：

**粒度**：
- 每个 TODO 应在 2-10 分钟内可完成（单轮 claude -p 可执行）
- 如果一个 TODO 需要修改超过 3 个文件，考虑拆分

**TDD 配对**：
- 每个实现类 TODO 前，配一个对应的测试 TODO
- 格式：`T{N}: 写测试 — {功能}` → `T{N+1}: 实现 — {功能}`

**TODO 格式**：
```markdown
- [ ] T{编号}: {描述}
  - 文件: {涉及的文件列表}
  - 验收: {验收条件}
  - 依赖: {前置 TODO 编号，如有}
```

**排序原则**：
1. 基础设施 / 数据结构优先
2. 核心功能次之
3. 边缘场景和优化最后
4. 测试 TODO 在对应实现 TODO 之前

### Step 4：写入 TODO.md

将生成的 TODO 追加到 `docs/TODO.md`。

如果已有未完成的 TODO：
- 新 TODO 追加到末尾，不打乱现有顺序
- 编号从现有最大编号 +1 开始

### Step 5：初始化 STATE.md

更新 `docs/STATE.md`：
- 记录当前阶段（来自 PRD 里程碑）
- 记录 TODO 总数和起止编号
- 设置 `current_todo` 为第一个新 TODO

### Step 6：输出摘要

```
TODO 清单已生成：

  新增: T{start} ~ T{end}（共 N 个）
  测试 TODO: M 个
  实现 TODO: K 个

Phase 规划：
  Phase 1: T{a} ~ T{b} — {描述}
  Phase 2: T{c} ~ T{d} — {描述}

下一步：
  - 审核 docs/TODO.md 确认任务合理
  - 运行 /execute 开始逐个执行
  - 或启动 bash scripts/claude_loop.sh 自动循环执行
```

---

## 规则

- PRD 状态必须为 `approved`，否则拒绝执行
- TODO 编号全局唯一，不与现有编号冲突
- 每个 TODO 必须有明确的验收条件
- 实现类 TODO 必须配对测试 TODO（纯文档/配置类除外）
- 不要生成超过 30 个 TODO，如果方案过大，建议用户分期
