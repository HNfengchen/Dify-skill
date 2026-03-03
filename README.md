# Dify 离线部署完整指南

## 一、概述

本文档提供 Dify 平台的完整离线部署方案，包含所有必要的依赖项、配置文件、数据库架构和静态资源。适用于无网络连接或网络受限的环境。

---

## 二、系统要求

### 2.1 硬件要求

| 资源 | 最低要求 | 推荐配置 | 说明 |
|------|---------|---------|------|
| CPU | 2 核心 | 4+ 核心 | 影响并发处理能力 |
| 内存 | 4 GB | 8+ GB | 包含数据库和缓存 |
| 磁盘 | 50 GB | 100+ GB | 包含镜像和存储 |
| 网络 | 100 Mbps | 1 Gbps | 内部服务通信 |

### 2.2 软件要求

| 软件 | 版本要求 | 检查命令 |
|------|---------|---------|
| Docker | 19.03+ | `docker --version` |
| Docker Compose | 1.28+ | `docker compose version` |
| 操作系统 | Ubuntu 18.04+ / CentOS 7+ / RHEL 7+ | `cat /etc/os-release` |

### 2.3 端口要求

| 端口 | 服务 | 说明 |
|------|------|------|
| 80 | Nginx | HTTP 入口 |
| 443 | Nginx | HTTPS 入口 |
| 5001 | API | 后端 API 服务 |
| 5003 | Plugin Daemon | 插件调试端口 |

---

## 三、离线包目录结构

```
dify-offline/
├── images/                      # Docker 镜像文件
│   ├── dify-all-images.tar      # 合并的镜像包（推荐）
│   ├── langgenius_dify-api_1.13.0.tar
│   ├── langgenius_dify-web_1.13.0.tar
│   ├── langgenius_dify-plugin-daemon_0.5.3-local.tar
│   ├── langgenius_dify-sandbox_0.2.12.tar
│   ├── postgres_15-alpine.tar
│   ├── redis_6-alpine.tar
│   ├── semitechnologies_weaviate_1.27.0.tar
│   ├── nginx_latest.tar
│   ├── ubuntu_squid_latest.tar
│   └── busybox_latest.tar
│
├── backup/                      # 备份文件
│   ├── dify_db_YYYYMMDD_HHMMSS.sql      # 主数据库备份
│   ├── dify_plugin_db_YYYYMMDD_HHMMSS.sql # 插件数据库备份
│   └── storage_YYYYMMDD_HHMMSS.tar.gz   # 存储文件备份
│
├── config/                      # 配置文件
│   ├── .env                     # 环境变量配置
│   ├── docker-compose.yaml      # Docker Compose 配置
│   ├── middleware.env           # 中间件配置
│   └── nginx/                   # Nginx 配置目录
│
├── scripts/                     # 部署脚本
│   ├── package.sh               # 打包脚本
│   └── install.sh               # 安装脚本
│
└── docs/                        # 文档
    └── README.md                # 本文档
```

---

## 四、安装前检查

### 4.1 检查 Docker 环境

```bash
# 检查 Docker 是否安装
docker --version
# 预期输出: Docker version 20.x.x 或更高

# 检查 Docker Compose 是否安装
docker compose version
# 预期输出: Docker Compose version v2.x.x 或更高

# 检查 Docker 服务状态
sudo systemctl status docker
```

### 4.2 检查系统资源

```bash
# 检查内存
free -h
# 确保可用内存 >= 4GB

# 检查磁盘空间
df -h /
# 确保可用空间 >= 50GB

# 检查 CPU
nproc
# 确保核心数 >= 2
```

### 4.3 检查端口占用

```bash
# 检查端口是否被占用
netstat -tlnp | grep -E ':80|:443|:5001|:5003'
# 如果有输出，需要先停止占用端口的服务
```

---

## 五、安装步骤

### 5.1 准备工作

```bash
# 1. 创建安装目录
sudo mkdir -p /opt/dify
sudo chown -R $(whoami):$(whoami) /opt/dify

# 2. 复制离线包到目标服务器
# 使用 scp、rsync 或其他方式传输
scp -r dify-offline user@target-server:/tmp/
```

### 5.2 自动安装（推荐）

```bash
# 进入离线包目录
cd /tmp/dify-offline

# 执行安装脚本
chmod +x scripts/install.sh
./scripts/install.sh /opt/dify
```

### 5.3 手动安装

#### 步骤 1: 加载 Docker 镜像

```bash
cd /tmp/dify-offline

# 方式一：加载合并的镜像包（推荐）
docker load -i images/dify-all-images.tar

# 方式二：分开加载镜像
for img in images/*.tar; do
    echo "加载: $img"
    docker load -i "$img"
done

# 验证镜像加载
docker images | grep -E "dify|postgres|redis|weaviate|nginx"
```

#### 步骤 2: 复制配置文件

```bash
# 创建目录
mkdir -p /opt/dify/docker

# 复制配置文件
cp config/.env /opt/dify/docker/
cp config/docker-compose.yaml /opt/dify/docker/
cp config/middleware.env /opt/dify/docker/ 2>/dev/null || true
cp -r config/nginx /opt/dify/docker/ 2>/dev/null || true
```

#### 步骤 3: 修改配置

```bash
# 编辑环境变量
nano /opt/dify/docker/.env

# 必须修改的配置项：
# - CONSOLE_API_URL: 控制台 API 地址
# - SERVICE_API_URL: 服务 API 地址
# - APP_WEB_URL: 应用 Web 地址
# - SECRET_KEY: 安全密钥（随机生成）
# - DB_PASSWORD: 数据库密码
# - REDIS_PASSWORD: Redis 密码
```

#### 步骤 4: 启动服务

```bash
cd /opt/dify/docker
docker compose up -d

# 查看服务状态
docker compose ps

# 查看启动日志
docker compose logs -f api
```

#### 步骤 5: 恢复数据库（可选）

```bash
# 启动数据库
docker compose up -d db_postgres
sleep 10

# 恢复主数据库
cat /tmp/dify-offline/backup/dify_db_*.sql | \
    docker exec -i docker-db_postgres-1 psql -U postgres dify

# 恢复插件数据库
cat /tmp/dify-offline/backup/dify_plugin_db_*.sql | \
    docker exec -i docker-db_postgres-1 psql -U postgres dify_plugin
```

---

## 六、验证测试

### 6.1 服务状态检查

```bash
# 检查所有容器状态
docker compose ps

# 预期输出：所有服务状态为 "running" 或 "healthy"
```

### 6.2 健康检查

```bash
# 检查 API 健康状态
curl http://localhost/health

# 检查初始化页面
curl -s -o /dev/null -w "%{http_code}" http://localhost/install
# 预期输出: 200
```

### 6.3 功能测试

1. **访问初始化页面**: http://localhost/install
2. **设置管理员账号**
3. **创建测试应用**
4. **测试对话功能**

---

## 七、配置说明

### 7.1 核心配置项

```env
# 服务地址配置（必须修改）
CONSOLE_API_URL=http://your-server/console/api
SERVICE_API_URL=http://your-server/api
APP_WEB_URL=http://your-server
FILES_URL=http://your-server

# 安全配置（必须修改）
SECRET_KEY=your-random-secret-key-at-least-32-characters

# 数据库配置
DB_USERNAME=postgres
DB_PASSWORD=your-secure-password
DB_HOST=db_postgres
DB_PORT=5432
DB_DATABASE=dify

# Redis 配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password

# 存储配置
STORAGE_TYPE=local
STORAGE_LOCAL_PATH=storage

# 向量数据库配置
VECTOR_STORE=weaviate
WEAVIATE_ENDPOINT=http://weaviate:8080
```

### 7.2 修改配置后重启

```bash
cd /opt/dify/docker
docker compose down
docker compose up -d
```

---

## 八、常见问题排查

### 8.1 服务无法启动

```bash
# 查看详细日志
docker compose logs api
docker compose logs worker
docker compose logs db_postgres

# 检查端口占用
netstat -tlnp | grep -E '80|443|5001'

# 检查磁盘空间
df -h /
```

### 8.2 数据库连接失败

```bash
# 检查数据库容器状态
docker compose ps db_postgres

# 测试数据库连接
docker exec docker-db_postgres-1 psql -U postgres -d dify -c "SELECT 1"

# 检查数据库日志
docker compose logs db_postgres
```

### 8.3 内存不足

```bash
# 检查内存使用
free -h

# 重启服务释放内存
docker compose restart

# 调整 Docker 内存限制
# 编辑 docker-compose.yaml 添加：
# deploy:
#   resources:
#     limits:
#       memory: 2G
```

### 8.4 镜像加载失败

```bash
# 检查镜像文件完整性
ls -lh images/

# 分开加载镜像
docker load -i images/langgenius_dify-api_1.13.0.tar

# 检查 Docker 存储空间
docker system df
```

### 8.5 网络问题

```bash
# 检查 Docker 网络
docker network ls
docker network inspect docker_default

# 重建网络
docker compose down
docker compose up -d
```

---

## 九、服务管理命令

```bash
# 进入项目目录
cd /opt/dify/docker

# 启动所有服务
docker compose up -d

# 停止所有服务
docker compose down

# 重启所有服务
docker compose restart

# 重启单个服务
docker compose restart api

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f
docker compose logs -f api
docker compose logs --tail 100 worker

# 进入容器
docker exec -it docker-api-1 bash

# 清理资源
docker system prune -a
```

---

## 十、备份与恢复

### 10.1 数据备份

```bash
# 备份数据库
docker exec docker-db_postgres-1 pg_dump -U postgres dify > dify_backup.sql
docker exec docker-db_postgres-1 pg_dump -U postgres dify_plugin > dify_plugin_backup.sql

# 备份存储文件
docker exec docker-api-1 tar -czf /tmp/storage.tar.gz -C /app storage
docker cp docker-api-1:/tmp/storage.tar.gz ./storage_backup.tar.gz

# 备份配置文件
cp /opt/dify/docker/.env ./env_backup
cp /opt/dify/docker/docker-compose.yaml ./docker-compose_backup.yaml
```

### 10.2 数据恢复

```bash
# 恢复数据库
cat dify_backup.sql | docker exec -i docker-db_postgres-1 psql -U postgres dify

# 恢复存储文件
docker cp storage_backup.tar.gz docker-api-1:/tmp/
docker exec docker-api-1 tar -xzf /tmp/storage.tar.gz -C /app
```

---

## 十一、升级指南

### 11.1 升级步骤

```bash
# 1. 备份数据
./scripts/backup.sh

# 2. 拉取新镜像（在线环境）
docker compose pull

# 3. 停止服务
docker compose down

# 4. 更新配置文件
# 对比新旧配置文件，更新必要配置

# 5. 启动新版本
docker compose up -d

# 6. 验证升级
docker compose logs -f api
```

---

## 十二、安全建议

1. **修改默认密码**: 更改数据库、Redis 等服务的默认密码
2. **配置防火墙**: 只开放必要的端口
3. **启用 HTTPS**: 配置 SSL 证书
4. **定期备份**: 设置自动备份计划
5. **更新维护**: 定期更新到最新版本
6. **日志审计**: 启用日志记录并定期审计

---

## 十三、技术支持

- 官方文档: https://docs.dify.ai/
- GitHub: https://github.com/langgenius/dify
- 社区论坛: https://github.com/langgenius/dify/discussions
