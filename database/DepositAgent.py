from sqlalchemy import (
    Column,
    Float,
    PrimaryKeyConstraint,
)
from sqlalchemy.orm import Session
from database.Worker import Worker
from database.DB import lock_and_release


class DepositAgent(Worker):
    __tablename__ = "deposit_agents"
    approved_deposits = Column(Float, default=0)
    approved_deposits_num = Column(Float, default=0)
    approved_deposits_week = Column(Float, default=0)
    weekly_rewards_balance = Column(Float, default=0)
    __table_args__ = (PrimaryKeyConstraint("id", name="_id_check_what_uc"),)

    @staticmethod
    @lock_and_release
    async def update_worker_approved_deposits(
        worker_id: int, amount: float, s: Session = None
    ):
        s.query(DepositAgent).filter_by(id=worker_id).update(
            {
                DepositAgent.approved_deposits: DepositAgent.approved_deposits + amount,
                DepositAgent.approved_deposits_week: DepositAgent.approved_deposits_week
                + amount,
            }
        )

    @staticmethod
    @lock_and_release
    async def weekly_reward_worker(worker_id: int, amount: float, s: Session = None):
        s.query(DepositAgent).filter_by(id=worker_id).update(
            {
                DepositAgent.weekly_rewards_balance: amount,
                DepositAgent.approved_deposits_week: 0,
            }
        )
