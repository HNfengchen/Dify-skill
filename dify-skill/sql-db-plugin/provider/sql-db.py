from typing import Any
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


class SqlDbProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        db_uri = credentials.get("db_uri")
        db_type = credentials.get("db_type", "postgresql")
        
        if not db_uri:
            host = credentials.get("host")
            port = credentials.get("port")
            username = credentials.get("username", "")
            password = credentials.get("password", "")
            database = credentials.get("database")
            
            if not host and db_type != 'sqlite':
                raise ToolProviderCredentialValidationError("Host is required")
            if not database:
                raise ToolProviderCredentialValidationError("Database name is required")
            
            db_uri = self._build_uri(db_type, host, port, username, password, database)
        
        try:
            engine = create_engine(db_uri, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            engine.dispose()
        except SQLAlchemyError as e:
            raise ToolProviderCredentialValidationError(f"Database connection failed: {str(e)}")
        except Exception as e:
            raise ToolProviderCredentialValidationError(f"Validation error: {str(e)}")

    def _build_uri(self, db_type: str, host: str, port: int, 
                   username: str, password: str, database: str) -> str:
        default_ports = {
            'postgresql': 5432,
            'mysql': 3306,
            'oracle': 1521,
            'sqlite': None
        }
        
        if db_type == 'sqlite':
            return f'sqlite:///{database}'
        
        port = port or default_ports.get(db_type)
        
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
            raise ValueError(f"Unsupported database type: {db_type}")
