from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    Chat,
)
from telegram.ext import ContextTypes, ConversationHandler
from models import DepositOrder, DepositAgent, Checker
from common.common import (
    notify_workers,
    build_user_keyboard,
    build_back_button,
    send_to_photos_archive,
)
from common.stringifies import stringify_deposit_order
from common.constants import *
from common.back_to_home_page import back_to_user_home_page_button
import asyncio

DEPOSIT_AMOUNT, SCREENSHOT = range(3, 5)


async def bemo_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_deposit_method"),
            back_to_user_home_page_button[0],
        ]
        if not update.callback_query.data.startswith("back"):
            context.user_data["deposit_method"] = update.callback_query.data

        await update.callback_query.edit_message_text(
            text="أدخل المبلغ",
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return DEPOSIT_AMOUNT


async def get_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_deposit_amount"),
            back_to_user_home_page_button[0],
        ]
        method = context.user_data["deposit_method"]
        text = (
            f"قم بإرسال المبلغ المراد إيداعه إلى:\n\n"
            f"<code>{context.bot_data['data'][f'{method}_number']}</code>\n\n"
            f"ثم أرسل لقطة شاشة لعملية الدفع إلى البوت لنقوم بتوثيقها.\n\n"
        )
        if update.message:
            context.user_data["deposit_amount"] = float(update.message.text)
            await update.message.reply_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        else:
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
        return SCREENSHOT


back_to_deposit_amount = bemo_deposit


async def send_to_check_deposit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.effective_user.id
    photo = update.message.photo[-1]

    amount = context.user_data["deposit_amount"]
    acc_number = context.user_data["account_deposit"]
    method = context.user_data["deposit_method"]
    target_group = context.bot_data["data"]["deposit_orders_group"]

    serial = await DepositOrder.add_deposit_order(
        user_id=user_id,
        group_id=target_group,
        method=method,
        acc_number=acc_number,
        deposit_wallet=context.bot_data["data"][f"{method}_number"],
        amount=amount,
    )

    caption = stringify_deposit_order(
        amount=amount,
        serial=serial,
        method=method,
        account_number=acc_number,
        wal=context.bot_data["data"][f"{method}_number"],
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

    await DepositOrder.add_message_ids(
        serial=serial,
        pending_check_message_id=message.id,
    )

    workers = DepositAgent.get_workers()
    asyncio.create_task(
        notify_workers(
            context=context,
            workers=workers,
            text=f"انتباه يوجد طلب تحقق إيداع جديد 🚨",
        )
    )
    workers = Checker.get_workers(check_what="deposit", method=method)
    asyncio.create_task(
        notify_workers(
            context=context,
            workers=workers,
            text=f"انتباه يوجد طلب تحقق إيداع جديد 🚨",
        )
    )


async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        await send_to_check_deposit(update, context)

        await update.message.reply_text(
            text="شكراً لك، تم إرسال طلبك إلى قسم المراجعة، سيصلك رد خلال وقت قصير.",
            reply_markup=build_user_keyboard(),
        )

        return ConversationHandler.END
