from sqlalchemy import (
    Column,
    Integer,
    String,
    TIMESTAMP,
    PrimaryKeyConstraint,
    Boolean,
    select,
    and_,
    func,
)
from models.DB import Base, connect_and_close
from sqlalchemy.orm import Session


class Conv(Base):
    __abstract__ = True
    serial = Column(Integer)
    order_type = Column(String)
    msg = Column(String)
    count = Column(Integer)
    from_user = Column(Boolean)
    send_date = Column(TIMESTAMP, server_default=func.current_timestamp())

    @classmethod
    @connect_and_close
    def get_conv(
        cls,
        serial: int,
        order_type: str,
        s: Session = None,
    ):
        res = s.execute(
            select(cls)
            .where(
                and_(
                    cls.serial == serial,
                    cls.order_type == order_type,
                )
            )
            .order_by(cls.count)
        )
        try:
            return list(map(lambda x: x[0], res.tuples().fetchall()))
        except:
            pass
