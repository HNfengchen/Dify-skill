#!/bin/bash

set -e

BACKUP_DIR="${1:-/home/fengchen/projects/Dify/dify-offline/backup}"
DIFY_DIR="/home/fengchen/projects/Dify/dify-deploy/docker"

echo "=========================================="
echo "  Dify 数据恢复脚本"
echo "=========================================="

if [ ! -d "$BACKUP_DIR" ]; then
    echo "错误: 备份目录不存在: $BACKUP_DIR"
    exit 1
fi

echo ""
echo "可用的备份文件:"
echo ""

echo "数据库备份:"
ls -lt "$BACKUP_DIR"/*.sql 2>/dev/null | head -5 || echo "  无数据库备份"
echo ""

echo "存储文件备份:"
ls -lt "$BACKUP_DIR"/*.tar.gz 2>/dev/null | head -5 || echo "  无存储备份"
echo ""

echo "配置文件备份:"
ls -lt "$BACKUP_DIR"/env_* "$BACKUP_DIR"/docker-compose_* 2>/dev/null | head -5 || echo "  无配置备份"
echo ""

read -p "是否继续恢复? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "已取消"
    exit 0
fi

echo ""
echo "[1/3] 恢复数据库..."
latest_db=$(ls -t "$BACKUP_DIR"/dify_db_*.sql 2>/dev/null | head -1)
latest_plugin_db=$(ls -t "$BACKUP_DIR"/dify_plugin_db_*.sql 2>/dev/null | head -1)

if [ -f "$latest_db" ]; then
    echo "  恢复主数据库: $(basename $latest_db)"
    docker exec -i docker-db_postgres-1 psql -U postgres -c "CREATE DATABASE dify;" 2>/dev/null || true
    cat "$latest_db" | docker exec -i docker-db_postgres-1 psql -U postgres dify
else
    echo "  未找到主数据库备份"
fi

if [ -f "$latest_plugin_db" ]; then
    echo "  恢复插件数据库: $(basename $latest_plugin_db)"
    docker exec -i docker-db_postgres-1 psql -U postgres -c "CREATE DATABASE dify_plugin;" 2>/dev/null || true
    cat "$latest_plugin_db" | docker exec -i docker-db_postgres-1 psql -U postgres dify_plugin
else
    echo "  未找到插件数据库备份"
fi

echo ""
echo "[2/3] 恢复配置文件..."
latest_env=$(ls -t "$BACKUP_DIR"/env_* 2>/dev/null | head -1)
latest_compose=$(ls -t "$BACKUP_DIR"/docker-compose_*.yaml 2>/dev/null | head -1)

if [ -f "$latest_env" ]; then
    echo "  恢复环境变量: $(basename $latest_env)"
    cp "$latest_env" "$DIFY_DIR/.env"
fi

if [ -f "$latest_compose" ]; then
    echo "  恢复 Docker Compose 配置: $(basename $latest_compose)"
    cp "$latest_compose" "$DIFY_DIR/docker-compose.yaml"
fi

echo ""
echo "[3/3] 恢复存储文件..."
latest_storage=$(ls -t "$BACKUP_DIR"/storage_*.tar.gz 2>/dev/null | head -1)

if [ -f "$latest_storage" ]; then
    echo "  恢复存储文件: $(basename $latest_storage)"
    docker cp "$latest_storage" docker-api-1:/tmp/
    docker exec docker-api-1 tar -xzf "/tmp/$(basename $latest_storage)" -C /app
else
    echo "  未找到存储文件备份"
fi

echo ""
echo "=========================================="
echo "  恢复完成!"
echo ""
echo "  请重启服务使配置生效:"
echo "  cd $DIFY_DIR && docker compose restart"
echo "=========================================="
