from telegram import Update, Chat, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler

from custom_filters import Admin

from admin.agent_settings.common import build_agent_settings_keyboard


async def agent_settings(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        await update.callback_query.edit_message_text(
            text="اختر ماذا تريد أن تفعل:",
            reply_markup=InlineKeyboardMarkup(build_agent_settings_keyboard()),
        )
        return ConversationHandler.END

back_to_agent_settings = agent_settings

agent_settings_handler = CallbackQueryHandler(agent_settings, "^agent_settings$")
