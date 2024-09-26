from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from models import DepositAgent, DepositOrder
from common.stringifies import stringify_deposit_order
from common.common import notify_workers
import asyncio


async def send_deposit_without_check(
    context: ContextTypes.DEFAULT_TYPE,
    acc_number: int,
    user_id: int,
    amount: float,
    method: str,
):
    target_group = context.bot_data["data"]["deposit_orders_group"]
    serial = await DepositOrder.add_deposit_order(
        user_id=user_id,
        group_id=target_group,
        method=method,
        amount=amount,
        acc_number=acc_number,
    )
    order_text = stringify_deposit_order(
        amount=amount,
        serial=serial,
        method=method,
        account_number=acc_number,
    )

    message = await context.bot.send_message(
        chat_id=context.bot_data["data"]["deposit_after_check_group"],
        text=order_text,
        reply_markup=InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(
                text="قبول الطلب ✅",
                callback_data=f"verify_deposit_order_{serial}",
            )
        ),
    )

    await DepositOrder.send_order(
        pending_process_message_id=message.id,
        serial=serial,
        group_id=context.bot_data["data"]["deposit_after_check_group"],
        ex_rate=0,
    )
    workers = DepositAgent.get_workers(is_point=False)
    asyncio.create_task(
        notify_workers(
            context=context,
            workers=workers,
            text=f"انتباه تم استلام {method} جديد 🚨",
        )
    )
    return amount
