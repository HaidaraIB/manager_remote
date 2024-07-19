from sqlalchemy import (
    Column,
    Float,
    PrimaryKeyConstraint,
    select,
    insert,
)
from database.DB import (
    connect_and_close,
    lock_and_release,
)
from sqlalchemy.orm import Session
from database.BaseUser import BaseUser


class User(BaseUser):
    __tablename__ = "users"
    deposit_balance = Column(Float, default=0)
    gifts_balance = Column(Float, default=0)
    __table_args__ = (PrimaryKeyConstraint("id", name="_id_check_what_uc"),)

    @staticmethod
    @lock_and_release
    async def add_new_user(user_id: int, username: str, name: str, s: Session = None):
        s.execute(
            insert(User)
            .values(id=user_id, username=username if username else "", name=name)
            .prefix_with("OR IGNORE")
        )

    @staticmethod
    @connect_and_close
    def get_all_users(s: Session = None):
        res = s.execute(select(User))
        try:
            return list(map(lambda x: x[0], res.tuples().all()))
        except:
            pass

    @staticmethod
    @connect_and_close
    def get_user(user_id: int, s: Session = None):
        res = s.execute(select(User).where(User.id == user_id))
        try:
            return res.fetchone().t[0]
        except:
            pass

    @staticmethod
    @lock_and_release
    async def update_balance(user_id: int, amount: float = None, s: Session = None):
        if amount:
            s.query(User).filter_by(id=user_id).update(
                {User.deposit_balance: User.deposit_balance + amount}
            )

    @staticmethod
    @lock_and_release
    async def update_gifts_balance(user_id: int, amount: int = None, s: Session = None):
        s.query(User).filter_by(id=user_id).update(
            {User.gifts_balance: User.gifts_balance + amount}
        )

    @staticmethod
    @lock_and_release
    async def million_gift_user(user_id: int, amount: int = None, s: Session = None):
        s.query(User).filter_by(id=user_id).update(
            {
                User.gifts_balance: User.gifts_balance + amount,
                User.deposit_balance: User.deposit_balance + 1_000_000,
            }
        )
