from sqlalchemy import Column, String, insert, select, desc
from sqlalchemy.orm import Session
from models.DB import connect_and_close, lock_and_release
from models.PaymentOrder import PaymentOrder


class WithdrawOrder(PaymentOrder):
    __tablename__ = "withdraw_orders"
    acc_number = Column(String)
    withdraw_code = Column(String)

    @staticmethod
    @lock_and_release
    async def add_withdraw_order(
        user_id: int,
        group_id: int,
        method: str,
        withdraw_code: str,
        bank_account_name: str,
        payment_method_number: int,
        acc_number: str,
        s: Session = None,
    ):
        res = s.execute(
            insert(WithdrawOrder).values(
                user_id=user_id,
                group_id=group_id,
                method=method,
                withdraw_code=withdraw_code,
                bank_account_name=bank_account_name,
                payment_method_number=payment_method_number,
                acc_number=acc_number,
            )
        )
        return res.lastrowid

    @staticmethod
    @connect_and_close
    def check_withdraw_code(withdraw_code: str, s: Session = None):
        res = s.execute(
            select(WithdrawOrder)
            .where(WithdrawOrder.withdraw_code == withdraw_code)
            .order_by(desc(WithdrawOrder.serial))
        )
        try:
            return res.fetchone().t[0]
        except:
            pass
