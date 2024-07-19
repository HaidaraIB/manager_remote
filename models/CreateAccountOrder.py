from sqlalchemy import (
    Column,
    Integer,
    String,
    TIMESTAMP,
    insert,
    func,
)
from sqlalchemy.orm import Session
from models.BaseOrder import BaseOrder
from models.DB import lock_and_release


class CreateAccountOrder(BaseOrder):
    __tablename__ = "create_account_orders"
    serial = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    full_name = Column(String)
    national_number = Column(String)
    state = Column(String, default="pending")
    order_date = Column(TIMESTAMP, server_default=func.current_timestamp())

    @staticmethod
    @lock_and_release
    async def add_create_account_order(
        user_id: int,
        full_name: str,
        nat_num: int,
        s: Session = None,
    ):
        res = s.execute(
            insert(CreateAccountOrder).values(
                user_id=user_id,
                full_name=full_name,
                national_number=nat_num,
            )
        )
        return res.lastrowid
