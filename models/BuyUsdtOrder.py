from sqlalchemy import insert
from sqlalchemy.orm import Session
from models.PaymentOrder import PaymentOrder
from models.DB import lock_and_release


class BuyUsdtdOrder(PaymentOrder):
    __tablename__ = "busdt_orders"

    @staticmethod
    @lock_and_release
    async def add_buy_usdt_order(
        user_id: int,
        group_id: int,
        method: str,
        amount: float,
        bank_account_name: str,
        payment_method_number: int,
        s: Session = None,
    ):
        res = s.execute(
            insert(BuyUsdtdOrder).values(
                user_id=user_id,
                group_id=group_id,
                method=method,
                amount=amount,
                bank_account_name=bank_account_name,
                payment_method_number=payment_method_number,
            )
        )
        return res.lastrowid
