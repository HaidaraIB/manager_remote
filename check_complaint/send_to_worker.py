from telegram import (
    Update,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)

from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
)

from common.common import build_complaint_keyboard, parent_to_child_models_mapper
from check_complaint.check_complaint import make_complaint_main_text
import models


async def send_to_worker_user_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        callback_data = update.callback_query.data.split("_")
        serial = int(callback_data[-1])
        order_type = callback_data[-2]
        op = parent_to_child_models_mapper[order_type].get_one_order(serial=serial)
        complaint = models.Complaint.get_complaint(
            order_serial=serial, order_type=order_type
        )

        media = models.Photo.get(order_serial=serial, order_type=order_type)
        main_text = make_complaint_main_text(
            order_serial=serial, order_type=order_type, reason=complaint.reason
        )

        if media:
            media_group = [InputMediaPhoto(media=photo) for photo in media]
            await context.bot.send_media_group(
                chat_id=op.worker_id if op.worker_id else op.checker_id,
                media=media_group,
                caption=main_text,
            )
        else:
            await context.bot.send_message(
                chat_id=op.worker_id if op.worker_id else op.checker_id,
                text=main_text,
            )

        await context.bot.send_message(
            chat_id=op.worker_id if op.worker_id else op.checker_id,
            text=update.effective_message.text_html,
            reply_markup=build_complaint_keyboard(
                data=callback_data,
                send_to_worker=False,
            ),
        )

        await update.callback_query.answer(
            text="تم إرسال الشكوى إلى الموظف المسؤول✅", show_alert=True
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تم إرسال الشكوى إلى الموظف المسؤول ✅",
                    callback_data="✅✅✅✅✅✅✅✅✅✅✅✅✅",
                )
            ),
        )


send_to_worker_user_complaint_handler = CallbackQueryHandler(
    callback=send_to_worker_user_complaint,
    pattern="^send_to_worker_user_complaint",
)
