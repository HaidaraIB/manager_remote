from telegram import Update, Chat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters
from common.common import send_message_to_user
from custom_filters import Account, Declined
import models


def create_invalid_foramt_string():
    res = (
        "تنسيق خاطئ الرجاء الالتزام بالقالب التالي:\n\n"
        "رقم الحساب\n"
        "كلمة المرور\n\n"
        "مثال:\n"
        "12345\n"
        "abcd123"
    )
    return res


async def invalid_account_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        if (
            not update.effective_chat.id
            == context.bot_data["data"]["accounts_orders_group"]
            or not update.message
        ):
            return
        await update.message.reply_text(text=create_invalid_foramt_string())


async def reply_to_create_account_order(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.SUPERGROUP, Chat.GROUP]:

        if (
            not update.effective_chat.id
            == context.bot_data["data"]["accounts_orders_group"]
        ):
            return
        
        account = update.message.text.split("\n")
        res = await models.Account.add_account(
            acc_num=int(account[0]),
            password=account[1],
        )

        if res:
            await update.effective_message.reply_text(
                text="هذا الحساب مسجل لدينا مسبقاً"
            )
            return

        await update.message.reply_text(text="تم ✅")


invalid_account_format_handler = MessageHandler(
    filters=~Account(),
    callback=invalid_account_format,
)
store_account_handler = MessageHandler(
    filters=Account(),
    callback=reply_to_create_account_order,
)
