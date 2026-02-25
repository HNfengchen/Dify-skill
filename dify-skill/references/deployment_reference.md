# Dify 部署参考文档

## 系统要求

### 硬件要求

| 资源 | 最低要求 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核心 | 4+ 核心 |
| 内存 | 4 GB | 8+ GB |
| 磁盘 | 20 GB | 50+ GB |

### 软件要求

| 软件 | 版本要求 |
|------|---------|
| Docker | 19.03+ |
| Docker Compose | 1.28+ |
| Git | 任意版本 |

### 操作系统支持

- Ubuntu 18.04+
- CentOS 7+
- RHEL 7+
- Rocky Linux 8+
- AlmaLinux 8+
- macOS 10.14+

## 部署方式

### 方式一：Docker Compose 部署（推荐）

```bash
# 克隆仓库
git clone https://github.com/langgenius/dify.git
cd dify/docker

# 复制环境变量文件
cp .env.example .env

# 启动服务
docker compose up -d
```

### 方式二：源码部署

```bash
# 克隆仓库
git clone https://github.com/langgenius/dify.git
cd dify

# 安装后端依赖
cd api
pip install -r requirements.txt

# 安装前端依赖
cd ../web
npm install

# 配置环境变量
cp .env.example .env

# 启动服务
docker compose -f docker-compose.middleware.yaml up -d
flask run --host 0.0.0.0 --port=5001
```

## 环境变量配置

### 核心配置

```env
# 服务地址
CONSOLE_API_URL=http://localhost/console/api
SERVICE_API_URL=http://localhost/api
APP_WEB_URL=http://localhost
FILES_URL=http://localhost

# 安全配置
SECRET_KEY=your-secret-key-here

# 日志级别
LOG_LEVEL=INFO
DEBUG=false
```

### 数据库配置

```env
# PostgreSQL
DB_USERNAME=postgres
DB_PASSWORD=difyai123456
DB_HOST=db
DB_PORT=5432
DB_DATABASE=dify
```

### Redis 配置

```env
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=difyai123456
```

### 存储配置

```env
# 本地存储
STORAGE_TYPE=local
STORAGE_LOCAL_PATH=storage

# S3 存储
STORAGE_TYPE=s3
S3_BUCKET_NAME=your-bucket
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_REGION=us-east-1
```

### 向量数据库配置

```env
# Weaviate（默认）
VECTOR_STORE=weaviate
WEAVIATE_ENDPOINT=http://weaviate:8080

# Milvus
VECTOR_STORE=milvus
MILVUS_URI=http://milvus:19530

# Qdrant
VECTOR_STORE=qdrant
QDRANT_URL=http://qdrant:6333
```

## 服务管理命令

### 启动服务

```bash
cd dify/docker
docker compose up -d
```

### 停止服务

```bash
cd dify/docker
docker compose down
```

### 重启服务

```bash
cd dify/docker
docker compose restart
```

### 查看日志

```bash
# 查看所有日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f api
docker compose logs -f worker
docker compose logs -f web
```

### 查看服务状态

```bash
docker compose ps
```

## 升级指南

### 标准升级流程

```bash
# 1. 进入项目目录
cd dify

# 2. 拉取最新代码
git pull origin main

# 3. 进入 docker 目录
cd docker

# 4. 拉取最新镜像
docker compose pull

# 5. 重启服务
docker compose up -d
```

### 数据备份

```bash
# 备份 PostgreSQL 数据库
docker compose exec db pg_dump -U postgres dify > backup_$(date +%Y%m%d).sql

# 备份存储文件
tar -czvf storage_backup_$(date +%Y%m%d).tar.gz ./storage
```

### 数据恢复

```bash
# 恢复数据库
cat backup.sql | docker compose exec -T db psql -U postgres dify

# 恢复存储文件
tar -xzvf storage_backup.tar.gz
```

## SSL/HTTPS 配置

### 使用 Certbot（推荐）

```bash
# 进入 certbot 目录
cd dify/docker/certbot

# 配置域名
# 编辑 init-letsencrypt.sh 设置域名

# 运行初始化脚本
./init-letsencrypt.sh
```

### 手动配置 SSL

1. 获取 SSL 证书文件
2. 将证书放置到 `docker/nginx/ssl/` 目录
3. 修改 `docker/nginx/conf.d/default.conf` 配置
4. 重启 nginx 服务

## 性能优化

### 数据库优化

```env
# PostgreSQL 连接池
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=10
```

### Redis 优化

```env
# Redis 连接池
REDIS_MAX_CONNECTIONS=50
```

### Worker 优化

```env
# Celery 并发数
CELERY_WORKER_CONCURRENCY=4
```

## 故障排查

### 常见问题

#### 1. 服务无法启动

```bash
# 检查端口占用
netstat -tlnp | grep -E '80|443|5001'

# 检查 Docker 状态
docker info

# 检查容器日志
docker compose logs
```

#### 2. 数据库连接失败

```bash
# 检查数据库容器状态
docker compose ps db

# 检查数据库日志
docker compose logs db

# 测试数据库连接
docker compose exec db psql -U postgres -d dify
```

#### 3. 内存不足

```bash
# 检查内存使用
free -h

# 增加 Docker 内存限制
# 编辑 docker-compose.yaml 添加内存限制
```

#### 4. 磁盘空间不足

```bash
# 检查磁盘使用
df -h

# 清理 Docker 资源
docker system prune -a
```

## 监控配置

### 启用 OpenTelemetry

```env
ENABLE_OTEL=true
OTLP_BASE_ENDPOINT=http://otel-collector:4317
```

### 配置 Grafana

```bash
# 导入 Dify Dashboard
# 参考 docker/monitoring 目录
```

## 安全建议

1. **修改默认密码**：更改数据库、Redis 等服务的默认密码
2. **配置防火墙**：只开放必要的端口
3. **启用 HTTPS**：使用 SSL 证书加密通信
4. **定期备份**：设置自动备份计划
5. **更新维护**：定期更新到最新版本
6. **日志审计**：启用日志记录并定期审计

## 参考链接

- [Dify 官方文档](https://docs.dify.ai/)
- [Dify GitHub](https://github.com/langgenius/dify)
- [Docker 官方文档](https://docs.docker.com/)
