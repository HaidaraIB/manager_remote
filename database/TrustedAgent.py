from sqlalchemy import (
    Column,
    Integer,
    String,
    PrimaryKeyConstraint,
    select,
    insert,
    and_,
)
from sqlalchemy.orm import Session
from database.DB import Base, connect_and_close, lock_and_release
from database.TrustedAgentsOrder import TrustedAgentsOrder
import datetime


class TrustedAgent(Base):
    __tablename__ = "trusted_agents"

    user_id = Column(Integer, primary_key=True)
    gov = Column(String)
    order_serial = Column(Integer)
    team_cash_user_id = Column(String)
    team_cash_password = Column(String)
    team_cash_workplace_id = Column(String)
    promo_username = Column(String)
    promo_password = Column(String)
    __table_args__ = (PrimaryKeyConstraint("user_id", "gov", name="_user_id_gov_uc"),)

    @staticmethod
    @connect_and_close
    def get_trusted_agents(gov: str, user_id: int = None, s: Session = None):
        try:
            if user_id:
                res = s.execute(
                    select(TrustedAgent).where(
                        and_(TrustedAgent.gov == gov, TrustedAgent.user_id == user_id)
                    )
                )
                return res.fetchone().t[0]
            else:
                res = s.execute(select(TrustedAgent).where(TrustedAgent.gov == gov))
                return list(map(lambda x: x[0], res.tuples().all()))
        except:
            pass

    @staticmethod
    @lock_and_release
    async def add_trusted_agent(
        user_id: int,
        gov: str,
        order_serial: int,
        team_cash_user_id: str,
        team_cash_password: str,
        team_cash_workplace_id: str,
        promo_username: str,
        promo_password: str,
        s: Session = None,
    ):
        s.execute(
            insert(TrustedAgent).values(
                user_id=user_id,
                gov=gov,
                team_cash_user_id=team_cash_user_id,
                team_cash_password=team_cash_password,
                team_cash_workplace_id=team_cash_workplace_id,
                promo_username=promo_username,
                promo_password=promo_password,
                order_serial=order_serial,
            )
        )
        s.query(TrustedAgentsOrder).filter_by(serial=order_serial).update(
            {
                TrustedAgentsOrder.approve_date: datetime.datetime.now(),
                TrustedAgentsOrder.state: "approved",
            }
        )
