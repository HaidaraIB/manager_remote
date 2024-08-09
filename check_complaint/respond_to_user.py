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

from custom_filters import Complaint, ResponseToUserComplaint
from check_complaint.check_complaint import make_conv_text, make_complaint_main_text
from common.common import (
    build_complaint_keyboard,
    parent_to_child_models_mapper,
    send_to_photos_archive,
)
from common.constants import EXT_COMPLAINT_LINE
import models


async def handle_respond_to_user_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:
        data = update.callback_query.data.split("_")
        order_type = data[-2]
        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بما تريد إرساله إلى المستخدم.",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="الرجوع عن الرد على المستخدم🔙",
                    callback_data=f"back_from_respond_to_user_complaint_{order_type}_{data[-1]}",
                )
            )
        )


async def respond_to_user_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:

        callback_data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data.split("_")
        order_type = callback_data[-2]
        serial = int(callback_data[-1])

        op = parent_to_child_models_mapper[order_type].get_one_order(serial=serial)
        complaint = models.Complaint.get_complaint(
            order_serial=serial,
            order_type=order_type,
        )

        media = models.Photo.get(
            order_serial=serial,
            order_type=order_type,
        )

        main_text = make_complaint_main_text(
            order_serial=serial, order_type=order_type, reason=complaint.reason
        )

        try:
            await context.bot.send_message(
                chat_id=op.user_id,
                text=f"تمت الإجابة الشكوى الخاصة بطلبك ذي الرقم التسلسلي <b>{op.serial}</b>\n\nإليك الطلب⬇️⬇️⬇️",
            )
            respond_button = InlineKeyboardButton(
                text="إرسال رد⬅️",
                callback_data=f"user_reply_to_complaint_{1 if update.effective_chat.type == Chat.PRIVATE else 0}_{order_type}_{serial}",
            )
            if not update.message.photo and not media:
                await context.bot.send_message(
                    chat_id=op.user_id,
                    text=main_text,
                    reply_markup=InlineKeyboardMarkup.from_button(respond_button),
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
                await context.bot.send_media_group(
                    chat_id=op.user_id,
                    media=[InputMediaPhoto(media=photo) for photo in photos],
                    caption=main_text,
                )

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

            conv_text = (
                EXT_COMPLAINT_LINE.format(serial)
                + make_conv_text(complaint_id=complaint.id)
            )
            await context.bot.send_message(
                chat_id=op.user_id,
                text=conv_text,
                reply_markup=InlineKeyboardMarkup.from_button(respond_button),
            )

        except:
            pass

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تمت الإجابة على الشكوى✅",
                    callback_data="✅✅✅✅✅✅✅✅✅✅✅✅✅",
                )
            ),
        )


async def back_from_respond_to_user_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:
        callback_data = update.callback_query.data.split("_")
        await update.callback_query.edit_message_reply_markup(
            reply_markup=build_complaint_keyboard(
                data=callback_data,
                send_to_worker=update.effective_chat.type != Chat.PRIVATE,
            )
        )


handle_respond_to_user_complaint_handler = CallbackQueryHandler(
    callback=handle_respond_to_user_complaint,
    pattern="^respond_to_user_complaint",
)
respond_to_user_complaint_handler = MessageHandler(
    filters=filters.REPLY
    & Complaint()
    & ResponseToUserComplaint()
    & (filters.CAPTION | filters.PHOTO | filters.TEXT),
    callback=respond_to_user_complaint,
)

back_from_respond_to_user_complaint_handler = CallbackQueryHandler(
    callback=back_from_respond_to_user_complaint,
    pattern="^back_from_respond_to_user_complaint",
)
