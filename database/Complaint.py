from sqlalchemy import Column, Integer, String, insert, select, and_
from database.DB import (
    Base,
    lock_and_release,
    connect_and_close,
)
from sqlalchemy.orm import Session


class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_serial = Column(Integer)
    order_type = Column(String)
    reason = Column(String)

    @staticmethod
    @lock_and_release
    async def add_complaint(
        order_serial: int,
        order_type: str,
        reason: str,
        s: Session = None,
    ):
        s.execute(
            insert(Complaint).values(
                order_serial=order_serial,
                order_type=order_type,
                reason=reason,
            )
        )

    @staticmethod
    @connect_and_close
    def get_complaint(
        order_serial: int,
        order_type: str,
        s: Session = None,
    ):
        res = s.execute(
            select(Complaint)
            .where(
                and_(
                    Complaint.order_serial == order_serial,
                    Complaint.order_type == order_type,
                )
            )
            .order_by(Complaint.id)
        )
        try:
            return res.tuples().all()[-1][0]
        except:
            pass
