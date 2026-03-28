# 语言特定规则参考库

> 本文件是**可选参考库**，包含各语言的编码规则集合。
> 用户应根据项目使用的语言，将对应章节复制到 `CLAUDE.md` 的代码风格段落中。
> 通用规则（安全、性能、Git 工作流等）已内置在 `CLAUDE.md` 中，本文件只包含语言特定的补充。

---

## Python 代码风格

### 格式化与检查

- 格式化工具: `black`（行长 88）
- Lint 工具: `ruff`（替代 flake8 + isort + pyupgrade）
- 类型检查: `mypy --strict` 或 `pyright`
- import 排序: `ruff` 自动处理（stdlib → third-party → local）

### 类型标注

- 所有公开函数必须有完整的类型标注（参数 + 返回值）
- 内部函数建议标注，复杂逻辑必须标注
- 使用 `from __future__ import annotations` 延迟求值
- 优先使用内置泛型（`list[str]` 而非 `List[str]`，Python 3.9+）
- 复杂类型使用 `TypeAlias` 或 `TypedDict`

### 文档字符串

- 风格: Google 风格 docstring
- 所有公开函数、类、模块必须有 docstring
- 包含: 功能描述、Args、Returns、Raises

```python
def fetch_data(url: str, timeout: int = 30) -> dict[str, Any]:
    """从指定 URL 获取数据。

    Args:
        url: 目标 URL。
        timeout: 超时时间（秒）。

    Returns:
        解析后的 JSON 数据。

    Raises:
        HTTPError: 请求失败时。
    """
```

### 命名规范

- 变量/函数: `snake_case`
- 类: `PascalCase`
- 常量: `UPPER_SNAKE_CASE`
- 私有: `_leading_underscore`
- 模块: `snake_case.py`

### 项目结构

```
project/
├── src/project_name/    # 源码（使用 src layout）
│   ├── __init__.py
│   ├── models/
│   ├── services/
│   └── utils/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── pyproject.toml       # 统一配置（替代 setup.py + setup.cfg）
└── requirements.txt     # 或 poetry.lock / uv.lock
```

### 常用约定

- 异步优先: 涉及 I/O 的模块使用 `async/await`
- Context manager: 资源管理使用 `with` 语句
- Dataclass / Pydantic: 数据容器优先使用，避免裸 dict 传递
- 环境变量: 使用 `pydantic-settings` 或 `python-dotenv` 管理

---

## TypeScript 代码风格

### 格式化与检查

- 格式化工具: `prettier`
- Lint 工具: `eslint` + `@typescript-eslint`
- 严格模式: `tsconfig.json` 中启用 `"strict": true`

### 类型系统

- 导出函数/变量必须显式标注类型
- 内部变量可以依赖类型推断
- 优先 `interface` 定义对象形状（可扩展）；`type` 用于联合类型、交叉类型、工具类型
- 运行时验证使用 `zod`（替代手动类型守卫）

```typescript
// Good: 导出时显式标注
export function parseConfig(raw: string): AppConfig {
  return configSchema.parse(JSON.parse(raw));
}

// Good: zod schema 作为单一类型源
const configSchema = z.object({
  port: z.number().int().positive(),
  dbUrl: z.string().url(),
});
type AppConfig = z.infer<typeof configSchema>;
```

### 命名规范

- 变量/函数: `camelCase`
- 类/接口/类型: `PascalCase`
- 常量: `UPPER_SNAKE_CASE` 或 `camelCase`（视团队约定）
- 枚举值: `PascalCase`
- 文件: `camelCase.ts` 或 `kebab-case.ts`（保持项目一致）

### 项目结构

```
project/
├── src/
│   ├── index.ts
│   ├── routes/
│   ├── services/
│   ├── models/
│   └── utils/
├── tests/
│   ├── unit/
│   └── integration/
├── tsconfig.json
├── package.json
└── .eslintrc.js
```

### 常用约定

- 不可变优先: 使用 `const`、`readonly`、`Readonly<T>`
- 错误处理: 使用自定义 Error 类，避免抛出字符串
- 空值处理: 启用 `strictNullChecks`，使用可选链 `?.` 和空值合并 `??`
- 异步: 使用 `async/await`，避免 `.then()` 链
- 导入: 使用 ES modules（`import/export`），避免 `require`

---

## Go 代码风格

### 格式化与检查

- 格式化工具: `gofmt`（无配置，强制统一）
- Lint 工具: `golangci-lint`（集成多种 linter）
- Vet: `go vet`（编译级静态检查）

### 接口设计

- 小接口优先: 接口不超过 3-5 个方法
- 在消费方定义接口，而非实现方
- 使用标准库接口（`io.Reader`、`io.Writer`、`fmt.Stringer`）

```go
// Good: 小接口，在消费方定义
type UserStore interface {
    GetUser(ctx context.Context, id string) (*User, error)
}

// Bad: 大而全的接口
type UserService interface {
    GetUser(...)
    CreateUser(...)
    UpdateUser(...)
    DeleteUser(...)
    ListUsers(...)
    SearchUsers(...)
}
```

### 错误处理

- 使用 `fmt.Errorf("context: %w", err)` 包装错误
- 在调用链顶层处理错误，中间层只包装和传递
- 自定义错误类型实现 `error` 接口
- 不要忽略错误（`_ = doSomething()` 是代码异味）

### 命名规范

- 变量/函数: `camelCase`（首字母大写为导出）
- 包名: 小写单词，不用下划线
- 接口: 单方法接口以 `-er` 结尾（`Reader`、`Writer`）
- 文件: `snake_case.go`
- 测试: `xxx_test.go`

### 项目结构

```
project/
├── cmd/
│   └── server/
│       └── main.go
├── internal/          # 私有包
│   ├── handler/
│   ├── service/
│   └── repository/
├── pkg/               # 公开包（可选）
├── go.mod
└── go.sum
```

### 常用约定

- Context: 所有 I/O 操作传 `context.Context` 作为第一个参数
- 并发: 使用 channel 通信，避免共享内存；用 `sync.WaitGroup` 等待 goroutine
- 依赖注入: 通过构造函数注入依赖，不使用全局变量
- 测试: 表驱动测试（table-driven tests）是标准模式
