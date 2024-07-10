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

(CHOOSE_EXCHANGE_RATE_TO_UPDATE, NEW_RATE, BUY_OR_SELL) = range(3)


async def choose_exchange_rate_to_update(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        exchange_rates_keyboard = [
            [
                InlineKeyboardButton(
                    text="شراء USDT", callback_data="buyusdt/usdt_to_syp"
                )
            ],
            [InlineKeyboardButton(text="USDT", callback_data="USDT/usdt_to_syp")],
            [
                InlineKeyboardButton(
                    text="Perfect Money",
                    callback_data="Perfect Money/perfect_money_to_syp",
                )
            ],
            [InlineKeyboardButton(text="Payeer", callback_data="Payeer/payeer_to_syp")],
            back_to_admin_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="اختر النسبة التي تريد تعديلها",
            reply_markup=InlineKeyboardMarkup(exchange_rates_keyboard),
        )
        return CHOOSE_EXCHANGE_RATE_TO_UPDATE


async def get_new_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        data = update.callback_query.data.split("/")
        context.user_data["exchange_rates_data"] = data
        back_buttons = [
            build_back_button("back_to_choose_exchange_rate_to_update"),
            back_to_admin_home_page_button[0],
        ]
        shared_text = (
            f"أرسل السعر الجديد، السعر الحالي:\n\n"
        )
        if data[0] == "buyusdt":
            text = shared_text + (
                f"Buy USDT: <b>{context.bot_data['data']['usdt_to_syp']}</b>"
            )
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return NEW_RATE
        try:
            context.bot_data["data"][f"{data[1]}_sell_rate"]
            context.bot_data["data"][f"{data[1]}_buy_rate"]
        except KeyError:
            context.bot_data["data"][f"{data[1]}_sell_rate"] = 14500
            context.bot_data["data"][f"{data[1]}_buy_rate"] = 14200
        text = shared_text + (
            f"بيع: <b>{context.bot_data['data'][f'{data[1]}_buy_rate']} SYP</b>\n"
            f"شراء: <b>{context.bot_data['data'][f'{data[1]}_sell_rate']} SYP</b>"
        )
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return NEW_RATE


back_to_choose_exchange_rate_to_update = choose_exchange_rate_to_update


async def buy_or_sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        buy_or_sell_keyboard = [
            [
                InlineKeyboardButton(text="بيع", callback_data="buy_rate"),
                InlineKeyboardButton(text="شراء", callback_data="sell_rate"),
            ],
            build_back_button("back_to_get_new_rate"),
            back_to_admin_home_page_button[0],
        ]
        data = context.user_data["exchange_rates_data"]
        if data[0] == "buyusdt":
            context.bot_data["data"][data[1]] = float(update.message.text)
            await update.message.reply_text(
                text=f"تم تعديل السعر بنجاح ✅",
                reply_markup=build_admin_keyboard(),
            )
            return ConversationHandler.END
        elif update.message:
            context.user_data["new_rate"] = float(update.message.text)
            await update.message.reply_text(
                text=f"هذا السعر:",
                reply_markup=InlineKeyboardMarkup(buy_or_sell_keyboard),
            )
        else:
            await update.callback_query.edit_message_text(
                text=f"هذا السعر:",
                reply_markup=InlineKeyboardMarkup(buy_or_sell_keyboard),
            )

        return BUY_OR_SELL


back_to_get_new_rate = buy_or_sell


async def verify_update_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        data = context.user_data["exchange_rates_data"]
        rate = f"{data[1]}_{update.callback_query.data}"
        context.bot_data["data"][rate] = context.user_data["new_rate"]
        await update.callback_query.edit_message_text(
            text=f"تم تعديل السعر بنجاح ✅",
            reply_markup=build_admin_keyboard(),
        )
        return ConversationHandler.END


update_exchange_rates_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(choose_exchange_rate_to_update, "^update exchange rates$")
    ],
    states={
        CHOOSE_EXCHANGE_RATE_TO_UPDATE: [
            CallbackQueryHandler(get_new_rate, lambda x: x.endswith("to_syp"))
        ],
        NEW_RATE: [
            MessageHandler(filters=filters.Regex("^\d+\.?\d*$"), callback=buy_or_sell)
        ],
        BUY_OR_SELL: [
            CallbackQueryHandler(verify_update_rate, "^((buy)|(sell))_rate$")
        ],
    },
    fallbacks=[
        CallbackQueryHandler(
            back_to_choose_exchange_rate_to_update,
            "^back_to_choose_exchange_rate_to_update$",
        ),
        CallbackQueryHandler(
            back_to_get_new_rate,
            "^back_to_get_new_rate$",
        ),
        back_to_admin_home_page_handler,
        start_command,
    ],
)
