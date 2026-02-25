---
name: dify
description: |
  Dify 平台部署、插件安装与开发辅助工具。支持 Ubuntu 和 CentOS 操作系统。
  
  使用场景：
  - 一键部署 Dify 平台到本地或服务器
  - 安装和管理 Dify 插件
  - 开发和调试 Dify 插件
  - 配置和优化 Dify 服务
  - 配置本地模型（如 Ollama）接入 Dify
  - 排查 Dify 部署和运行问题
  
  触发条件：
  - 用户请求部署 Dify
  - 用户需要安装 Dify 插件
  - 用户需要开发 Dify 插件
  - 用户需要配置本地模型
  - 用户询问 Dify 相关配置或问题
---

# Dify Skill

Dify 是一个开源的 LLM 应用开发平台，提供可视化工作流、RAG 管道、Agent 能力等功能。此 Skill 帮助完成 Dify 的部署、插件安装、模型配置和开发工作。

## 核心能力

### 1. 一键部署 Dify

自动完成环境检查、依赖安装、配置生成和服务启动。

**使用脚本部署：**

```bash
# 部署 Dify
sudo python scripts/deploy_dify.py deploy --dir /opt

# 停止服务
sudo python scripts/deploy_dify.py stop --dir /opt/dify

# 重启服务
sudo python scripts/deploy_dify.py restart --dir /opt/dify

# 升级版本
sudo python scripts/deploy_dify.py upgrade --dir /opt/dify
```

**手动部署步骤：**

```bash
# 1. 克隆仓库
git clone https://github.com/langgenius/dify.git
cd dify/docker

# 2. 配置环境变量
cp .env.example .env

# 3. 启动服务
docker compose up -d

# 4. 访问初始化页面
# http://localhost/install
```

**系统要求：**
- CPU >= 2 核心
- 内存 >= 4 GB
- Docker 19.03+
- Docker Compose 1.28+

**部署验证：**

```bash
# 检查服务状态
docker compose ps

# 验证 Web 服务
curl -s -o /dev/null -w "%{http_code}" http://localhost/install
# 应返回 200
```

### 2. 配置本地模型（Ollama）

Dify 支持接入本地运行的 Ollama 模型，需要解决 Docker 容器访问宿主机服务的问题。

#### 2.1 问题背景

Docker 容器内的 `127.0.0.1` 或 `localhost` 指向容器自身，无法直接访问宿主机上运行的 Ollama 服务。需要通过 `host.docker.internal` 或宿主机 IP 来访问。

#### 2.2 配置 Docker 支持 host.docker.internal

编辑 `docker/docker-compose.yaml`，为需要访问宿主机服务的容器添加 `extra_hosts` 配置：

```yaml
  api:
    image: langgenius/dify-api:1.13.0
    restart: always
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      # ... 其他配置

  worker:
    image: langgenius/dify-api:1.13.0
    restart: always
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      # ... 其他配置

  worker_beat:
    image: langgenius/dify-api:1.13.0
    restart: always
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      # ... 其他配置
```

**关键说明：**
- `host.docker.internal` - Docker 提供的特殊 DNS 名称
- `host-gateway` - Docker 会自动解析为宿主机网关 IP
- 需要为 `api`、`worker`、`worker_beat` 三个服务都添加此配置

#### 2.3 重启服务使配置生效

```bash
cd dify/docker
docker compose down
docker compose up -d
```

#### 2.4 验证配置

```bash
# 检查 hosts 文件是否包含配置
docker exec docker-api-1 cat /etc/hosts | grep host.docker.internal

# 测试容器内访问 Ollama
docker exec docker-api-1 curl -s http://host.docker.internal:11434/api/tags
```

#### 2.5 在 Dify 中配置 Ollama

1. 打开 Dify 控制台: http://localhost
2. 进入 **设置** → **模型提供商**
3. 找到 **Ollama**，点击设置
4. 填写配置：

| 配置项 | 值 |
|--------|-----|
| Base URL | `http://host.docker.internal:11434` |

**注意事项：**
- ❌ 不要使用 `http://127.0.0.1:11434`（容器内无法访问）
- ❌ 不要使用宿主机 IP（如 `http://172.26.197.97:11434`），除非 Ollama 监听 `0.0.0.0`
- ✅ 使用 `http://host.docker.internal:11434`

#### 2.6 Ollama 监听配置（可选）

如果需要从其他机器访问 Ollama，需要让它监听所有网络接口：

```bash
# 方法一：临时启动
OLLAMA_HOST=0.0.0.0:11434 ollama serve &

# 方法二：永久配置（添加到 ~/.bashrc）
echo 'export OLLAMA_HOST=0.0.0.0:11434' >> ~/.bashrc
source ~/.bashrc

# 方法三：systemd 服务配置
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/environment.conf << 'EOF'
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
EOF
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

验证监听地址：
```bash
ss -tlnp | grep 11434
# 正确: LISTEN 0  4096  0.0.0.0:11434  0.0.0.0:*
# 错误: LISTEN 0  4096  127.0.0.1:11434  0.0.0.0:*
```

### 3. 插件安装

支持通过 GitHub URL、本地路径或 Marketplace 安装插件。

**使用脚本安装：**

```bash
# 从 GitHub 安装
python scripts/install_plugin.py https://github.com/user/dify-plugin --type github

# 从本地路径安装
python scripts/install_plugin.py /path/to/plugin --type local

# 仅打包插件
python scripts/install_plugin.py https://github.com/user/dify-plugin --package-only

# 调试模式
python scripts/install_plugin.py https://github.com/user/dify-plugin --debug --dify-dir /opt/dify
```

**手动安装步骤：**

1. 安装 Dify CLI 工具：
```bash
# macOS/Linux (Homebrew)
brew tap langgenius/dify
brew install dify

# Linux (二进制)
curl -LO https://github.com/langgenius/dify-plugin-daemon/releases/latest/download/dify-plugin-linux-amd64
chmod +x dify-plugin-linux-amd64
sudo mv dify-plugin-linux-amd64 /usr/local/bin/dify
```

2. 打包插件：
```bash
dify plugin package ./my-plugin
```

3. 在 Dify 控制台上传 `.difypkg` 文件

### 4. 插件开发辅助

提供完整的插件开发流程支持。

**创建新插件：**

```bash
dify plugin init
```

按提示选择插件类型：
- **Tool**: 工具提供者，如 Google Search、Stable Diffusion
- **Model**: 模型提供者，如 OpenAI、Anthropic
- **Agent Strategy**: 自定义 Agent 策略
- **Extension**: 扩展功能，如 Endpoints

**配置调试环境：**

1. 在 Dify 控制台获取调试信息：
   - 点击右上角"插件"图标
   - 点击调试图标（虫子图标）
   - 复制 API Key 和 Host Address

2. 配置 `.env` 文件：
```env
INSTALL_METHOD=remote
REMOTE_INSTALL_HOST=debug-plugin.dify.dev
REMOTE_INSTALL_PORT=5003
REMOTE_INSTALL_KEY=your-api-key
```

3. 运行插件：
```bash
pip install -r requirements.txt
python -m main
```

**关闭签名验证（开发环境）：**

在 `docker/middleware.env` 添加：
```env
force_verifying_signature=false
```

## 工作流决策树

```
用户请求
    │
    ├─ 部署 Dify?
    │   ├─ 检查系统要求（CPU/内存/Docker）
    │   ├─ 安装 Docker（如需要）
    │   ├─ 克隆代码仓库
    │   ├─ 配置环境变量
    │   ├─ 启动服务
    │   └─ 验证服务状态
    │
    ├─ 配置本地模型?
    │   ├─ 检查 Ollama 服务状态
    │   ├─ 配置 Docker extra_hosts
    │   ├─ 重启 Dify 服务
    │   └─ 在 Dify 中添加模型提供商
    │
    ├─ 安装插件?
    │   ├─ 检查 Python 版本
    │   ├─ 安装 Dify CLI
    │   ├─ 获取插件源码
    │   ├─ 打包插件
    │   └─ 上传安装
    │
    └─ 开发插件?
        ├─ 创建插件项目
        ├─ 编写插件代码
        ├─ 配置调试环境
        └─ 测试和打包
```

## 常用命令速查

| 操作 | 命令 |
|------|------|
| 启动服务 | `cd dify/docker && docker compose up -d` |
| 停止服务 | `cd dify/docker && docker compose down` |
| 重启服务 | `cd dify/docker && docker compose restart` |
| 查看日志 | `cd dify/docker && docker compose logs -f` |
| 拉取更新 | `cd dify && git pull && cd docker && docker compose pull` |
| 创建插件 | `dify plugin init` |
| 打包插件 | `dify plugin package ./plugin-name` |
| 检查 Ollama | `curl http://localhost:11434/api/tags` |
| 容器内测试 | `docker exec docker-api-1 curl http://host.docker.internal:11434/api/tags` |

## 参考文档

- [插件开发指南](references/plugin_development.md) - 详细的插件开发流程和示例
- [部署参考文档](references/deployment_reference.md) - 部署配置和故障排查
- [API 快速参考](references/api_reference.md) - Dify API 端点和使用示例

## 资源文件

### scripts/

- `deploy_dify.py` - 一键部署脚本，支持 Ubuntu 和 CentOS
- `install_plugin.py` - 插件安装脚本

### references/

- `plugin_development.md` - 插件开发完整指南
- `deployment_reference.md` - 部署配置参考
- `api_reference.md` - API 快速参考

## 故障排查

### 服务无法启动

```bash
# 检查端口占用
netstat -tlnp | grep -E '80|443|5001'

# 检查容器状态
docker compose ps

# 查看错误日志
docker compose logs api
```

### Ollama 连接被拒绝

**错误信息：**
```
Connection refused (host='127.0.0.1', port=11434)
Connection refused (host='172.26.197.97', port=11434)
```

**原因分析：**
1. Docker 容器内的 `127.0.0.1` 指向容器自身，无法访问宿主机
2. Ollama 默认只监听 `127.0.0.1:11434`，不接受外部连接
3. 未配置 `host.docker.internal`

**解决方案：**
```bash
# 1. 检查 Ollama 监听地址
ss -tlnp | grep 11434

# 2. 配置 Docker extra_hosts（见上文 2.2 节）

# 3. 重启 Dify 服务
docker compose down && docker compose up -d

# 4. 验证配置
docker exec docker-api-1 curl http://host.docker.internal:11434/api/tags

# 5. 在 Dify 中使用正确的 Base URL
# http://host.docker.internal:11434
```

### Docker 镜像拉取失败

```bash
# 重试拉取
docker compose pull

# 或使用代理
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port
docker compose pull
```

### 插件安装失败

```bash
# 检查 Python 版本
python --version  # 需要 >= 3.12

# 检查 Dify CLI
dify version

# 检查网络连接
curl -I https://github.com
```

### 数据库连接问题

```bash
# 检查数据库容器
docker compose ps db

# 测试连接
docker compose exec db psql -U postgres -d dify
```

## 实施经验总结

### 部署最佳实践

1. **环境检查先行**：部署前务必检查 CPU、内存、磁盘空间是否满足最低要求
2. **网络稳定性**：Docker 镜像较大，确保网络稳定或配置镜像加速
3. **服务验证**：部署后使用 `curl` 验证 Web 服务响应状态码

### 本地模型配置要点

1. **理解 Docker 网络**：容器内 `localhost` ≠ 宿主机 `localhost`
2. **使用 host.docker.internal**：这是 Docker 官方推荐的宿主机访问方式
3. **三个服务都要配置**：`api`、`worker`、`worker_beat` 都需要访问外部服务
4. **配置后必须重启**：修改 `docker-compose.yaml` 后需要 `docker compose down && up`

### WSL 环境特殊处理

在 WSL 环境下：
- Ollama 可能运行在 Windows 端或 Linux 端
- 检查进程运行位置：`ps aux | grep ollama`
- 确认监听地址：`ss -tlnp | grep 11434`
- 如果 Ollama 在 Windows 端，可能需要额外配置端口转发

## 官方资源

- [Dify 官方文档](https://docs.dify.ai/)
- [Dify GitHub](https://github.com/langgenius/dify)
- [Dify Plugin Daemon](https://github.com/langgenius/dify-plugin-daemon)
- [Dify Cloud](https://cloud.dify.ai/)
