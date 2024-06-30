from telegram import Chat, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from common.common import build_admin_keyboard, build_back_button

from common.back_to_home_page import back_to_admin_home_page_button

from common.back_to_home_page import back_to_admin_home_page_handler

from start import start_command

from custom_filters.Admin import Admin

(
    CHOOSE_EXCHANGE_RATE_TO_UPDATE,
    NEW_RATE,
) = range(2)


async def choose_exchange_rate_to_update(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        exchange_rates_keyboard = [
            [InlineKeyboardButton(text="USDT", callback_data="USDT usdt_to_syp")],
            [
                InlineKeyboardButton(
                    text="Perfect Money",
                    callback_data="Perfect Money perfect_money_to_syp",
                )
            ],
            [InlineKeyboardButton(text="Payeer", callback_data="Payeer payeer_to_syp")],
            back_to_admin_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="اختر النسبة التي تريد تعديلها",
            reply_markup=InlineKeyboardMarkup(exchange_rates_keyboard),
        )
        return CHOOSE_EXCHANGE_RATE_TO_UPDATE


async def get_new_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        data = update.callback_query.data.split(" ")
        context.user_data["exchange_rates_data"] = data
        try:
            context.bot_data["data"][data[1]]
        except KeyError:
            context.bot_data["data"][data[1]] = 14200
        await update.callback_query.edit_message_text(
            text=f"أرسل سعر {data[0]} مقابل الليرة السورية الجديد، السعر الحالي: <b>{context.bot_data['data'][data[1]]} SYP</b>",
            reply_markup=InlineKeyboardMarkup(
                build_back_button("back_to_choose_exchange_rate_to_update")
            ),
        )
        return NEW_RATE


back_to_choose_exchange_rate_to_update = choose_exchange_rate_to_update


async def verify_update_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        data = context.user_data["exchange_rates_data"]
        context.bot_data["data"][data[0]] = float(update.message.text)
        await update.message.reply_text(
            text=f"تم تعديل سعر {data[1]} مقابل الليرة السورية بنجاح✅",
            reply_markup=build_admin_keyboard(),
        )
        return ConversationHandler.END


update_exchange_rates_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(choose_exchange_rate_to_update, "^update exchange rates$")
    ],
    states={
        CHOOSE_EXCHANGE_RATE_TO_UPDATE: [
            MessageHandler(filters=filters.Regex("^.+to_syp$"), callback=get_new_rate)
        ],
        NEW_RATE: [
            MessageHandler(
                filters=filters.Regex("^\d+\.?\d*$"), callback=verify_update_rate
            )
        ],
    },
    fallbacks=[
        CallbackQueryHandler(
            back_to_choose_exchange_rate_to_update,
            "^back_to_choose_exchange_rate_to_update$",
        ),
        back_to_admin_home_page_handler,
        start_command,
    ],
)
