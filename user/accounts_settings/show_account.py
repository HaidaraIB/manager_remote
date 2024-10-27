from telegram import Update, Chat, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler
from user.accounts_settings.common import reply_with_user_accounts
from common.stringifies import stringify_account
from common.common import build_accounts_keyboard, build_back_button
from common.back_to_home_page import (
    back_to_user_home_page_button,
    back_to_user_home_page_handler,
)
from common.decorators import (
    check_if_user_present_decorator,
    check_if_user_created_account_from_bot_decorator,
)
from common.force_join import check_if_user_member_decorator
from user.accounts_settings.accounts_settings import back_to_accounts_settings_handler
from start import start_command

import models

ACCOUNT = 0


@check_if_user_present_decorator
@check_if_user_member_decorator
@check_if_user_created_account_from_bot_decorator
async def show_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        await reply_with_user_accounts(
            update=update,
            context=context,
            back_data="back_to_accounts_settings",
        )
        return ACCOUNT


async def choose_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if not update.callback_query.data.startswith("back"):
            acc_num = update.callback_query.data
            context.user_data["acc_num_to_show"] = acc_num
        else:
            acc_num = context.user_data["acc_num_to_show"]

        acc = models.Account.get_account(acc_num=acc_num)
        accounts = build_accounts_keyboard(user_id=update.effective_user.id)
        keybaord = [
            accounts,
            build_back_button("back_to_accounts_settings"),
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text=stringify_account(account=acc),
            reply_markup=InlineKeyboardMarkup(keybaord),
        )


show_account_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            show_account,
            "^show_account$",
        )
    ],
    states={
        ACCOUNT: [
            CallbackQueryHandler(
                choose_account,
                "^\d+$",
            ),
        ]
    },
    fallbacks=[
        start_command,
        back_to_user_home_page_handler,
        back_to_accounts_settings_handler,
    ],
    name="show_account_conversation",
    persistent=True,
)
