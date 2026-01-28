from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from api.core import Base
from passlib.context import CryptContext
from sqlalchemy.orm import Session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    def set_password(self, password: str):
        '''
        设置用户密码,密码会被加密存储
        '''
        self.password = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        '''
        验证用户密码是否正确
        '''
        return pwd_context.verify(password, self.password)

    @classmethod
    def get_user_by_username(cls, db: Session, username: str):
        return db.query(cls).filter(cls.username == username).first()


