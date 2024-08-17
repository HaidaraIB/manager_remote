from sqlalchemy import (
    Column,
    Integer,
    String,
    PrimaryKeyConstraint,
    select,
    and_,
)
from sqlalchemy.orm import Session
from models.DB import Base, connect_and_close


class WorkerWithUs(Base):
    __abstract__ = True

    user_id = Column(Integer)
    gov = Column(String)
    neighborhood = Column(String)
    order_serial = Column(Integer)
    promo_username = Column(String)
    promo_password = Column(String)
    __table_args__ = (PrimaryKeyConstraint("user_id", "gov", name="_user_id_gov_uc"),)

    @classmethod
    @connect_and_close
    def get_workers(
        cls,
        gov: str = None,
        user_id: int = None,
        order_serial: int = None,
        s: Session = None,
    ):
        try:
            if order_serial:
                res = s.execute(select(cls).where(cls.order_serial == order_serial))
            elif user_id and gov:
                res = s.execute(
                    select(cls).where(and_(cls.gov == gov, cls.user_id == user_id))
                )
            elif user_id:
                res = s.execute(select(cls).where(cls.user_id == user_id))
            else:
                res = s.execute(select(cls).where(cls.gov == gov))

            if gov and not user_id:
                return list(map(lambda x: x[0], res.tuples().all()))
            else:
                return res.fetchone().t[0]
        except:
            pass
