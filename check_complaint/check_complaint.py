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
from custom_filters.ModAmountUserComplaint import ModAmountUserComplaint

from DB import DB
import os
from common.common import (
    build_complaint_keyboard,
)

import user.make_complaint as mkc


async def make_complaint_data(context: ContextTypes.DEFAULT_TYPE, callback_data: list):
    try:
        data = context.user_data["complaint_data"]
    except KeyError:
        data = {
            "text": (
                f"شكوى جديدة:\n\n"
                f"{mkc.stringify_order(serial=int(callback_data[-1]), order_type=callback_data[-2])}\n"
                "سبب الشكوى:\n"
                f"<b>{context.user_data['reason']}</b>"
            ),
            "media": (
                await mkc.get_photos_from_archive(
                    message_ids=[
                        m_id for m_id in map(int, callback_data[-3].split(","))
                    ]
                )
            ),
        }
        context.user_data["complaint_data"] = data
    return data


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
                        callback_data=f"skip_close_complaint_{data[-3]}_{data[-2]}_{data[-1]}",
                    ),
                    InlineKeyboardButton(
                        text="الرجوع عن إغلاق الشكوى🔙",
                        callback_data=f"back_from_close_complaint_{data[-3]}_{data[-2]}_{data[-1]}",
                    ),
                ]
            )
        )


async def skip_close_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:
        callback_data = update.callback_query.data.split("_")
        op = DB.get_one_order(
            order_type=callback_data[-2], serial=int(callback_data[-1])
        )

        data = await make_complaint_data(context, callback_data)

        text_list: list = data["text"].split("\n")
        text_list.insert(0, "تم إغلاق الشكوى✅")
        user_text = f"تمت معالجة الشكوى الخاصة بك عن الطلب ذي الرقم التسلسلي <code>{op['serial']}</code> إليك النسخة النهائية⬇️⬇️⬇️\n\n"
        if data["media"]:
            await context.bot.send_media_group(
                chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
                media=[InputMediaPhoto(media=photo) for photo in data["media"]],
                caption="\n".join(text_list),
            )
            await context.bot.send_media_group(
                chat_id=op["user_id"],
                media=[InputMediaPhoto(media=photo) for photo in data["media"]],
                caption=user_text + "\n".join(text_list),
            )
        else:
            await context.bot.send_message(
                chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
                text="\n".join(text_list),
            )
            await context.bot.send_message(
                chat_id=op["user_id"],
                text=user_text + "\n".join(text_list),
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

        await DB.set_complaint_took_care_of(
            serial=op["serial"],
            order_type=callback_data[-2],
            took_care_of=1,
        )
        context.bot_data["suspended_workers"].discard(op["worker_id"])


async def reply_on_close_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:
        callback_data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data.split("_")

        data = await make_complaint_data(context, callback_data)

        op = DB.get_one_order(
            order_type=callback_data[-2], serial=int(callback_data[-1])
        )

        text_list: list = data["text"].split("\n")
        if update.message.text:
            text_list.insert(
                len(text_list), f"رد الدعم على الشكوى:\n<b>{update.message.text}</b>"
            )
        elif update.message.caption:
            text_list.insert(
                len(text_list),
                f"رد الدعم على الشكوى:\n<b>{update.message.caption}</b>",
            )
        user_text = f"تمت معالجة الشكوى الخاصة بك عن الطلب ذي الرقم التسلسلي <code>{op['serial']}</code> إليك النسخة النهائية⬇️⬇️⬇️\n\n"
        if not update.message.photo:
            if data["media"]:
                await context.bot.send_media_group(
                    chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
                    media=[InputMediaPhoto(media=photo) for photo in data["media"]],
                    caption="\n".join(text_list),
                )
                await context.bot.send_media_group(
                    chat_id=op["user_id"],
                    media=[InputMediaPhoto(media=photo) for photo in data["media"]],
                    caption=user_text + "\n".join(text_list),
                )
            else:
                await context.bot.send_message(
                    chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
                    text="\n".join(text_list),
                )
                await context.bot.send_message(
                    chat_id=op["user_id"],
                    text=user_text + "\n".join(text_list),
                )
        else:
            photos = [update.message.photo[-1]]
            if data["media"]:
                photos = data["media"]
                photos.append(update.message.photo[-1])

            await context.bot.send_media_group(
                chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
                media=[InputMediaPhoto(media=photo) for photo in data["media"]],
                caption="\n".join(text_list),
            )
            await context.bot.send_media_group(
                chat_id=op["user_id"],
                media=[InputMediaPhoto(media=photo) for photo in data["media"]],
                caption=user_text + "\n".join(text_list),
            )

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="تم إغلاق الشكوى✅",
                    callback_data="✅✅✅✅✅✅✅✅✅✅✅✅✅",
                )
            ),
        )

        await DB.set_complaint_took_care_of(
            serial=op["serial"],
            order_type=data["about"],
            took_care_of=1,
        )
        context.bot_data["suspended_workers"].discard(op["worker_id"])


async def handle_respond_to_user_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:
        data = update.callback_query.data.split("_")
        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بما تريد إرساله إلى المستخدم."
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="الرجوع عن الرد على المستخدم🔙",
                    callback_data=f"back_from_respond_to_user_complaint_{data[-3]}_{data[-2]}_{data[-1]}",
                )
            )
        )


async def handle_edit_amount_user_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:

        data = update.callback_query.data.split("_")
        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بقيمة المبلغ الجديدة.", show_alert=True
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(
                    text="الرجوع عن تعديل المبلغ🔙",
                    callback_data=f"back_from_mod_amount_to_user_complaint_{data[-3]}_{data[-2]}_{data[-1]}",
                )
            )
        )


async def edit_order_amount_user_complaint(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:

        callback_data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data.split("_")

        op = DB.get_one_order(
            order_type=callback_data[-2], serial=int(callback_data[-1])
        )

        data = await make_complaint_data(context, callback_data)

        new_amount = float(update.message.text)
        old_amount = op["amount"]

        await DB.edit_order_amount(
            order_type=callback_data[-2],
            serial=op["serial"],
            new_amount=new_amount,
        )

        if op["worker_id"]:
            if callback_data[-2] in ["withdraw", "buy usdt"]:
                await DB.update_worker_approved_withdraws(
                    worder_id=op["worker_id"],
                    method=op["method"],
                    amount=-old_amount + new_amount,
                )
            elif callback_data[-2] == "deposit":
                await DB.update_worker_approved_deposits(
                    worder_id=op["worker_id"],
                    amount=-old_amount + new_amount,
                )

        text_list = data["text"].split("\n")
        text_list[4] = f"المبلغ: <b>{new_amount}</b>"
        data["text"] = "\n".join(text_list)

        context.user_data["complaint_data"] = data

        reply_to_text = update.message.reply_to_message.text
        if "ملحق بالشكوى" not in reply_to_text:
            reply_to_text = "\n".join(text_list)
        else:
            reply_to_text = (
                f"<b>ملحق بالشكوى على الطلب ذي الرقم التسلسلي {op['serial']}</b>\n\n"
                "تم تعديل المبلغ بنجاح✅\n\n"
                f"المبلغ: <b>{new_amount}</b>"
            )

        await update.message.delete()

        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            text=reply_to_text,
            reply_markup=build_complaint_keyboard(
                data=callback_data,
                from_worker=(
                    True if update.effective_chat.type == Chat.PRIVATE else False
                ),
                send_to_worker="_".join(callback_data[:-3])
                == "send_to_worker_user_complaint",
            ),
        )


async def respond_to_user_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:

        callback_data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data.split("_")

        op = DB.get_one_order(
            order_type=callback_data[-2], serial=int(callback_data[-1])
        )

        data = await make_complaint_data(context, callback_data)

        user_text = f"تمت الإجابة الشكوى الخاصة بطلبك ذي الرقم التسلسلي <b>{op['serial']}</b>\n\nإليك الطلب⬇️⬇️⬇️"

        try:
            await context.bot.send_message(
                chat_id=op["user_id"],
                text=user_text,
            )
        except:
            pass

        text_list: list = data["text"].split("\n")

        if update.message.text:
            text_list.insert(
                len(text_list), f"رد الدعم على الشكوى:\n<b>{update.message.text}</b>"
            )
        elif update.message.caption:
            text_list.insert(
                len(text_list),
                f"رد الدعم على الشكوى:\n<b>{update.message.caption}</b>",
            )

        data["text"] = "\n".join(text_list)

        context.user_data["complaint_data"] = data

        text_list.insert(0, "تمت الإجابة على الشكوى✅")
        button_text = (
            f"تمت الإجابة على الشكوى✅\n\n"
            f"<b>ملحق بالشكوى على الطلب ذي الرقم التسلسلي {op['serial']}</b>"
        )

        try:
            if not update.message.photo and not data["media"]:
                await context.bot.send_message(
                    chat_id=op["user_id"],
                    text=button_text if data["media"] else "\n".join(text_list),
                    reply_markup=InlineKeyboardMarkup.from_button(
                        InlineKeyboardButton(
                            text="إرسال رد⬅️",
                            callback_data=f"user_reply_to_complaint_{1 if update.effective_chat.type == Chat.PRIVATE else 0}_{data[-3]}_{data[-2]}_{data[-1]}",
                        )
                    ),
                )
            else:
                photos = data["media"] if data["media"] else []
                if update.message.photo:
                    photos.append(update.message.photo[-1])

                await context.bot.send_media_group(
                    chat_id=op["user_id"],
                    media=[InputMediaPhoto(media=photo) for photo in photos],
                    caption="\n".join(text_list),
                )
                await context.bot.send_message(
                    chat_id=op["user_id"],
                    text=button_text,
                    reply_markup=InlineKeyboardMarkup.from_button(
                        InlineKeyboardButton(
                            text="إرسال رد⬅️",
                            callback_data=f"user_reply_to_complaint_{data[-3]}_{data[-2]}_{data[-1]}",
                        )
                    ),
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


async def send_to_worker_user_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        callback_data = update.callback_query.data.split("_")

        op = DB.get_one_order(
            order_type=callback_data[-2], serial=int(callback_data[-1])
        )

        data = await make_complaint_data(context, callback_data)

        try:
            if data["media"]:
                media_group = [InputMediaPhoto(media=photo) for photo in data["media"]]
                await context.bot.send_media_group(
                    chat_id=op["worker_id"],
                    media=media_group,
                    caption=data["text"],
                )
                await context.bot.send_message(
                    chat_id=op["worker_id"],
                    text=f"<b>ملحق بالشكوى على الطلب ذي الرقم التسلسلي {op['serial']}</b>\n\nقم باختيار ماذا تريد أن تفعل⬇️",
                    reply_markup=build_complaint_keyboard(
                        data=callback_data,
                        from_worker=(
                            True
                            if update.effective_chat.type == Chat.PRIVATE
                            else False
                        ),
                        send_to_worker="_".join(callback_data[:-3])
                        == "send_to_worker_user_complaint",
                    ),
                )
            else:
                await context.bot.send_message(
                    chat_id=op["worker_id"],
                    text=data["text"],
                    reply_markup=build_complaint_keyboard(
                        data=callback_data,
                        from_worker=(
                            True
                            if update.effective_chat.type == Chat.PRIVATE
                            else False
                        ),
                        send_to_worker="_".join(callback_data[:-3])
                        == "send_to_worker_user_complaint",
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
        except Exception as e:
            import traceback

            traceback.print_exc()
            pass


async def back_from_respond_to_user_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:
        callback_data = update.callback_query.data.split("_")
        await update.callback_query.edit_message_reply_markup(
            reply_markup=build_complaint_keyboard(
                data=callback_data,
                from_worker=(
                    True if update.effective_chat.type == Chat.PRIVATE else False
                ),
                send_to_worker="_".join(callback_data[:-3])
                == "send_to_worker_user_complaint",
            )
        )


back_from_mod_amount_user_complaint = back_from_respond_to_user_complaint

back_from_close_complaint = back_from_respond_to_user_complaint


send_to_worker_user_complaint_handler = CallbackQueryHandler(
    callback=send_to_worker_user_complaint,
    pattern="^send_to_worker_user_complaint",
)


handle_edit_amount_user_complaint_handler = CallbackQueryHandler(
    callback=handle_edit_amount_user_complaint,
    pattern="^mod_amount_user_complaint",
)


edit_order_amount_user_complaint_handler = MessageHandler(
    filters=filters.REPLY
    & Complaint()
    & ModAmountUserComplaint()
    & filters.Regex("^\d+$"),
    callback=edit_order_amount_user_complaint,
)


handle_respond_to_user_complaint_handler = CallbackQueryHandler(
    callback=handle_respond_to_user_complaint,
    pattern="^respond_to_user_complaint",
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

back_from_mod_amount_user_complaint_handler = CallbackQueryHandler(
    callback=back_from_mod_amount_user_complaint,
    pattern="^back_from_mod_amount_to_user_complaint",
)

back_from_close_complaint_handler = CallbackQueryHandler(
    callback=back_from_close_complaint,
    pattern="^back_from_close_complaint",
)
