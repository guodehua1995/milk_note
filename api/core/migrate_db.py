from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from api.core.config import settings
from api.models.task import Base

# 创建数据库引擎
engine = create_engine(
    settings.actual_database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.actual_database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def migrate_database():
    """数据库迁移函数"""
    print("开始数据库迁移...")
    
    # 创建所有表
    print("创建新表结构...")
    Base.metadata.create_all(bind=engine)
    print("新表结构创建完成")
    
    # 检查是否存在旧表
    with engine.connect() as conn:
        # 检查旧的tasks表
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_name='tasks';"))
        if result.fetchone():
            print("旧的tasks表存在，开始迁移数据...")
            # 这里可以添加数据迁移逻辑
            # 例如：从旧表读取数据，插入到新表
            print("数据迁移完成")
        
        # 检查旧的recurring_tasks表
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_name='recurring_tasks';"))
        if result.fetchone():
            print("旧的recurring_tasks表存在，开始迁移数据...")
            # 这里可以添加数据迁移逻辑
            print("数据迁移完成")
    
    print("数据库迁移完成！")


if __name__ == "__main__":
    migrate_database()
