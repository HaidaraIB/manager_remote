from telegram import Update, Chat
from telegram.ext import ContextTypes, CallbackQueryHandler

from common.common import parent_to_child_models_mapper

from admin.order_settings.common import refresh_order_settings_message

from PyroClientSingleton import PyroClientSingleton


async def unset_working_on_it(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        data = update.callback_query.data.split("_")
        serial = int(data[-1])
        order_type = data[-3]
        order = parent_to_child_models_mapper[order_type].get_one_order(serial=serial)
        if order.state == "checking" and order_type in ["withdraw", "busdt"]:
            msg_id = order.checking_message_id
            state = "pending"
        elif order.state == "processing":
            msg_id = order.processing_message_id
            state = "sent"
        await parent_to_child_models_mapper[order_type].unset_working_on_it(
            serial=serial,
            state=state,
        )
        try:
            await PyroClientSingleton().delete_messages(
                chat_id=order.checker_id,
                message_ids=msg_id,
            )
        except:
            pass
        await update.callback_query.delete_message()
        await refresh_order_settings_message(
            update=update,
            context=context,
            serial=serial,
            order_type=order_type,
            note="\n\nيمكن للموظف الآن إعادة معالجة الطلب ✅",
        )


unset_working_on_it_handler = CallbackQueryHandler(
    unset_working_on_it, "unset_working_on_it_((deposit)|(withdraw)|(busdt))_order"
)
