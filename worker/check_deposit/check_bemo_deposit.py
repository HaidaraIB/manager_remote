from telegram import Update, Chat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from common.common import apply_ex_rate, notify_workers, build_worker_keyboard
from worker.common import decline_order, decline_order_reason, check_order
from common.stringifies import stringify_deposit_order
from common.constants import *
from worker.check_deposit.common import build_check_deposit_keyboard
import models
import asyncio
from custom_filters import Declined, DepositAgent, Deposit, DepositAmount


async def check_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.PRIVATE]:
        await check_order(update=update, order_type="deposit")


async def edit_deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.PRIVATE]:
        serial = int(update.callback_query.data.split("_")[-1])

        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بالمبلغ الجديد",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="الرجوع عن تعديل المبلغ 🔙",
                    callback_data=f"back_from_edit_deposit_amount_{serial}",
                )
            )
        )


async def get_new_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.PRIVATE]:
        serial = int(
            update.message.reply_to_message.reply_markup.inline_keyboard[0][
                0
            ].callback_data.split("_")[-1]
        )
        d_order = models.DepositOrder.get_one_order(serial=serial)
        checker = models.Checker.get_workers(
            worker_id=update.effective_user.id,
            method=d_order.method,
            check_what="deposit",
        )
        new_amount = float(update.message.text)
        order_text = stringify_deposit_order(
            amount=new_amount,
            serial=serial,
            method=d_order.method,
            account_number=d_order.acc_number,
            wal=d_order.deposit_wallet,
            ref_num=d_order.ref_number,
        )
        if (
            d_order.amount < new_amount
            and (new_amount - d_order.amount) > checker.pre_balance
        ):
            await update.message.delete()
            await update.message.reply_to_message.edit_text(
                text=order_text + "\n\nليس لديك رصيد كافي ❗️",
                reply_markup=build_check_deposit_keyboard(serial),
            )
            return

        await models.DepositOrder.edit_order_amount(
            new_amount=new_amount, serial=serial
        )

        await update.message.delete()

        await update.message.reply_to_message.edit_text(
            text=order_text + "\n\nتم تعديل المبلغ ✅",
            reply_markup=build_check_deposit_keyboard(serial),
        )


async def send_deposit_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.PRIVATE]:
        serial = int(update.callback_query.data.split("_")[-1])
        d_order = models.DepositOrder.get_one_order(serial=serial)

        amount, ex_rate = apply_ex_rate(
            method=d_order.method,
            amount=d_order.amount,
            order_type="deposit",
            context=context,
        )

        workplace_id = None
        if not d_order.acc_number:
            agent = models.TrustedAgent.get_workers(
                gov=d_order.gov, user_id=d_order.agent_id
            )
            workplace_id = agent.team_cash_workplace_id

        message = await context.bot.send_message(
            chat_id=context.bot_data["data"]["deposit_after_check_group"],
            text=stringify_deposit_order(
                amount=amount,
                serial=d_order.serial,
                method=d_order.method,
                account_number=d_order.acc_number,
                wal=d_order.deposit_wallet,
                ref_num=d_order.ref_number,
                workplace_id=workplace_id,
            ),
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="قبول الطلب ✅", callback_data=f"verify_deposit_order_{serial}"
                )
            ),
        )

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تم إرسال الطلب ✅",
                    callback_data="✅✅✅✅✅✅✅✅✅✅",
                )
            )
        )

        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="تم إرسال الطلب ✅",
            reply_markup=build_worker_keyboard(
                deposit_agent=DepositAgent().filter(update)
            ),
        )

        await models.DepositOrder.send_order(
            pending_process_message_id=message.id,
            serial=serial,
            group_id=(
                context.bot_data["data"]["deposit_after_check_group"]
                if d_order.acc_number
                else context.bot_data["data"]["agents_deposit_after_check_group"]
            ),
            ex_rate=ex_rate,
        )

        await models.Checker.update_pre_balance(
            check_what="deposit",
            method=d_order.method,
            worker_id=update.effective_user.id,
            amount=-amount,
        )

        workers = models.DepositAgent.get_workers(is_point=(workplace_id is not None))
        asyncio.create_task(
            notify_workers(
                context=context,
                workers=workers,
                text=f"انتباه تم استلام إيداع جديد 🚨",
            )
        )


async def decline_deposit_order(update: Update, _: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.PRIVATE]:
        await decline_order(update=update, order_type="deposit")


async def decline_deposit_order_reason(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.PRIVATE]:
        await decline_order_reason(update=update, context=context, order_type="deposit")


back_to_check_deposit = check_deposit


check_deposit_handler = CallbackQueryHandler(
    callback=check_deposit,
    pattern="^check_deposit",
)

edit_deposit_amount_handler = CallbackQueryHandler(
    callback=edit_deposit_amount,
    pattern="^edit_deposit_amount",
)
get_new_amount_handler = MessageHandler(
    filters=filters.REPLY & filters.Regex("^\d+\.?\d*$") & Deposit() & DepositAmount(),
    callback=get_new_amount,
)

send_deposit_order_handler = CallbackQueryHandler(
    callback=send_deposit_order,
    pattern="^send_deposit_order",
)

decline_deposit_order_handler = CallbackQueryHandler(
    callback=decline_deposit_order,
    pattern="^decline_deposit_order",
)
decline_deposit_order_reason_handler = MessageHandler(
    filters=filters.REPLY & filters.TEXT & Deposit() & Declined(),
    callback=decline_deposit_order_reason,
)
back_from_decline_deposit_order_handler = CallbackQueryHandler(
    callback=back_to_check_deposit,
    pattern="^back_from_((decline_deposit_order)|(edit_deposit_amount))",
)
