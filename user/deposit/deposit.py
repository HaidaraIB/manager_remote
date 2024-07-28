from telegram import (
    Update,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from common.common import (
    build_user_keyboard,
    build_methods_keyboard,
    payment_method_pattern,
    build_back_button,
)

from common.decorators import (
    check_if_user_created_account_from_bot_decorator,
    check_if_user_present_decorator,
    check_user_call_on_or_off_decorator,
    check_user_pending_orders_decorator,
)
from common.force_join import check_if_user_member_decorator
from common.back_to_home_page import (
    back_to_user_home_page_handler,
    back_to_user_home_page_button,
)
from start import start_command
from models import Account, PaymentMethod
from user.deposit.common import send_to_check_deposit
from common.constants import *
from user.deposit.common import SEND_MONEY_TEXT

(
    ACCOUNT_DEPOSIT,
    DEPOSIT_AMOUNT,
    DEPOSIT_METHOD,
    SCREENSHOT,
) = range(4)


@check_user_pending_orders_decorator
@check_user_call_on_or_off_decorator
@check_if_user_present_decorator
@check_if_user_member_decorator
@check_if_user_created_account_from_bot_decorator
async def make_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        accounts = Account.get_user_accounts(user_id=update.effective_user.id)
        accounts_keyboard = [
            InlineKeyboardButton(
                text=a.acc_num,
                callback_data=str(a.acc_num),
            )
            for a in accounts
        ]
        keybaord = [
            accounts_keyboard,
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="اختر حساباً من حساباتك المسجلة لدينا - Choose an account",
            reply_markup=InlineKeyboardMarkup(keybaord),
        )
        return ACCOUNT_DEPOSIT


async def account_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        back_buttons = [
            build_back_button("back_to_account_deposit"),
            back_to_user_home_page_button[0],
        ]
        if not update.callback_query.data.startswith("back"):
            context.user_data["account_deposit"] = int(update.callback_query.data)
        await update.callback_query.edit_message_text(
            text="أرسل الملبغ - Send the amount",
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return DEPOSIT_AMOUNT


back_to_account_deposit = make_deposit


async def deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        deposit_methods = build_methods_keyboard()
        deposit_methods.append(build_back_button("back_to_deposit_amount"))
        deposit_methods.append(back_to_user_home_page_button[0])
        if update.message:
            context.user_data["deposit_amount"] = float(update.message.text)
            await update.message.reply_text(
                text="اختر وسيلة الدفع 💳 - Choose payment method 💳",
                reply_markup=InlineKeyboardMarkup(deposit_methods),
            )
        else:
            await update.callback_query.edit_message_text(
                text="اختر وسيلة الدفع 💳 - Choose payment method 💳",
                reply_markup=InlineKeyboardMarkup(deposit_methods),
            )
        return DEPOSIT_METHOD


back_to_deposit_amount = account_deposit


async def deposit_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        data = update.callback_query.data
        method = PaymentMethod.get_payment_method(name=data)
        if method.on_off == 0:
            await update.callback_query.answer(METHOD_IS_OFF_TEXT)
            return
        context.user_data["deposit_method"] = data
        back_buttons = [
            build_back_button("back_to_deposit_method"),
            back_to_user_home_page_button[0],
        ]
        text = SEND_MONEY_TEXT
        if data == "USDT":
            text += "<b>ملاحظة هامة: الشبكة المستخدمه هي TRC20 - Note that the network is TRC20</b>\n"

        await update.callback_query.edit_message_text(
            text=SEND_MONEY_TEXT.format(
                context.bot_data["data"][f"{data}_number"],
                context.bot_data["data"][f"{data}_number"],
            ),
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )
        return SCREENSHOT


back_to_deposit_method = deposit_amount


async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        await send_to_check_deposit(
            context=context,
            user_id=update.effective_user.id,
            screenshot=update.message.photo[-1],
            amount=context.user_data["deposit_amount"],
            acc_number=context.user_data["account_deposit"],
            method=context.user_data["deposit_method"],
            target_group=context.bot_data["data"]["deposit_orders_group"],
        )
        await update.message.reply_text(
            text=THANK_YOU_TEXT,
            reply_markup=build_user_keyboard(),
        )

        return ConversationHandler.END


deposit_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(make_deposit, "^deposit$")],
    states={
        ACCOUNT_DEPOSIT: [CallbackQueryHandler(account_deposit, "^\d+$")],
        DEPOSIT_AMOUNT: [
            MessageHandler(filters=filters.Regex("^\d+.?\d*$"), callback=deposit_amount)
        ],
        DEPOSIT_METHOD: [CallbackQueryHandler(deposit_method, payment_method_pattern)],
        SCREENSHOT: [MessageHandler(filters=filters.PHOTO, callback=get_screenshot)],
    },
    fallbacks=[
        start_command,
        back_to_user_home_page_handler,
        CallbackQueryHandler(back_to_deposit_method, "^back_to_deposit_method$"),
        CallbackQueryHandler(back_to_deposit_amount, "^back_to_deposit_amount$"),
        CallbackQueryHandler(back_to_account_deposit, "^back_to_account_deposit$"),
    ],
    name="deposit_handler",
    persistent=True,
)
