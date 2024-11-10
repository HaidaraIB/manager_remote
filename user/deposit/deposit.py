from telegram import Update, Chat
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from common.constants import *
from common.common import build_user_keyboard, payment_method_pattern
from common.back_to_home_page import back_to_user_home_page_handler
from start import start_command
from user.deposit.common import (
    ACCOUNT_DEPOSIT,
    DEPOSIT_METHOD,
    DEPOSIT_AMOUNT,
    REF_NUM,
    make_deposit,
    account_deposit,
    choose_deposit_method,
    get_deposit_amount,
    send_to_check_deposit,
    back_to_account_deposit,
    back_to_choose_deposit_method,
    back_to_get_deposit_amount,
)


async def get_ref_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        res = await send_to_check_deposit(update=update, context=context)
        if not res:
            await update.message.reply_text(
                text="رقم عملية مكرر ❗️",
            )
            return

        await update.message.reply_text(
            text="شكراً لك، سيتم التحقق من العملية وإضافة المبلغ المودع خلال وقت قصير.",
            reply_markup=build_user_keyboard(),
        )

        return ConversationHandler.END


deposit_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            make_deposit,
            "^deposit$",
        ),
    ],
    states={
        ACCOUNT_DEPOSIT: [
            CallbackQueryHandler(
                account_deposit,
                "^\d+$",
            ),
        ],
        DEPOSIT_METHOD: [
            CallbackQueryHandler(
                choose_deposit_method,
                payment_method_pattern,
            ),
        ],
        REF_NUM: [
            MessageHandler(
                filters=filters.Regex("^[0-9]+$"),
                callback=get_ref_num,
            ),
        ],
        DEPOSIT_AMOUNT: [
            MessageHandler(
                filters=filters.Regex("^\d+\.?\d*$"),
                callback=get_deposit_amount,
            )
        ],
    },
    fallbacks=[
        start_command,
        back_to_user_home_page_handler,
        CallbackQueryHandler(
            back_to_get_deposit_amount, "^back_to_get_deposit_amount$"
        ),
        CallbackQueryHandler(
            back_to_choose_deposit_method, "^back_to_choose_deposit_method$"
        ),
        CallbackQueryHandler(
            back_to_account_deposit, "^back_to_account_number_deposit$"
        ),
    ],
    name="deposit_handler",
    persistent=True,
)
