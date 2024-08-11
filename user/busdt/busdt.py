from telegram import (
    Update,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from common.common import (
    build_user_keyboard,
    payment_method_pattern,
    build_back_button,
    build_methods_keyboard,
    format_amount,
)

from common.decorators import (
    check_if_user_present_decorator,
    check_user_call_on_or_off_decorator,
    check_user_pending_orders_decorator,
)
from common.force_join import check_if_user_member_decorator
from common.back_to_home_page import (
    back_to_user_home_page_handler,
    back_to_user_home_page_button,
)
from user.withdraw.common import request_aeban_number, request_bank_account_name
from start import start_command
from user.busdt.common import *
from models import PaymentMethod
from common.constants import *

(
    USDT_TO_BUY_AMOUNT,
    YES_NO_BUSDT,
    BUSDT_METHOD,
    CASH_CODE,
    AEBAN_NUMBER,
    BANK_ACCOUNT_NAME_BUSDT,
    BUSDT_CHECK,
) = range(7)


@check_user_pending_orders_decorator
@check_user_call_on_or_off_decorator
@check_if_user_present_decorator
@check_if_user_member_decorator
async def busdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        await update.callback_query.edit_message_text(
            text=BUSDT_AMOUNT_TEXT.format(context.bot_data["data"]["usdt_to_aed"]),
            reply_markup=InlineKeyboardMarkup(back_to_user_home_page_button),
        )
        return USDT_TO_BUY_AMOUNT


async def usdt_to_buy_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_usdt_to_buy_amount"),
            back_to_user_home_page_button[0],
        ]
        if update.message:
            amount = float(update.message.text)

            if amount <= 0:
                await update.message.reply_text(
                    text=SEND_POSITIVE_TEXT,
                    reply_markup=InlineKeyboardMarkup(back_buttons),
                )
                return

            context.user_data["usdt_to_buy_amount"] = amount
        else:
            amount = context.user_data["usdt_to_buy_amount"]

        keyboard = [
            [
                InlineKeyboardButton(text=AGREE_TEXT, callback_data="yes busdt"),
                InlineKeyboardButton(text=DISAGREE_TEXT, callback_data="no busdt"),
            ],
            *back_buttons,
        ]
        if update.message:
            await update.message.reply_text(
                text=DO_YOU_AGREE_TEXT.format(
                    amount,
                    format_amount(amount * context.bot_data["data"]["usdt_to_aed"]),
                ),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            await update.callback_query.edit_message_text(
                text=DO_YOU_AGREE_TEXT.format(
                    amount,
                    format_amount(amount * context.bot_data["data"]["usdt_to_aed"]),
                ),
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        return YES_NO_BUSDT


back_to_usdt_to_buy_amount = busdt


async def yes_no_busdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if update.callback_query.data.startswith("no"):
            await update.callback_query.answer(
                "Canceled - تم الإلغاء",
                show_alert=True,
            )
            await update.callback_query.edit_message_text(
                text=HOME_PAGE_TEXT,
                reply_markup=build_user_keyboard(),
            )
            return ConversationHandler.END
        else:
            busdt_methods = build_methods_keyboard(busdt=True)
            busdt_methods.append(build_back_button("back_to_yes_no_busdt"))
            busdt_methods.append(back_to_user_home_page_button[0])
            await update.callback_query.edit_message_text(
                text=CHOOSE_METHOD_TEXT,
                reply_markup=InlineKeyboardMarkup(busdt_methods),
            )
            return BUSDT_METHOD


back_to_yes_no_busdt = usdt_to_buy_amount


async def busdt_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        data = update.callback_query.data
        if not data.startswith("back"):
            method = PaymentMethod.get_payment_method(name=data)

            if not method.on_off:
                await update.callback_query.answer(METHOD_IS_OFF_TEXT)
                return
            method = data
            context.user_data["payment_method_busdt"] = method
        else:
            method = context.user_data["payment_method_busdt"]


        back_keyboard = [
            build_back_button("back_to_busdt_method"),
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text=SEND_PAYMENT_INFO_TEXT.format(method, method),
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )
        return CASH_CODE


back_to_busdt_method = yes_no_busdt


async def get_cash_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        back_keyboard = [
            build_back_button("back_to_get_cash_code_busdt"),
            back_to_user_home_page_button[0],
        ]
        if update.message:
            context.user_data["payment_method_number_busdt"] = update.message.text
        method = context.user_data["payment_method_busdt"]
        if method in AEBAN_LIST:
            await request_aeban_number(update, back_keyboard)
            return AEBAN_NUMBER

        elif method not in CRYPTO_LIST:
            await request_bank_account_name(update, back_keyboard)
            return BANK_ACCOUNT_NAME_BUSDT

        await update.message.reply_text(
            text=SEND_MONEY_TEXT.format(
                context.bot_data["data"]["USDT_number"],
                context.bot_data["data"]["USDT_number"],
            ),
            reply_markup=InlineKeyboardMarkup(back_keyboard),
        )

        return BUSDT_CHECK


back_to_get_cash_code_busdt = busdt_method


async def get_aeban_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_keyboard = [
            build_back_button("back_to_get_aeban_number_busdt"),
            back_to_user_home_page_button[0],
        ]
        if update.message:
            context.user_data["aeban_number_busdt"] = update.message.text
        await request_bank_account_name(update, back_keyboard)
        return BANK_ACCOUNT_NAME_BUSDT


back_to_get_aeban_number_busdt = get_cash_code


async def get_bank_account_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_keyboard = [
            build_back_button("back_to_get_bank_account_name_busdt"),
            back_to_user_home_page_button[0],
        ]
        if update.message:
            context.user_data["bank_account_name_busdt"] = update.message.text
            await update.message.reply_text(
                text=SEND_MONEY_TEXT.format(
                    context.bot_data["data"]["USDT_number"],
                    context.bot_data["data"]["USDT_number"],
                ),
                reply_markup=InlineKeyboardMarkup(back_keyboard),
            )
        else:
            await update.callback_query.edit_message_text(
                text=SEND_MONEY_TEXT.format(
                    context.bot_data["data"]["USDT_number"],
                    context.bot_data["data"]["USDT_number"],
                ),
                reply_markup=InlineKeyboardMarkup(back_keyboard),
            )

        return BUSDT_CHECK


back_to_get_bank_account_name_busdt = get_cash_code


async def busdt_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        await send_busdt_order_to_check(update, context)

        await update.message.reply_text(
            text=THANK_YOU_TEXT,
            reply_markup=build_user_keyboard(),
        )
        return ConversationHandler.END


busdt_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(busdt, "^busdt$")],
    states={
        USDT_TO_BUY_AMOUNT: [
            MessageHandler(
                filters=filters.Regex("^[1-9]+\.?\d*$"), callback=usdt_to_buy_amount
            )
        ],
        YES_NO_BUSDT: [CallbackQueryHandler(yes_no_busdt, "^yes busdt$|^no busdt$")],
        BUSDT_METHOD: [CallbackQueryHandler(busdt_method, payment_method_pattern)],
        CASH_CODE: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_cash_code,
            )
        ],
        AEBAN_NUMBER: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_aeban_number,
            )
        ],
        BANK_ACCOUNT_NAME_BUSDT: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=get_bank_account_name,
            )
        ],
        BUSDT_CHECK: [
            MessageHandler(
                filters=filters.PHOTO | filters.Document.PDF, callback=busdt_check
            )
        ],
    },
    fallbacks=[
        CallbackQueryHandler(
            back_to_usdt_to_buy_amount, "^back_to_usdt_to_buy_amount$"
        ),
        CallbackQueryHandler(back_to_yes_no_busdt, "^back_to_yes_no_busdt$"),
        CallbackQueryHandler(back_to_busdt_method, "^back_to_busdt_method$"),
        CallbackQueryHandler(
            back_to_get_cash_code_busdt, "^back_to_get_cash_code_busdt$"
        ),
        CallbackQueryHandler(
            back_to_get_aeban_number_busdt, "^back_to_get_aeban_number_busdt$"
        ),
        CallbackQueryHandler(
            back_to_get_bank_account_name_busdt, "^back_to_get_bank_account_name_busdt$"
        ),
        back_to_user_home_page_handler,
        start_command,
    ],
    name="busdt_handler",
    persistent=True,
)
