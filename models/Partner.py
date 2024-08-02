from sqlalchemy import (
    insert,
)
from sqlalchemy.orm import Session
from models.DB import lock_and_release
from models.WorkerWithUs import WorkerWithUs

class Partner(WorkerWithUs):
    __tablename__ = "partners"

    @staticmethod
    @lock_and_release
    async def add_partner(
        user_id: int,
        gov: str,
        neighborhood: str,
        order_serial: int,
        promo_username: str,
        promo_password: str,
        s: Session = None,
    ):
        s.execute(
            insert(Partner)
            .values(
                user_id=user_id,
                gov=gov,
                neighborhood=neighborhood,
                promo_username=promo_username,
                promo_password=promo_password,
                order_serial=order_serial,
            )
            .prefix_with("OR IGNORE")
        )
