# API 接口文档（YAPI 缓存）

> **维护方式**：运行 `/sync-context api` 从 YAPI MCP 自动同步，或手动维护。
> **最后同步**：未初始化

## 如何初始化

1. 复制 `.claude/settings.json.example` 为 `.claude/settings.json`，填写 YAPI Token
2. 在 `CLAUDE.md` 的 "MCP 工具" 段落填写 `yapi_project_ids`
3. 运行 `/sync-context api`，Claude 会自动写入本文件
4. 或手动将 YAPI 接口文档粘贴到下方

## 何时更新

- 新增或修改接口定义后，重新运行 `/sync-context api`
- Claude 优先读此文件，避免每次查询 YAPI MCP 浪费 token

---

<!-- /sync-context 写入的内容从此处开始 -->
