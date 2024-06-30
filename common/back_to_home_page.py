from telegram import Update, InlineKeyboardButton, Chat, error

from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
)

from common.force_join import check_if_user_member_decorator

from common.common import build_user_keyboard, build_admin_keyboard

from custom_filters.Admin import Admin

back_to_admin_home_page_button = [
    [
        InlineKeyboardButton(
            text="العودة إلى القائمة الرئيسية🔙",
            callback_data="back to admin home page",
        )
    ],
]

back_to_user_home_page_button = [
    [
        InlineKeyboardButton(
            text="العودة إلى القائمة الرئيسية🔙",
            callback_data="back to user home page",
        )
    ],
]


@check_if_user_member_decorator
async def back_to_user_home_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        try:
            await update.callback_query.edit_message_text(
                text="القائمة الرئيسية🔝", reply_markup=build_user_keyboard()
            )
        except error.BadRequest:
            await update.effective_message.delete()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="القائمة الرئيسية🔝",
                reply_markup=build_user_keyboard(),
            )
        return ConversationHandler.END


async def back_to_admin_home_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        try:
            await update.callback_query.edit_message_text(
                text="القائمة الرئيسية🔝", reply_markup=build_admin_keyboard()
            )
        except error.BadRequest:
            await update.effective_message.delete()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="القائمة الرئيسية🔝",
                reply_markup=build_admin_keyboard(),
            )
        return ConversationHandler.END


back_to_user_home_page_handler = CallbackQueryHandler(
    back_to_user_home_page, "^back to user home page$"
)
back_to_admin_home_page_handler = CallbackQueryHandler(
    back_to_admin_home_page, "^back to admin home page$"
)
