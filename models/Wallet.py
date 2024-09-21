from sqlalchemy import (
    Column,
    String,
    Float,
    select,
    insert,
    delete,
    func,
    and_,
    PrimaryKeyConstraint,
)
from models.DB import Base, lock_and_release, connect_and_close
from sqlalchemy.orm import Session


class Wallet(Base):
    __tablename__ = "wallets"
    number = Column(String)
    method = Column(String)
    balance = Column(Float, default=0)
    limit = Column(Float)
    __table_args__ = (
        PrimaryKeyConstraint("number", "method", name="_number_method_uc"),
    )

    @classmethod
    @lock_and_release
    async def add_wallet(
        cls,
        number: str,
        method: str,
        limit: float,
        s: Session = None,
    ):
        s.execute(
            insert(cls)
            .values(
                number=number,
                method=method,
                limit=limit,
            )
            .prefix_with("OR IGNORE")
        )

    @classmethod
    @lock_and_release
    async def update_balance(
        cls, amout: float, number: str, method: str, s: Session = None
    ):
        s.query(cls).filter_by(number=number, method=method).update(
            {
                cls.balance: cls.balance + amout,
            }
        )

    @classmethod
    @connect_and_close
    def get_wallets(
        cls, method: str, number: str = None, amount: float = None, s: Session = None
    ):
        if amount:
            try:
                res = (
                    s.query(cls)
                    .filter(
                        cls.method == method,
                        cls.limit > cls.balance,
                        cls.limit - cls.balance >= amount,
                    )
                    .order_by(cls.balance.desc())
                    .first()
                )

                return res
            except:
                return

        elif number:
            res = s.execute(
                select(cls).where(
                    and_(
                        cls.method == method,
                        cls.number == number,
                    )
                )
            )
            try:
                return res.fetchone().t[0]
            except:
                pass
        else:
            res = s.execute(select(cls).where(cls.method == method))

            try:
                return list(map(lambda x: x[0], res.tuples().all()))
            except:
                pass

    @classmethod
    @lock_and_release
    async def update_wallets(
        cls,
        method: str,
        option: str,
        value,
        number: str = None,
        s: Session = None,
    ):
        if number:
            s.query(cls).filter_by(method=method, number=number).update(
                {
                    getattr(cls, option): value,
                }
            )
        else:
            s.query(cls).filter_by(method=method).update(
                {
                    getattr(cls, option): value,
                }
            )

    @classmethod
    @lock_and_release
    async def remove_wallet(cls, method: str, number: str, s: Session = None):
        s.execute(
            delete(cls).where(
                and_(
                    cls.method == method,
                    cls.number == number,
                )
            )
        )
