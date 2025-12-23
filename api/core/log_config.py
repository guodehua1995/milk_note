import logging
import sys
from colorlog import ColoredFormatter
from .config import settings

def setup_logging():
    """设置日志配置，支持彩色控制台输出"""
    
    # 1. 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    
    # 2. 清除已有的处理器（避免重复配置）
    root_logger.handlers.clear()
    
    # 3. 创建控制台处理器（开发环境使用）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.LOG_LEVEL)
    
    # 4. 配置彩色日志格式
    if settings.ENVIRONMENT == "dev":
        # 开发环境：彩色日志，详细格式
        color_formatter = ColoredFormatter(
            "%(log_color)s%(asctime)s [%(levelname)-8s] %(name)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                'DEBUG': 'cyan',      # 调试：青色
                'INFO': 'green',       # 信息：绿色
                'WARNING': 'yellow',   # 警告：黄色
                'ERROR': 'red',        # 错误：红色
                'CRITICAL': 'bold_red' # 致命：粗红色
            }
        )
        console_handler.setFormatter(color_formatter)
    else:
        # 生产环境：普通格式（可扩展为文件日志）
        formatter = logging.Formatter(settings.LOG_FORMAT)
        console_handler.setFormatter(formatter)
    
    # 5. 添加处理器到根日志记录器
    root_logger.addHandler(console_handler)
    
    # 6. 设置第三方库的日志级别（可选，避免过于冗长）
    logging.getLogger("uvicorn").setLevel(logging.INFO)  # Uvicorn日志级别
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)  # SQLAlchemy日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)  # HTTPX日志级别

# 创建模块级别的日志记录器（供其他模块使用）
logger = logging.getLogger(__name__)