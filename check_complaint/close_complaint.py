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
from common.common import parent_to_child_models_mapper
from custom_filters import Complaint, ResponseToUserComplaint
from check_complaint.respond_to_user import back_from_respond_to_user_complaint
from check_complaint.check_complaint import make_complaint_data

import os


async def close_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:
        data = update.callback_query.data.split("_")
        await update.callback_query.answer(
            "قم بالرد على هذه الرسالة بما تريد إرساله إلى المستخدم إن وجد، إن لم يوجد اضغط تخطي.",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_column(
                [
                    InlineKeyboardButton(
                        text="تخطي⬅️",
                        callback_data=f"skip_close_complaint_{data[-2]}_{data[-1]}",
                    ),
                    InlineKeyboardButton(
                        text="الرجوع عن إغلاق الشكوى🔙",
                        callback_data=f"back_from_close_complaint_{data[-2]}_{data[-1]}",
                    ),
                ]
            )
        )


async def skip_close_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:
        callback_data = update.callback_query.data.split("_")
        op = parent_to_child_models_mapper[callback_data[-2]].get_one_order(
            serial=int(callback_data[-1])
        )

        data = await make_complaint_data(context, callback_data)

        final_text = (
            data["text"]
            + "\n\n"
            + update.effective_message.text_html
            + "\n\n🏁🏁 النسخة النهائية 🏁🏁"
        )
        if data["media"]:
            await context.bot.send_media_group(
                chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
                media=[InputMediaPhoto(media=photo) for photo in data["media"]],
                caption=final_text,
            )
            await context.bot.send_media_group(
                chat_id=op.user_id,
                media=[InputMediaPhoto(media=photo) for photo in data["media"]],
                caption=final_text,
            )
        else:
            await context.bot.send_message(
                chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
                text=final_text,
            )
            await context.bot.send_message(
                chat_id=op.user_id,
                text=final_text,
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

        await parent_to_child_models_mapper[
            callback_data[-2]
        ].set_complaint_took_care_of(
            serial=op.serial,
            took_care_of=1,
        )
        context.bot_data["suspended_workers"].discard(op.worker_id)


async def reply_on_close_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:
        callback_data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data.split("_")

        data = await make_complaint_data(context, callback_data)

        op = parent_to_child_models_mapper[callback_data[-2]].get_one_order(
            serial=int(callback_data[-1])
        )
        final_text = (
            data["text"] + "\n\n" + update.effective_message.reply_to_message.text_html
        )
        if update.message.caption or update.message.text:
            final_text += f"\n\nرد الدعم على الشكوى:\n<b>{update.message.caption if update.message.caption else update.message.text}</b>"
        final_text += "\n\n🏁🏁 النسخة النهائية 🏁🏁"
        if not update.message.photo and not data["media"]:
            await context.bot.send_message(
                chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
                text=final_text,
            )
            await context.bot.send_message(
                chat_id=op.user_id,
                text=final_text,
            )
        else:
            photos = data["media"] if data["media"] else []
            if update.message.photo:
                photos.append(update.message.photo[-1])
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

        await parent_to_child_models_mapper[
            callback_data[-2]
        ].set_complaint_took_care_of(serial=op.serial, took_care_of=1)

        context.bot_data["suspended_workers"].discard(op.worker_id)


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
    & (filters.CAPTION | filters.PHOTO | filters.TEXT),
    callback=reply_on_close_complaint,
)
