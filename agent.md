# agent.md — Codex 兼容垫片

> 本文件为 Codex 执行器保留。完整项目规范在 `CLAUDE.md`，本文件仅提供 Codex 所需的最小上下文。
> 如果你是 Claude Code，请忽略本文件，直接遵循 CLAUDE.md。

## 角色

<!-- TODO: 替换为你的项目描述 -->
当前执行器是本仓库内的任务代理，职责是按 `docs/TODO.md` 的顺序逐步完成项目任务。

## 执行要求

- 完整规范见 `CLAUDE.md`，以下为核心摘要
- **最高优先级**：检查 `bug_fix/` 目录（排除 `resolved/`），如有 `.md` 文件则为紧急 bug，优先修复后移入 `bug_fix/resolved/`
- 只执行一个 `ACTIVE_TODO`
- 执行前必须阅读：`docs/TODO.md`、`docs/STATE.md`、`docs/FEEDBACK.md`、`CLAUDE.md`
- 反馈自检：阅读 `docs/FEEDBACK.md` 中所有 `status: open` 条目，将其 action 作为强制约束
- 只修改完成该任务所必需的文件
- 必须更新 `docs/STATE.md`
- 仅在任务真实完成时勾选 `docs/TODO.md`

## 编码规范（摘要）

<!-- TODO: 根据你的项目调整 -->
1. 新增/删除第三方依赖时同步更新依赖文件
2. 项目结构/API/启动方式变化时同步更新 README.md
3. 代码必须有合适的注释和文档
4. 安全：禁止硬编码密钥，用户输入必须验证，使用参数化查询
5. 性能：避免 N+1 查询，大数据集分页/流式处理
6. Git：commit 格式 `<type>: <description>`（feat/fix/refactor/docs/test/chore）
7. 新功能：先 PRD（`docs/PRD.md`）→ 审批 → TDD 实现（`docs/TDD.md`）
8. Bug 修复：先写测试复现 → 修复 → 验证
9. 每次会话结束前主动更新 `docs/MEMORY.md`

## 输出 JSON

```json
{
  "run_status": "success | blocked | failed",
  "active_todo": "Txxx",
  "completed": true | false,
  "summary": "short summary",
  "bugs_fixed": ["filename.md", ...],
  "files_changed": ["a", "b"],
  "state_updated": true | false,
  "todo_updated": true | false,
  "next_todo": "",
  "blockers": []
}
```
