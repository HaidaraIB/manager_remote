from telegram import Update, InlineKeyboardButton, Chat, error

from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler

from common.common import (
    build_user_keyboard,
    build_admin_keyboard,
    build_worker_keyboard,
    build_agent_keyboard,
)

from custom_filters import Admin, DepositAgent
from common.force_join import check_if_user_member_decorator
from common.constants import *

back_to_admin_home_page_button = [
    [
        InlineKeyboardButton(
            text=BACK_TO_HOME_PAGE_TEXT,
            callback_data="back_to_admin_home_page",
        )
    ],
]

back_to_user_home_page_button = [
    [
        InlineKeyboardButton(
            text=BACK_TO_HOME_PAGE_TEXT,
            callback_data="back_to_user_home_page",
        )
    ],
]

back_to_agent_home_page_button = [
    [
        InlineKeyboardButton(
            text=BACK_TO_HOME_PAGE_TEXT,
            callback_data="back_to_agent_home_page",
        )
    ],
]

back_to_worker_home_page_button = [
    [
        InlineKeyboardButton(
            text=BACK_TO_HOME_PAGE_TEXT,
            callback_data="back_to_worker_home_page",
        )
    ],
]


async def back_to_agent_home_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        try:
            await update.callback_query.edit_message_text(
                text=HOME_PAGE_TEXT,
                reply_markup=build_agent_keyboard(),
            )
        except error.BadRequest:
            await update.effective_message.delete()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=HOME_PAGE_TEXT,
                reply_markup=build_agent_keyboard(),
            )
        return ConversationHandler.END


@check_if_user_member_decorator
async def back_to_user_home_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        try:
            await update.callback_query.edit_message_text(
                text=HOME_PAGE_TEXT,
                reply_markup=build_user_keyboard(),
            )
        except error.BadRequest:
            await update.effective_message.delete()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=HOME_PAGE_TEXT,
                reply_markup=build_user_keyboard(),
            )
        return ConversationHandler.END


async def back_to_admin_home_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and (
        Admin().filter(update) or DepositAgent().filter(update)
    ):
        try:
            await update.callback_query.edit_message_text(
                text=HOME_PAGE_TEXT,
                reply_markup=(
                    build_admin_keyboard()
                    if Admin().filter(update)
                    else build_worker_keyboard(deposit_agent=True)
                ),
            )
        except error.BadRequest:
            await update.effective_message.delete()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=HOME_PAGE_TEXT,
                reply_markup=(
                    build_admin_keyboard()
                    if Admin().filter(update)
                    else build_worker_keyboard(deposit_agent=True)
                ),
            )
        return ConversationHandler.END


async def back_to_worker_home_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        await update.callback_query.edit_message_text(
            text=HOME_PAGE_TEXT,
            reply_markup=build_worker_keyboard(
                deposit_agent=DepositAgent().filter(update),
            ),
        )
        return ConversationHandler.END


back_to_user_home_page_handler = CallbackQueryHandler(
    back_to_user_home_page, "^back_to_user_home_page$"
)
back_to_worker_home_page_handler = CallbackQueryHandler(
    back_to_worker_home_page, "^back_to_worker_home_page$"
)
back_to_admin_home_page_handler = CallbackQueryHandler(
    back_to_admin_home_page, "^back_to_admin_home_page$"
)
back_to_agent_home_page_handler = CallbackQueryHandler(
    back_to_agent_home_page, "^back_to_agent_home_page$"
)
