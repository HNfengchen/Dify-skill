# Dify 插件开发指南

## 环境要求

- Python >= 3.12
- Dify CLI 工具 (dify-plugin-daemon)
- Git

## 安装 Dify CLI 工具

### 通过 Homebrew 安装 (推荐)

```bash
# macOS 和 Linux
brew tap langgenius/dify
brew install dify

# 验证安装
dify version
```

### 通过二进制文件安装

```bash
# Linux amd64
curl -LO https://github.com/langgenius/dify-plugin-daemon/releases/latest/download/dify-plugin-linux-amd64
chmod +x dify-plugin-linux-amd64
sudo mv dify-plugin-linux-amd64 /usr/local/bin/dify

# Linux arm64
curl -LO https://github.com/langgenius/dify-plugin-daemon/releases/latest/download/dify-plugin-linux-arm64
chmod +x dify-plugin-linux-arm64
sudo mv dify-plugin-linux-arm64 /usr/local/bin/dify

# macOS arm64 (M系列芯片)
curl -LO https://github.com/langgenius/dify-plugin-daemon/releases/latest/download/dify-plugin-darwin-arm64
chmod +x dify-plugin-darwin-arm64
sudo mv dify-plugin-darwin-arm64 /usr/local/bin/dify

# 验证安装
dify version
```

## 创建插件项目

```bash
# 创建新插件
dify plugin init
```

按照提示填写以下信息：
- 插件名称
- 作者
- 描述
- 仓库 URL (可选)
- 支持的语言
- 插件类型
- Dify 最低版本要求

## 插件类型

### 1. Tool 插件
用于集成第三方 API 和服务，如 Google Search、Stable Diffusion 等。

### 2. Model 插件
用于集成 AI 模型，如 OpenAI、Anthropic 等。

### 3. Agent Strategy 插件
用于实现自定义 Agent 策略，如 Function Calling、ReAct、ToT、CoT 等。

### 4. Extension 插件
用于扩展 Dify 平台功能，如 Endpoints 和 WebAPP。

### 5. Data Source 插件
作为知识库管道的文档数据源。

### 6. Trigger 插件
在第三方事件发生时自动触发工作流执行。

## 插件目录结构

```
my-plugin/
├── .env                    # 环境变量配置
├── .env.example            # 环境变量示例
├── requirements.txt        # Python 依赖
├── main.py                 # 插件入口
├── manifest.yaml           # 插件清单
├── README.md               # 说明文档
├── README_CN.md            # 中文说明文档
└── provider/               # 提供者目录
    ├── provider.yaml       # 提供者配置
    └── provider.py         # 提供者实现
```

## Tool 插件开发示例

### provider.yaml

```yaml
identity:
  name: my_tool
  author: Your Name
  label:
    en_US: My Tool
    zh_Hans: 我的工具
  description:
    en_US: A sample tool
    zh_Hans: 示例工具
  icon: icon.svg
credentials_for_provider:
  api_key:
    type: text-input
    required: true
    label:
      en_US: API Key
      zh_Hans: API 密钥
    placeholder:
      en_US: Enter your API key
      zh_Hans: 输入您的 API 密钥
```

### tools/tool.yaml

```yaml
identity:
  name: search
  author: Your Name
  label:
    en_US: Search
    zh_Hans: 搜索
description:
  human:
    en_US: Search for information
    zh_Hans: 搜索信息
  llm: Use this tool to search for information
parameters:
  - name: query
    type: string
    required: true
    label:
      en_US: Query
      zh_Hans: 查询
    human_description:
      en_US: The search query
      zh_Hans: 搜索查询
    llm_description: the search query string
    form: llm
```

### tools/tool.py

```python
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from typing import Generator, Any

class SearchTool(Tool):
    def _invoke(self, tool_parameters: dict) -> Generator[ToolInvokeMessage, None, None]:
        query = tool_parameters.get("query", "")
        
        # 实现搜索逻辑
        result = self._search(query)
        
        yield self.create_json_message(result)
    
    def _search(self, query: str) -> dict:
        # 调用外部 API
        return {"result": f"Search result for: {query}"}
```

## 配置调试环境

### 1. 获取调试信息

1. 登录 Dify 控制台
2. 点击右上角的"插件"图标
3. 点击调试图标（虫子图标）
4. 复制 API Key 和 Host Address

### 2. 配置 .env 文件

```bash
# 复制示例配置
cp .env.example .env

# 编辑 .env 文件
```

```env
INSTALL_METHOD=remote
REMOTE_INSTALL_HOST=debug-plugin.dify.dev
REMOTE_INSTALL_PORT=5003
REMOTE_INSTALL_KEY=your-api-key-here
```

### 3. 运行插件

```bash
# 安装依赖
pip install -r requirements.txt

# 运行插件
python -m main
```

## 打包和发布插件

### 打包插件

```bash
# 在插件目录的父目录执行
dify plugin package ./my-plugin
```

这将生成 `my-plugin.difypkg` 文件。

### 关闭签名验证（开发环境）

在 Dify 的 `docker/middleware.env` 文件中添加：

```env
force_verifying_signature=false
```

### 安装插件

1. 登录 Dify 控制台
2. 点击右上角的"插件"图标
3. 点击"安装插件"按钮
4. 选择 `.difypkg` 文件上传

## 工具标签分类

```python
class ToolLabelEnum(Enum):
    SEARCH = "search"
    IMAGE = "image"
    VIDEOS = "videos"
    WEATHER = "weather"
    FINANCE = "finance"
    DESIGN = "design"
    TRAVEL = "travel"
    SOCIAL = "social"
    NEWS = "news"
    MEDICAL = "medical"
    PRODUCTIVITY = "productivity"
    EDUCATION = "education"
    BUSINESS = "business"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities"
    OTHER = "other"
```

## 常见问题排查

### 1. 插件无法启动

- 检查 Python 版本是否 >= 3.12
- 检查依赖是否正确安装
- 查看 .env 配置是否正确

### 2. 连接调试服务器失败

- 确认 Dify 服务正在运行
- 检查 Host Address 和 API Key 是否正确
- 确认网络连接正常

### 3. 插件签名错误

- 开发环境可关闭签名验证
- 生产环境需要正确签名

### 4. 权限问题

- 确保插件有正确的权限声明
- 检查 manifest.yaml 中的权限配置

## 最佳实践

1. **代码结构清晰**：将不同功能模块分离
2. **完善的错误处理**：捕获并处理异常
3. **详细的文档**：提供清晰的使用说明
4. **版本兼容性**：声明支持的 Dify 版本
5. **安全性**：不要在代码中硬编码敏感信息
6. **测试**：编写单元测试确保功能正确

## 参考资源

- [Dify 官方文档](https://docs.dify.ai/plugins/introduction)
- [Dify Plugin Daemon](https://github.com/langgenius/dify-plugin-daemon)
- [Dify GitHub](https://github.com/langgenius/dify)
