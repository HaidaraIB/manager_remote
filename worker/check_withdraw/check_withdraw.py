from telegram import Chat, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from custom_filters import Withdraw, Declined, Sent, DepositAgent
from models import WithdrawOrder, PaymentAgent
from common.constants import *
import asyncio
from common.stringifies import stringify_process_withdraw_order
from worker.common import decline_order, decline_order_reason, check_order
from common.common import (
    build_worker_keyboard,
    apply_ex_rate,
    notify_workers,
    ensure_positive_amount,
)


async def check_withdraw(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.PRIVATE]:
        await check_order(update=update, order_type="withdraw")


async def send_withdraw_order(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.PRIVATE]:
        serial = int(update.callback_query.data.split("_")[-1])

        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بمبلغ السحب",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="الرجوع عن المبلغ 🔙",
                    callback_data=f"back_from_get_withdraw_order_amount_{serial}",
                )
            )
        )


async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.PRIVATE]:
        amount = float(update.message.text)
        is_pos = await ensure_positive_amount(amount=amount, update=update)
        if not is_pos:
            return
        serial = int(
            update.message.reply_to_message.reply_markup.inline_keyboard[0][
                0
            ].callback_data.split("_")[-1]
        )
        await WithdrawOrder.edit_order_amount(
            new_amount=amount,
            serial=serial,
        )

        w_order = WithdrawOrder.get_one_order(serial=serial)

        method = w_order.method
        target_group = f"{method}_group"

        amount, ex_rate = apply_ex_rate(
            method=method,
            amount=amount,
            order_type="withdraw",
            context=context,
        )

        message = await context.bot.send_message(
            chat_id=context.bot_data["data"][target_group],
            text=stringify_process_withdraw_order(
                amount=amount,
                serial=serial,
                method=method,
                payment_method_number=w_order.payment_method_number,
            ),
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="قبول الطلب ✅",
                    callback_data=f"verify_withdraw_order_{serial}",
                )
            ),
        )

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تم إرسال الطلب✅",
                    callback_data="✅✅✅✅✅✅✅✅✅",
                )
            ),
        )

        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="تم إرسال الطلب✅",
            reply_markup=build_worker_keyboard(
                deposit_agent=DepositAgent().filter(update),
            ),
        )

        await WithdrawOrder.send_order(
            pending_process_message_id=message.id,
            serial=serial,
            group_id=context.bot_data["data"][target_group],
            ex_rate=ex_rate,
        )
        workers = PaymentAgent.get_workers(method=method)

        asyncio.create_task(
            notify_workers(
                context=context,
                workers=workers,
                text=f"انتباه تم استلام سحب {method} جديد 🚨",
            )
        )


async def decline_withdraw_order(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.PRIVATE]:
        await decline_order(update=update, order_type="withdraw")


async def decline_withdraw_order_reason(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.PRIVATE]:
        await decline_order_reason(
            update=update, context=context, order_type="withdraw"
        )


back_to_withdraw_check = check_withdraw


check_withdraw_handler = CallbackQueryHandler(
    callback=check_withdraw,
    pattern="^check_withdraw_order",
)

back_to_withdraw_check_handler = CallbackQueryHandler(
    callback=back_to_withdraw_check,
    pattern="^back_from_((decline_withdraw_order)|(get_withdraw_order_amount))",
)

get_withdraw_order_amount_handler = CallbackQueryHandler(
    callback=send_withdraw_order,
    pattern="^send_withdraw_order",
)
send_withdraw_order_handler = MessageHandler(
    filters=filters.REPLY & filters.Regex("^\d+\.?\d*$") & Withdraw() & Sent(),
    callback=get_amount,
)
decline_withdraw_order_handler = CallbackQueryHandler(
    callback=decline_withdraw_order,
    pattern="^decline_withdraw_order",
)
decline_withdraw_order_reason_handler = MessageHandler(
    filters=filters.REPLY & filters.TEXT & Withdraw() & Declined(),
    callback=decline_withdraw_order_reason,
)
