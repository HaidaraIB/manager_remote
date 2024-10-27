from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from common.common import notify_workers
from common.stringifies import stringify_check_withdraw_order
from models import WithdrawOrder, Checker, PaymentAgent
from common.constants import *
import asyncio


def build_withdraw_settings_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
                text="إنشاء طلب سحب 📝",
                callback_data="withdraw",
            ),
            InlineKeyboardButton(
                text="ادارة طلبات السحب المعلقة ⏳",
                callback_data="manage_pending_withdraws",
            ),
        ]
    ]
    return keyboard


def make_payment_method_info(payment_method_number):
    return f"<b>Payment info</b>: <code>{payment_method_number}</code>"


async def send_withdraw_order_to_check(
    context: ContextTypes.DEFAULT_TYPE,
    is_player_withdraw: bool,
    withdraw_code: str,
    user_id: int,
    agent_id: int = 0,
    password: str = "",
):
    if is_player_withdraw:
        acc_number = context.user_data["withdraw_account"]
        method = context.user_data["payment_method"]
        payment_method_number = context.user_data["payment_method_number"]
        target_group = context.bot_data["data"]["withdraw_orders_group"]
        gov = context.user_data[f"{context.user_data['agent_option']}_point"]
    else:
        acc_number = context.user_data["withdraw_account"]
        method = context.user_data["payment_method"]
        payment_method_number = context.user_data["payment_method_number"]
        target_group = context.bot_data["data"]["withdraw_orders_group"]
        gov = ""

    code_present = WithdrawOrder.check_withdraw_code(withdraw_code=withdraw_code)

    if code_present and code_present.state == "approved":
        return False

    serial = await WithdrawOrder.add_withdraw_order(
        group_id=target_group,
        user_id=user_id,
        method=method,
        acc_number=acc_number,
        withdraw_code=withdraw_code,
        payment_method_number=payment_method_number,
        agent_id=agent_id,
        gov=gov,
    )

    message = await context.bot.send_message(
        chat_id=target_group,
        text=stringify_check_withdraw_order(
            acc_number=acc_number,
            password=password,
            withdraw_code=withdraw_code,
            method=method,
            serial=serial,
            method_info=make_payment_method_info(
                payment_method_number=payment_method_number
            ),
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

    workers = Checker.get_workers(check_what="withdraw", method=method)
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
    return serial
