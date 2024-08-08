from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from common.common import notify_workers
from common.stringifies import stringify_check_withdraw_order
from models import WithdrawOrder, Checker, PaymentAgent
from constants import *
import asyncio


async def send_withdraw_order_to_check(
    context: ContextTypes.DEFAULT_TYPE,
    withdraw_code: str,
    method: str,
    target_group: int,
    user_id: int,
    acc_number: str,
    bank_account_name: str,
    payment_method_number: str,
    w_type: str,
    password:str = None,
    agent_id: int = None,
):

    code_present = WithdrawOrder.check_withdraw_code(withdraw_code=withdraw_code)

    if code_present and code_present.state == "approved":
        return False

    serial = await WithdrawOrder.add_withdraw_order(
        group_id=target_group,
        user_id=user_id,
        method=method,
        acc_number=acc_number,
        withdraw_code=withdraw_code,
        bank_account_name=bank_account_name,
        payment_method_number=payment_method_number,
        agent_id=agent_id,
    )

    method_info = f"<b>Payment info</b>: <code>{payment_method_number}</code>" + (
        f"\nاسم صاحب الحساب: <b>{bank_account_name}</b>"
        if method in [BARAKAH, BARAKAH]
        else ""
    )
    message = await context.bot.send_message(
        chat_id=target_group,
        text=stringify_check_withdraw_order(
            w_type=w_type,
            acc_number=acc_number,
            password=password,
            withdraw_code=withdraw_code,
            method=method,
            serial=serial,
            method_info=method_info,
        ),
        reply_markup=InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(
                text="التحقق ☑️", callback_data=f"check_withdraw_order_{serial}"
            )
        ),
    )

    await WithdrawOrder.add_message_ids(
        serial=serial,
        pending_check_message_id=message.id,
    )

    workers = Checker.get_workers(check_what="withdraw")
    asyncio.create_task(
        notify_workers(
            context=context,
            workers=workers,
            text=f"انتباه يوجد طلب تحقق سحب {method} جديد 🚨",
        )
    )

    workers = PaymentAgent.get_workers(method=method)
    asyncio.create_task(
        notify_workers(
            context=context,
            workers=workers,
            text=f"انتباه يوجد طلب سحب {method} قيد التحقق 🚨",
        )
    )
    return True
