from sqlalchemy import select, and_, or_, desc
from models.DB import (
    Base,
    lock_and_release,
    connect_and_close,
)
from models.RefNumber import RefNumber
from sqlalchemy.orm import Session
import datetime


class BaseOrder(Base):
    __abstract__ = True

    @classmethod
    @lock_and_release
    async def change_order_state(
        cls,
        state: str,
        serial: int,
        s: Session = None,
    ):
        s.query(cls).filter_by(serial=serial).update(
            {
                cls.state: state,
            }
        )

    @classmethod
    @lock_and_release
    async def add_order_reason(cls, reason: str, serial: int, s: Session = None):
        s.query(cls).filter_by(serial=serial).update(
            {
                cls.reason: reason,
            }
        )

    @classmethod
    @lock_and_release
    async def set_working_on_it(
        cls,
        worker_id: int,
        checker_id: int,
        state: str,
        serial: int,
        amount: float = None,
        s: Session = None,
    ):
        values = {
            cls.working_on_it: 1,
            cls.worker_id: worker_id,
            cls.state: state,
        }
        if checker_id:
            values[cls.checker_id] = checker_id
        if amount:
            values[cls.pre_balance] = cls.pre_balance - amount
        s.query(cls).filter_by(serial=serial).update(values)

    @classmethod
    @lock_and_release
    async def unset_working_on_it(
        cls,
        serial: int,
        state: str,
        s: Session = None,
    ):
        s.query(cls).filter_by(serial=serial).update(
            {
                cls.working_on_it: 0,
                cls.worker_id: 0,
                cls.state: state,
            }
        )

    @classmethod
    @lock_and_release
    async def set_complaint_took_care_of(
        cls, took_care_of: int, serial: int, s: Session = None
    ):
        s.query(cls).filter_by(serial=serial).update(
            {
                cls.complaint_took_care_of: took_care_of,
            }
        )

    @classmethod
    @connect_and_close
    def get_orders(cls, user_id: int, s: Session = None):
        res = s.execute(select(cls).where(cls.user_id == user_id))
        try:
            return list(map(lambda x: x[0], res.tuples().all()))
        except:
            pass

    @classmethod
    @connect_and_close
    def get_one_order(
        cls,
        serial: int = None,
        ref_num: str = None,
        method: str = None,
        s: Session = None,
    ):
        if serial:
            res = s.execute(select(cls).where(cls.serial == serial))
        elif ref_num and method:
            res = s.execute(
                select(cls)
                .where(
                    and_(
                        cls.ref_number == ref_num,
                        cls.method == method,
                    )
                )
                .order_by(desc(cls.order_date))
            )
        elif ref_num:
            res = s.execute(
                select(cls)
                .where(and_(cls.ref_number == ref_num))
                .order_by(desc(cls.order_date))
            )
        try:
            return res.fetchone().t[0]
        except:
            pass

    @classmethod
    @lock_and_release
    async def add_message_ids(
        cls,
        serial: int,
        checking_message_id: int = 0,
        pending_check_message_id: int = 0,
        processing_message_id: int = 0,
        pending_process_message_id: int = 0,
        s: Session = None,
    ):
        update_dict = {
            cls.processing_message_id: processing_message_id,
            cls.pending_process_message_id: pending_process_message_id,
            cls.pending_check_message_id: pending_check_message_id,
            cls.checking_message_id: checking_message_id,
        }
        # Remove keys with zero values
        update_dict = {k: v for k, v in update_dict.items() if v}
        s.query(cls).filter_by(serial=serial).update(update_dict)

    @classmethod
    @lock_and_release
    async def edit_order_amount(cls, new_amount: float, serial: int, s: Session = None):
        s.query(cls).filter_by(serial=serial).update(
            {
                cls.amount: new_amount,
            }
        )

    @classmethod
    @lock_and_release
    async def decline_order(
        cls,
        reason: str,
        serial: int,
        s: Session = None,
    ):
        s.query(cls).filter_by(serial=serial).update(
            {
                cls.state: "declined",
                cls.working_on_it: 0,
                cls.reason: reason,
                cls.decline_date: datetime.datetime.now(),
            }
        )

    @classmethod
    @lock_and_release
    async def undecline_order(
        cls,
        serial: int,
        s: Session = None,
    ):
        s.query(cls).filter_by(serial=serial).update(
            {
                cls.state: "pending",
                cls.reason: "",
            }
        )

    @classmethod
    @lock_and_release
    async def return_order(
        cls,
        reason: str,
        serial: int,
        s: Session = None,
    ):
        s.query(cls).filter_by(serial=serial).update(
            {
                cls.state: "returned",
                cls.reason: reason,
            }
        )

    @classmethod
    @lock_and_release
    async def add_date(cls, serial: int, date_type: str, s: Session = None):
        s.query(cls).filter_by(serial=serial).update(
            {
                cls.send_date: (
                    datetime.datetime.now() if date_type == "send" else cls.send_date
                ),
                cls.return_date: (
                    datetime.datetime.now()
                    if date_type == "return"
                    else cls.return_date
                ),
                cls.approve_date: (
                    datetime.datetime.now()
                    if date_type == "approve"
                    else cls.approve_date
                ),
                cls.decline_date: (
                    datetime.datetime.now()
                    if date_type == "decline"
                    else cls.decline_date
                ),
            }
        )

    @classmethod
    @lock_and_release
    async def send_order(
        cls,
        pending_process_message_id: int,
        serial: int,
        group_id: int,
        ex_rate: float,
        ref_info: RefNumber = None,
        s: Session = None,
    ):
        if ref_info:
            s.query(RefNumber).filter_by(
                number=ref_info.number,
                method=ref_info.method,
            ).update({RefNumber.order_serial: serial})
        s.query(cls).filter_by(serial=serial).update(
            {
                cls.state: "sent",
                cls.pending_process_message_id: pending_process_message_id,
                cls.working_on_it: 0,
                cls.group_id: group_id,
                cls.ex_rate: ex_rate,
                cls.send_date: datetime.datetime.now(),
                cls.amount: ref_info.amount if ref_info else cls.amount,
            }
        )

    @classmethod
    @lock_and_release
    async def unsend_order(
        cls,
        serial: int,
        group_id: int,
        s: Session = None,
    ):
        s.query(cls).filter_by(serial=serial).update(
            {
                cls.state: "pending",
                cls.pending_process_message_id: 0,
                cls.working_on_it: 0,
                cls.group_id: group_id,
                cls.ex_rate: 0,
                cls.amount: 0,
            }
        )

    @classmethod
    @connect_and_close
    def get_check_order(cls, method: str, s: Session = None):
        res = s.execute(
            select(cls)
            .where(
                and_(
                    cls.working_on_it == 0,
                    cls.state == "pending",
                    cls.method == method,
                )
            )
            .limit(1)
        )
        try:
            return res.fetchone().t[0]
        except:
            pass

    @classmethod
    @connect_and_close
    def check_user_pending_orders(cls, user_id: int, s: Session = None):
        res = s.execute(
            select(cls)
            .where(
                and_(
                    or_(
                        cls.state == "pending",
                        cls.state == "sent",
                        cls.state == "checking",
                        cls.state == "processing",
                    ),
                    cls.user_id == user_id,
                )
            )
            .order_by(desc(cls.order_date))
        )
        try:
            return res.fetchone().t[0]
        except:
            pass

    @classmethod
    @connect_and_close
    def get_all_orders(cls, s: Session = None):
        res = s.execute(select(cls))
        try:
            return list(map(lambda x: x[0], res.tuples().all()))
        except:
            pass
