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
    MessageHandler,
    filters,
)
from common.common import parent_to_child_models_mapper, send_to_photos_archive, send_message_to_user
from custom_filters import Complaint, ResponseToUserComplaint
from check_complaint.respond_to_user import back_from_respond_to_user_complaint
from check_complaint.check_complaint import make_complaint_main_text, make_conv_text
from common.constants import EXT_COMPLAINT_LINE

import models
import os


async def close_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:
        data: list[str] = update.callback_query.data.split("_")
        order_type = data[-2]
        await update.callback_query.answer(
            "قم بالرد على هذه الرسالة بما تريد إرساله إلى المستخدم إن وجد، إن لم يوجد اضغط تخطي.",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_column(
                [
                    InlineKeyboardButton(
                        text="تخطي⬅️",
                        callback_data=f"skip_close_complaint_{order_type}_{data[-1]}",
                    ),
                    InlineKeyboardButton(
                        text="الرجوع عن إغلاق الشكوى🔙",
                        callback_data=f"back_from_close_complaint_{order_type}_{data[-1]}",
                    ),
                ]
            )
        )


async def skip_close_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:
        callback_data = update.callback_query.data.split("_")
        serial = int(callback_data[-1])
        order_type = callback_data[-2]
        op = parent_to_child_models_mapper[order_type].get_one_order(serial=serial)

        complaint = models.Complaint.get_complaint(
            order_serial=serial, order_type=order_type
        )
        photos = models.Photo.get(order_serial=serial, order_type=order_type)

        final_text = (
            make_complaint_main_text(
                order_serial=serial, order_type=order_type, reason=complaint.reason
            )
            + make_conv_text(complaint_id=complaint.id)
            + "\n\n🏁🏁 النسخة النهائية 🏁🏁"
        )
        if photos:
            media = [InputMediaPhoto(media=photo) for photo in photos]
            await context.bot.send_media_group(
                chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
                media=media,
                caption=final_text,
            )
            await context.bot.send_media_group(
                chat_id=op.user_id,
                media=media,
                caption=final_text,
            )
        else:
            await context.bot.send_message(
                chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
                text=final_text,
            )
            await send_message_to_user(
                update=update,
                context=context,
                user_id=op.user_id,
                msg=final_text,
            )

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.id,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تم إغلاق الشكوى✅",
                    callback_data="✅✅✅✅✅✅✅✅✅✅✅✅✅",
                )
            ),
        )

        await parent_to_child_models_mapper[order_type].set_complaint_took_care_of(
            serial=op.serial,
            took_care_of=1,
        )


async def reply_on_close_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:
        callback_data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data.split("_")
        order_type = callback_data[-2]
        serial = int(callback_data[-1])

        op = parent_to_child_models_mapper[order_type].get_one_order(serial=serial)
        complaint = models.Complaint.get_complaint(
            order_serial=serial, order_type=order_type
        )
        media = models.Photo.get(order_serial=serial, order_type=order_type)

        if update.message.caption or update.message.text:
            msg = (
                update.message.caption
                if update.message.caption
                else update.message.text
            )
            await models.ComplaintConv.add_response(
                complaint_id=complaint.id,
                msg=msg,
                from_user=False,
            )

        final_text = (
            make_complaint_main_text(
                order_serial=serial, order_type=order_type, reason=complaint.reason
            )
            + make_conv_text(complaint_id=complaint.id)
            + "\n\n🏁🏁 النسخة النهائية 🏁🏁"
        )

        if not update.message.photo and not media:
            await context.bot.send_message(
                chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
                text=final_text,
            )
            await send_message_to_user(
                update=update,
                context=context,
                user_id=op.user_id,
                msg=final_text,
            )
        else:
            photos = media if media else []
            if update.message.photo:
                photos.append(update.message.photo[-1])
                await send_to_photos_archive(
                    context=context,
                    photo=update.message.photo[-1],
                    order_type=order_type,
                    serial=serial,
                )
            media = [InputMediaPhoto(media=photo) for photo in photos]
            await context.bot.send_media_group(
                chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
                media=media,
                caption=final_text,
            )
            await context.bot.send_media_group(
                chat_id=op.user_id,
                media=media,
                caption=final_text,
            )

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تم إغلاق الشكوى✅",
                    callback_data="✅✅✅✅✅✅✅✅✅✅✅✅✅",
                )
            ),
        )

        await parent_to_child_models_mapper[order_type].set_complaint_took_care_of(
            serial=op.serial, took_care_of=1
        )



back_from_close_complaint = back_from_respond_to_user_complaint


back_from_close_complaint_handler = CallbackQueryHandler(
    callback=back_from_close_complaint,
    pattern="^back_from_close_complaint",
)


close_complaint_handler = CallbackQueryHandler(
    callback=close_complaint,
    pattern="^close_complaint",
)


skip_close_complaint_handler = CallbackQueryHandler(
    callback=skip_close_complaint,
    pattern="^skip_close_complaint",
)


reply_on_close_complaint_handler = MessageHandler(
    filters=filters.REPLY
    & Complaint()
    & ResponseToUserComplaint(name="close complaint")
    & (filters.CAPTION | filters.PHOTO | (filters.TEXT & ~filters.COMMAND)),
    callback=reply_on_close_complaint,
)
