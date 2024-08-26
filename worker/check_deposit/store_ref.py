from telegram import (
    Update,
    Chat,
)

from telegram.ext import (
    ContextTypes,
    MessageHandler,
)

from custom_filters import Ref
from models import RefNumber, DepositOrder, PaymentMethod
from worker.check_deposit.check_deposit import send_order_to_process, check_deposit_lock
from common.common import ensure_positive_amount


async def store_ref_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        if (
            not update.effective_chat.id
            == context.bot_data["data"]["ref_numbers_group"]
        ):
            return

        ref_number_info = update.message.text.split("\n")

        amount = float(ref_number_info[2].split(": ")[1])
        is_pos = await ensure_positive_amount(amount=amount, update=update)
        if not is_pos:
            return
        
        number = ref_number_info[0].split(": ")[1]
        method = ref_number_info[1]

        ref_present = RefNumber.get_ref_number(
            number=number,
            method=method,
        )
        if ref_present:
            await update.message.reply_text(
                text="رقم عملية مكرر!",
            )
            return
        await RefNumber.add_ref_number(
            number=number,
            method=method,
            amount=amount,
        )
        ref = RefNumber.get_ref_number(
            number=number,
            method=method,
        )
        await update.message.reply_text(text="تم ✅")

        d_order = DepositOrder.get_one_order(ref_num=number, method=method)

        await check_deposit_lock.acquire()
        if d_order and d_order.state == "pending":
            await send_order_to_process(
                d_order=d_order,
                ref_info=ref,
                context=context,
            )
        check_deposit_lock.release()


def create_invalid_foramt_string():
    methods = PaymentMethod.get_payment_methods()
    res = "تنسيق خاطئ الرجاء نسخ أحد القوالب التالية لتفادي الخطأ:\n\n"
    for method in methods:
        res += "<code>رقم العملية: \n" f"{method.name}\n" "المبلغ: </code>\n\n"
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
