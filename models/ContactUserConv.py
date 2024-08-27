from sqlalchemy import Column, Integer, PrimaryKeyConstraint, select, insert, func
from models.DB import lock_and_release
from sqlalchemy.orm import Session
from models.Conv import Conv


class ContactUserConv(Conv):
    __tablename__ = "contact_user_conv"
    admin_id = Column(Integer)
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
