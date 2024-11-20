from telegram import Chat, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from custom_filters import Withdraw, Declined, Sent, DepositAgent
import asyncio
from worker.common import decline_order, decline_order_reason, check_order
from common.constants import *
from common.stringifies import stringify_process_withdraw_order
from common.common import (
    build_worker_keyboard,
    apply_ex_rate,
    notify_workers,
    ensure_positive_amount,
)
from common.functions import end_offer, check_offer
import models


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

        w_order = models.WithdrawOrder.get_one_order(serial=serial)
        
        await models.WithdrawOrder.edit_order_amount(
            new_amount=amount,
            serial=serial,
        )


        method = w_order.method
        target_group = f"{method}_group"

        amount, ex_rate = apply_ex_rate(
            method=method,
            amount=amount,
            order_type="withdraw",
            context=context,
        )

        total_amount = amount
        offer_id = 0
        offer_factor = 0
        if w_order.return_date:
            if w_order.offer:
                offer = models.Offer.get(offer_id=w_order.offer)
                offer_id = offer.id
                offer_factor = offer.factor
                old_amount, _ = apply_ex_rate(
                    method=method,
                    amount=w_order.amount,
                    order_type="withdraw",
                    context=context,
                )
                context.bot_data["withdraw_offer_total_stats"] -= old_amount * (
                    offer.factor / 100
                )
                if amount >= offer.min_amount and amount <= offer.max_amount:
                    gift = amount * (offer.factor / 100)
                    total_amount += gift
                    context.bot_data["withdraw_offer_total_stats"] += gift
                else:
                    await models.WithdrawOrder.detach_offer(serial=serial)
        else:
            offer_factor = check_offer(context, amount, "withdraw")
            if offer_factor:
                offer_id = await models.Offer.add(
                    serial=w_order.serial,
                    factor=offer_factor,
                    offer_name=WITHDRAW_OFFER,
                    min_amount=context.bot_data[f"withdraw_offer_min_amount"],
                    max_amount=context.bot_data[f"withdraw_offer_max_amount"],
                )
                total_amount += amount * (offer_factor / 100)
            if context.bot_data["withdraw_offer_total"] == -1:
                await end_offer(context, "withdraw")

        message = await context.bot.send_message(
            chat_id=context.bot_data["data"][target_group],
            text=stringify_process_withdraw_order(
                amount=total_amount,
                order_amount=amount,
                serial=serial,
                method=method,
                payment_method_number=w_order.payment_method_number,
                offer=offer_factor,
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

        await models.WithdrawOrder.send_order(
            pending_process_message_id=message.id,
            serial=serial,
            group_id=context.bot_data["data"][target_group],
            ex_rate=ex_rate,
            offer=offer_id,
        )
        workers = models.PaymentAgent.get_workers(method=method)

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
