from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
from pathlib import Path

class Settings(BaseSettings):
    """应用配置类，支持从环境变量和.env文件加载配置"""
    
    # 配置模型配置
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",  # 指向api目录下的.env文件
        env_file_encoding="utf-8",  # 编码格式
        case_sensitive=False,       # 环境变量不区分大小写
        extra="ignore"              # 忽略未知的环境变量
    )
    
    # 1. 基础配置
    PROJECT_NAME: str = "My Web API"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True  # 默认开发环境
    
    # 2. 环境标识（核心：通过此变量切换环境）
    ENVIRONMENT: str = "dev"  # 可选：development/production/test
    
    # 3. 数据库配置
    # 开发环境默认SQLite，生产环境使用PostgreSQL
    DATABASE_URL: Optional[str] = None
    SQLITE_DB_PATH: str = "./db.sqlite3"
    
    # PostgreSQL配置（生产环境使用）
    POSTGRES_DB: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    
    # 4. CORS配置
    BACKEND_CORS_ORIGINS: List[str] = ["*"]  # 开发环境允许所有来源
    
    # 5. 日志配置
    LOG_LEVEL: str = "DEBUG"  # 开发环境详细日志
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"  # 日志格式
    
    # 6. 敏感配置（生产环境必须通过环境变量设置）
    SECRET_KEY: str = "dev-secret-key"  # 开发环境默认值，生产环境必须修改
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    MILK_NOTE_API_KEY: str = "MILK_NOTE_API_KEY"

    API_KEY: Optional[str] = None
    
    @property
    def actual_database_url(self) -> str:
        """根据环境返回实际数据库URL"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        if self.ENVIRONMENT == "production":
            # 生产环境：使用PostgreSQL
            return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@\
{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        else:
            # 开发环境：使用SQLite
            return f"sqlite:///{self.SQLITE_DB_PATH}"

# 创建全局配置实例（应用启动时加载）
settings = Settings()

# 根据环境动态调整配置
if settings.ENVIRONMENT == "production":
    # 生产环境：收紧配置
    if not settings.SECRET_KEY or settings.SECRET_KEY == "dev-secret-key":
        raise ValueError("生产环境必须设置有效的SECRET_KEY")
    settings.DEBUG = False
    settings.LOG_LEVEL = "INFO"
    # 生产环境CORS设置（示例：只允许特定域名）
    # settings.BACKEND_CORS_ORIGINS = ["https://example.com"]
elif settings.ENVIRONMENT == "test":
    # 测试环境：特殊配置
    settings.DEBUG = False
    settings.LOG_LEVEL = "WARNING"

if __name__ == "__main__":
    print(settings)