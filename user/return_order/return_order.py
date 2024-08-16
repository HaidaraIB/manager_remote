from telegram import (
    Update,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

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

from common.back_to_home_page import back_to_user_home_page_handler

from models import WithdrawOrder

from common.stringifies import (
    stringify_deposit_order,
    stringify_process_withdraw_order,
    stringify_process_busdt_order,
    stringify_returned_order,
)

(SEND_ATTACHMENTS,) = range(1)


async def handle_returned_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        data = update.callback_query.data.split("_")
        order_type = data[2]
        order = parent_to_child_models_mapper[order_type].get_one_order(
            serial=int(data[-1])
        )
        if order_type == "withdraw":
            code_present = WithdrawOrder.check_withdraw_code(
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
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="إرفاق المطلوب",
                    callback_data=f"handle_return_deposit_{data[-2]}_{data[-1]}",
                )
            )
        )
        return ConversationHandler.END


async def send_attachments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        data: list[str] = context.user_data["returned_data"]
        order_type = data[2]
        order = parent_to_child_models_mapper[order_type].get_one_order(
            serial=int(data[-1])
        )
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
        if order_type == "withdraw" or (order_type == "deposit" and order.ref_number):
            await context.bot.send_message(
                chat_id=int(data[-2]),
                text=stringify_returned_order(
                    update.message.text,
                    (
                        stringify_deposit_order
                        if order_type == "deposit"
                        else stringify_process_withdraw_order
                    ),
                    amount,
                    order.serial,
                    order.method,
                    (
                        order.acc_number
                        if order_type == "deposit"
                        else order.payment_method_number
                    ),
                    order.deposit_wallet if order_type == "deposit" else None,
                    order.ref_number if order_type == "deposit" else None,
                ),
                reply_markup=reply_markup,
            )
        else:
            await context.bot.send_photo(
                chat_id=int(data[-2]),
                photo=context.user_data["effective_photo"],
                caption=stringify_returned_order(
                    update.message.text,
                    (
                        stringify_deposit_order
                        if order_type == "deposit"
                        else stringify_process_busdt_order
                    ),
                    amount if order_type == "deposit" else order.amount,
                    order.serial,
                    order.method,
                    (
                        order.acc_number
                        if order_type == "deposit"
                        else order.payment_method_number
                    ),
                    order.deposit_wallet if order_type == "deposit" else None,
                    order.ref_number if order_type == "deposit" else None,
                ),
                reply_markup=reply_markup,
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
