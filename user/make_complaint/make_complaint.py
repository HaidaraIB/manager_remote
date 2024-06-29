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
    build_user_keyboard,
    build_back_button,
    build_complaint_keyboard,
)

from common.force_join import check_if_user_member_decorator
from common.back_to_home_page import (
    back_to_user_home_page_handler,
    back_to_user_home_page_button,
)

from user.make_complaint.notify import notify_operation

from start import start_command

from DB import DB

from user.make_complaint.common import *

(
    COMPLAINT_ABOUT,
    CHOOSE_OPERATION,
    NOTIFY_OPERATION,
    COMPLAINT_REASON,
    COMPLAINT_CONFIRMATION,
) = range(5)


@check_if_user_member_decorator
async def make_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if not context.bot_data["data"]["user_calls"]["make_complaint"]:
            await update.callback_query.answer("قسم الشكاوي متوقف حالياً❗️")
            return ConversationHandler.END

        user = DB.get_user(user_id=update.effective_user.id)
        if not user:
            new_user = update.effective_user
            await DB.add_new_user(
                user_id=new_user.id, username=new_user.username, name=new_user.full_name
            )

        await update.callback_query.edit_message_text(
            text="شكوى فيما يخص:",
            reply_markup=InlineKeyboardMarkup(complaints_keyboard),
        )
        return COMPLAINT_ABOUT


async def complaint_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        about = update.callback_query.data.replace(" complaint", "")
        context.user_data["complaint_about"] = about

        if about == "deposit":
            ar_texts = ["إيداع", "الإيداع"]
        elif about == "withdraw":
            ar_texts = ["سحب", "السحب"]
        else:
            ar_texts = ["شراء USDT", "شراء USDT"]

        res = await handle_complaint_about(
            update=update,
            context=context,
            about=about,
        )

        if not res:
            await update.callback_query.answer(f"لم تقم بأي عملية {ar_texts[0]} بعد❗️")
            return

        return CHOOSE_OPERATION


async def choose_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if not update.callback_query.data.startswith("back"):
            serial = int(update.callback_query.data.replace("serial ", ""))
            context.user_data["complaint_serial"] = serial
        else:
            serial = context.user_data["complaint_serial"]

        op = DB.get_one_order(
            serial=serial,
            order_type=context.user_data["complaint_about"],
        )

        op_text = (
            f"تفاصيل العملية:\n\n"
            f"الرقم التسلسلي: <code>{op['serial']}</code>\n"
            f"الكمية: <b>{op['amount']}</b>\n"
            f"وسيلة الدفع: <b>{op['method']}</b>\n"
            f"الحالة: <b>{state_dict_en_to_ar[op['state']]}</b>\n"
            f"سبب إعادة/رفض: <b>{op['reason'] if op['reason'] else 'لا يوجد'}</b>\n\n"
        )

        if op["state"] in ["sent", "pending"]:
            alert_button = [
                [
                    InlineKeyboardButton(
                        text="إرسال تنبيه🔔",
                        callback_data=f"notify_{op['state']}_operation_{serial}",
                    )
                ],
                build_back_button("back to choose operation"),
                back_to_user_home_page_button[0],
            ]
            if op["state"] == "sent":
                text = op_text + "<b>عملية قيد التنفيذ، يمكنك إرسال تذكير بشأنها.</b>"

            else:
                text = op_text + "<b>عملية قيد التحقق، يمكنك إرسال تذكير بشأنها.</b>"

            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(alert_button),
            )
            return NOTIFY_OPERATION

        keyboard = [
            build_back_button("back to choose operation"),
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text=op_text + "<b>أرسل سبب هذه الشكوى</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return COMPLAINT_REASON


async def complaint_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        context.user_data["reason"] = update.message.text
        complaint_text = (
            f"هل أنت متأكد من أنك تريد إرسال شكوى فيما يخص الطلب:\n\n"
            f"{stringify_order(serial=context.user_data['complaint_serial'], order_type=context.user_data['complaint_about'])}\n"
            "سبب الشكوى:\n"
            f"<b>{update.message.text}</b>"
        )

        keyboard = [
            [
                InlineKeyboardButton(text="نعم👍", callback_data="yes complaint"),
                InlineKeyboardButton(text="لا👎", callback_data="no complaint"),
            ],
            build_back_button("back to complaint reason"),
            back_to_user_home_page_button[0],
        ]

        await update.message.reply_text(
            text=complaint_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return COMPLAINT_CONFIRMATION


async def complaint_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if update.callback_query.data.startswith("yes"):
            serial = context.user_data["complaint_serial"]
            order_type = context.user_data["complaint_about"]
            op = DB.get_one_order(order_type=order_type, serial=serial)

            archive_message_ids: str = op["archive_message_ids"]

            complaint_text = (
                f"شكوى جديدة:\n\n"
                f"{stringify_order(serial=serial, order_type=order_type)}\n"
                "سبب الشكوى:\n"
                f"<b>{context.user_data['reason']}</b>\n"
            )
            photos = await get_photos_from_archive(
                message_ids=[m_id for m_id in map(int, archive_message_ids.split(","))]
            )

            if op["worker_id"]:
                context.bot_data["suspended_workers"].add(op["worker_id"])

            data = [order_type, serial]
            complaint_keyboard = build_complaint_keyboard(data, True)

            if not photos:  # Means there's no picture, it's a declined withdraw order.
                await context.bot.send_message(
                    chat_id=context.bot_data["data"]["complaints_group"],
                    text=complaint_text,
                )
            else:
                media_group = [InputMediaPhoto(media=photo) for photo in photos]
                await context.bot.send_media_group(
                    chat_id=context.bot_data["data"]["complaints_group"],
                    media=media_group,
                    caption=complaint_text,
                )

            await context.bot.send_message(
                chat_id=context.bot_data["data"]["complaints_group"],
                text=f"<b>ملحق بالشكوى على الطلب ذي الرقم التسلسلي {serial}</b>\n\nقم باختيار ماذا تريد أن تفعل⬇️\n\n",
                reply_markup=complaint_keyboard,
            )

            await update.callback_query.edit_message_text(
                text="شكراً لك، تم إرسال الشكوى خاصتك إلى قسم المراجعة بنجاح، سنعمل على إصلاح المشكلة والرد عليك في أقرب وقت ممكن.",
                reply_markup=build_user_keyboard(),
            )

            await DB.add_complaint(
                order_serial=serial,
                order_type=order_type,
                reason=context.user_data["reason"],
            )

            return ConversationHandler.END

        else:  # in case of no complaint selection
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=choose_operations_text,
                reply_markup=InlineKeyboardMarkup(
                    context.user_data["operations_keyboard"]
                ),
            )
            return CHOOSE_OPERATION


async def back_to_choose_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        await update.callback_query.edit_message_text(
            text=choose_operations_text,
            reply_markup=InlineKeyboardMarkup(context.user_data["operations_keyboard"]),
        )
        return CHOOSE_OPERATION


back_to_complaint_reason = choose_operation


async def back_to_complaint_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        await update.callback_query.edit_message_text(
            text="شكوى فيما يخص:",
            reply_markup=InlineKeyboardMarkup(complaints_keyboard),
        )
        return COMPLAINT_ABOUT


complaint_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(make_complaint, "^make complaint$")],
    states={
        COMPLAINT_ABOUT: [
            CallbackQueryHandler(
                complaint_about,
                "^deposit complaint$|^buyusdt complaint$|^withdraw complaint$",
            )
        ],
        CHOOSE_OPERATION: [CallbackQueryHandler(choose_operation, "^serial \d+$")],
        NOTIFY_OPERATION: [
            CallbackQueryHandler(
                notify_operation,
                "^notify",
            )
        ],
        COMPLAINT_REASON: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND, callback=complaint_reason
            )
        ],
        COMPLAINT_CONFIRMATION: [
            CallbackQueryHandler(
                complaint_confirmation, "^yes complaint$|^no complaint$"
            )
        ],
    },
    fallbacks=[
        CallbackQueryHandler(back_to_complaint_about, "^back to complaint about$"),
        CallbackQueryHandler(back_to_complaint_reason, "^back to complaint reason$"),
        CallbackQueryHandler(back_to_choose_operation, "^back to choose operation$"),
        back_to_user_home_page_handler,
        start_command,
    ],
    name="make_complaint_handler",
    persistent=True,
)
