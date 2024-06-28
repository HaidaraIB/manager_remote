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

from custom_filters.User import User

from common.common import (
    build_complaint_keyboard,
)

from DB import DB

from check_complaint.check_complaint import make_complaint_data

(CORRECT_RETURNED_COMPLAINT,) = range(1)


async def reply_to_returned_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بما تريد إرساله، يمكنك إرسال صورة أو نص أو الاثنين معاً.",
            show_alert=True,
        )

        data = update.callback_query.data.split("_")

        context.user_data["callback_data"] = data

        await make_complaint_data(context, data)

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="الرجوع عن الرد على الشكوى🔙",
                    callback_data=f"back_from_reply_to_returned_complaint_{data[-2]}_{data[-1]}",
                )
            )
        )

        return CORRECT_RETURNED_COMPLAINT


async def correct_returned_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):

        data = context.user_data["complaint_data"]

        op = DB.get_one_order(
            context.user_data["callback_data"][-2],
            serial=int(context.user_data["callback_data"][-1]),
        )

        context.user_data["complaint_data"] = data

        chat_id = (
            op["worker_id"]
            if int(context.user_data["callback_data"][-3])
            else context.bot_data["data"]["complaints_group"]
        )

        if not update.message.photo and not data["media"]:
            await context.bot.send_message(
                chat_id=chat_id,
                text=data["text"],
            )

        else:
            photos = data["media"] if data["media"] else []
            if update.message.photo:
                photos.append(update.message.photo[-1])

            await context.bot.send_media_group(
                chat_id=chat_id,
                media=[InputMediaPhoto(media=photo) for photo in photos],
                caption=data["text"],
            )

        await context.bot.send_message(
            chat_id=chat_id,
            text=update.effective_message.reply_to_message.text_html
            + f"\n\nرد المستخدم على الشكوى:\n<b>{update.message.caption if update.message.caption else update.message.text}</b>",
            reply_markup=build_complaint_keyboard(
                data=context.user_data["callback_data"],
                from_worker=context.user_data["callback_data"][-3],
                send_to_worker=False,
            ),
        )
        await update.message.reply_text(
            text="تم إرسال الرد✅",
        )

        del context.user_data["complaint_data"]

        return ConversationHandler.END


async def back_from_reply_to_returned_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        data = update.callback_query.data.split("_")
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="إرسال رد⬅️",
                    callback_data=f"user_reply_to_complaint_{data[-3]}_{data[-2]}_{data[-1]}",
                )
            ),
        )
        return ConversationHandler.END


reply_to_returned_complaint_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            reply_to_returned_complaint,
            "^user_reply_to_complaint",
        )
    ],
    states={
        CORRECT_RETURNED_COMPLAINT: [
            MessageHandler(
                filters=filters.REPLY
                & ~filters.COMMAND
                & (filters.CAPTION | filters.PHOTO | filters.TEXT),
                callback=correct_returned_complaint,
            )
        ]
    },
    fallbacks=[
        CallbackQueryHandler(
            back_from_reply_to_returned_complaint,
            "^back_from_reply_to_returned_complaint",
        ),
    ],
)
