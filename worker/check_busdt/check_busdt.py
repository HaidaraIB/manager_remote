from telegram import Chat, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from models import BuyUsdtdOrder, PaymentAgent
from custom_filters import BuyUSDT, Declined, DepositAgent
from worker.common import decline_order, decline_order_reason, check_order
from common.common import build_worker_keyboard, notify_workers
from common.stringifies import stringify_process_busdt_order
import asyncio


async def check_busdt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:

        await check_order(update=update, order_type="busdt")


async def send_busdt_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:
        serial = int(update.callback_query.data.split("_")[-1])
        b_order = BuyUsdtdOrder.get_one_order(serial=serial)
        method = b_order.method

        target_group = f"{method}_group"

        amount = b_order.amount

        message = await context.bot.send_photo(
            chat_id=context.bot_data["data"][target_group],
            photo=update.effective_message.photo[-1],
            caption=stringify_process_busdt_order(
                amount=amount * context.bot_data["data"]["usdt_to_syp"],
                serial=serial,
                method=method,
                payment_method_number=b_order.payment_method_number,
            ),
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="قبول الطلب ✅", callback_data=f"verify_busdt_order_{serial}"
                )
            ),
        )

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تم إرسال الطلب✅",
                    callback_data="✅✅✅✅✅✅✅✅✅✅",
                )
            )
        )

        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="تم إرسال الطلب✅",
            reply_markup=build_worker_keyboard(
                deposit_agent=DepositAgent().filter(update)
            ),
        )

        await BuyUsdtdOrder.send_order(
            pending_process_message_id=message.id,
            serial=serial,
            group_id=context.bot_data["data"][target_group],
            ex_rate=context.bot_data["data"]["usdt_to_syp"],
        )
        workers = PaymentAgent.get_workers(method=method)

        asyncio.create_task(
            notify_workers(
                context=context,
                workers=workers,
                text=f"انتباه تم استلام دفع {method} جديد 🚨",
            )
        )


async def decline_busdt_order(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:
        await decline_order(update=update, order_type="busdt")


async def decline_busdt_order_reason(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:
        await decline_order_reason(update=update, context=context, order_type="busdt")


async def back_to_busdt_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [
        Chat.PRIVATE,
    ]:
        await check_order(update=update, order_type="busdt")


check_busdt_handler = CallbackQueryHandler(
    callback=check_busdt,
    pattern="^check_busdt",
)

send_busdt_order_handler = CallbackQueryHandler(
    callback=send_busdt_order,
    pattern="^send_busdt_order",
)

decline_busdt_order_handler = CallbackQueryHandler(
    callback=decline_busdt_order,
    pattern="^decline_busdt_order",
)
decline_busdt_order_reason_handler = MessageHandler(
    filters=filters.REPLY & filters.TEXT & BuyUSDT() & Declined(),
    callback=decline_busdt_order_reason,
)
back_from_decline_busdt_order_handler = CallbackQueryHandler(
    callback=back_to_busdt_check,
    pattern="^back_from_decline_busdt_order",
)
