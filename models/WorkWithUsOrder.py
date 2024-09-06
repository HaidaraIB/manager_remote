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
    and_,
)
from sqlalchemy.orm import Session
from models.BaseOrder import BaseOrder
from models.DB import lock_and_release, connect_and_close
import datetime


class WorkWithUsOrder(BaseOrder):
    __tablename__ = "work_with_us_orders"

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
    role = Column(Text)

    amount = Column(Float)
    ref_number = Column(Text)
    order_date = Column(TIMESTAMP, server_default=func.current_timestamp())
    approve_date = Column(TIMESTAMP)
    decline_date = Column(TIMESTAMP)
    delete_date = Column(TIMESTAMP)

    @staticmethod
    @lock_and_release
    async def decline_work_with_us_order(serial: int, reason: str, s: Session = None):
        s.query(WorkWithUsOrder).filter_by(serial=serial).update(
            {
                WorkWithUsOrder.decline_date: datetime.datetime.now(),
                WorkWithUsOrder.state: "decline",
                WorkWithUsOrder.reason: reason,
            }
        )

    @staticmethod
    @lock_and_release
    async def add_work_with_us_order(
        user_id: int,
        gov: str,
        neighborhood: str,
        latitude: str,
        longitude: str,
        email: str,
        phone: str,
        amount: float,
        ref_num: str,
        role: str,
        s: Session = None,
    ):
        res = s.execute(
            insert(WorkWithUsOrder).values(
                user_id=user_id,
                gov=gov,
                neighborhood=neighborhood,
                latitude=latitude,
                longitude=longitude,
                email=email,
                phone=phone,
                amount=amount,
                ref_number=ref_num,
                role=role,
            )
        )
        return res.lastrowid

    @staticmethod
    @lock_and_release
    async def approve_order(order_serial: int, s: Session = None):
        s.query(WorkWithUsOrder).filter_by(serial=order_serial).update(
            {
                WorkWithUsOrder.approve_date: datetime.datetime.now(),
                WorkWithUsOrder.state: "approved",
            }
        )

    @staticmethod
    @lock_and_release
    async def delete_order(order_serial: int, s: Session = None):
        s.query(WorkWithUsOrder).filter_by(serial=order_serial).update(
            {
                WorkWithUsOrder.delete_date: datetime.datetime.now(),
                WorkWithUsOrder.state: "deleted",
            }
        )

    @staticmethod
    @connect_and_close
    def get_user_ids(role: str, s: Session = None):
        res = s.execute(
            select(WorkWithUsOrder.user_id)
            .where(
                and_(WorkWithUsOrder.role == role, WorkWithUsOrder.state == "approved"),
            )
            .distinct()
        )
        try:
            return list(map(lambda x: x[0], res.tuples().all()))
        except:
            pass
