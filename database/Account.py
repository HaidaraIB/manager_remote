from sqlalchemy import Column, Integer, String, TIMESTAMP, exc, select, insert, func
from database.DB import (
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

    @staticmethod
    @lock_and_release
    async def connect_account_to_user(user_id: int, acc_num: str, s: Session = None):
        s.query(Account).filter_by(acc_num=acc_num).update({Account.user_id: user_id})

    @staticmethod
    @connect_and_close
    def get_account(acc_num: str, s: Session = None):
        res = s.execute(select(Account).where(Account.acc_num == acc_num))
        try:
            return res.fetchone().t[0]
        except:
            pass

    @staticmethod
    @connect_and_close
    def get_user_accounts(user_id: int, s: Session = None):
        res = s.execute(select(Account).where(Account.user_id == user_id))
        try:
            return list(map(lambda x: x[0], res.tuples().all()))
        except:
            pass

    @staticmethod
    @lock_and_release
    async def add_account(
        acc_num: str,
        user_id: int,
        password: str,
        full_name: str,
        serial: int,
        s: Session = None,
    ):
        try:
            s.execute(
                insert(Account).values(
                    acc_num=acc_num,
                    user_id=user_id,
                    password=password,
                    full_name=full_name,
                    serial=serial,
                )
            )
        except exc.IntegrityError:
            return True
