from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from .core import settings, setup_logging, logger
from .route.router import api_router
from .core.database import Base,engine
from .tasks.rag_document_processor import rag_document_processor
from .tasks.task_scheduler import task_scheduler

# 初始化日志配置
setup_logging()

logger.info(f"启动应用：{settings.PROJECT_NAME}")
logger.info(f"环境：{settings.ENVIRONMENT}")
logger.info(f"日志级别：{settings.LOG_LEVEL}")

# 定义生命周期事件处理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    - 启动时：启动RAG文档处理器和任务调度器
    - 关闭时：关闭RAG文档处理器和任务调度器
    """
    # 启动事件
    rag_document_processor.start()
    task_scheduler.start()
    yield
    # 关闭事件
    task_scheduler.shutdown()
    rag_document_processor.shutdown()

# 创建 FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

# 自定义中间件：设置全局UTF-8编码
class UTF8ResponseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if isinstance(response, Response):
            # 设置内容类型为UTF-8编码
            if "content-type" in response.headers:
                content_type = response.headers["content-type"]
                if "charset" not in content_type.lower():
                    response.headers["content-type"] = f"{content_type}; charset=utf-8"
            else:
                response.headers["content-type"] = "application/json; charset=utf-8"
        return response

# 添加UTF-8编码中间件
app.add_middleware(UTF8ResponseMiddleware)

# 添加CORS中间件以支持前端跨域请求
if settings.ENVIRONMENT == "dev":
    # 开发环境允许特定的前端开发服务器
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8080",  # Vue开发服务器
            "http://127.0.0.1:8080",
            "http://localhost:8081",  # Vue开发服务器
            "http://127.0.0.1:8081",
            "http://localhost:8082",  # Vue开发服务器
            "http://127.0.0.1:8082",
            "http://localhost:3000",  # 其他可能的前端端口
            "http://127.0.0.1:3000",
            "http://localhost:5173",  # Vite开发服务器
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # 生产环境配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS.split(",") if hasattr(settings, 'ALLOWED_ORIGINS') and settings.ALLOWED_ORIGINS else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

if settings.ENVIRONMENT == "dev":
    # 初始化sqllite表
    logger.info(f"初始化数据库表")
    Base.metadata.create_all(bind=engine)
    logger.info(f"数据库表初始化完成")

app.include_router(api_router)
logger.info(f"路由注册完成")
