from sqlalchemy import Column, String, insert
from sqlalchemy.orm import Session
from models.DB import lock_and_release
from models.WorkerWithUs import WorkerWithUs


class TrustedAgent(WorkerWithUs):
    __tablename__ = "trusted_agents"

    team_cash_user_id = Column(String)
    team_cash_password = Column(String)
    team_cash_workplace_id = Column(String)

    @staticmethod
    @lock_and_release
    async def add_trusted_agent(
        user_id: int,
        gov: str,
        neighborhood: str,
        order_serial: int,
        team_cash_user_id: str,
        team_cash_password: str,
        team_cash_workplace_id: str,
        promo_username: str,
        promo_password: str,
        s: Session = None,
    ):
        s.execute(
            insert(TrustedAgent)
            .values(
                user_id=user_id,
                gov=gov,
                neighborhood=neighborhood,
                team_cash_user_id=team_cash_user_id,
                team_cash_password=team_cash_password,
                team_cash_workplace_id=team_cash_workplace_id,
                promo_username=promo_username,
                promo_password=promo_password,
                order_serial=order_serial,
            )
            .prefix_with("OR IGNORE")
        )
