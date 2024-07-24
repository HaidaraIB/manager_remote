from sqlalchemy import (
    Column,
    Integer,
    String,
    TIMESTAMP,
    Text,
    Float,
    func,
    insert,
    select,
)
from sqlalchemy.orm import Session
from models.BaseOrder import BaseOrder
from models.DB import lock_and_release, connect_and_close
import datetime


class TrustedAgentsOrder(BaseOrder):
    __tablename__ = "trusted_agents_orders"

    serial = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    gov = Column(String)
    neighborhood = Column(Text)
    latitude = Column(Text)
    longitude = Column(Text)
    email = Column(Text)
    phone = Column(Text)
    state = Column(String, default="pending")
    reason = Column(Text)

    amount = Column(Float)
    ref_number = Column(Text)
    creation_date = Column(TIMESTAMP, server_default=func.current_timestamp())
    approve_date = Column(TIMESTAMP)
    decline_date = Column(TIMESTAMP)

    @staticmethod
    @lock_and_release
    async def decline_trusted_agent_order(serial: int, reason: str, s: Session = None):
        s.query(TrustedAgentsOrder).filter_by(serial=serial).update(
            {
                TrustedAgentsOrder.decline_date: datetime.datetime.now(),
                TrustedAgentsOrder.state: "decline",
                TrustedAgentsOrder.reason: reason,
            }
        )

    @staticmethod
    @lock_and_release
    async def add_trusted_agent_order(
        user_id: int,
        gov: str,
        neighborhood: str,
        latitude: str,
        longitude: str,
        email: str,
        phone: str,
        amount: float,
        ref_num: str,
        s: Session = None,
    ):
        res = s.execute(
            insert(TrustedAgentsOrder).values(
                user_id=user_id,
                gov=gov,
                neighborhood=neighborhood,
                latitude=latitude,
                longitude=longitude,
                email=email,
                phone=phone,
                amount=amount,
                ref_number=ref_num,
            )
        )
        return res.lastrowid

    @staticmethod
    @lock_and_release
    async def approve_order(order_serial: int, s: Session = None):
        s.query(TrustedAgentsOrder).filter_by(serial=order_serial).update(
            {
                TrustedAgentsOrder.approve_date: datetime.datetime.now(),
                TrustedAgentsOrder.state: "approved",
            }
        )

    @staticmethod
    @connect_and_close
    def get_user_ids(s: Session = None):
        res = s.execute(
            select(TrustedAgentsOrder.user_id)
            .where(
                TrustedAgentsOrder.state == "approved",
            )
            .distinct()
        )
        try:
            return list(map(lambda x: x[0], res.tuples().all()))
        except:
            pass
