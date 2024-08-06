from telegram import (
    Update,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from common.common import (
    build_complaint_keyboard,
    send_to_media_archive,
    parent_to_child_models_mapper,
)
from models import Complaint, ComplaintConv, Photo
from custom_filters import UserRespondToComplaint
from check_complaint.check_complaint import make_complaint_main_text, make_conv_text
from common.constants import EXT_COMPLAINT_LINE

(CORRECT_RETURNED_COMPLAINT,) = range(1)


async def reply_to_returned_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE:
        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بما تريد إرساله، يمكنك إرسال صورة أو نص أو الاثنين معاً.",
            show_alert=True,
        )

        data = update.callback_query.data.split("_")

        order_type = data[-2]
        from_worker = int(data[-3])

        context.user_data["callback_data"] = data

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="الرجوع عن الرد على الشكوى 🔙",
                    callback_data=f"back_from_reply_to_returned_complaint_{from_worker}_{order_type}_{data[-1]}",
                )
            )
        )

        return CORRECT_RETURNED_COMPLAINT


async def correct_returned_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE:

        callback_data = context.user_data["callback_data"]
        order_type: str = callback_data[-2]
        from_worker = int(callback_data[-3])
        serial = int(callback_data[-1])

        complaint = Complaint.get_complaint(order_serial=serial, order_type=order_type)
        main_text = make_complaint_main_text(
            order_serial=serial, order_type=order_type, reason=complaint.reason
        )
        media = Photo.get(
            order_serial=serial, order_type=order_type.replace("busdt", "buy_usdt")
        )

        op = parent_to_child_models_mapper[order_type].get_one_order(
            serial=serial,
        )
        chat_id = (
            (op.worker_id if op.worker_id else op.checker_id)
            if int(from_worker)
            else context.bot_data["data"]["complaints_group"]
        )

        if not update.message.photo and not media:
            await context.bot.send_message(
                chat_id=chat_id,
                text=main_text,
            )

        else:
            photos = media if media else []
            if update.message.photo:
                photos.append(update.message.photo[-1])
                await send_to_media_archive(
                    context=context,
                    media=update.message.photo[-1],
                    order_type=order_type.replace("busdt", "buy_usdt"),
                    serial=serial,
                )

            await context.bot.send_media_group(
                chat_id=chat_id,
                media=[InputMediaPhoto(media=photo) for photo in photos],
                caption=main_text,
            )

        if update.message.caption or update.message.text:
            msg = (
                update.message.caption
                if update.message.caption
                else update.message.text
            )
            await ComplaintConv.add_response(
                complaint_id=complaint.id,
                msg=msg,
                from_user=True,
            )

        conv_text = (
            EXT_COMPLAINT_LINE.format(serial)
            + make_conv_text(complaint_id=complaint.id)
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=conv_text,
            reply_markup=build_complaint_keyboard(
                data=callback_data,
                send_to_worker=(not int(from_worker)),
            ),
        )
        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_user.id,
            message_id=update.message.reply_to_message.id,
        )
        await update.message.reply_text(
            text="تم إرسال الرد ✅",
        )

        return ConversationHandler.END


async def back_from_reply_to_returned_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE:
        data = update.callback_query.data.split("_")
        order_type = data[-2]
        from_worker = int(data[-3])
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="إرسال رد⬅️",
                    callback_data=f"user_reply_to_complaint_{from_worker}_{order_type}_{data[-1]}",
                )
            ),
        )
        return ConversationHandler.END


reply_to_returned_complaint_handler = CallbackQueryHandler(
    reply_to_returned_complaint,
    "^user_reply_to_complaint",
)
correct_returned_complaint_handler = MessageHandler(
    filters=filters.REPLY
    & UserRespondToComplaint()
    & (filters.CAPTION | filters.PHOTO | (filters.TEXT & ~filters.COMMAND)),
    callback=correct_returned_complaint,
)
back_from_reply_to_returned_complaint_handler = CallbackQueryHandler(
    back_from_reply_to_returned_complaint,
    "^back_from_reply_to_returned_complaint",
)
