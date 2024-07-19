from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    TIMESTAMP,
    func,
)
from database.BaseOrder import (
    BaseOrder,
)


class Order(BaseOrder):
    __abstract__ = True

    serial = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    group_id = Column(Integer)
    checker_id = Column(Integer, default=0)
    worker_id = Column(Integer, default=0)
    state = Column(String, default="pending")
    method = Column(String)
    amount = Column(Float)
    ex_rate = Column(Float)
    acc_number = Column(String)

    reason = Column(String, default="")
    pending_process_message_id = Column(Integer, default=0)
    processing_message_id = Column(Integer, default=0)
    archive_message_ids = Column(String, default="")
    complaint_took_care_of = Column(Integer, default=0)
    working_on_it = Column(Integer, default=0)

    order_date = Column(TIMESTAMP, server_default=func.current_timestamp())
    send_date = Column(TIMESTAMP)
    return_date = Column(TIMESTAMP)
    approve_date = Column(TIMESTAMP)
    decline_date = Column(TIMESTAMP)
