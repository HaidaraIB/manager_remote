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

from custom_filters.Complaint import Complaint
from custom_filters.ResponseToUserComplaint import ResponseToUserComplaint

from DB import DB
from common.common import (
    build_complaint_keyboard,
)

from check_complaint.check_complaint import make_complaint_data


async def handle_respond_to_user_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:
        data = update.callback_query.data.split("_")
        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بما تريد إرساله إلى المستخدم.",
            show_alert=True,
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="الرجوع عن الرد على المستخدم🔙",
                    callback_data=f"back_from_respond_to_user_complaint_{data[-2]}_{data[-1]}",
                )
            )
        )


async def respond_to_user_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:

        callback_data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data.split("_")

        op = DB.get_one_order(
            order_type=callback_data[-2],
            serial=int(callback_data[-1]),
        )

        data = await make_complaint_data(context, callback_data)

        user_text = f"تمت الإجابة الشكوى الخاصة بطلبك ذي الرقم التسلسلي <b>{op['serial']}</b>\n\nإليك الطلب⬇️⬇️⬇️"

        try:
            await context.bot.send_message(
                chat_id=op["user_id"],
                text=user_text,
            )
            respond_button = InlineKeyboardButton(
                text="إرسال رد⬅️",
                callback_data=f"user_reply_to_complaint_{1 if update.effective_chat.type == Chat.PRIVATE else 0}_{callback_data[-2]}_{callback_data[-1]}",
            )
            if not update.message.photo and not data["media"]:
                await context.bot.send_message(
                    chat_id=op["user_id"],
                    text=data["text"],
                    reply_markup=InlineKeyboardMarkup.from_button(respond_button),
                )
            else:
                photos = data["media"] if data["media"] else []
                if update.message.photo:
                    photos.append(update.message.photo[-1])

                await context.bot.send_media_group(
                    chat_id=op["user_id"],
                    media=[InputMediaPhoto(media=photo) for photo in photos],
                    caption=data["text"],
                )
            await context.bot.send_message(
                chat_id=op["user_id"],
                text=update.effective_message.reply_to_message.text_html
                + f"\n\nرد الدعم على الشكوى:\n<b>{update.message.caption if update.message.caption else update.message.text}</b>",
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
