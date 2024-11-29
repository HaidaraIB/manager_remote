from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    PrimaryKeyConstraint,
    select,
    insert,
    and_,
)
from sqlalchemy.orm import Session
from models.DB import Base, lock_and_release, connect_and_close


class RefNumber(Base):
    __tablename__ = "ref_numbers"
    order_serial = Column(Integer, default=-1)
    number = Column(String)
    amount = Column(Float)
    method = Column(String)
    last_name = Column(String, default="", server_default="")
    __table_args__ = (
        PrimaryKeyConstraint("number", "method", name="_number_method_uc"),
    )

    @staticmethod
    @lock_and_release
    async def add_ref_number(
        number: str, amount: float, method: str, last_name: str, s: Session = None
    ):
        s.execute(
            insert(RefNumber).values(
                number=number,
                method=method,
                amount=amount,
                last_name=last_name,
            )
        )

    @staticmethod
    @connect_and_close
    def get_ref_number(number: str, method: str, s: Session = None):
        res = s.execute(
            select(RefNumber).where(
                and_(RefNumber.number == number, RefNumber.method == method)
            )
        )
        try:
            return res.fetchone().t[0]
        except:
            pass
