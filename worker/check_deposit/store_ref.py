from telegram import Update, Chat
from telegram.ext import ContextTypes, MessageHandler, filters
from custom_filters import Ref
from models import RefNumber, DepositOrder, PaymentMethod, Wallet
from worker.check_deposit.check_deposit import send_order_to_process, check_deposit_lock
from common.common import ensure_positive_amount, format_amount
from common.constants import BANKS


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
        if method in BANKS:
            last_name = ref_number_info[3].split(": ")[1]
        else:
            last_name = ""

        ref_present = RefNumber.get_ref_number(
            number=number,
            method=method,
        )
        if ref_present:
            await update.message.reply_text(
                text="رقم عملية مكرر ❗️",
            )
            return
        await RefNumber.add_ref_number(
            number=number, method=method, amount=amount, last_name=last_name
        )
        ref = RefNumber.get_ref_number(
            number=number,
            method=method,
        )
        await update.message.reply_text(text="تم ✅")

        d_order = DepositOrder.get_one_order(ref_num=number, method=method)

        if not d_order:
            return

        await Wallet.update_balance(
            amout=amount,
            number=d_order.deposit_wallet,
            method=method,
        )

        if d_order.amount and d_order.amount != amount:
            await context.bot.send_message(
                chat_id=d_order.user_id,
                text=(
                    f"تم تصحيح مبلغ إيداع الطلب صاحب رقم العملية: <code>{number}</code> "
                    f"من: <b>{format_amount(d_order.amount)}</b> "
                    f"إلى: <b>{format_amount(amount)}</b>"
                ),
            )
        try:
            await check_deposit_lock.acquire()
            if d_order.state == "pending":
                await send_order_to_process(
                    d_order=d_order,
                    ref_info=ref,
                    context=context,
                )
        finally:
            check_deposit_lock.release()


def create_invalid_foramt_string():
    methods = PaymentMethod.get_payment_methods()
    res = "تنسيق خاطئ الرجاء نسخ أحد القوالب التالية لتفادي الخطأ:\n\n"
    for method in methods:
        if method.name in BANKS:
            res += (
                "<code>رقم العملية: \n"
                f"{method.name}\n"
                "المبلغ: \n"
                "الكنية: </code>\n\n\n"
            )
            continue
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
invalid_ref_format_handler = MessageHandler(
    filters=~Ref() & ~filters.COMMAND, callback=invalid_ref_format
)
