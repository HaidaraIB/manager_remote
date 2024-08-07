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
    stringify_order,
    build_actions_keyboard,
    back_to_choose_action,
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
            build_back_button(f"back_from_edit_order_amount"),
            back_to_admin_home_page_button[0],
        ]

        await update.callback_query.answer(
            text="أرسل قيمة المبلغ الجديدة", show_alert=True
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

        actions_keyboard = build_actions_keyboard(order_type, serial)

        await update.message.delete()
        tg_user = await context.bot.get_chat(chat_id=new_order.user_id)
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=context.user_data["edit_order_msg_id"],
            text=stringify_order(
                serial,
                order_type,
                "@" + tg_user.username if tg_user.username else tg_user.full_name,
            )
            + "\n\nتم تعديل المبلغ ✅",
            reply_markup=InlineKeyboardMarkup(actions_keyboard),
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
            "back_from_edit_order_amount",
        ),
        back_to_admin_home_page_handler,
    ],
)
