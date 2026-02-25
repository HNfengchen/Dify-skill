# Dify API 快速参考

## API 端点

### 基础 URL

- 控制台 API: `http://localhost/console/api`
- 服务 API: `http://localhost/api`

## 认证

所有 API 请求需要在 Header 中携带 API Key：

```
Authorization: Bearer {api_key}
```

## 应用 API

### 创建应用

```http
POST /console/api/apps
Content-Type: application/json

{
  "name": "My App",
  "mode": "chat",
  "icon": "🤖",
  "icon_background": "#FFEAD6"
}
```

### 获取应用列表

```http
GET /console/api/apps?page=1&limit=20
```

### 获取应用详情

```http
GET /console/api/apps/{app_id}
```

### 更新应用

```http
PUT /console/api/apps/{app_id}
Content-Type: application/json

{
  "name": "Updated App Name"
}
```

### 删除应用

```http
DELETE /console/api/apps/{app_id}
```

## 对话 API

### 发送消息

```http
POST /v1/chat-messages
Content-Type: application/json
Authorization: Bearer {api_key}

{
  "inputs": {},
  "query": "Hello",
  "response_mode": "blocking",
  "conversation_id": "",
  "user": "user-123"
}
```

### 流式响应

```http
POST /v1/chat-messages
Content-Type: application/json
Authorization: Bearer {api_key}

{
  "inputs": {},
  "query": "Hello",
  "response_mode": "streaming",
  "conversation_id": "",
  "user": "user-123"
}
```

### 获取对话历史

```http
GET /v1/messages?conversation_id={conversation_id}&user=user-123
```

### 反馈消息

```http
POST /v1/message-feedbacks
Content-Type: application/json
Authorization: Bearer {api_key}

{
  "message_id": "message-id",
  "rating": "like",
  "user": "user-123"
}
```

## 文件 API

### 上传文件

```http
POST /v1/files/upload
Content-Type: multipart/form-data
Authorization: Bearer {api_key}

file: [binary]
user: user-123
```

### 获取文件信息

```http
GET /v1/files/{file_id}
Authorization: Bearer {api_key}
```

## 知识库 API

### 创建知识库

```http
POST /console/api/datasets
Content-Type: application/json

{
  "name": "My Knowledge Base"
}
```

### 上传文档

```http
POST /console/api/datasets/{dataset_id}/document/create-by-file
Content-Type: multipart/form-data

file: [binary]
name: Document Name
indexing_technique: high_quality
process_rule:
  mode: automatic
```

### 创建文本文档

```http
POST /console/api/datasets/{dataset_id}/document/create-by-text
Content-Type: application/json

{
  "name": "Text Document",
  "text": "Document content...",
  "indexing_technique": "high_quality",
  "process_rule": {
    "mode": "automatic"
  }
}
```

### 获取文档列表

```http
GET /console/api/datasets/{dataset_id}/documents?page=1&limit=20
```

### 删除文档

```http
DELETE /console/api/datasets/{dataset_id}/documents/{document_id}
```

## 工作流 API

### 执行工作流

```http
POST /v1/workflows/run
Content-Type: application/json
Authorization: Bearer {api_key}

{
  "inputs": {
    "query": "Hello"
  },
  "response_mode": "blocking",
  "user": "user-123"
}
```

### 停止工作流

```http
POST /v1/workflows/tasks/{task_id}/stop
Content-Type: application/json
Authorization: Bearer {api_key}

{
  "user": "user-123"
}
```

## 模型 API

### 获取模型列表

```http
GET /console/api/workspaces/current/model-providers
```

### 获取模型参数

```http
GET /console/api/workspaces/current/model-providers/{provider}/models/{model}
```

## 插件 API

### 获取插件列表

```http
GET /console/api/plugins
```

### 安装插件

```http
POST /console/api/plugins/install
Content-Type: multipart/form-data

file: [plugin.difypkg]
```

### 卸载插件

```http
DELETE /console/api/plugins/{plugin_id}
```

## 错误响应

### 错误格式

```json
{
  "code": "invalid_param",
  "message": "Invalid parameter: name is required",
  "status": 400
}
```

### 常见错误码

| 错误码 | 描述 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |

## 速率限制

- 默认限制：60 请求/分钟
- 可在 `.env` 文件中配置：

```env
API_RATE_LIMIT=60
```

## Webhook 事件

### 消息完成事件

```json
{
  "event": "message_completed",
  "message_id": "msg-xxx",
  "conversation_id": "conv-xxx",
  "answer": "Response content",
  "created_at": 1234567890
}
```

### 工作流完成事件

```json
{
  "event": "workflow_finished",
  "workflow_run_id": "run-xxx",
  "status": "succeeded",
  "outputs": {
    "result": "Output value"
  }
}
```

## SDK 使用示例

### Python SDK

```python
import requests

API_KEY = "your-api-key"
BASE_URL = "http://localhost/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 发送消息
response = requests.post(
    f"{BASE_URL}/chat-messages",
    headers=headers,
    json={
        "query": "Hello",
        "response_mode": "blocking",
        "user": "user-123"
    }
)

print(response.json())
```

### JavaScript SDK

```javascript
const API_KEY = 'your-api-key';
const BASE_URL = 'http://localhost/v1';

// 发送消息
const response = await fetch(`${BASE_URL}/chat-messages`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'Hello',
    response_mode: 'blocking',
    user: 'user-123'
  })
});

const data = await response.json();
console.log(data);
```
