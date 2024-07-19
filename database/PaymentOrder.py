from sqlalchemy import Column, Integer, String, select, and_
from sqlalchemy.orm import Session
from database.Order import Order
from database.DB import connect_and_close, lock_and_release
from database.PaymentAgent import PaymentAgent
import datetime


class PaymentOrder(Order):
    __abstract__ = True
    bank_account_name = Column(String)
    payment_method_number = Column(String)
    pending_check_message_id = Column(Integer)
    checking_message_id = Column(Integer, default=0)

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
                and_(cls.working_on_it == 0, cls.method == method, cls.state == "sent")
            )
            .limit(1)
        )
        try:
            return res.fetchone().t[0]
        except:
            pass

    @classmethod
    @lock_and_release
    async def reply_with_payment_proof(
        cls,
        archive_message_ids: int,
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
                cls.archive_message_ids: archive_message_ids,
                cls.approve_date: datetime.datetime.now(),
            }
        )
        s.query(PaymentAgent).filter_by(id=worker_id, method=method).update(
            {
                PaymentAgent.approved_withdraws: PaymentAgent.approved_withdraws
                + amount,
                PaymentAgent.approved_withdraws_day: PaymentAgent.approved_withdraws_day
                + amount,
                PaymentAgent.approved_withdraws_num: PaymentAgent.approved_withdraws_num
                + 1,
                PaymentAgent.pre_balance: PaymentAgent.pre_balance - amount,
            }
        )
