from telegram import PhotoSize, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from models import DepositOrder, DepositAgent
from worker.check_deposit.check_deposit import check_deposit, stringify_order
from common.common import notify_workers, send_to_photos_archive
import asyncio


async def send_to_check_deposit(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    amount:float,
    screenshot: PhotoSize,
    method: str,
    acc_number: str,
    target_group: int,
    agent_id: int = None,
):
    serial = await DepositOrder.add_deposit_order(
        user_id=user_id,
        method=method,
        acc_number=acc_number,
        agent_id=agent_id if agent_id else 0,
    )

    await send_to_photos_archive(
        context,
        photo=screenshot,
        serial=serial,
        order_type="deposit",
    )

    await context.bot.send_photo(
        chat_id=target_group,
        photo=screenshot,
        caption=stringify_order(
            amount=amount,
            account_number=acc_number,
            method=method,
            serial=serial,
        ),
        reply_markup=InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(
                text="التحقق ☑️", callback_data=f"check_deposit_order_{serial}"
            )
        ),
    )

    workers = DepositAgent.get_workers()
    asyncio.create_task(
        notify_workers(
            context=context,
            workers=workers,
            text=f"انتباه يوجد طلب تحقق إيداع جديد 🚨",
        )
    )
    return True
