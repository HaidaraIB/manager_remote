from telegram.ext import (
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from common.common import payment_method_pattern
from common.back_to_home_page import back_to_user_home_page_handler
from start import start_command
from user.deposit.common import (
    ACCOUNT_DEPOSIT,
    DEPOSIT_AMOUNT,
    DEPOSIT_METHOD,
    SCREENSHOT,
    make_deposit,
    account_deposit,
    deposit_method,
    deposit_amount,
    get_screenshot,
    back_to_account_deposit,
    back_to_deposit_amount,
    back_to_deposit_method,
)


deposit_without_acc_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(make_deposit, "^deposit_without_acc$")],
    states={
        ACCOUNT_DEPOSIT: [
            MessageHandler(
                filters=filters.Regex("^\d+$"),
                callback=account_deposit,
            ),
        ],
        DEPOSIT_AMOUNT: [
            MessageHandler(
                filters=filters.Regex("^\d+.?\d*$"),
                callback=deposit_amount,
            )
        ],
        DEPOSIT_METHOD: [
            CallbackQueryHandler(
                deposit_method,
                payment_method_pattern,
            ),
        ],
        SCREENSHOT: [
            MessageHandler(
                filters=filters.PHOTO | filters.Document.PDF,
                callback=get_screenshot,
            )
        ],
    },
    fallbacks=[
        start_command,
        back_to_user_home_page_handler,
        CallbackQueryHandler(back_to_deposit_method, "^back_to_deposit_method$"),
        CallbackQueryHandler(back_to_deposit_amount, "^back_to_deposit_amount$"),
        CallbackQueryHandler(back_to_account_deposit, "^back_to_account_deposit$"),
    ],
    name="deposit_without_acc_handler",
    persistent=True,
)
