from sqlalchemy import Column, Integer, String, TIMESTAMP, exc, select, insert, func
from models.DB import (
    Base,
    lock_and_release,
    connect_and_close,
)
from sqlalchemy.orm import Session


class Account(Base):
    __tablename__ = "accounts"
    acc_num = Column(String, primary_key=True)
    user_id = Column(Integer)
    password = Column(String)
    full_name = Column(String)
    serial = Column(Integer)
    creation_date = Column(TIMESTAMP, server_default=func.current_timestamp())

    @classmethod
    @lock_and_release
    async def connect_account_to_user(
        cls, user_id: int, acc_num: str, s: Session = None
    ):
        s.query(cls).filter_by(acc_num=acc_num).update(
            {
                cls.user_id: user_id,
            }
        )

    @classmethod
    @connect_and_close
    def get_account(cls, acc_num: str = None, new: bool = False, s: Session = None):
        if acc_num:
            res = s.execute(select(cls).where(cls.acc_num == acc_num))
        elif new:
            res = s.execute(select(cls).where(cls.user_id == None))

        try:
            return res.fetchone().t[0]
        except:
            pass

    @classmethod
    @connect_and_close
    def get_user_accounts(cls, user_id: int, s: Session = None):
        res = s.execute(select(cls).where(cls.user_id == user_id))
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
