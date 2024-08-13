from telegram import (
    Update,
    Chat,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from common.common import (
    parent_to_child_models_mapper,
    build_back_button,
)
from common.back_to_home_page import (
    back_to_admin_home_page_button,
    back_to_admin_home_page_handler,
)
from admin.order_settings.common import (
    back_to_choose_action,
    refresh_order_settings_message,
)

import models

(NEW_AMOUNT,) = range(1)


async def edit_order_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        data = update.callback_query.data.split("_")
        serial = int(data[-1])
        order_type = data[-4]
        context.user_data["edit_order_amount_serial"] = serial
        context.user_data["edit_order_amount_type"] = order_type
        context.user_data["edit_order_msg_id"] = update.effective_message.id
        back_buttons = [
            build_back_button(
                f"back_from_edit_order_amount__{order_type}_order_{serial}"
            ),
            back_to_admin_home_page_button[0],
        ]

        await update.callback_query.answer(
            text="أرسل قيمة المبلغ الجديدة",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(back_buttons)
        )
        return NEW_AMOUNT


async def get_new_amount(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.effective_chat.type == Chat.PRIVATE:

        serial = context.user_data["edit_order_amount_serial"]
        order_type = context.user_data["edit_order_amount_type"]

        order = parent_to_child_models_mapper[order_type].get_one_order(serial=serial)

        new_amount = float(update.message.text)
        old_amount = order.amount

        await parent_to_child_models_mapper[order_type].edit_order_amount(
            serial=serial,
            new_amount=new_amount,
        )

        if order.worker_id:
            updated_amount = new_amount - old_amount
            if order_type in ["withdraw", "busdt"]:
                await models.PaymentAgent.update_worker_approved_withdraws(
                    worker_id=order.worker_id,
                    method=order.method,
                    amount=updated_amount,
                )
            elif order_type == "deposit":
                await models.DepositAgent.update_worker_approved_deposits(
                    worker_id=order.worker_id,
                    amount=updated_amount,
                )

        new_order = parent_to_child_models_mapper[order_type].get_one_order(
            serial=serial
        )
        await update.message.delete()
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=context.user_data["edit_order_msg_id"],
        )
        await refresh_order_settings_message(
            update=update,
            context=context,
            serial=serial,
            order_type=order_type,
            note="\n\nتم تعديل المبلغ ✅",
        )
        return ConversationHandler.END


edit_order_amount_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            edit_order_amount, "^edit_((deposit)|(withdraw)|(busdt))_order_amount"
        )
    ],
    states={
        NEW_AMOUNT: [
            MessageHandler(
                filters=filters.Regex("^\d+\.?\d*$"),
                callback=get_new_amount,
            )
        ]
    },
    fallbacks=[
        CallbackQueryHandler(
            back_to_choose_action,
            "^back_from_edit_order_amount",
        ),
    ],
)
