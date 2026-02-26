# AGENTS.md

## 项目概述

Dify 是一个开源的 LLM 应用开发平台，提供直观的界面，集成 Agent 工作流、RAG 管道、Agent 能力和模型管理功能。

代码库位于 `/home/fengchen/projects/Dify/dify-deploy/`，分为以下部分：
- **后端 API** (`/api`): Python Flask 应用，采用领域驱动设计
- **前端 Web** (`/web`): Next.js 应用，使用 TypeScript 和 React
- **Docker 部署** (`/docker`): 容器化部署配置

---

## 构建/代码检查/测试命令

### 开发环境设置

```bash
cd /home/fengchen/projects/Dify/dify-deploy
make dev-setup              # 运行所有设置步骤
make prepare-docker         # 设置 Docker 中间件（Redis、数据库等）
make prepare-web            # 设置前端环境（pnpm install）
make prepare-api            # 设置后端环境（uv sync + db upgrade）
```

### 后端命令 (Python/Flask)

通过 `uv run --project api <command>` 运行命令：

```bash
cd /home/fengchen/projects/Dify/dify-deploy

# 格式化和代码检查
make format                 # 使用 ruff 格式化代码
make check                 # 使用 ruff 检查代码
make lint                  # 格式化、修复和代码检查（ruff、imports、dotenv）

# 类型检查
make type-check             # 运行类型检查（basedpyright、mypy、ty）

# 测试
make test                   # 运行所有后端单元测试
make test TARGET_TESTS=./api/tests/<path_to_test.py>  # 运行单个测试
# 示例：make test TARGET_TESTS=./api/tests/unit/core/workflow/test_node_executor.py
```

### 前端命令 (TypeScript/Next.js)

```bash
cd /home/fengchen/projects/Dify/dify-deploy/web

pnpm install                # 安装依赖
pnpm dev                    # 启动开发服务器
pnpm build                  # 构建生产版本
pnpm lint:fix               # 修复代码检查问题（推荐）
pnpm type-check:tsgo       # TypeScript 类型检查
```

### Docker 命令

```bash
cd /home/fengchen/projects/Dify/dify-deploy/docker

docker compose up -d                    # 启动所有服务
docker compose down                      # 停止所有服务
docker compose -f docker-compose.middleware.yaml up -d  # 仅启动中间件
```

---

## 代码风格指南

### Python (后端)

**格式化和代码检查：**
- 使用 Ruff 进行格式化和代码检查（遵循 `.ruff.toml`）
- 每行不超过 120 个字符
- 提交前运行 `make lint`

**命名约定：**
- 变量/函数：`snake_case`
- 类：`PascalCase`
- 常量：`UPPER_CASE`

**类型提示：**
- 使用现代类型形式：`list[str]`、`dict[str, int]`
- 除非有充分理由，否则避免使用 `Any`
- 在函数和属性上保留类型提示
- 实现相关的特殊方法（`__repr__`、`__str__`）

**类布局：**
```python
from datetime import datetime

class Example:
    user_id: str
    created_at: datetime

    def __init__(self, user_id: str, created_at: datetime) -> None:
        self.user_id = user_id
        self.created_at = created_at
```

**错误处理：**
- 永远不要使用 `print`；使用 `logger = logging.getLogger(__name__)`
- 抛出领域特定的异常（`services/errors`、`core/errors`）
- 在控制器中将异常转换为 HTTP 响应
- 可重试事件记录为 `warning`，终端失败记录为 `error`

**SQLAlchemy 模式：**
- 模型继承自 `models.base.TypeBase`
- 使用上下文管理器管理会话：
```python
with Session(db.engine, expire_on_commit=False) as session:
    stmt = select(Model).where(...)
    result = session.execute(stmt).scalar_one_or_none()
```
- 始终按 `tenant_id` 限定查询范围

**Pydantic v2：**
- 使用 Pydantic v2 定义 DTO，默认禁止 extras
- 使用 `@field_validator` / `@model_validator` 实现领域规则

### TypeScript/React (前端)

- 使用严格的 TypeScript 配置
- 避免使用 `any` 类型
- 运行 `pnpm lint:fix` 自动修复
- 运行 `pnpm type-check:tsgo` 进行类型检查

---

## 架构与模式

### 后端（DDD + 清洁架构）

```
controller → service → core/domain
```

- **Controllers**: 通过 Pydantic 解析输入，调用服务，返回序列化的响应；不含业务逻辑
- **Services**: 协调仓储、提供商、后台任务；保持副作用显式
- 使用 `configs.dify_config` 进行配置——不要直接读取环境变量
- 端到端保持租户感知；`tenant_id` 必须贯穿每一层
- 通过 `services/async_workflow_service` 排队异步工作；在 `tasks/` 下实现任务

### 前端

- 用户可见的字符串必须使用 `web/i18n/en-US/`；避免硬编码文本
- 遵循 `web/docs/test.md` 中的测试指南

---

## 测试实践

**后端：**
- 遵循 TDD：red → green → refactor
- 使用 `pytest` 的 Arrange-Act-Assert 结构
- 运行单个测试：`make test TARGET_TESTS=./api/tests/<path>`

**前端：**
- 遵循 `./docs/test.md` 生成测试
- 测试必须符合 `frontend-testing` skill 规范

---

## 通用实践

- 优先编辑现有文件；只有在明确要求时才添加新文档
- 通过构造函数注入依赖
- 保持文件在 ~800 行以内；必要时拆分
- 编写自解释代码；只添加解释意图的注释
- 在修改代码前阅读模块/类/函数的文档字符串——将其视为规范的一部分
- 如果文档字符串与代码冲突，以代码为准并更新文档

---

## 快速参考

| 任务 | 命令 |
|------|------|
| 格式化后端 | `make format` |
| 代码检查后端 | `make lint` |
| 类型检查后端 | `make type-check` |
| 运行后端测试 | `make test` |
| 运行单个测试 | `make test TARGET_TESTS=./api/tests/...` |
| 代码检查前端 | `pnpm lint:fix` |
| 类型检查前端 | `pnpm type-check:tsgo` |
