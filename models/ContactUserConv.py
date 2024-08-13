from sqlalchemy import (
    Column,
    Integer,
    String,
    TIMESTAMP,
    PrimaryKeyConstraint,
    Boolean,
    select,
    insert,
    and_,
    func,
)
from models.DB import (
    Base,
    lock_and_release,
    connect_and_close,
)
from sqlalchemy.orm import Session


class ContactUserConv(Base):
    __tablename__ = "contact_user_conv"
    serial = Column(Integer)
    order_type = Column(String)
    admin_id = Column(Integer)
    msg = Column(String)
    count = Column(Integer)
    from_user = Column(Boolean)
    send_date = Column(TIMESTAMP, server_default=func.current_timestamp())
    __table_args__ = (
        PrimaryKeyConstraint(
            "serial", "order_type", "count", name="_serial_order_type_count_uc"
        ),
    )

    @staticmethod
    @lock_and_release
    async def add_response(
        serial: int,
        order_type: str,
        admin_id: int,
        msg: str,
        from_user: bool,
        s: Session = None,
    ):
        res = s.execute(
            select(func.max(ContactUserConv.count)).where(
                ContactUserConv.serial == serial,
                ContactUserConv.order_type == order_type,
            )
        )
        count = res.fetchone().t[0]
        s.execute(
            insert(ContactUserConv).values(
                serial=serial,
                order_type=order_type,
                admin_id=admin_id,
                msg=msg,
                count=count + 1 if count else 1,
                from_user=from_user,
            )
        )

    @staticmethod
    @connect_and_close
    def get_conv(serial: int, order_type: str, s: Session = None):
        res = s.execute(
            select(ContactUserConv)
            .where(
                and_(
                    ContactUserConv.serial == serial,
                    ContactUserConv.order_type == order_type,
                )
            )
            .order_by(ContactUserConv.count)
        )
        try:
            return list(map(lambda x: x[0], res.tuples().fetchall()))
        except:
            pass
