from telegram import (
    Chat,
    Update,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    CommandHandler,
)
from common.back_to_home_page import (
    back_to_admin_home_page_button,
    back_to_admin_home_page_handler,
)
import models
from datetime import datetime, timedelta
from common.common import build_admin_keyboard, request_buttons, format_amount
from start import admin_command, start_command
from custom_filters import Admin
from admin.admin_calls.common import build_turn_user_calls_on_or_off_keyboard
from common.constants import *
from PyroClientSingleton import PyroClientSingleton
import os
import random
from pyrogram.errors.exceptions.bad_request_400 import PeerIdInvalid
from telegram.error import BadRequest

USER_CALL_TO_TURN_ON_OR_OFF = 0


async def find_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if update.effective_message.users_shared:
            await update.message.reply_text(
                text=f"🆔: <code>{update.effective_message.users_shared.users[0].user_id}</code>",
            )
        else:
            await update.message.reply_text(
                text=f"🆔: <code>{update.effective_message.chat_shared.chat_id}</code>",
            )


async def hide_ids_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if (
            not context.user_data.get("request_keyboard_hidden", None)
            or not context.user_data["request_keyboard_hidden"]
        ):
            context.user_data["request_keyboard_hidden"] = True
            await update.callback_query.delete_message()
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="تم الإخفاء ✅",
                reply_markup=ReplyKeyboardRemove(),
            )
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=HOME_PAGE_TEXT,
                reply_markup=build_admin_keyboard(),
            )
        else:
            context.user_data["request_keyboard_hidden"] = False

            await update.callback_query.delete_message()
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="تم الإظهار ✅",
                reply_markup=ReplyKeyboardMarkup(request_buttons, resize_keyboard=True),
            )
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=HOME_PAGE_TEXT,
                reply_markup=build_admin_keyboard(),
            )


async def turn_user_calls_on_or_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        if not update.callback_query.data == "turn user calls on or off":
            data = update.callback_query.data.replace("on_off ", "")
            if context.bot_data["user_calls"].get(data, True):
                context.bot_data["user_calls"][data] = False
                await update.callback_query.answer(
                    text="تم إيقاف الزر 🔴",
                    show_alert=True,
                )
            else:
                context.bot_data["user_calls"][data] = True
                await update.callback_query.answer(
                    text="تم تشغيل الزر 🟢",
                    show_alert=True,
                )

        keyboard = build_turn_user_calls_on_or_off_keyboard(context=context)
        keyboard.append(back_to_admin_home_page_button[0])
        await update.callback_query.edit_message_text(
            text="اختر الزر🔘",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return USER_CALL_TO_TURN_ON_OR_OFF


async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        try:
            res = await PyroClientSingleton().ban_chat_member(
                chat_id=int(os.getenv("CHANNEL_ID")),
                user_id=int(context.args[0]),
            )
            if res:
                await update.message.reply_text(text="تم ✅")
            else:
                await update.message.reply_text(text="حصل خطأ ما ❗️")
        except ValueError:
            await update.message.reply_text(
                text="تأكد من أن الآيدي بعد الأمر /ban عبارة عن أرقام فقط ❗️"
            )
        except PeerIdInvalid as p:
            await update.message.reply_text(text="آيدي المستخدم غير صحيح ❗️")


ban_command = CommandHandler("ban", ban)


async def send_lucky_offer_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        order_type_dict = {
            models.WithdrawOrder: "السحب",
            models.DepositOrder: "الإيداع",
        }
        team_names = ["مدريد", "برشلونة", "ميلان", "ليفربول", "باريس"]

        offer_entries = models.Offer.get(
            offer_name=LUCKY_HOUR_OFFER, factor=context.args[0]
        )
        offer_orders: list[models.DepositOrder | models.WithdrawOrder] = []
        for entry in offer_entries:
            order = models.WithdrawOrder.get_one_order(serial=entry.order_serial)
            if not order:
                order = models.DepositOrder.get_one_order(serial=entry.order_serial)
            offer_orders.append(order)

        start_time = (
            (
                datetime.fromisoformat(str(offer_orders[0].order_date))
                + timedelta(hours=3)
            )
            .time()
            .strftime(r"%I:%M %p")
        )
        end_time = (
            (
                datetime.fromisoformat(str(offer_orders[0].order_date))
                + timedelta(hours=4)
            )
            .time()
            .strftime(r"%I:%M %p")
        )
        offer_text = (
            '"خليك بساعة الحظ، الحظ بده رضاك\n'
            'ما تروح وتسيبها، يمكن تربح معاك"\n\n'
            f"<b>ساعة {random.choice(team_names)} {format_amount(offer_entries[0].factor)}%</b> 🔥\n\n"
            f"لطلبات {order_type_dict[type(offer_orders[0])]}\n"
            f"من ال: <b>{start_time}</b>\n"
            f"حتى ال: <b>{end_time}</b>\n\n"
            "الرابحون:\n\n"
        )

        for order in offer_orders:
            order: models.DepositOrder | models.WithdrawOrder = order
            try:
                user = await context.bot.get_chat(chat_id=order.user_id)
                name = (
                    "@" + user.username if user.username else f"<b>{user.full_name}</b>"
                )
            except BadRequest:
                user = models.User.get_user(user_id=order.user_id)
                name = "@" + user.username if user.username else f"<b>{user.name}</b>"
            offer_text += (
                f"الاسم:\n{name}\n" f"رقم الحساب: <code>{order.acc_number}</code>\n\n"
            )

        offer_text += (
            "<b>ملاحظة: نظراً للعدد الكبير تم الاكتفاء بذكر أسماء أبرز المستفيدين</b>"
        )
        await context.bot.send_message(
            chat_id=int(os.getenv("CHANNEL_ID")),
            text=offer_text,
            message_thread_id=int(os.getenv("LUCKY_HOUR_TOPIC_ID")),
        )


send_lucky_offer_text_command = CommandHandler(["slot"], send_lucky_offer_text)


turn_user_calls_on_or_off_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            turn_user_calls_on_or_off,
            "^turn user calls on or off$",
        )
    ],
    states={
        USER_CALL_TO_TURN_ON_OR_OFF: [
            CallbackQueryHandler(
                turn_user_calls_on_or_off,
                "^on_off",
            )
        ]
    },
    fallbacks=[
        back_to_admin_home_page_handler,
        admin_command,
        start_command,
    ],
)


hide_ids_keyboard_handler = CallbackQueryHandler(
    callback=hide_ids_keyboard, pattern="^hide ids keyboard$"
)

find_id_handler = MessageHandler(
    filters=filters.StatusUpdate.USER_SHARED | filters.StatusUpdate.CHAT_SHARED,
    callback=find_id,
)
