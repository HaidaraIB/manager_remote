from sqlalchemy import Column, Integer, TIMESTAMP, String, insert, select, and_, func
from models.DB import Base, lock_and_release, connect_and_close
from sqlalchemy.orm import Session
from common.constants import GHAFLA_OFFER
import datetime
import pytz


class Offer(Base):
    __tablename__ = "offers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_serial = Column(Integer)
    factor = Column(Integer)
    offer_name = Column(String, server_default=GHAFLA_OFFER)
    offer_date = Column(TIMESTAMP, server_default=func.current_timestamp())

    @classmethod
    @lock_and_release
    async def add(cls, serial: int, factor: int, offer_name: str, s: Session = None):
        s.execute(
            insert(cls).values(
                order_serial=serial,
                factor=factor,
                offer_name=offer_name,
            )
        )

    @classmethod
    @connect_and_close
    def get(
        cls,
        offer_id: int = None,
        today: bool = None,
        offer_name: str = "",
        factor:float = 0,
        s: Session = None,
    ):
        if offer_id:
            res = s.execute(select(cls).where(cls.id == offer_id))
            try:
                return res.fetchone().t[0]
            except:
                pass

        elif today is not None:
            today = datetime.datetime.now(tz=pytz.timezone("Asia/Damascus")).strftime(
                "%Y-%m-%d"
            )
            res = s.execute(
                select(cls).where(
                    func.date(func.datetime(cls.offer_date, "+3 hours")) == today
                )
            )
        elif offer_name:
            res = s.execute(select(cls).where(and_(cls.offer_name == offer_name, cls.factor==factor)))
        else:
            res = s.execute(select(cls))

        try:
            return list(map(lambda x: x[0], res.tuples().all()))
        except:
            pass
