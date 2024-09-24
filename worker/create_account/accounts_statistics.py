from telegram import Update, Chat
from telegram.ext import ContextTypes, CommandHandler
import models
from start import set_commands


async def accounts_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.SUPERGROUP, Chat.GROUP]:
        await set_commands(update, context)
        if (
            not update.effective_chat.id
            == context.bot_data["data"]["accounts_orders_group"]
        ):
            return

        free_count, connected_count = models.Account.count_accounts()
        text = (
            "إحصائيات الحسابات:\n\n"
            f"عدد الحسابات الجديدة المستخدمة: {connected_count}\n"
            f"عدد الحسابات الجديدة غير المستخدمة: {free_count}\n"
        )
        await update.message.reply_text(text=text)


accounts_count_hanlder = CommandHandler("count", accounts_count)
