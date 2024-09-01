from sqlalchemy import Column, Float, Boolean, PrimaryKeyConstraint, select, and_
from sqlalchemy.orm import Session
from models.Worker import Worker
from models.DB import lock_and_release, connect_and_close


class DepositAgent(Worker):
    __tablename__ = "deposit_agents"
    approved_deposits = Column(Float, default=0)
    approved_deposits_num = Column(Float, default=0)
    approved_deposits_week = Column(Float, default=0)
    weekly_rewards_balance = Column(Float, default=0)
    is_point = Column(Boolean, default=False)
    __table_args__ = (PrimaryKeyConstraint("id", "is_point", name="_id_is_point_uc"),)

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

    @classmethod
    @connect_and_close
    def get_workers(
        cls,
        worker_id: int = None,
        is_point: bool = None,
        s: Session = None,
    ):
        if worker_id and (is_point is not None):
            res = s.execute(
                select(cls).where(and_(cls.is_point == is_point, cls.id == worker_id))
            )  # get deposit agent
            try:
                return res.fetchone().t[0]
            except:
                pass
        elif worker_id:
            res = s.execute(
                select(cls).where(cls.id == worker_id)
            )  # get deposit agents by id
            try:
                return list(map(lambda x: x[0], res.tuples().all()))
            except:
                pass
        elif is_point is not None:
            res = s.execute(
                select(cls).where(cls.is_point == is_point)
            )  # get all point deposit agents
            try:
                return list(map(lambda x: x[0], res.tuples().all()))
            except:
                pass

        else:
            return super().get_workers()
