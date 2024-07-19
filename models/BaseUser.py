from sqlalchemy import (
    Column,
    Integer,
    String,
)
from models.DB import Base


class BaseUser(Base):
    __abstract__ = True
    id = Column(Integer, nullable=False)
    username = Column(String)
    name = Column(String)

