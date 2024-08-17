from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import models
import asyncio
from common.common import notify_workers, send_to_photos_archive
from common.stringifies import stringify_deposit_order
from common.constants import *

from user.work_with_us.common import syrian_govs_en_ar


async def send_to_check_deposit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.effective_user.id
    photo = update.message.photo[-1]

    ref_number = context.user_data["point_deposit_ref_num"]
    deposit_wallet = context.bot_data["data"]["طلبات الوكيل_number"]
    amount = context.user_data["point_deposit_amount"]
    target_group = context.bot_data["data"]["deposit_orders_group"]

    serial = await models.DepositOrder.add_deposit_order(
        user_id=user_id,
        group_id=target_group,
        method=SYRCASH,
        deposit_wallet=deposit_wallet,
        amount=amount,
        ref_number=ref_number,
        agent_id=user_id,
    )
    agent = models.TrustedAgent.get_workers(
        user_id=user_id, gov=context.user_data["point_deposit_point"]
    )
    caption = stringify_deposit_order(
        amount=amount,
        serial=serial,
        method=SYRCASH,
        wal=context.bot_data["data"]["طلبات الوكيل_number"],
        ref_num=ref_number,
        workplace_id=agent.team_cash_workplace_id,
    )
    markup = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(
            text="التحقق ☑️", callback_data=f"check_deposit_order_{serial}"
        )
    )
    message = await context.bot.send_photo(
        chat_id=target_group,
        photo=photo,
        caption=caption,
        reply_markup=markup,
    )

    await send_to_photos_archive(
        context,
        photo=photo,
        serial=serial,
        order_type="deposit",
    )

    await models.DepositOrder.add_message_ids(
        serial=serial,
        pending_check_message_id=message.id,
    )

    workers = models.DepositAgent.get_workers(is_point=True)
    asyncio.create_task(
        notify_workers(
            context=context,
            workers=workers,
            text=f"انتباه يوجد طلب تحقق إيداع جديد 🚨",
        )
    )
    workers = models.Checker.get_workers(check_what="deposit", method=SYRCASH)
    asyncio.create_task(
        notify_workers(
            context=context,
            workers=workers,
            text=f"انتباه يوجد طلب تحقق إيداع جديد 🚨",
        )
    )

def govs_pattern(callback_data: str):
    return callback_data in syrian_govs_en_ar