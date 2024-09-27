from sqlalchemy import Column, Integer, insert
from models.DB import Base, lock_and_release
from sqlalchemy.orm import Session


class GhaflaOffer(Base):
    __tablename__ = "ghafla_offers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_serial = Column(Integer)
    factor = Column(Integer)

    @classmethod
    @lock_and_release
    async def add(cls, serial: int, factor: int, s: Session = None):
        s.execute(insert(cls).values(order_serial=serial, factor=factor))
