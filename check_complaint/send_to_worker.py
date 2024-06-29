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

from DB import DB
from common.common import (
    build_complaint_keyboard,
)

from check_complaint.check_complaint import make_complaint_data


async def send_to_worker_user_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        callback_data = update.callback_query.data.split("_")

        op = DB.get_one_order(
            order_type=callback_data[-2], serial=int(callback_data[-1])
        )

        data = await make_complaint_data(context, callback_data)

        if data["media"]:
            media_group = [InputMediaPhoto(media=photo) for photo in data["media"]]
            await context.bot.send_media_group(
                chat_id=op["worker_id"] if op['worker_id'] else op['checker_id'],
                media=media_group,
                caption=data["text"],
            )
        else:
            await context.bot.send_message(
                chat_id=op["worker_id"] if op['worker_id'] else op['checker_id'],
                text=data["text"],
            )

        await context.bot.send_message(
            chat_id=op["worker_id"] if op['worker_id'] else op['checker_id'],
            text=update.effective_message.text_html,
            reply_markup=build_complaint_keyboard(
                data=callback_data,
                send_to_worker=False,
            ),
        )

        await update.callback_query.answer(
            text="تم إرسال الشكوى إلى الموظف المسؤول✅",
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
