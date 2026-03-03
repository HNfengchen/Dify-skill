# SQL Database Tool - Dify 插件使用文档

## 一、插件概述

SQL Database Tool 是一个强大的 Dify 插件，支持多种主流数据库的查询操作。通过此插件，LLM 可以直接连接和查询数据库，实现数据分析和信息检索功能。

### 支持的数据库类型

| 数据库 | 默认端口 | 驱动 | 状态 |
|--------|---------|------|------|
| PostgreSQL | 5432 | psycopg2 | ✅ 支持 |
| MySQL | 3306 | pymysql | ✅ 支持 |
| SQL Server | 1433 | pyodbc | ✅ 支持 |
| Oracle | 1521 | oracledb | ✅ 支持 |
| SQLite | - | 内置 | ✅ 支持 |

### 主要功能

- 多数据库类型支持
- 多种输出格式（JSON、CSV、Markdown、HTML、YAML）
- 完善的错误处理和提示
- SQL 安全检查
- 连接池管理

---

## 二、安装步骤

### 2.1 下载插件

插件文件：`sql-db-plugin.difypkg`

### 2.2 在 Dify 中安装

1. 打开 Dify 控制台：http://localhost
2. 进入 **设置** → **插件**
3. 点击 **安装插件**
4. 选择 `sql-db-plugin.difypkg` 文件
5. 等待安装完成

### 2.3 验证安装

安装成功后，在插件列表中可以看到 "SQL Database Tool"。

---

## 三、配置说明

### 3.1 连接参数

#### 方式一：使用独立参数（推荐）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| db_type | select | 是 | 数据库类型 |
| host | string | 是* | 数据库主机地址 |
| port | number | 否 | 端口号（不填使用默认端口） |
| username | string | 否 | 用户名 |
| password | string | 否 | 密码 |
| database | string | 是 | 数据库名称 |

*SQLite 不需要 host 参数

#### 方式二：使用连接 URI（高级）

| 参数 | 格式 |
|------|------|
| db_uri | `dialect+driver://username:password@host:port/database` |

### 3.2 各数据库连接示例

#### PostgreSQL

```
db_type: postgresql
host: localhost
port: 5432
username: postgres
password: your_password
database: mydb
```

或使用 URI：
```
postgresql+psycopg2://postgres:your_password@localhost:5432/mydb
```

#### MySQL

```
db_type: mysql
host: localhost
port: 3306
username: root
password: your_password
database: mydb
```

或使用 URI：
```
mysql+pymysql://root:your_password@localhost:3306/mydb
```

#### SQL Server

```
db_type: sqlserver
host: localhost
port: 1433
username: sa
password: your_password
database: mydb
```

或使用 URI：
```
mssql+pyodbc://sa:your_password@localhost:1433/mydb?driver=ODBC+Driver+17+for+SQL+Server
```

#### Oracle

```
db_type: oracle
host: localhost
port: 1521
username: system
password: your_password
database: ORCL
```

或使用 URI：
```
oracle+oracledb://system:your_password@localhost:1521/ORCL
```

#### SQLite

```
db_type: sqlite
database: /path/to/database.db
```

或使用 URI：
```
sqlite:////path/to/database.db
```

### 3.3 输出格式

| 格式 | 说明 |
|------|------|
| JSON | 标准 JSON 格式，包含列名和行数据 |
| JSON rows array | JSON 数组格式，仅包含行数据 |
| CSV file | CSV 文件格式 |
| YAML file | YAML 文件格式 |
| YAML string | YAML 字符串格式 |
| Markdown file | Markdown 表格文件 |
| Markdown string | Markdown 表格字符串 |
| HTML file | HTML 表格文件 |
| HTML string | HTML 表格字符串 |

---

## 四、使用示例

### 4.1 基本查询

**SQL 查询：**
```sql
SELECT * FROM users LIMIT 10
```

**输出（JSON 格式）：**
```json
{
  "success": true,
  "columns": ["id", "name", "email", "created_at"],
  "row_count": 10,
  "rows": [
    {"id": 1, "name": "张三", "email": "zhangsan@example.com", "created_at": "2024-01-01"},
    {"id": 2, "name": "李四", "email": "lisi@example.com", "created_at": "2024-01-02"}
  ]
}
```

### 4.2 条件查询

```sql
SELECT name, email FROM users WHERE created_at > '2024-01-01' ORDER BY name
```

### 4.3 聚合查询

```sql
SELECT department, COUNT(*) as count, AVG(salary) as avg_salary 
FROM employees 
GROUP BY department 
ORDER BY count DESC
```

### 4.4 多表关联

```sql
SELECT o.order_id, c.customer_name, o.total_amount
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.order_date > '2024-01-01'
```

---

## 五、常见问题排查

### 5.1 连接被拒绝

**错误信息：**
```
Connection refused
```

**解决方案：**
1. 检查数据库服务是否运行
2. 检查主机地址和端口是否正确
3. 检查防火墙设置

### 5.2 认证失败

**错误信息：**
```
Authentication failed / Access denied
```

**解决方案：**
1. 检查用户名和密码是否正确
2. 检查用户是否有访问权限
3. 检查数据库是否允许远程连接

### 5.3 数据库不存在

**错误信息：**
```
Database does not exist
```

**解决方案：**
1. 检查数据库名称拼写
2. 确认数据库已创建

### 5.4 连接超时

**错误信息：**
```
Connection timeout
```

**解决方案：**
1. 检查网络连接
2. 检查防火墙规则
3. 增加连接超时时间

### 5.5 SQL 语法错误

**错误信息：**
```
Syntax error
```

**解决方案：**
1. 检查 SQL 语句语法
2. 确认表名和列名正确
3. 注意不同数据库的 SQL 方言差异

### 5.6 表不存在

**错误信息：**
```
Table not found
```

**解决方案：**
1. 检查表名拼写
2. 确认表在当前数据库中
3. 检查 schema 设置

---

## 六、安全注意事项

### 6.1 SQL 注入防护

- 插件会检测危险 SQL 关键字（DROP、DELETE、TRUNCATE 等）
- 建议只允许 SELECT 查询
- 不要在 SQL 中拼接用户输入

### 6.2 凭证安全

- 使用只读数据库用户
- 限制数据库用户权限
- 定期更换密码
- 不要在日志中记录密码

### 6.3 网络安全

- 使用 SSL/TLS 加密连接
- 限制数据库访问 IP
- 使用 VPN 或内网连接

---

## 七、高级配置

### 7.1 连接池设置

插件默认配置：
- 连接池预检测：启用
- 连接回收时间：3600 秒
- 连接超时：30 秒

### 7.2 自定义驱动

如需使用其他驱动，可在 `requirements.txt` 中添加：

```txt
# PostgreSQL 其他驱动
pg8000>=1.30.0

# MySQL 其他驱动
mysql-connector-python>=8.0.0
```

然后在 URI 中指定驱动：
```
postgresql+pg8000://user:pass@host/db
mysql+mysqlconnector://user:pass@host/db
```

---

## 八、版本历史

### v0.0.2 (当前版本)
- 新增 MySQL 支持
- 新增 SQL Server 支持
- 新增 Oracle 支持
- 新增 SQLite 支持
- 完善错误处理机制
- 添加 SQL 安全检查
- 优化连接池管理

### v0.0.1
- 初始版本
- 仅支持 PostgreSQL

---

## 九、技术支持

- 原项目：https://github.com/QJZT/sql-db
- Dify 官方文档：https://docs.dify.ai/
- 问题反馈：在 GitHub Issues 中提交
