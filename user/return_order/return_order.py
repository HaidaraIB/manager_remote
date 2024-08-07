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
    parent_to_child_models_mapper,
    apply_ex_rate,
)

from common.back_to_home_page import back_to_user_home_page_handler

from models import WithdrawOrder

from worker.check_buy_usdt import check_buy_usdt
from worker.check_deposit import check_deposit
from worker.check_withdraw import check_withdraw

(SEND_ATTACHMENTS,) = range(1)


async def handle_returned_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        
        await update.callback_query.edit_message_reply_markup()
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
            "قم بإرفاق المطلوب في السبب.", show_alert=True
        )
        context.user_data["returned_data"] = data
        if update.effective_message.photo:
            context.user_data["effective_photo"] = update.effective_message.photo[-1]
        return SEND_ATTACHMENTS


async def send_attachments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        data: list[str] = context.user_data["returned_data"]
        order_type = data[2]
        order = parent_to_child_models_mapper[order_type].get_one_order(
            serial=int(data[-1])
        )
        reply_markup = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(
                text="قبول الطلب✅",
                callback_data=f"verify_{order_type}_order_{order.serial}",
            )
        )
        if order_type in ["withdraw", "deposit"]:
            amount, _ = apply_ex_rate(
                method=order.method,
                amount=order.amount,
                order_type=order_type,
                context=context,
            )
            await context.bot.send_message(
                chat_id=int(data[-2]),
                text=stringify_returned_order(
                    update.message.text,
                    (
                        check_deposit.stringify_order
                        if order_type == "deposit"
                        else check_withdraw.stringify_order
                    ),
                    amount,
                    order.serial,
                    order.method,
                    (
                        order.acc_number
                        if order_type == "deposit"
                        else order.payment_method_number
                    ),
                    order.ref_number if order_type == "deposit" else None,
                    order.deposit_wallet if order_type == "deposit" else None,
                    
                ),
                reply_markup=reply_markup,
            )
        else:
            await context.bot.send_photo(
                chat_id=int(data[-2]),
                photo=context.user_data["effective_photo"],
                caption=stringify_returned_order(
                    update.message.text,
                    check_buy_usdt.stringify_order,
                    order.amount,
                    order.serial,
                    order.method,
                    order.payment_method_number,
                ),
                reply_markup=reply_markup,
            )
        await parent_to_child_models_mapper[order_type].add_date(
            serial=int(data[-1]),
            date_type="return",
        )
        await update.message.reply_text(
            text="شكراً لك، تمت إعادة طلبك إلى قسم المراجعة، سيصلك رد خلال وقت قصير.",
            reply_markup=build_user_keyboard(),
        )
        return ConversationHandler.END


def stringify_returned_order(attachments: str, stringify_order, *args):
    order = stringify_order(*args)
    order += "<b>" + "\n\nطلب معاد، المرفقات:\n\n" + attachments + "</b>"
    return order


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
    fallbacks=[back_to_user_home_page_handler],
    name="return_order_conversation",
    persistent=True,
)
