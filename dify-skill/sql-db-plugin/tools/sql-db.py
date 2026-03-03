from collections.abc import Generator
from typing import Any
from datetime import date, datetime
import re
import json
import logging
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """Exception raised for database connection errors."""
    pass


class QueryExecutionError(Exception):
    """Exception raised for query execution errors."""
    pass


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        return super().default(obj)


class SqlDbTool(Tool):
    DEFAULT_PORTS = {
        'postgresql': 5432,
        'mysql': 3306,
        'oracle': 1521,
        'sqlite': None
    }

    def _build_connection_uri(self, db_type: str, host: str, port: int, 
                               username: str, password: str, database: str) -> str:
        if db_type == 'sqlite':
            return f'sqlite:///{database}'
        
        if not host:
            raise DatabaseConnectionError(f"Host is required for {db_type}")
        if not database:
            raise DatabaseConnectionError(f"Database name is required for {db_type}")
        
        port = port or self.DEFAULT_PORTS.get(db_type)
        
        # URL encode username and password to handle special characters
        encoded_username = quote_plus(username) if username else ''
        encoded_password = quote_plus(password) if password else ''
        
        if db_type == 'postgresql':
            return f'postgresql+psycopg2://{encoded_username}:{encoded_password}@{host}:{port}/{database}'
        elif db_type == 'mysql':
            return f'mysql+pymysql://{encoded_username}:{encoded_password}@{host}:{port}/{database}'
        elif db_type == 'oracle':
            return f'oracle+oracledb://{encoded_username}:{encoded_password}@{host}:{port}/?service_name={database}'
        else:
            raise DatabaseConnectionError(f"Unsupported database type: {db_type}")

    def _validate_sql_query(self, sql_query: str) -> None:
        sql_upper = sql_query.upper().strip()
        
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'GRANT', 'REVOKE']
        
        for keyword in dangerous_keywords:
            pattern = rf'\b{keyword}\b'
            if re.search(pattern, sql_upper):
                logger.warning(f"Potentially dangerous SQL keyword detected: {keyword}")

    def _format_value(self, value: Any) -> str:
        if value is None:
            return 'NULL'
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        if isinstance(value, bytes):
            return value.decode('utf-8', errors='replace')
        return str(value)

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        db_uri = tool_parameters.get("db_uri")
        db_type = tool_parameters.get("db_type", "postgresql")
        sql_query = tool_parameters.get("sql_query", "").strip()
        output_format = tool_parameters.get("format", "json")

        if not sql_query:
            yield self.create_text_message("Error: SQL query cannot be empty")
            return

        self._validate_sql_query(sql_query)

        if not db_uri:
            host = tool_parameters.get("host")
            port = tool_parameters.get("port")
            username = tool_parameters.get("username", "")
            password = tool_parameters.get("password", "")
            database = tool_parameters.get("database")

            try:
                db_uri = self._build_connection_uri(db_type, host, port, username, password, database)
            except DatabaseConnectionError as e:
                yield self.create_text_message(f"Connection Error: {str(e)}")
                return

        try:
            engine = create_engine(
                db_uri,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={'connect_timeout': 30} if db_type != 'sqlite' else {}
            )
            
            with engine.connect() as connection:
                result = connection.execute(text(sql_query))
                
                columns = list(result.keys())
                rows = [dict(zip(columns, row)) for row in result.fetchall()]

                if output_format == 'json':
                    yield self.create_json_message({
                        "success": True,
                        "columns": columns,
                        "row_count": len(rows),
                        "rows": rows,
                    })
                
                elif output_format == 'json rows arr':
                    rows_arr = []
                    for row in rows:
                        row_values = [self._format_value(row[col]) for col in columns]
                        rows_arr.append(row_values)
                    yield self.create_json_message({
                        "success": True,
                        "columns": columns,
                        "row_count": len(rows_arr),
                        "rows": rows_arr
                    })
                
                elif output_format == 'Markdown to string':
                    md_result = self._generate_markdown(sql_query, columns, rows)
                    yield self.create_text_message(md_result)
                
                elif output_format == 'Markdown to file':
                    md_result = self._generate_markdown(sql_query, columns, rows)
                    yield self.create_blob_message(
                        md_result, 
                        meta={'mime_type': 'text/markdown', 'filename': 'result.md'}
                    )
                
                elif output_format == 'csv':
                    csv_result = self._generate_csv(columns, rows)
                    yield self.create_blob_message(
                        csv_result, 
                        meta={'mime_type': 'text/csv', 'filename': 'result.csv'}
                    )
                
                elif output_format == 'yaml to file':
                    yaml_result = self._generate_yaml(columns, rows)
                    yield self.create_blob_message(
                        yaml_result, 
                        meta={'mime_type': 'text/yaml', 'filename': 'result.yaml'}
                    )
                
                elif output_format == 'yaml to string':
                    yaml_result = self._generate_yaml(columns, rows)
                    yield self.create_text_message(yaml_result)
                
                elif output_format == 'html to file':
                    html_result = self._generate_html(columns, rows)
                    yield self.create_blob_message(
                        html_result, 
                        meta={'mime_type': 'text/html', 'filename': 'result.html'}
                    )
                
                elif output_format == 'html to string':
                    html_result = self._generate_html(columns, rows)
                    yield self.create_text_message(html_result)
                
                else:
                    yield self.create_json_message({
                        "success": True,
                        "columns": columns,
                        "row_count": len(rows),
                        "rows": rows,
                    })

        except SQLAlchemyError as e:
            error_msg = str(e)
            logger.error(f"SQLAlchemy error: {error_msg}")
            yield self.create_json_message({
                "success": False,
                "error": "DatabaseError",
                "message": error_msg,
                "hint": self._get_error_hint(error_msg)
            })
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Unexpected error: {error_msg}")
            yield self.create_json_message({
                "success": False,
                "error": "UnexpectedError",
                "message": error_msg
            })

    def _generate_markdown(self, sql_query: str, columns: list, rows: list) -> str:
        result = f"```sql\n{sql_query}\n```\n\n"
        result += "| " + " | ".join(columns) + " |\n"
        result += "| " + " | ".join(["---" for _ in columns]) + " |\n"
        for row in rows:
            result += "| " + " | ".join([self._format_value(v) for v in row.values()]) + " |\n"
        return result

    def _generate_csv(self, columns: list, rows: list) -> str:
        result = ",".join(columns) + "\n"
        for row in rows:
            result += ",".join([f'"{self._format_value(v)}"' for v in row.values()]) + "\n"
        return result

    def _generate_yaml(self, columns: list, rows: list) -> str:
        result = "---\ncolumns:\n"
        for col in columns:
            result += f"  - {col}\n"
        result += "rows:\n"
        for row in rows:
            result += "  - \n"
            for key, value in row.items():
                formatted_value = self._format_value(value)
                result += f"    {key}: {formatted_value}\n"
        return result

    def _generate_html(self, columns: list, rows: list) -> str:
        result = "<table border='1' cellpadding='5' cellspacing='0' style='border-collapse: collapse;'>\n"
        result += "  <tr style='background-color: #f2f2f2;'>\n"
        for col in columns:
            result += f"    <th style='border: 1px solid #ddd; padding: 8px;'>{col}</th>\n"
        result += "  </tr>\n"
        for row in rows:
            result += "  <tr>\n"
            for value in row.values():
                result += f"    <td style='border: 1px solid #ddd; padding: 8px;'>{self._format_value(value)}</td>\n"
            result += "  </tr>\n"
        result += "</table>"
        return result

    def _get_error_hint(self, error_msg: str) -> str:
        error_lower = error_msg.lower()
        
        if 'connection refused' in error_lower:
            return "Check if the database server is running and accessible"
        elif 'authentication failed' in error_lower or 'access denied' in error_lower:
            return "Check your username and password"
        elif 'database' in error_lower and 'does not exist' in error_lower:
            return "Check if the database name is correct"
        elif 'timeout' in error_lower:
            return "Connection timed out. Check network connectivity and firewall settings"
        elif 'syntax' in error_lower:
            return "Check your SQL query syntax"
        elif 'table' in error_lower and 'not found' in error_lower:
            return "Check if the table exists in the database"
        else:
            return "Please check your connection parameters and SQL query"
