#!/bin/bash

set -e

OFFLINE_DIR="/home/fengchen/projects/Dify/dify-offline"
DIFY_DIR="/home/fengchen/projects/Dify/dify-deploy/docker"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=========================================="
echo "  Dify 离线部署包打包工具"
echo "  时间: $(date)"
echo "=========================================="

mkdir -p "$OFFLINE_DIR"/{images,backup,scripts,docs,config}

echo ""
echo "[1/7] 导出 Docker 镜像..."
cd "$DIFY_DIR"

IMAGES=(
    "langgenius/dify-api:1.13.0"
    "langgenius/dify-web:1.13.0"
    "langgenius/dify-plugin-daemon:0.5.3-local"
    "langgenius/dify-sandbox:0.2.12"
    "postgres:15-alpine"
    "redis:6-alpine"
    "semitechnologies/weaviate:1.27.0"
    "nginx:latest"
    "ubuntu/squid:latest"
    "busybox:latest"
)

for image in "${IMAGES[@]}"; do
    safe_name=$(echo "$image" | sed 's/[:/]/_/g')
    echo "  导出: $image"
    docker pull "$image" 2>/dev/null || true
    docker save -o "$OFFLINE_DIR/images/${safe_name}.tar" "$image" 2>/dev/null || echo "  警告: $image 导出失败"
done

echo "  合并所有镜像到一个文件..."
docker save -o "$OFFLINE_DIR/images/dify-all-images.tar" "${IMAGES[@]}" 2>/dev/null || {
    echo "  分开导出的镜像已保存在 images/ 目录"
}

echo ""
echo "[2/7] 备份数据库..."
docker exec docker-db_postgres-1 pg_dump -U postgres dify > "$OFFLINE_DIR/backup/dify_db_$TIMESTAMP.sql"
docker exec docker-db_postgres-1 pg_dump -U postgres dify_plugin > "$OFFLINE_DIR/backup/dify_plugin_db_$TIMESTAMP.sql"
echo "  数据库备份完成"

echo ""
echo "[3/7] 备份配置文件..."
cp "$DIFY_DIR/.env" "$OFFLINE_DIR/config/.env"
cp "$DIFY_DIR/docker-compose.yaml" "$OFFLINE_DIR/config/docker-compose.yaml"
cp "$DIFY_DIR/middleware.env" "$OFFLINE_DIR/config/middleware.env" 2>/dev/null || true
cp -r "$DIFY_DIR/nginx" "$OFFLINE_DIR/config/" 2>/dev/null || true
echo "  配置文件备份完成"

echo ""
echo "[4/7] 备份存储文件..."
docker exec docker-db_postgres-1 tar -czf /tmp/storage.tar.gz -C /app storage 2>/dev/null || true
docker cp docker-db_postgres-1:/tmp/storage.tar.gz "$OFFLINE_DIR/backup/storage_$TIMESTAMP.tar.gz" 2>/dev/null || {
    echo "  警告: 存储文件备份失败，尝试其他方式..."
    mkdir -p "$OFFLINE_DIR/backup/storage"
    docker cp docker-api-1:/app/storage/. "$OFFLINE_DIR/backup/storage/" 2>/dev/null || echo "  存储目录为空或不存在"
}

echo ""
echo "[5/7] 复制部署脚本..."
cp -r "$DIFY_DIR/../api" "$OFFLINE_DIR/" 2>/dev/null || true
cp -r "$DIFY_DIR/../web" "$OFFLINE_DIR/" 2>/dev/null || true

echo ""
echo "[6/7] 创建离线安装脚本..."
cat > "$OFFLINE_DIR/scripts/install.sh" << 'INSTALL_EOF'
#!/bin/bash
set -e

INSTALL_DIR="${1:-/opt/dify}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "  Dify 离线部署安装脚本"
echo "  安装目录: $INSTALL_DIR"
echo "=========================================="

if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装"
    echo "请先安装 Docker 和 Docker Compose"
    exit 1
fi

if ! command -v docker &> /dev/null || ! docker compose version &> /dev/null; then
    echo "错误: Docker Compose 未安装"
    exit 1
fi

echo ""
echo "[1/5] 创建安装目录..."
sudo mkdir -p "$INSTALL_DIR"
sudo chown -R $(whoami):$(whoami) "$INSTALL_DIR"

echo ""
echo "[2/5] 加载 Docker 镜像..."
if [ -f "$BASE_DIR/images/dify-all-images.tar" ]; then
    docker load -i "$BASE_DIR/images/dify-all-images.tar"
else
    for image_file in "$BASE_DIR/images/"*.tar; do
        echo "  加载: $image_file"
        docker load -i "$image_file"
    done
fi

echo ""
echo "[3/5] 复制配置文件..."
cp -r "$BASE_DIR/config/"* "$INSTALL_DIR/docker/"

echo ""
echo "[4/5] 恢复数据库..."
read -p "是否恢复数据库备份? (y/n): " restore_db
if [ "$restore_db" = "y" ]; then
    echo "  启动数据库服务..."
    cd "$INSTALL_DIR/docker"
    docker compose up -d db_postgres redis
    sleep 10
    
    latest_db=$(ls -t "$BASE_DIR/backup/dify_db_"*.sql | head -1)
    latest_plugin_db=$(ls -t "$BASE_DIR/backup/dify_plugin_db_"*.sql | head -1)
    
    if [ -f "$latest_db" ]; then
        echo "  恢复主数据库..."
        cat "$latest_db" | docker exec -i docker-db_postgres-1 psql -U postgres dify
    fi
    
    if [ -f "$latest_plugin_db" ]; then
        echo "  恢复插件数据库..."
        cat "$latest_plugin_db" | docker exec -i docker-db_postgres-1 psql -U postgres dify_plugin
    fi
fi

echo ""
echo "[5/5] 启动服务..."
cd "$INSTALL_DIR/docker"
docker compose up -d

echo ""
echo "=========================================="
echo "  安装完成!"
echo "  访问地址: http://localhost"
echo "=========================================="
INSTALL_EOF
chmod +x "$OFFLINE_DIR/scripts/install.sh"

echo ""
echo "[7/7] 创建部署文档..."
cat > "$OFFLINE_DIR/docs/README.md" << 'DOC_EOF'
# Dify 离线部署指南

## 一、系统要求

### 硬件要求

| 资源 | 最低要求 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核心 | 4+ 核心 |
| 内存 | 4 GB | 8+ GB |
| 磁盘 | 50 GB | 100+ GB |

### 软件要求

| 软件 | 版本要求 |
|------|---------|
| Docker | 19.03+ |
| Docker Compose | 1.28+ |
| 操作系统 | Ubuntu 18.04+ / CentOS 7+ |

## 二、目录结构

```
dify-offline/
├── images/              # Docker 镜像文件
│   ├── dify-all-images.tar  # 合并的镜像包
│   └── *.tar            # 单独的镜像文件
├── backup/              # 备份文件
│   ├── dify_db_*.sql    # 主数据库备份
│   ├── dify_plugin_db_*.sql  # 插件数据库备份
│   └── storage_*.tar.gz # 存储文件备份
├── config/              # 配置文件
│   ├── .env             # 环境变量
│   ├── docker-compose.yaml
│   └── middleware.env
├── scripts/             # 部署脚本
│   └── install.sh       # 安装脚本
└── docs/                # 文档
    └── README.md
```

## 三、安装步骤

### 步骤 1: 准备环境

```bash
# 检查 Docker 版本
docker --version
docker compose version

# 如果未安装 Docker，请先安装
# Ubuntu
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# CentOS
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker
```

### 步骤 2: 复制离线包

将整个 `dify-offline` 目录复制到目标服务器。

### 步骤 3: 执行安装

```bash
cd dify-offline
./scripts/install.sh /opt/dify
```

### 步骤 4: 验证安装

```bash
# 检查服务状态
docker compose ps

# 检查日志
docker compose logs -f api

# 访问测试
curl http://localhost/install
```

## 四、手动安装步骤

如果自动脚本失败，可以手动执行：

### 4.1 加载镜像

```bash
cd dify-offline
docker load -i images/dify-all-images.tar
```

### 4.2 创建目录并复制配置

```bash
sudo mkdir -p /opt/dify/docker
sudo chown -R $(whoami):$(whoami) /opt/dify
cp -r config/* /opt/dify/docker/
```

### 4.3 启动服务

```bash
cd /opt/dify/docker
docker compose up -d
```

### 4.4 恢复数据库（可选）

```bash
# 启动数据库
docker compose up -d db_postgres

# 等待数据库就绪
sleep 10

# 恢复数据
cat backup/dify_db_*.sql | docker exec -i docker-db_postgres-1 psql -U postgres dify
cat backup/dify_plugin_db_*.sql | docker exec -i docker-db_postgres-1 psql -U postgres dify_plugin
```

## 五、配置说明

### 5.1 环境变量

编辑 `/opt/dify/docker/.env` 文件：

```env
# 服务地址（根据实际情况修改）
CONSOLE_API_URL=http://your-server/console/api
SERVICE_API_URL=http://your-server/api
APP_WEB_URL=http://your-server

# 安全配置
SECRET_KEY=your-secret-key

# 数据库配置
DB_PASSWORD=your-db-password

# Redis 配置
REDIS_PASSWORD=your-redis-password
```

### 5.2 修改配置后重启

```bash
cd /opt/dify/docker
docker compose down
docker compose up -d
```

## 六、常见问题

### 6.1 端口冲突

```bash
# 检查端口占用
netstat -tlnp | grep -E '80|443|5001'

# 修改 docker-compose.yaml 中的端口映射
```

### 6.2 权限问题

```bash
# 修改目录权限
sudo chown -R $(whoami):$(whoami) /opt/dify

# 修改 Docker 权限
sudo usermod -aG docker $USER
```

### 6.3 镜像加载失败

```bash
# 分开加载镜像
for img in images/*.tar; do
    docker load -i "$img"
done
```

### 6.4 数据库连接失败

```bash
# 检查数据库状态
docker compose ps db_postgres

# 查看数据库日志
docker compose logs db_postgres

# 重启数据库
docker compose restart db_postgres
```

## 七、服务管理

```bash
# 启动服务
docker compose up -d

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 查看日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f api
```

## 八、升级指南

1. 备份当前数据
2. 加载新版本镜像
3. 停止服务
4. 更新配置文件
5. 启动服务

## 九、技术支持

- 官方文档: https://docs.dify.ai/
- GitHub: https://github.com/langgenius/dify
DOC_EOF

echo ""
echo "=========================================="
echo "  打包完成!"
echo "  输出目录: $OFFLINE_DIR"
echo ""
echo "  目录大小:"
du -sh "$OFFLINE_DIR"/*
echo ""
echo "  总大小:"
du -sh "$OFFLINE_DIR"
echo "=========================================="
