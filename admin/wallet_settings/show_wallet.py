from telegram import Update, Chat, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler

from custom_filters import Admin, DepositAgent
from common.back_to_home_page import (
    back_to_admin_home_page_handler,
    back_to_admin_home_page_button,
)
from common.common import payment_method_pattern, build_back_button
from common.stringifies import stringify_wallet
from admin.wallet_settings.common import (
    CHOOSE_METHOD,
    WALLET,
    choose_wallet_settings_option,
    choose_method,
    back_to_choose_method,
    back_to_choose_wallet_settings_option_handler,
)
from start import admin_command, worker_command

import models


async def show_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and (
        Admin().filter(update) or DepositAgent().filter(update)
    ):
        wallet = models.Wallet.get_wallets(
            method=context.user_data["wallet_setting_method"],
            number=update.callback_query.data.split("_")[1],
        )
        back_buttons = [
            build_back_button("back_to_choose_wallet_to_show"),
            back_to_admin_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text=stringify_wallet(wallet),
            reply_markup=InlineKeyboardMarkup(back_buttons),
        )


back_to_choose_wallet_to_show = choose_method

show_wallet_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(choose_wallet_settings_option, "^show_wallet$")],
    states={
        CHOOSE_METHOD: [
            CallbackQueryHandler(
                choose_method,
                payment_method_pattern,
            )
        ],
        WALLET: [
            CallbackQueryHandler(
                show_wallet,
                "^show",
            ),
        ],
    },
    fallbacks=[
        admin_command,
        worker_command,
        back_to_admin_home_page_handler,
        back_to_choose_wallet_settings_option_handler,
        CallbackQueryHandler(back_to_choose_method, "^back_to_choose_method$"),
        CallbackQueryHandler(
            back_to_choose_wallet_to_show, "^back_to_choose_wallet_to_show$"
        ),
    ],
)
