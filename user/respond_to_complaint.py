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
    build_user_keyboard,
    build_complaint_keyboard,
)

from check_complaint import check_complaint as chc

from DB import DB

(
    CORRECT_RETURNED_COMPLAINT,
) = range(1)


async def reply_to_returned_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type == Chat.PRIVATE and User().filter(update):
        await update.callback_query.answer(
            text="قم بإرسال ردك، يمكنك إرسال صورة أو نص أو الاثنين معاً.",
            show_alert=True,
        )

        data = update.callback_query.data.split("_")

        context.user_data["callback_data"] = data

        context.user_data["from_worker"] = int(data[-5])

        await chc.make_complaint_data(context, data)

        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="الرجوع عن الرد على الشكوى🔙",
                    callback_data=f"back_from_reply_to_returned_complaint_{data[-4]}_{data[-3]}_{data[-2]}_{data[-1]}",
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

        text_list: list = data["reason"].split("\n")

        if update.message.text:
            text_list.insert(
                len(text_list), f"رد المستخدم على الشكوى:\n<b>{update.message.text}</b>"
            )
        elif update.message.caption:
            text_list.insert(
                len(text_list),
                f"رد المستخدم على الشكوى:\n<b>{update.message.caption}</b>",
            )

        data["reason"] = "\n".join(text_list)

        context.user_data["complaint_data"] = data

        chat_id = (
            op["worker_id"]
            if context.user_data["from_worker"]
            else context.bot_data["data"]["complaints_group"]
        )

        reply_markup = build_complaint_keyboard(
            context.user_data["callback_data"],
            context.user_data["from_worker"],
            False,
        )

        if not update.message.photo and not data["media"]:
            await context.bot.send_message(
                chat_id=chat_id,
                text=data["reason"],
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=data["text"],
                reply_markup=reply_markup,
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
                text=data["reason"],
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"<b>ملحق بالشكوى على الطلب ذي الرقم التسلسلي {op['serial']}</b>\n\nقم باختيار ماذا تريد أن تفعل⬇️",
                reply_markup=reply_markup,
            )
        await update.message.reply_text(
            text="تم إرسال الرد✅",
        )

        del context.user_data['complaint_data']

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
                filters=filters.TEXT
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