from sqlalchemy import Column, String, Integer, TIMESTAMP, Float, insert, select, desc
from sqlalchemy.orm import Session
from models.DB import connect_and_close, lock_and_release
from models.PaymentOrder import PaymentOrder

from datetime import datetime


class WithdrawOrder(PaymentOrder):
    __tablename__ = "withdraw_orders"
    acc_number = Column(String)
    withdraw_code = Column(String)
    agent_id = Column(Integer, default=0)
    gov = Column(String, default="")

    cancel_date = Column(TIMESTAMP)
    split_date = Column(TIMESTAMP)

    @classmethod
    @lock_and_release
    async def add_withdraw_order(
        cls,
        user_id: int,
        group_id: int,
        method: str,
        withdraw_code: str,
        payment_method_number: int,
        acc_number: str,
        agent_id: int = 0,
        gov: str = "",
        s: Session = None,
    ):
        res = s.execute(
            insert(cls).values(
                user_id=user_id,
                group_id=group_id,
                method=method,
                withdraw_code=withdraw_code,
                payment_method_number=payment_method_number,
                acc_number=acc_number,
                agent_id=agent_id,
                gov=gov,
            )
        )
        return res.lastrowid

    @classmethod
    @connect_and_close
    def check_withdraw_code(cls, withdraw_code: str, s: Session = None):
        res = s.execute(
            select(cls)
            .where(cls.withdraw_code == withdraw_code)
            .order_by(desc(cls.serial))
        )
        try:
            return res.fetchone().t[0]
        except:
            pass

    @classmethod
    @lock_and_release
    async def cancel(cls, serial: int, amount: float = 0, s: Session = None):
        s.query(cls).filter_by(serial=serial).update(
            {
                cls.state: "canceled",
                cls.cancel_date: datetime.now(),
                cls.amount: amount,
            }
        )

    @classmethod
    @lock_and_release
    async def split(
        cls,
        serial: int,
        pending_process_message_id: int,
        amount: float,
        s: Session = None,
    ):
        s.query(cls).filter_by(serial=serial).update(
            {
                cls.state: "split",
                cls.pending_process_message_id: pending_process_message_id,
                cls.amount: amount,
                cls.split_date: datetime.now(),
            }
        )

    @classmethod
    @lock_and_release
    async def detach_offer(cls, serial: int, s: Session = None):
        s.query(cls).filter_by(serial=serial).update({cls.offer: 0})
