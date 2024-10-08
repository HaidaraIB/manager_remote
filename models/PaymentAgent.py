from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    PrimaryKeyConstraint,
    select,
    and_,
)
from sqlalchemy.orm import Session
from models.Worker import Worker
from models.DB import lock_and_release, connect_and_close


class PaymentAgent(Worker):
    __tablename__ = "payment_agents"
    method = Column(String)
    approved_withdraws = Column(Integer, default=0)
    approved_withdraws_num = Column(Integer, default=0)
    approved_withdraws_day = Column(Float, default=0)
    daily_rewards_balance = Column(Float, default=0)
    pre_balance = Column(Float, default=0)
    __table_args__ = (PrimaryKeyConstraint("id", "method", name="_id_method_uc"),)

    @staticmethod
    @lock_and_release
    async def daily_reward_worker(
        worker_id: int,
        amount: float,
        method: str,
        s: Session = None,
    ):
        s.query(PaymentAgent).filter_by(id=worker_id, method=method).update(
            {
                PaymentAgent.daily_rewards_balance: amount,
                PaymentAgent.approved_withdraws_day: 0,
            }
        )

    @staticmethod
    @lock_and_release
    async def update_pre_balance(
        amount: float,
        worker_id: int,
        method: str,
        s: Session = None,
    ):
        s.query(PaymentAgent).filter_by(id=worker_id, method=method).update(
            {PaymentAgent.pre_balance: PaymentAgent.pre_balance + amount}
        )

    @staticmethod
    @lock_and_release
    async def update_worker_approved_withdraws(
        worker_id: int,
        method: str,
        amount: float,
        s: Session = None,
    ):
        s.query(PaymentAgent).filter_by(id=worker_id, method=method).update(
            {
                PaymentAgent.approved_withdraws: PaymentAgent.approved_withdraws
                + amount,
                PaymentAgent.approved_withdraws_day: PaymentAgent.approved_withdraws_day
                + amount,
                PaymentAgent.pre_balance: PaymentAgent.pre_balance - amount,
            }
        )

    @classmethod
    @connect_and_close
    def get_workers(
        cls,
        worker_id: int = None,
        method: str = None,
        s: Session = None,
    ):
        if worker_id and method:
            res = s.execute(
                select(cls).where(
                    and_(
                        cls.id == worker_id,
                        cls.method == method,
                    )
                )
            )
            try:
                return res.fetchone().t[0]
            except:
                pass

        elif method:
            res = s.execute(select(cls).where(cls.method == method))
            try:
                return list(map(lambda x: x[0], res.tuples().all()))
            except:
                pass
        elif worker_id:
            return super().get_workers(worker_id=worker_id)
        else:
            return super().get_workers()

