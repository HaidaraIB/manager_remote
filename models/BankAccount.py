from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    TIMESTAMP,
    exc,
    PrimaryKeyConstraint,
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


class BankAccount(Base):
    __tablename__ = "bank_accounts"
    user_id = Column(Integer)
    bank_account_number = Column(String)
    full_name = Column(String)
    bank = Column(String)
    last_modified = Column(TIMESTAMP, server_default=func.current_timestamp())

    __table_args__ = (PrimaryKeyConstraint("user_id", "bank", name="_user_id_bank_uc"),)

    @classmethod
    @lock_and_release
    async def add(
        cls,
        user_id: int,
        bank_account_number: str,
        full_name: str,
        bank: str,
        s: Session = None,
    ):
        res = s.execute(
            insert(cls).values(
                user_id=user_id,
                bank_account_number=bank_account_number,
                full_name=full_name,
                bank=bank,
            )
        )
        return res.lastrowid

    @classmethod
    @connect_and_close
    def get(
        cls,
        user_id: int = None,
        bank: str = None,
        bank_account_number: str = None,
        s: Session = None,
    ):
        if bank:
            res = s.execute(
                select(cls).where(
                    and_(
                        cls.user_id == user_id,
                        cls.bank == bank,
                    )
                )
            )
            try:
                return res.fetchone().t[0]
            except:
                pass
        elif bank_account_number:
            res = s.execute(
                select(cls).where(
                    cls.bank_account_number == bank_account_number,
                )
            )
            try:
                return res.fetchone().t[0]
            except:
                pass
        else:
            res = s.execute(select(cls).where(cls.user_id == user_id))
            try:
                return list(map(lambda x: x[0], res.tuples().all()))
            except:
                pass

    @classmethod
    @lock_and_release
    async def update(cls, user_id: int, bank: str, field, value, s: Session = None):
        s.query(cls).filter_by(user_id=user_id, bank=bank).update(
            {
                getattr(cls, field): value,
                cls.last_modified: datetime.now(),
            }
        )
