import sqlalchemy as sa
from sqlalchemy.orm import Session
from models.DB import Base, connect_and_close, lock_and_release


class Referral(Base):
    __tablename__ = "referrals"

    referred_user_id = sa.Column(sa.Integer, primary_key=True)
    referrer_id = sa.Column(sa.Integer)
    created_at = sa.Column(sa.DateTime, default=sa.func.now())

    @classmethod
    @lock_and_release
    async def add(cls, referrer_id: int, referred_user_id: int, s: Session = None):
        s.execute(
            sa.insert(cls).values(
                usereferrer_idr_id=referrer_id,
                referred_user_id=referred_user_id,
            )
        )

    @classmethod
    @connect_and_close
    def get_by(
        cls,
        referrer_id: int = None,
        referred_user_id: int = None,
        s: Session = None,
    ):
        if referrer_id:
            res = s.execute(
                sa.select(cls).where(
                    cls.referrer_id == referrer_id,
                )
            )
            try:
                return list(map(lambda x: x[0], res.tuples().fetchall()))
            except:
                pass
        elif referred_user_id:
            res = s.execute(
                sa.select(cls).where(
                    cls.referred_user_id == referred_user_id,
                )
            )
            try:
                return res.fetchone().t[0]
            except:
                pass
