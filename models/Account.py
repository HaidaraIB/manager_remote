from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    TIMESTAMP,
    exc,
    select,
    insert,
    delete,
    desc,
    and_,
    func,
)
from models.DB import Base, lock_and_release, connect_and_close
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta


class Account(Base):
    __tablename__ = "accounts"
    acc_num = Column(String, primary_key=True)
    user_id = Column(Integer)
    password = Column(String)
    full_name = Column(String)
    deposit_gift = Column(Float)
    serial = Column(Integer)
    creation_date = Column(TIMESTAMP, server_default=func.current_timestamp())
    connect_to_user_date = Column(TIMESTAMP)

    @classmethod
    @lock_and_release
    async def connect_account_to_user(
        cls, user_id: int, acc_num: str, deposit_gift: float, s: Session = None
    ):
        s.query(cls).filter_by(acc_num=acc_num).update(
            {
                cls.user_id: user_id,
                cls.deposit_gift: deposit_gift,
                cls.connect_to_user_date: datetime.now(),
            }
        )

    @classmethod
    @connect_and_close
    def get_account(cls, acc_num: str = None, new: bool = False, s: Session = None):
        if acc_num:
            res = s.execute(
                select(cls).where(cls.acc_num == acc_num),
            )
        elif new:
            res = s.execute(
                select(cls)
                .where(cls.user_id == None)
                .order_by(desc(cls.creation_date)),
            )

        try:
            return res.fetchone().t[0]
        except:
            pass

    @classmethod
    @connect_and_close
    def get_user_accounts(cls, user_id: int, s: Session = None):
        res = s.execute(
            select(cls)
            .where(cls.user_id == user_id)
            .order_by(desc(cls.connect_to_user_date))
        )
        try:
            return list(map(lambda x: x[0], res.tuples().all()))
        except:
            pass

    @classmethod
    @lock_and_release
    async def add_account(
        cls,
        acc_num: str,
        password: str,
        s: Session = None,
    ):
        try:
            s.execute(
                insert(cls).values(
                    acc_num=acc_num,
                    password=password,
                )
            )
        except exc.IntegrityError:
            return True

    @classmethod
    @lock_and_release
    async def delete_account(cls, acc_num: str, s: Session = None):
        s.execute(delete(cls).where(cls.acc_num == acc_num))

    @classmethod
    @connect_and_close
    def count_accounts(cls, today: date = None, s: Session = None):
        if today:
            today_count_res = s.execute(
                select(func.count())
                .select_from(cls)
                .where(func.date(cls.connect_to_user_date) == today)
            )
            return today_count_res.fetchone().t[0]
        else:
            free_count_res = s.execute(
                select(func.count()).select_from(cls).where(cls.user_id == None)
            )
            connected_count_res = s.execute(
                select(func.count())
                .select_from(cls)
                .where(and_(cls.deposit_gift != None, cls.user_id != None))
            )
            free_count = free_count_res.fetchone().t[0]
            connected_count = connected_count_res.fetchone().t[0]
            return free_count, connected_count
