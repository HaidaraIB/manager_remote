from sqlalchemy import Column, Integer, String, Boolean, select, insert
from models.DB import Base, lock_and_release, connect_and_close
from sqlalchemy.orm import Session
from common.constants import *


class PaymentMethod(Base):
    __tablename__ = "payment_methods"
    name = Column(String, primary_key=True)
    deposit_on_off = Column(Boolean, default=1)
    withdraw_on_off = Column(Boolean, default=1)
    busdt_on_off = Column(Boolean, default=1)

    @staticmethod
    @lock_and_release
    async def turn_payment_method_on_or_off(
        name: str,
        proccess: str,
        on: int = 0,
        s: Session = None,
    ):
        s.query(PaymentMethod).filter_by(name=name).update(
            {
                getattr(PaymentMethod, f"{proccess}_on_off"): on,
            }
        )

    @staticmethod
    @connect_and_close
    def get_payment_method(name: str, s: Session = None):
        res = s.execute(select(PaymentMethod).where(PaymentMethod.name == name))
        try:
            return res.fetchone().t[0]
        except:
            pass

    @staticmethod
    @connect_and_close
    def get_payment_methods(s: Session = None):
        res = s.execute(select(PaymentMethod))
        try:
            return list(map(lambda x: x[0], res.tuples().all()))
        except:
            pass

    @staticmethod
    @lock_and_release
    async def init_payment_methods(s: Session = None):
        s.execute(
            insert(PaymentMethod)
            .values([{"name": method} for method in PAYMENT_METHODS_LIST])
            .prefix_with("OR IGNORE")
        )
