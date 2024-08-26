from telegram import Update, Chat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from common.common import (
    build_user_keyboard,
    apply_ex_rate,
    build_back_button,
    parent_to_child_models_mapper,
)
from common.stringifies import (
    stringify_deposit_order,
    stringify_process_withdraw_order,
    stringify_process_busdt_order,
    stringify_returned_order,
)
import models


SEND_ATTACHMENTS = 0


async def handle_returned_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        data = update.callback_query.data.split("_")
        order_type = data[2]
        order = parent_to_child_models_mapper[order_type].get_one_order(
            serial=int(data[-1])
        )
        if order.state == "deleted":
            await update.message.reply_text(
                text="طلب محذوف ❗️",
            )
            return ConversationHandler.END

        if order_type == "withdraw":
            code_present = models.WithdrawOrder.check_withdraw_code(
                withdraw_code=order.withdraw_code
            )
            if code_present and code_present.state == "approved":
                await update.message.reply_text(
                    text="تمت الموافقة على هذا الطلب بالفعل",
                )
                return ConversationHandler.END

        await update.callback_query.answer(
            "قم بإرفاق المطلوب في السبب.",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                *build_back_button("back_to_handle_returned_order")
            )
        )
        context.user_data["returned_data"] = data
        context.user_data["effective_return_message_id"] = update.effective_message.id
        if update.effective_message.photo:
            context.user_data["effective_photo"] = update.effective_message.photo[-1]
        return SEND_ATTACHMENTS


async def back_to_handle_returned_order(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE:
        data: list[str] = context.user_data["returned_data"]
        serial = int(data[-1])
        worker_id = int(data[-2])
        order_type = data[2]
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="إرفاق المطلوب",
                    callback_data=f"handle_return_{order_type}_{worker_id}_{serial}",
                )
            )
        )
        return ConversationHandler.END


async def send_attachments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        data: list[str] = context.user_data["returned_data"]
        serial = int(data[-1])
        worker_id = int(data[-2])
        order_type = data[2]
        order = parent_to_child_models_mapper[order_type].get_one_order(serial=serial)
        reply_markup = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(
                text="قبول الطلب ✅",
                callback_data=f"verify_{order_type}_order_{order.serial}",
            )
        )
        amount, _ = apply_ex_rate(
            method=order.method,
            amount=order.amount,
            order_type=order_type,
            context=context,
        )
        if order_type in ["withdraw", "busdt"]:
            stringify_returned_payment_order_args = (
                update.message.text,
                (
                    stringify_process_withdraw_order
                    if order_type == "withdraw"
                    else stringify_process_busdt_order
                ),
                amount,
                order.serial,
                order.method,
                order.payment_method_number,
            )
            if order_type == "withdraw":
                message = await context.bot.send_message(
                    chat_id=worker_id,
                    text=stringify_returned_order(
                        *stringify_returned_payment_order_args
                    ),
                    reply_markup=reply_markup,
                )
            else:
                message = await context.bot.send_photo(
                    chat_id=worker_id,
                    photo=context.user_data["effective_photo"],
                    caption=stringify_returned_order(
                        *stringify_returned_payment_order_args
                    ),
                    reply_markup=reply_markup,
                )
        else:
            workplace_id = None
            if not order.acc_number:
                workplace_id = models.TrustedAgent.get_workers(
                    gov=order.gov, user_id=order.agent_id
                ).team_cash_workplace_id
            stringify_returned_deposit_order_args = (
                update.message.text,
                stringify_deposit_order,
                amount,
                order.serial,
                order.method,
                order.acc_number,
                order.deposit_wallet,
                order.ref_number,
                workplace_id,
            )
            if order.ref_number:
                message = await context.bot.send_message(
                    chat_id=worker_id,
                    text=stringify_returned_order(
                        *stringify_returned_deposit_order_args
                    ),
                    reply_markup=reply_markup,
                )
            else:
                message = await context.bot.send_photo(
                    chat_id=worker_id,
                    photo=context.user_data["effective_photo"],
                    caption=stringify_returned_order(
                        *stringify_returned_deposit_order_args
                    ),
                    reply_markup=reply_markup,
                )

        await parent_to_child_models_mapper[order_type].return_order_to_worker(
            serial=serial,
            processing_message_id=message.id,
        )
        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=context.user_data["effective_return_message_id"],
        )
        await update.message.reply_text(
            text="شكراً لك، تمت إعادة طلبك إلى قسم المراجعة، سيصلك رد خلال وقت قصير.",
            reply_markup=build_user_keyboard(),
        )
        return ConversationHandler.END


handle_returned_order_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            handle_returned_order,
            "^handle_return",
        )
    ],
    states={
        SEND_ATTACHMENTS: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=send_attachments,
            )
        ]
    },
    fallbacks=[
        CallbackQueryHandler(
            back_to_handle_returned_order,
            "^back_to_handle_returned_order$",
        ),
    ],
    name="return_order_conversation",
    persistent=True,
)
