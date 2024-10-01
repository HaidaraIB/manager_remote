from telegram import Update, Chat
from telegram.ext import ContextTypes, CommandHandler

from custom_filters import Admin


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        context.bot_data["restart"] = True
        context.application.stop_running()


restart_handler = CommandHandler("restart", restart)
