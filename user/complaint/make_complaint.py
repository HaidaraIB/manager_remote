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
    parent_to_child_models_mapper,
)
from common.decorators import (
    check_if_user_present_decorator,
    check_user_call_on_or_off_decorator,
)
from common.force_join import check_if_user_member_decorator
from common.back_to_home_page import (
    back_to_user_home_page_handler,
    back_to_user_home_page_button,
)
from common.stringifies import complaint_stringify_order, state_dict_en_to_ar
from user.complaint.notify import notify_operation
from user.complaint.common import *
from start import start_command
from models import Complaint, Photo
from constants import CHOOSE_OPERATIONS_TEXT, EXT_COMPLAINT_LINE

(
    COMPLAINT_ABOUT,
    CHOOSE_OPERATION,
    NOTIFY_OPERATION,
    COMPLAINT_REASON,
    COMPLAINT_CONFIRMATION,
) = range(5)


@check_user_call_on_or_off_decorator
@check_if_user_present_decorator
@check_if_user_member_decorator
async def make_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        await update.callback_query.edit_message_text(
            text="شكوى فيما يخص:",
            reply_markup=InlineKeyboardMarkup(complaints_keyboard),
        )
        return COMPLAINT_ABOUT


async def complaint_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if not update.callback_query.data.startswith("back"):
            about = update.callback_query.data.replace(" complaint", "")
            context.user_data["complaint_about"] = about
        else:
            about = context.user_data["complaint_about"]

        if about == "deposit":
            ar_texts = ["إيداع", "الإيداع"]
        elif about == "withdraw":
            ar_texts = ["سحب", "السحب"]
        else:
            ar_texts = ["شراء USDT", "شراء USDT"]

        operations = parent_to_child_models_mapper[about].get_orders(
            user_id=update.effective_user.id
        )

        keyboard = build_operations_keyboard(
            serials=[op.serial for op in operations if not op.complaint_took_care_of]
        )
        if not operations or len(keyboard) == 2:
            await update.callback_query.answer(f"لم تقم بأي عملية {ar_texts[0]} بعد ❗️")
            return

        await update.callback_query.edit_message_text(
            text=CHOOSE_OPERATIONS_TEXT,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        return CHOOSE_OPERATION


back_to_complaint_about = make_complaint


async def choose_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if not update.callback_query.data.startswith("back"):
            serial = int(update.callback_query.data.replace("serial ", ""))
            context.user_data["complaint_serial"] = serial
        else:
            serial = context.user_data["complaint_serial"]

        op = parent_to_child_models_mapper[
            context.user_data["complaint_about"]
        ].get_one_order(
            serial=serial,
        )

        op_text = (
            f"تفاصيل العملية:\n\n"
            f"الرقم التسلسلي: <code>{op.serial}</code>\n"
            f"المبلغ: <b>{op.amount}</b>\n"
            f"وسيلة الدفع: <b>{op.method}</b>\n"
            f"الحالة: <b>{state_dict_en_to_ar[op.state]}</b>\n"
            f"سبب إعادة/رفض: <b>{op.reason if op.reason else 'لا يوجد'}</b>\n\n"
        )

        back_buttons = [
            build_back_button("back_to_choose_operation"),
            back_to_user_home_page_button[0],
        ]

        if context.user_data["complaint_about"] == "deposit" and op.state == "pending":
            await update.callback_query.answer(
                text="إيداع قيد التحقق، يقوم البوت بالتحقق بشكل دوري من نجاح العملية، الرجاء التحلي بالصبر.",
                show_alert=True,
            )
            return

        elif op.state == "returned":
            await update.callback_query.edit_message_text(
                text=(
                    op_text
                    + "<b>طلب معاد راجع محادثة البوت وقم بإرفاق المطلوب.\n"
                    + "في حال لم تجدها أعد تقديم الطلب من جديد، مع الأخذ بعين الاعتبار سبب الإعادة.</b>"
                ),
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return

        elif op.state in ["sent", "pending"]:
            alert_button = [
                [
                    InlineKeyboardButton(
                        text="إرسال تنبيه🔔",
                        callback_data=f"notify_{op.state}_operation_{serial}",
                    )
                ],
                *back_buttons,
            ]
            if op.state == "sent":
                op_text += "<b>عملية قيد التنفيذ، يمكنك إرسال تذكير بشأنها.</b>"

            else:
                op_text += "<b>عملية قيد التحقق، يمكنك إرسال تذكير بشأنها.</b>"

            await update.callback_query.edit_message_text(
                text=op_text,
                reply_markup=InlineKeyboardMarkup(alert_button),
            )
            return NOTIFY_OPERATION

        keyboard = [
            build_back_button("back_to_choose_operation"),
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text=op_text + "<b>أرسل سبب هذه الشكوى</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return COMPLAINT_REASON


back_to_choose_operation = complaint_about


async def complaint_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        context.user_data["reason"] = update.message.text
        complaint_text = (
            f"هل أنت متأكد من أنك تريد إرسال شكوى فيما يخص الطلب:\n\n"
            f"{complaint_stringify_order(serial=context.user_data['complaint_serial'], order_type=context.user_data['complaint_about'])}\n"
            "سبب الشكوى:\n"
            f"<b>{update.message.text}</b>"
        )

        keyboard = [
            [
                InlineKeyboardButton(text="نعم👍", callback_data="yes complaint"),
                InlineKeyboardButton(text="لا👎", callback_data="no complaint"),
            ],
            build_back_button("back_to_complaint_reason"),
            back_to_user_home_page_button[0],
        ]

        await update.message.reply_text(
            text=complaint_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return COMPLAINT_CONFIRMATION


back_to_complaint_reason = choose_operation


async def complaint_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        order_type: str = context.user_data["complaint_about"]
        serial = context.user_data["complaint_serial"]
        if update.callback_query.data.startswith("yes"):
            op = parent_to_child_models_mapper[order_type].get_one_order(serial=serial)

            complaint_text = (
                f"شكوى جديدة:\n\n"
                f"{complaint_stringify_order(serial=serial, order_type=order_type)}\n"
                "سبب الشكوى:\n"
                f"<b>{context.user_data['reason']}</b>\n"
            )
            photos = Photo.get(order_serial=serial, order_type=order_type)

            if op.worker_id:
                context.bot_data["suspended_workers"].add(op.worker_id)

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
                text=EXT_COMPLAINT_LINE.format(serial),
                reply_markup=complaint_keyboard,
            )

            await update.callback_query.edit_message_text(
                text="شكراً لك، تم إرسال الشكوى خاصتك إلى قسم المراجعة بنجاح، سنعمل على إصلاح المشكلة والرد عليك في أقرب وقت ممكن.",
                reply_markup=build_user_keyboard(),
            )

            await Complaint.add_complaint(
                order_serial=serial,
                order_type=order_type,
                reason=context.user_data["reason"],
            )

            return ConversationHandler.END

        else:  # in case of no complaint selection
            operations = parent_to_child_models_mapper[order_type].get_orders(
                user_id=update.effective_user.id,
            )
            keyboard = build_operations_keyboard(
                serials=[
                    op.serial for op in operations if not op.complaint_took_care_of
                ]
            )
            await update.callback_query.edit_message_text(
                text=CHOOSE_OPERATIONS_TEXT,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return CHOOSE_OPERATION


complaint_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(make_complaint, "^make complaint$")],
    states={
        COMPLAINT_ABOUT: [
            CallbackQueryHandler(
                complaint_about,
                "^((deposit)|(busdt)|(withdraw)) complaint$",
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
        CallbackQueryHandler(back_to_complaint_about, "^back_to_complaint_about$"),
        CallbackQueryHandler(back_to_complaint_reason, "^back_to_complaint_reason$"),
        CallbackQueryHandler(back_to_choose_operation, "^back_to_choose_operation$"),
        back_to_user_home_page_handler,
        start_command,
    ],
    name="make_complaint_handler",
    persistent=True,
)
