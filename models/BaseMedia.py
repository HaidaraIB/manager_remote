from sqlalchemy import Column, Integer, String
from models.DB import Base


class BaseMedia(Base):
    __abstract__ = True
    file_id = Column(String, primary_key=True)
    file_unique_id = Column(String)
    file_size = Column(Integer)
    order_serial = Column(Integer)
    order_type = Column(String)
