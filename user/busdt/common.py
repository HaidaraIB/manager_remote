from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import models

from common.stringifies import stringify_check_busdt_order
from common.common import send_to_photos_archive
from common.constants import *


async def send_busdt_order_to_check(update: Update, context: ContextTypes.DEFAULT_TYPE):

    method = context.user_data["payment_method_busdt"]
    payment_method_number = context.user_data["payment_method_number_busdt"]
    method_info = f"<b>Payment info</b>: <code>{payment_method_number}</code>"
    target_group = context.bot_data["data"]["busdt_orders_group"]
    amount = context.user_data["usdt_to_buy_amount"]

    serial = await models.BuyUsdtdOrder.add_busdt_order(
        group_id=target_group,
        user_id=update.effective_user.id,
        method=method,
        amount=amount,
        payment_method_number=payment_method_number,
    )
    message = await context.bot.send_photo(
        chat_id=target_group,
        photo=update.message.photo[-1],
        caption=stringify_check_busdt_order(
            amount=amount,
            method=method,
            serial=serial,
            method_info=method_info,
        ),
        reply_markup=InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(
                text="التحقق ☑️", callback_data=f"check_busdt_order_{serial}"
            )
        ),
    )
    photo = update.message.photo[-1]
    await send_to_photos_archive(
        context=context,
        photo=photo,
        serial=serial,
        order_type="busdt",
    )

    await models.BuyUsdtdOrder.add_message_ids(
        serial=serial,
        pending_check_message_id=message.id,
    )
