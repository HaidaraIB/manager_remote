from telegram import Update, Chat, InputMediaPhoto
from telegram.ext import ContextTypes, CallbackQueryHandler

from custom_filters import Admin

from admin.order_settings.common import refresh_order_settings_message
import models


async def request_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE and Admin().filter(update):
        data = update.callback_query.data.split("_")
        serial = int(data[-1])
        order_type = data[-4]
        photos = models.Photo.get(order_serial=serial, order_type=order_type)
        if not photos:
            await update.callback_query.answer(
                text="لا يوجد وثائق لهذا الطلب",
                show_alert=True,
            )
            return
        await context.bot.send_media_group(
            chat_id=update.effective_user.id,
            media=[InputMediaPhoto(media=p) for p in photos],
        )
        await update.callback_query.delete_message()
        await refresh_order_settings_message(
            update=update,
            context=context,
            serial=serial,
            order_type=order_type,
            note="\n\nتم إرسال الوثائق في الأعلى ✅",
        )


request_photos_handler = CallbackQueryHandler(
    request_photos, "^request_((deposit)|(withdraw)|(busdt))_order_photos"
)
