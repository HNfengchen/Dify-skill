#!/bin/bash

set -e

BACKUP_DIR="${1:-/home/fengchen/projects/Dify/dify-offline/backup}"
DIFY_DIR="/home/fengchen/projects/Dify/dify-deploy/docker"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=========================================="
echo "  Dify 数据备份脚本"
echo "  时间: $(date)"
echo "  备份目录: $BACKUP_DIR"
echo "=========================================="

mkdir -p "$BACKUP_DIR"

echo ""
echo "[1/4] 备份数据库..."
docker exec docker-db_postgres-1 pg_dump -U postgres dify > "$BACKUP_DIR/dify_db_$TIMESTAMP.sql"
docker exec docker-db_postgres-1 pg_dump -U postgres dify_plugin > "$BACKUP_DIR/dify_plugin_db_$TIMESTAMP.sql"
echo "  数据库备份完成"
echo "    - $BACKUP_DIR/dify_db_$TIMESTAMP.sql"
echo "    - $BACKUP_DIR/dify_plugin_db_$TIMESTAMP.sql"

echo ""
echo "[2/4] 备份配置文件..."
cp "$DIFY_DIR/.env" "$BACKUP_DIR/env_$TIMESTAMP"
cp "$DIFY_DIR/docker-compose.yaml" "$BACKUP_DIR/docker-compose_$TIMESTAMP.yaml"
cp "$DIFY_DIR/middleware.env" "$BACKUP_DIR/middleware_$TIMESTAMP.env" 2>/dev/null || true
echo "  配置文件备份完成"

echo ""
echo "[3/4] 备份存储文件..."
docker exec docker-api-1 tar -czf /tmp/storage_$TIMESTAMP.tar.gz -C /app storage 2>/dev/null || {
    echo "  警告: 无法从容器备份存储文件"
    mkdir -p "$BACKUP_DIR/storage_$TIMESTAMP"
    docker cp docker-api-1:/app/storage/. "$BACKUP_DIR/storage_$TIMESTAMP/" 2>/dev/null || {
        echo "  存储目录为空或不存在"
        rmdir "$BACKUP_DIR/storage_$TIMESTAMP" 2>/dev/null || true
    }
}
docker cp docker-api-1:/tmp/storage_$TIMESTAMP.tar.gz "$BACKUP_DIR/storage_$TIMESTAMP.tar.gz" 2>/dev/null || true
echo "  存储文件备份完成"

echo ""
echo "[4/4] 清理旧备份（保留最近 7 天）..."
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "env_*" -mtime +7 -delete 2>/dev/null || true
echo "  清理完成"

echo ""
echo "=========================================="
echo "  备份完成!"
echo ""
echo "  备份文件:"
ls -lh "$BACKUP_DIR"/*$TIMESTAMP* 2>/dev/null || echo "  无备份文件"
echo ""
echo "  备份目录大小:"
du -sh "$BACKUP_DIR"
echo "=========================================="
