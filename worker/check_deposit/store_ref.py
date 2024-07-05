from telegram import (
    Update,
    Chat,
)

from telegram.ext import (
    ContextTypes,
    MessageHandler,
)

from custom_filters import Ref
from DB import DB


async def store_ref_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        if (
            not update.effective_chat.id
            == context.bot_data["data"]["ref_numbers_group"]
        ):
            return
        ref_number_info = update.message.text.split("\n")
        ref_present = DB.get_ref_number(
            number=ref_number_info[0].split(": ")[1],
            method=ref_number_info[1],
        )
        if ref_present:
            await update.message.reply_text(
                text="رقم عملية مكرر!",
            )
            return
        await DB.add_ref_number(
            number=ref_number_info[0].split(": ")[1],
            method=ref_number_info[1],
            amount=float(ref_number_info[2].split(": ")[1]),
        )
        await update.message.reply_text(text="تم ✅")


def create_invalid_foramt_string():
    methods = DB.get_payment_methods()
    res = "تنسيق خاطئ الرجاء نسخ أحد القوالب التالية لتفادي الخطأ:\n\n"
    for method in methods:
        res += "<code>رقم العملية: \n" f"{method['name']}\n" "المبلغ: </code>\n\n"
    res += "مثال:\n" "رقم العملية: 1\n" "USDT\n" "المبلغ: 100"

    return res


async def invalid_ref_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        if (
            not update.effective_chat.id
            == context.bot_data["data"]["ref_numbers_group"]
            or not update.message
        ):
            return
        await update.message.reply_text(text=create_invalid_foramt_string())


store_ref_number_handler = MessageHandler(filters=Ref(), callback=store_ref_number)
invalid_ref_format_handler = MessageHandler(filters=~Ref(), callback=invalid_ref_format)
