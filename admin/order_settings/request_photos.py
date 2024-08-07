from telegram import (
    Update,
    Chat,
    InputMediaPhoto,
    InlineKeyboardMarkup,
)

from telegram.ext import ContextTypes, CallbackQueryHandler

from common.common import parent_to_child_models_mapper
from admin.order_settings.common import stringify_order, build_actions_keyboard
import models


async def request_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
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
        order = parent_to_child_models_mapper[order_type].get_one_order(serial=serial)
        tg_user = await context.bot.get_chat(chat_id=order.user_id)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=stringify_order(
                serial,
                order_type,
                "@" + tg_user.username if tg_user.username else tg_user.full_name,
            )
            + "\n\nتم إرسال الوثائق في الأعلى ✅",
            reply_markup=InlineKeyboardMarkup(
                build_actions_keyboard(order_type, serial)
            ),
        )


request_photos_handler = CallbackQueryHandler(
    request_photos, "^request_((deposit)|(withdraw)|(busdt))_order_photos"
)
