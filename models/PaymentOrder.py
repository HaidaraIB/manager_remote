from sqlalchemy import Column, Integer, String, select, and_
from sqlalchemy.orm import Session
from models.Order import Order
from models.DB import connect_and_close, lock_and_release
from models.PaymentAgent import PaymentAgent
import datetime


class PaymentOrder(Order):
    __abstract__ = True
    payment_method_number = Column(String)

    @classmethod
    @connect_and_close
    def get_payment_order(
        cls,
        method: str,
        s: Session = None,
    ):
        res = s.execute(
            select(cls)
            .where(
                and_(
                    cls.working_on_it == 0,
                    cls.method == method,
                    cls.state.in_(["sent", "split"]),
                )
            )
            .limit(1)
        )
        try:
            return res.fetchone().t[0]
        except:
            pass

    @classmethod
    @lock_and_release
    async def approve_payment_order(
        cls,
        serial: int,
        worker_id: int,
        method: str,
        amount: float,
        s: Session = None,
    ):
        s.query(cls).filter_by(serial=serial).update(
            {
                cls.state: "approved",
                cls.working_on_it: 0,
                cls.approve_date: datetime.datetime.now(),
            }
        )
        s.query(PaymentAgent).filter_by(id=worker_id, method=method).update(
            {
                PaymentAgent.approved_withdraws: (
                    PaymentAgent.approved_withdraws + amount
                ),
                PaymentAgent.approved_withdraws_day: (
                    PaymentAgent.approved_withdraws_day + amount
                ),
                PaymentAgent.approved_withdraws_num: (
                    PaymentAgent.approved_withdraws_num + 1
                ),
                PaymentAgent.pre_balance: PaymentAgent.pre_balance - amount,
            }
        )

    @classmethod
    @lock_and_release
    async def unapprove_payment_order(
        cls,
        serial: int,
        worker_id: int,
        method: str,
        amount: float,
        s: Session = None,
    ):
        s.query(cls).filter_by(serial=serial).update(
            {
                cls.state: "processing",
                cls.working_on_it: 0,
            }
        )
        s.query(PaymentAgent).filter_by(id=worker_id, method=method).update(
            {
                PaymentAgent.approved_withdraws: (
                    PaymentAgent.approved_withdraws - amount
                ),
                PaymentAgent.approved_withdraws_day: (
                    PaymentAgent.approved_withdraws_day - amount
                ),
                PaymentAgent.approved_withdraws_num: (
                    PaymentAgent.approved_withdraws_num - 1
                ),
                PaymentAgent.pre_balance: PaymentAgent.pre_balance + amount,
            }
        )
