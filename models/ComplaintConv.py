from sqlalchemy import (
    Column,
    Integer,
    String,
    TIMESTAMP,
    PrimaryKeyConstraint,
    Boolean,
    select,
    insert,
    func,
)
from models.DB import (
    Base,
    lock_and_release,
    connect_and_close,
)
from sqlalchemy.orm import Session


class ComplaintConv(Base):
    __tablename__ = "complaint_conv"
    complaint_id = Column(Integer)
    msg = Column(String)
    count = Column(Integer)
    from_user = Column(Boolean)
    send_date = Column(TIMESTAMP, server_default=func.current_timestamp())
    __table_args__ = (
        PrimaryKeyConstraint("complaint_id", "count", name="_complaint_id_count_uc"),
    )

    @staticmethod
    @lock_and_release
    async def add_response(
        complaint_id: int, msg: str, from_user: bool, s: Session = None
    ):
        res = s.execute(
            select(func.max(ComplaintConv.count)).where(
                ComplaintConv.complaint_id == complaint_id
            )
        )
        count = res.fetchone().t[0]
        s.execute(
            insert(ComplaintConv).values(
                complaint_id=complaint_id,
                msg=msg,
                count=count + 1 if count else 1,
                from_user=from_user,
            )
        )

    @staticmethod
    @connect_and_close
    def get_conv(complaint_id: int, s: Session = None):
        res = s.execute(
            select(ComplaintConv)
            .where(ComplaintConv.complaint_id == complaint_id)
            .order_by(ComplaintConv.count)
        )
        try:
            return list(map(lambda x: x[0], res.tuples().fetchall()))
        except:
            pass
