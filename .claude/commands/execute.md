# /execute — TDD 驱动逐个执行 TODO

> 在交互模式下逐个执行 TODO，遵循 TDD 流程。

---

## 执行步骤

### Step 1：扫描环境

按优先级顺序检查：

1. **bug_fix/**：如有未解决的 `.md` 文件，优先处理（参照 CLAUDE.md bug 修复流程）
2. **docs/FEEDBACK.md**：读取所有 `status: open` 条目，本轮必须遵守其 `action` 约束
3. **docs/TODO.md**：找到第一个未完成 TODO（`- [ ]`）
4. **docs/STATE.md**：读取当前进度
5. **docs/MEMORY.md**：读取历史经验
6. **docs/design/**（按需）：如当前 TODO 涉及特定模块：
   - 列出目录内容，跳过 `_template.md` 和 `_archive/`
   - 读文件头 `status`：`done` 的移入 `_archive/`；`active`/`reference` 的判断相关性后读取

如果没有未完成 TODO 且没有 bug_fix，输出：

```
所有任务已完成！运行 /status 查看项目概览。
```

### Step 2：展示当前 TODO

向用户展示即将执行的 TODO：

```
当前 TODO: T{编号} — {描述}
涉及文件: {文件列表}
验收条件: {条件}
```

等待用户确认（输入 `y` 继续，`s` 跳过，`q` 退出）。

### Step 3：TDD 执行

按 `docs/TDD.md` 规范执行：

**RED — 写测试**：
1. 根据 TODO 验收条件编写测试
2. 运行测试，确认失败（RED）
3. 如果是测试类 TODO，完成后跳到 Step 4

**GREEN — 最小实现**：
1. 编写最小代码使测试通过
2. 运行测试，确认通过（GREEN）

**REFACTOR — 重构**：
1. 在测试保护下优化代码结构
2. 运行测试，确认仍然通过
3. 检查是否违反 FEEDBACK 中的 open 约束

### Step 4：更新状态

1. 在 `docs/TODO.md` 中勾选完成的 TODO：`- [ ]` → `- [x]`
2. 更新 `docs/STATE.md`：
   - `current_todo`: 当前完成的 TODO
   - `last_updated`: 当前日期
   - 进度描述

### Step 5：提示继续

```
T{编号} 已完成 ✓

进度: {已完成}/{总数}（{百分比}%）
下一个: T{下一编号} — {描述}

继续执行？（y/s/q）
  y — 继续下一个 TODO
  s — 跳过下一个
  q — 退出，稍后运行 /execute 继续
  loop — 启动 bash scripts/claude_loop.sh 自动执行剩余任务
```

### Step 6：循环

如果用户选择继续，回到 Step 1。

---

## 规则

- 每次只执行一个 TODO，不合并
- bug_fix/ 优先级高于常规 TODO
- 必须遵循 TDD 流程（纯文档/配置类 TODO 除外）
- 每个 TODO 完成后必须更新 STATE.md
- 如果 TODO 无法完成（缺依赖、需求不清），标记为 blocked 并提示用户
- FEEDBACK open 条目的 action 是强制约束，执行中必须遵守
