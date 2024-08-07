from sqlalchemy import Column, String, Integer, select, insert, and_
from models.Order import Order
from models.DB import connect_and_close, lock_and_release
from models.DepositAgent import DepositAgent
from models.User import User
from sqlalchemy.orm import Session
import datetime


class DepositOrder(Order):
    __tablename__ = "deposit_orders"
    ref_number = Column(String)
    deposit_wallet = Column(String)
    acc_number = Column(String)
    agent_id = Column(Integer, default=0)

    @staticmethod
    @connect_and_close
    def get_deposit_after_check_order(s: Session = None):
        res = s.execute(
            select(DepositOrder)
            .where(and_(DepositOrder.working_on_it == 0, DepositOrder.state == "sent"))
            .limit(1)
        )
        try:
            return res.fetchone().t[0]
        except:
            pass

    @staticmethod
    @lock_and_release
    async def add_deposit_order(
        user_id: int,
        method: str,
        ref_number: str,
        acc_number: str,
        deposit_wallet:str,
        agent_id: int = None,
        s: Session = None,
    ):
        res = s.execute(
            insert(DepositOrder).values(
                user_id=user_id,
                method=method,
                ref_number=ref_number,
                acc_number=acc_number,
                deposit_wallet=deposit_wallet,
                agent_id=agent_id if agent_id else 0,
            ),
        )
        return res.lastrowid

    @staticmethod
    @lock_and_release
    async def reply_with_deposit_proof(
        serial: int,
        worker_id: int,
        user_id: int,
        amount: float,
        s: Session = None,
    ):
        s.query(DepositOrder).filter_by(serial=serial).update(
            {
                DepositOrder.state: "approved",
                DepositOrder.working_on_it: 0,
                DepositOrder.approve_date: datetime.datetime.now(),
            }
        )
        s.query(DepositAgent).filter_by(id=worker_id).update(
            {
                DepositAgent.approved_deposits: DepositAgent.approved_deposits + amount,
                DepositAgent.approved_deposits_week: DepositAgent.approved_deposits_week
                + amount,
                DepositAgent.approved_deposits_num: DepositAgent.approved_deposits_num
                + 1,
            }
        )
        s.query(User).filter_by(id=user_id).update(
            {
                User.deposit_balance: User.deposit_balance + amount,
            }
        )
