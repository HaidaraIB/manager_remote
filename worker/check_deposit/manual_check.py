from telegram import Update, Chat
from telegram.ext import ContextTypes, CommandHandler
from custom_filters import Admin
from models import RefNumber, DepositOrder
from worker.check_deposit.check_deposit import send_order_to_process


async def manual_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        serial = context.args[0]
        d_order = DepositOrder.get_one_order(
            serial=serial,
        )
        if not d_order:
            await update.message.reply_text(text="No such order ❗️")
            return

        if d_order and d_order.state != "pending":
            await update.message.reply_text(text="Not pending ❗️")
            return

        ref_present = RefNumber.get_ref_number(
            number=d_order.ref_number,
            method=d_order.method,
        )
        if ref_present:
            await send_order_to_process(
                d_order=d_order,
                ref_info=ref_present,
                context=context,
            )
            await update.message.reply_text(text="Done ✅")
        else:
            await update.message.reply_text(text="Not yet 🤌🏻")


manual_deposit_check_handler = CommandHandler("check_deposit", manual_check)
