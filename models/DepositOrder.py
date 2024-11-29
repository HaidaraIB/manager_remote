from sqlalchemy import Column, String, Integer, TIMESTAMP, select, insert, and_
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
    gov = Column(String, default="")
    from_withdraw_serial = Column(Integer, default=0)

    ignore_date = Column(TIMESTAMP)

    @classmethod
    @connect_and_close
    def get_deposit_after_check_order(cls, is_point_deposit: bool, s: Session = None):
        if is_point_deposit:
            res = s.execute(
                select(cls)
                .where(
                    and_(
                        cls.working_on_it == 0,
                        cls.state == "sent",
                        cls.acc_number == "",
                    )
                )
                .limit(1)
            )
        else:
            res = s.execute(
                select(cls)
                .where(and_(cls.working_on_it == 0, cls.state == "sent"))
                .limit(1)
            )
        try:
            return res.fetchone().t[0]
        except:
            pass

    @classmethod
    @lock_and_release
    async def add_deposit_order(
        cls,
        user_id: int,
        group_id: int,
        method: str,
        amount: float,
        deposit_wallet: str = "",
        acc_number: str = "",
        ref_number: str = "",
        agent_id: int = 0,
        gov: str = "",
        from_withdraw_serial: int = 0,
        s: Session = None,
    ):
        res = s.execute(
            insert(cls).values(
                user_id=user_id,
                method=method,
                amount=amount,
                ref_number=ref_number,
                acc_number=acc_number,
                group_id=group_id,
                deposit_wallet=deposit_wallet,
                agent_id=agent_id,
                gov=gov,
                from_withdraw_serial=from_withdraw_serial,
            ),
        )
        return res.lastrowid

    @classmethod
    @lock_and_release
    async def approve_deposit_order(
        cls,
        serial: int,
        worker_id: int,
        user_id: int,
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

    @classmethod
    @lock_and_release
    async def unapprove_deposit_order(
        cls,
        serial: int,
        worker_id: int,
        user_id: int,
        amount: float,
        s: Session = None,
    ):
        s.query(cls).filter_by(serial=serial).update(
            {
                cls.state: "processing",
                cls.working_on_it: 0,
            }
        )
        s.query(DepositAgent).filter_by(id=worker_id).update(
            {
                DepositAgent.approved_deposits_week: (
                    DepositAgent.approved_deposits_week - amount
                ),
                DepositAgent.approved_deposits_num: (
                    DepositAgent.approved_deposits_num - 1
                ),
                DepositAgent.approved_deposits: DepositAgent.approved_deposits - amount,
            }
        )
        s.query(User).filter_by(id=user_id).update(
            {
                User.deposit_balance: User.deposit_balance - amount,
            }
        )

    @classmethod
    @lock_and_release
    async def ignore_order(cls, serial: int, s: Session = None):
        s.query(cls).filter_by(serial=serial).update(
            {
                cls.state: "ignored",
                cls.ignore_date: datetime.datetime.now(),
                cls.working_on_it: 0,
            }
        )
