from sqlalchemy import Column, Float, PrimaryKeyConstraint, select, insert
from models.DB import connect_and_close, lock_and_release
from sqlalchemy.orm import Session
from models.BaseUser import BaseUser


class User(BaseUser):
    __tablename__ = "users"
    deposit_balance = Column(Float, default=0)
    gifts_balance = Column(Float, default=0)
    __table_args__ = (PrimaryKeyConstraint("id", name="_id_check_what_uc"),)

    @classmethod
    @lock_and_release
    async def add_new_user(
        cls, user_id: int, username: str, name: str, s: Session = None
    ):
        s.execute(
            insert(cls)
            .values(id=user_id, username=username if username else "", name=name)
            .prefix_with("OR IGNORE")
        )

    @classmethod
    @connect_and_close
    def get_all_users(cls, s: Session = None):
        res = s.execute(select(cls))
        try:
            return list(map(lambda x: x[0], res.tuples().all()))
        except:
            pass

    @classmethod
    @connect_and_close
    def get_user(cls, user_id: int, s: Session = None):
        res = s.execute(select(cls).where(cls.id == user_id))
        try:
            return res.fetchone().t[0]
        except:
            pass

    @classmethod
    @lock_and_release
    async def update_balance(
        cls, user_id: int, amount: float = None, s: Session = None
    ):
        if amount:
            s.query(cls).filter_by(id=user_id).update(
                {cls.deposit_balance: cls.deposit_balance + amount}
            )

    @classmethod
    @lock_and_release
    async def update_gifts_balance(
        cls, user_id: int, amount: int = None, s: Session = None
    ):
        s.query(cls).filter_by(id=user_id).update(
            {cls.gifts_balance: cls.gifts_balance + amount}
        )

    @classmethod
    @lock_and_release
    async def million_gift_user(
        cls, user_id: int, amount: int = None, s: Session = None
    ):
        s.query(cls).filter_by(id=user_id).update(
            {
                cls.gifts_balance: cls.gifts_balance + amount,
                cls.deposit_balance: cls.deposit_balance + 1_000_000,
            }
        )
