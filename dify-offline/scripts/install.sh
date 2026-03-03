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
