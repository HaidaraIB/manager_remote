from telegram import Update, Chat
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler
import user.accounts_settings.common as common


async def accounts_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        await update.callback_query.edit_message_text(
            text="إدارة حساباتك",
            reply_markup=common.build_accounts_settings_keyboard(),
        )
        return ConversationHandler.END


back_to_accounts_settings = accounts_settings

back_to_accounts_settings_handler = CallbackQueryHandler(
    back_to_accounts_settings, "^back_to_accounts_settings$"
)

accounts_settings_handler = CallbackQueryHandler(
    accounts_settings, "^accounts settings$"
)
