from telegram import Update, Chat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

from common.back_to_home_page import back_to_user_home_page_button


async def accounts_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        keyboard = [
            [
                InlineKeyboardButton(
                    text="إنشاء حساب موثق ™️",
                    callback_data="create account",
                ),
                InlineKeyboardButton(
                    text="حذف حساب 🗑",
                    callback_data="delete account",
                ),
            ],
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="إدارة حساباتك",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


back_to_accounts_settings = accounts_settings

back_to_accounts_settings_handler = CallbackQueryHandler(
    back_to_accounts_settings, "^back_to_accounts_settings$"
)

accounts_settings_handler = CallbackQueryHandler(
    accounts_settings, "^accounts settings$"
)
