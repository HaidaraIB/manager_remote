from telegram import Update, Chat
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler

from custom_filters import Admin, DepositAgent
from common.back_to_home_page import back_to_admin_home_page_handler
from common.common import payment_method_pattern
from admin.wallet_settings.common import (
    CHOOSE_METHOD,
    WALLET,
    choose_wallet_settings_option,
    choose_method,
    reply_with_wallets,
    reply_with_payment_methods,
    back_to_choose_method,
    back_to_choose_wallet_settings_option_handler,
)
from start import admin_command, worker_command

import models


async def remove_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and (
        Admin().filter(update) or DepositAgent().filter(update)
    ):
        await models.Wallet.remove_wallet(
            method=context.user_data["wallet_setting_method"],
            number=update.callback_query.data.split("_")[1],
        )
        await update.callback_query.answer(
            text="تمت إزالة المحفظة بنجاح ✅",
            show_alert=True,
        )
        res = await reply_with_wallets(
            context.user_data["wallet_setting_method"], update, context
        )
        if not res:
            await reply_with_payment_methods(update)
            return CHOOSE_METHOD


remove_wallet_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(choose_wallet_settings_option, "^remove_wallet$")
    ],
    states={
        CHOOSE_METHOD: [
            CallbackQueryHandler(
                choose_method,
                payment_method_pattern,
            )
        ],
        WALLET: [
            CallbackQueryHandler(
                remove_wallet,
                "^remove",
            ),
        ],
    },
    fallbacks=[
        admin_command,
        worker_command,
        back_to_admin_home_page_handler,
        back_to_choose_wallet_settings_option_handler,
        CallbackQueryHandler(back_to_choose_method, "^back_to_choose_method$"),
    ],
)
