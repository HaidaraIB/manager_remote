from telegram import Update, Chat
from telegram.ext import ContextTypes, CallbackQueryHandler
from custom_filters import Admin
from common.common import parent_to_child_models_mapper
from admin.order_settings.common import refresh_order_settings_message, make_conv_text
import models


async def request_returned_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        data = update.callback_query.data.split("_")
        serial = int(data[-1])
        order_type = data[1]
        conv = models.ReturnedConv.get_conv(order_type=order_type, serial=serial)
        if not conv:
            await update.callback_query.answer(
                text="لا يوجد محادثة إعادة لهذا الطلب",
                show_alert=True,
            )
            return
        conv_text = make_conv_text(conv)

        order = parent_to_child_models_mapper[order_type].get_one_order(serial=serial)
        if conv[-1].from_user:
            chat_id = order.worker_id
            name = "الموظف"
        else:
            chat_id = order.user_id
            name = "المستخدم"
        chat = await context.bot.get_chat(chat_id=chat_id)
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=conv_text + f"\n\nالطلب الآن عند {chat.mention_html(name=name)}",
            disable_web_page_preview=True,
        )
        await update.callback_query.delete_message()
        await refresh_order_settings_message(
            update=update,
            context=context,
            serial=serial,
            order_type=order_type,
            note="\n\nتم إرسال محادثة الإعادة في الأعلى ✅",
        )


request_returned_conv_handler = CallbackQueryHandler(
    request_returned_conv, "^request_((deposit)|(withdraw)|(busdt))_order_returned_conv"
)
