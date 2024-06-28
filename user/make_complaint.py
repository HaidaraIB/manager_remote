from telegram import (
    Update,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    PhotoSize,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from pyrogram.types import Message

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

from start import start_command

from PyroClientSingleton import PyroClientSingleton
from DB import DB
import datetime
import os

(
    COMPLAINT_ABOUT,
    CHOOSE_OPERATION,
    NOTIFY_OPERATION,
    COMPLAINT_REASON,
    COMPLAINT_CONFIRMATION,
) = range(5)


state_dict_en_to_ar = {
    "declined": "مرفوض",
    "approved": "تمت الموافقة",
    "returned": "طلب معاد",
    "pending": "بانتظار التحقق",
    "sent": "بانتظار التنفيذ",
}

choose_operations_text = (
    "يمكنك اختيار الرقم التسلسلي للعملية التي تريد الشكوى عنها من الأسفل⬇️\n\n"
    "<b>ملاحظة: الطلبات التي تمت معالجة شكوى عنها سابقاً ليست ضمن القائمة.</b>"
)


def stringify_order(serial: int, order_type: str):
    op = DB.get_one_order(order_type=order_type, serial=serial)
    payment_method_number = bank_account_name = "لا يوجد"
    if order_type != "deposit":
        payment_method_number = (
            op["payment_method_number"] if op["payment_method_number"] else "لا يوجد"
        )
        bank_account_name = (
            op["bank_account_name"] if op["bank_account_name"] else "لا يوجد"
        )

    return (
        f"الرقم التسلسلي: <code>{op['serial']}</code>\n"
        f"المبلغ: <b>{op['amount']}</b>\n"
        f"وسيلة الدفع: <b>{op['method']}</b>\n"
        f"عنوان الدفع: <code>{payment_method_number}</code>\n"
        f"اسم صاحب الحساب البنكي: <code>{bank_account_name}</code>\n"
        f"الحالة: <b>{state_dict_en_to_ar[op['state']]}</b>\n"
        f"سبب إعادة/رفض: <b>{op['reason'] if op['reason'] else 'لا يوجد'}</b>\n\n"
    )


async def check_complaint_date(
    context: ContextTypes.DEFAULT_TYPE,
    serial: int,
    order_type: str,
):
    if not context.user_data.get(f"notified_{order_type}_operations", False):
        context.user_data[f"notified_{order_type}_operations"] = {
            serial: {
                "serial": serial,
                "date": datetime.datetime.now(),
            }
        }
        return True

    elif not context.user_data[f"notified_{order_type}_operations"].get(serial, False):
        context.user_data[f"notified_{order_type}_operations"][serial] = {
            "serial": serial,
            "date": datetime.datetime.now(),
        }
        return True

    date: datetime.datetime = context.user_data[f"notified_{order_type}_operations"][
        serial
    ]["date"]

    if (datetime.datetime.now() - date).days < 1:

        return False

    return True


async def get_photos_from_archive(message_ids: list[int]):
    photos: list[PhotoSize] = []
    cpyro = PyroClientSingleton()

    try:
        await cpyro.start()
    except ConnectionError:
        pass

    ms: list[Message] = await cpyro.get_messages(
        chat_id=int(os.getenv("ARCHIVE_CHANNEL")),
        message_ids=message_ids,
    )
    for m in ms:
        if not m.photo:
            continue
        photos.append(
            PhotoSize(
                file_id=m.photo.file_id,
                file_unique_id=m.photo.file_unique_id,
                width=m.photo.width,
                height=m.photo.height,
                file_size=m.photo.file_size,
            )
        )

    await cpyro.stop()

    return photos


def build_operations_keyboard(serials: list[int]):
    if len(serials) % 3 == 0:
        keyboard = [
            [
                InlineKeyboardButton(
                    text=str(serials[i]), callback_data=f"serial {serials[i]}"
                ),
                InlineKeyboardButton(
                    text=str(serials[i + 1]), callback_data=f"serial {serials[i+1]}"
                ),
                InlineKeyboardButton(
                    text=str(serials[i + 2]), callback_data=f"serial {serials[i+2]}"
                ),
            ]
            for i in range(0, len(serials), 3)
        ]
    elif len(serials) % 3 == 1:
        keyboard = [
            [
                InlineKeyboardButton(
                    text=str(serials[i]), callback_data=f"serial {serials[i]}"
                ),
                InlineKeyboardButton(
                    text=str(serials[i + 1]), callback_data=f"serial {serials[i+1]}"
                ),
                InlineKeyboardButton(
                    text=str(serials[i + 2]), callback_data=f"serial {serials[i+2]}"
                ),
            ]
            for i in range(0, len(serials) - 1, 3)
        ]
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=str(serials[-1]), callback_data=f"serial {serials[-1]}"
                )
            ]
        )
    else:
        keyboard = [
            [
                InlineKeyboardButton(
                    text=str(serials[i]), callback_data=f"serial {serials[i]}"
                ),
                InlineKeyboardButton(
                    text=str(serials[i + 1]), callback_data=f"serial {serials[i+1]}"
                ),
                InlineKeyboardButton(
                    text=str(serials[i + 2]), callback_data=f"serial {serials[i+2]}"
                ),
            ]
            for i in range(0, len(serials) - 2, 3)
        ]
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=str(serials[-2]), callback_data=f"serial {serials[-2]}"
                ),
                InlineKeyboardButton(
                    text=str(serials[-1]), callback_data=f"serial {serials[-1]}"
                ),
            ]
        )

    return keyboard


async def handle_complaint_about(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    about: str,
):
    operations = DB.get_orders(order_type=about, user_id=update.effective_user.id)

    if not operations:
        return False

    keyboard = build_operations_keyboard(
        serials=[op["serial"] for op in operations if not op["complaint_took_care_of"]]
    )
    keyboard.append(build_back_button(f"back to complaint about"))
    keyboard.append(back_to_user_home_page_button[0])

    context.user_data["operations_keyboard"] = keyboard

    await update.callback_query.edit_message_text(
        text=choose_operations_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return True


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

        complaints_keyboard = [
            [InlineKeyboardButton(text="إيداع📥", callback_data="deposit complaint")],
            [InlineKeyboardButton(text="سحب💳", callback_data="withdraw complaint")],
            [
                InlineKeyboardButton(
                    text="شراء USDT💰", callback_data="buyusdt complaint"
                )
            ],
            back_to_user_home_page_button[0],
        ]
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
        serial = int(update.callback_query.data.replace("serial ", ""))
        context.user_data["complaint_serial"] = serial
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


async def notify_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:

        serial = int(update.callback_query.data.split("_")[-1])

        op = DB.get_one_order(
            order_type=context.user_data["complaint_about"],
            serial=serial,
        )
        res = await check_complaint_date(
            context=context,
            serial=serial,
            order_type=context.user_data["complaint_about"],
        )

        if not res:
            await update.callback_query.answer(
                "يمكنك إرسال تنبيه واحد عن كل طلب في اليوم❗️"
            )
            return

        cpyro = PyroClientSingleton()
        try:
            await cpyro.start()
        except ConnectionError:
            pass

        old_message = await cpyro.get_messages(
            chat_id=op["worker_id"] if op["working_on_it"] else op["group_id"],
            message_ids=(
                op["pending_process_message_id"]
                if op["pending_process_message_id"]
                else op["pending_check_message_id"]
            ),
        )
        message = await cpyro.copy_message(
            chat_id=op["worker_id"] if op["working_on_it"] else op["group_id"],
            from_chat_id=(op["worker_id"] if op["working_on_it"] else op["group_id"]),
            message_id=(
                op["pending_process_message_id"]
                if op["pending_process_message_id"]
                else op["pending_check_message_id"]
            ),
            reply_markup=old_message.reply_markup,
        )

        await cpyro.send_message(
            chat_id=op["worker_id"] if op["working_on_it"] else op["group_id"],
            text="وصلتنا شكوى تأخير بشأن الطلب أعلاه⬆️",
        )
        await cpyro.delete_messages(
            chat_id=op["worker_id"] if op["working_on_it"] else op["group_id"],
            message_ids=(
                op["pending_process_message_id"]
                if op["pending_process_message_id"]
                else op["pending_check_message_id"]
            ),
        )

        await cpyro.stop()

        if op["state"] == "sent":
            if op["working_on_it"]:
                await DB.add_message_ids(
                    order_type=context.user_data["complaint_about"],
                    serial=serial,
                    processing_message_id=message.id,
                )
            else:
                await DB.add_message_ids(
                    order_type=context.user_data["complaint_about"],
                    serial=serial,
                    pending_process_message_id=message.id,
                )
        else:
            if op["working_on_it"]:
                await DB.add_message_ids(
                    order_type=context.user_data["complaint_about"],
                    serial=serial,
                    checking_message_id=message.id,
                )
            else:
                await DB.add_message_ids(
                    order_type=context.user_data["complaint_about"],
                    serial=serial,
                    pending_check_message_id=message.id,
                )

        context.user_data[
            f"notified_{context.user_data['complaint_about']}_operations"
        ][serial]["date"] = datetime.datetime.now()

        await update.callback_query.edit_message_text(
            text="شكراً لك، لقد تمت العملية بنجاح.",
            reply_markup=build_user_keyboard(),
        )

        return ConversationHandler.END


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
            complaint_keyboard = build_complaint_keyboard(data, False, False)

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


async def back_to_complaint_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        keyboard = [
            build_back_button("back to choose operation"),
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text="أرسل سبب هذه الشكوى",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return COMPLAINT_REASON


async def back_to_complaint_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        complaints_keyboard = [
            [InlineKeyboardButton(text="إيداع📥", callback_data="deposit complaint")],
            [InlineKeyboardButton(text="سحب💳", callback_data="withdraw complaint")],
            [
                InlineKeyboardButton(
                    text="شراء USDT💰",
                    callback_data="buyusdt complaint",
                )
            ],
            back_to_user_home_page_button[0],
        ]
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
