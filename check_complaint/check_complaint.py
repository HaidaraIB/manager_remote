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


async def close_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:
        data = update.callback_query.data
        await update.callback_query.answer(
            "قم بالرد على هذه الرسالة بما تريد إرساله إلى المستخدم إن وجد، إن لم يوجد اضغط تخطي.",
            show_alert=True,
        )
        back_button_callback_data = {
            **data,
            "name": "back from close complaint",
            "effective_worker_id": update.effective_user.id,
            "from_worker": (
                True if update.effective_chat.type == Chat.PRIVATE else False
            ),
        }
        skip_button_callback_data = {
            **data,
            "name": "skip close complaint",
            "effective_worker_id": update.effective_user.id,
            "from_worker": (
                True if update.effective_chat.type == Chat.PRIVATE else False
            ),
        }
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="تخطي⬅️",
                            callback_data=skip_button_callback_data,
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="الرجوع عن إغلاق الشكوى🔙",
                            callback_data=back_button_callback_data,
                        )
                    ],
                ]
            )
        )




async def skip_close_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:
        data = update.callback_query.data
        text_list = data["text"].split("\n")
        text_list.insert(0, "تم إغلاق الشكوى✅")
        user_text = f"تمت معالجة الشكوى الخاصة بك عن الطلب ذي الرقم التسلسلي <code>{data['op']['serial']}</code> إليك النسخة النهائية⬇️⬇️⬇️\n\n"
        if data["media"]:
            await context.bot.send_media_group(
                chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
                media=[InputMediaPhoto(media=photo) for photo in data["media"]],
                caption="\n".join(text_list),
            )
            await context.bot.send_media_group(
                chat_id=data["op"]["user_id"],
                media=[InputMediaPhoto(media=photo) for photo in data["media"]],
                caption=user_text + "\n".join(text_list),
            )
        else:
            await context.bot.send_message(
                chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
                text="\n".join(text_list),
            )
            await context.bot.send_message(
                chat_id=data["op"]["user_id"],
                text=user_text + "\n".join(text_list),
            )

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.callback_query.message.id,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="تم إغلاق الشكوى✅",
                            callback_data="تم إغلاق الشكوى✅",
                        )
                    ]
                ]
            ),
        )

        await DB.set_complaint_took_care_of(
            serial=data["op"]["serial"],
            order_type=data["operation"],
            took_care_of=1,
        )
        context.bot_data["suspended_workers"].remove(data["op"]["worker_id"])



async def reply_on_close_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:
        data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data
        text_list = data["text"].split("\n")
        if update.message.text:
            text_list.insert(
                len(text_list), f"رد الدعم على الشكوى:\n<b>{update.message.text}</b>"
            )
        elif update.message.caption:
            text_list.insert(
                len(text_list),
                f"رد الدعم على الشكوى:\n<b>{update.message.caption}</b>",
            )
        user_text = f"تمت معالجة الشكوى الخاصة بك عن الطلب ذي الرقم التسلسلي <code>{data['op']['serial']}</code> إليك النسخة النهائية⬇️⬇️⬇️\n\n"
        if not update.message.photo:
            if data["media"]:
                await context.bot.send_media_group(
                    chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
                    media=[InputMediaPhoto(media=photo) for photo in data["media"]],
                    caption="\n".join(text_list),
                )
                await context.bot.send_media_group(
                    chat_id=data["op"]["user_id"],
                    media=[InputMediaPhoto(media=photo) for photo in data["media"]],
                    caption=user_text + "\n".join(text_list),
                )
            else:
                await context.bot.send_message(
                    chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
                    text="\n".join(text_list),
                )
                await context.bot.send_message(
                    chat_id=data["op"]["user_id"],
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
                chat_id=data["op"]["user_id"],
                media=[InputMediaPhoto(media=photo) for photo in data["media"]],
                caption=user_text + "\n".join(text_list),
            )

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="تم إغلاق الشكوى✅",
                            callback_data="تم إغلاق الشكوى✅",
                        )
                    ]
                ]
            ),
        )

        await DB.set_complaint_took_care_of(
            serial=data["op"]["serial"],
            order_type=data["operation"],
            took_care_of=1,
        )
        context.bot_data["suspended_workers"].remove(data["op"]["worker_id"])


async def handle_respond_to_user_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:

        data = update.callback_query.data
        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بما تريد إرساله إلى المستخدم."
        )
        back_button_callback_data = {
            **data,
            "name": "back from respond to user complaint",
            "effective_worker_id": update.effective_user.id,
            "from_worker": (
                True if update.effective_chat.type == Chat.PRIVATE else False
            ),
        }
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="الرجوع عن الرد على المستخدم🔙",
                            callback_data=back_button_callback_data,
                        )
                    ]
                ]
            )
        )


async def handle_edit_amount_user_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:

        data = update.callback_query.data
        back_button_callback_data = {
            **data,
            "name": "back from mod amount to user complaint",
            "effective_worker_id": update.effective_user.id,
            "from_worker": (
                True if update.effective_chat.type == Chat.PRIVATE else False
            ),
        }
        back_button = [
            [
                InlineKeyboardButton(
                    text="الرجوع عن تعديل المبلغ🔙",
                    callback_data=back_button_callback_data,
                )
            ]
        ]
        await update.callback_query.answer(
            text="قم بالرد على هذه الرسالة بقيمة المبلغ الجديدة.", show_alert=True
        )
        await update.callback_query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(back_button)
        )


async def edit_order_amount_user_complaint(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:

        data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data

        new_amount = float(update.message.text)
        old_amount = data["op"]["amount"]
        data["op"]["amount"] = new_amount

        await DB.edit_order_amount(
            order_type=data["operation"],
            serial=data["op"]["serial"],
            new_amount=new_amount,
        )


        if data["op"]["worker_id"]:
            if data["operation"] in ["withdraw", "buy usdt"]:
                await DB.update_worker_approved_withdraws(
                    worder_id=data["op"]["worker_id"], method=data['op']['method'], amount=-old_amount,
                )
                await DB.update_worker_approved_withdraws(
                    worder_id=data["op"]["worker_id"], method=data['op']['method'], amount=new_amount,
                )
            elif data["operation"] == "deposit":
                await DB.update_worker_approved_deposits(
                    worder_id=data["op"]["worker_id"], amount=-old_amount
                )
                await DB.update_worker_approved_deposits(
                    worder_id=data["op"]["worker_id"], amount=new_amount
                )

        text_list = data["text"].split("\n")
        text_list[4] = f"المبلغ: <b>{new_amount}</b>"
        data["text"] = "\n".join(text_list)

        reply_to_text = update.message.reply_to_message.text
        if "ملحق بالشكوى" not in reply_to_text:
            reply_to_text = "\n".join(text_list)
        else:
            reply_to_text = f"""<b>ملحق بالشكوى على الطلب ذي الرقم التسلسلي {data['op']['serial']}</b>

تم تعديل المبلغ بنجاح✅
        
المبلغ: <b>{new_amount}</b>
"""

        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
        )

        await update.message.reply_text(
            text=reply_to_text,
            reply_markup=build_complaint_keyboard(data=data),
        )


async def respond_to_user_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:

        data = update.message.reply_to_message.reply_markup.inline_keyboard[0][
            0
        ].callback_data

        if update.effective_user.id != data["effective_worker_id"]:
            return

        user_text = f"""تمت الإجابة الشكوى الخاصة بطلبك ذي الرقم التسلسلي <b>{data['op']['serial']}</b>\n\nإليك الطلب⬇️⬇️⬇️"""

        try:
            await context.bot.send_message(
                chat_id=data["op"]["user_id"],
                text=user_text,
            )
        except:
            pass

        text_list = data["text"].split("\n")

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

        user_button_callback_data = {
            **data,
            "name": "user reply to complaint",
            "from_worker": (
                True if update.effective_chat.type == Chat.PRIVATE else False
            ),
        }

        user_button = [
            [
                InlineKeyboardButton(
                    text="إرسال رد⬅️", callback_data=user_button_callback_data
                )
            ]
        ]

        text_list.insert(0, "تمت الإجابة على الشكوى✅")
        button_text = f"""تمت الإجابة على الشكوى✅

<b>ملحق بالشكوى على الطلب ذي الرقم التسلسلي {data['op']['serial']}</b>
"""
        try:
            if not update.message.photo:
                if data["media"]:
                    await context.bot.send_media_group(
                        chat_id=data["op"]["user_id"],
                        media=[InputMediaPhoto(media=photo) for photo in data["media"]],
                        caption="\n".join(text_list),
                    )
                    await context.bot.send_message(
                        chat_id=data["op"]["user_id"],
                        text=button_text,
                        reply_markup=InlineKeyboardMarkup(user_button),
                    )
                else:
                    await context.bot.send_message(
                        chat_id=data["op"]["user_id"],
                        text="\n".join(text_list),
                        reply_markup=InlineKeyboardMarkup(user_button),
                    )
            else:
                photos = [update.message.photo[-1]]
                if data["media"]:
                    photos = data["media"]
                    photos.append(update.message.photo[-1])

                await context.bot.send_media_group(
                    chat_id=data["op"]["user_id"],
                    media=[InputMediaPhoto(media=photo) for photo in photos],
                    caption="\n".join(text_list),
                )
                await context.bot.send_message(
                    chat_id=data["op"]["user_id"],
                    text=button_text,
                    reply_markup=InlineKeyboardMarkup(user_button),
                )
        except:
            pass

        await context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.message.reply_to_message.id,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="تمت الإجابة على الشكوى✅",
                            callback_data="تمت الإجابة على الشكوى✅",
                        )
                    ]
                ]
            ),
        )


async def send_to_worker_user_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        data: dict = update.callback_query.data
        try:
            if data["media"]:
                media_group = [InputMediaPhoto(media=photo) for photo in data["media"]]
                await context.bot.send_media_group(
                    chat_id=data["op"]["worker_id"],
                    media=media_group,
                    caption=data["text"],
                )
                await context.bot.send_message(
                    chat_id=data["op"]["worker_id"],
                    text=f"<b>ملحق بالشكوى على الطلب ذي الرقم التسلسلي {data['op']['serial']}</b>\n\nقم باختيار ماذا تريد أن تفعل⬇️",
                    reply_markup=build_complaint_keyboard(data=data),
                )
            else:
                await context.bot.send_message(
                    chat_id=data["op"]["worker_id"],
                    text=data["text"],
                    reply_markup=build_complaint_keyboard(data=data),
                )

            await update.callback_query.answer("تم إرسال الشكوى إلى الموظف المسؤول✅")
            await update.callback_query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="تم إرسال الشكوى إلى الموظف المسؤول✅",
                                callback_data="تم إرسال الشكوى إلى الموظف المسؤول✅",
                            )
                        ]
                    ]
                ),
            )
        except:
            pass


async def back_from_respond_to_user_complaint(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_chat.type in [Chat.GROUP, Chat.SUPERGROUP, Chat.PRIVATE]:
        await update.callback_query.edit_message_reply_markup(
            reply_markup=build_complaint_keyboard(data=update.callback_query.data)
        )


back_from_mod_amount_user_complaint = back_from_respond_to_user_complaint

back_from_close_complaint = back_from_respond_to_user_complaint


send_to_worker_user_complaint_handler = CallbackQueryHandler(
    callback=send_to_worker_user_complaint,
    pattern=lambda d: isinstance(d, dict)
    and d.get("name", False) == "send to worker user complaint",
)


handle_edit_amount_user_complaint_handler = CallbackQueryHandler(
    callback=handle_edit_amount_user_complaint,
    pattern=lambda d: isinstance(d, dict)
    and d.get("name", False) == "mod amount user complaint",
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
    pattern=lambda d: isinstance(d, dict)
    and d.get("name", False) == "respond to user complaint",
)


close_complaint_handler = CallbackQueryHandler(
    callback=close_complaint,
    pattern=lambda d: isinstance(d, dict) and d.get("name", False) == "close complaint",
)


skip_close_complaint_handler = CallbackQueryHandler(
    callback=skip_close_complaint,
    pattern=lambda d: isinstance(d, dict)
    and d.get("name", False) == "skip close complaint",
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
    pattern=lambda d: isinstance(d, dict)
    and d.get("name", False) == "back from respond to user complaint",
)

back_from_mod_amount_user_complaint_handler = CallbackQueryHandler(
    callback=back_from_mod_amount_user_complaint,
    pattern=lambda d: isinstance(d, dict)
    and d.get("name", False) == "back from mod amount to user complaint",
)

back_from_close_complaint_handler = CallbackQueryHandler(
    callback=back_from_close_complaint,
    pattern=lambda d: isinstance(d, dict)
    and d.get("name", False) == "back from close complaint",
)
