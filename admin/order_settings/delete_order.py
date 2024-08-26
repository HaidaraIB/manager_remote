from telegram import Update, Chat
from telegram.ext import ContextTypes, CallbackQueryHandler
from custom_filters import Admin
from common.common import parent_to_child_models_mapper
from admin.order_settings.common import refresh_order_settings_message
from PyroClientSingleton import PyroClientSingleton


async def delete_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        data = update.callback_query.data.split("_")
        serial = int(data[-1])
        order_type = data[-3]
        order = parent_to_child_models_mapper[order_type].get_one_order(serial=serial)

        try:
            await PyroClientSingleton().delete_messages(
                chat_id=order.user_id,
                message_ids=order.returned_message_id,
            )
        except:
            try:
                await PyroClientSingleton().delete_messages(
                    chat_id=order.user_id,
                    message_ids=order.processing_message_id,
                )
            except:
                pass

        await parent_to_child_models_mapper[order_type].delete_order(serial=serial)
        await update.callback_query.delete_message()
        await refresh_order_settings_message(
            update=update,
            context=context,
            serial=serial,
            order_type=order_type,
            note="\n\nتم حذف الطلب ✅",
        )


delete_order_handler = CallbackQueryHandler(
    delete_order, "delete_((deposit)|(withdraw)|(busdt))_order"
)
