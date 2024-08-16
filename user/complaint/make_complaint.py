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
    order_dict_en_to_ar,
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
from user.complaint.notify import notify_order
from user.complaint.common import *
from start import start_command
from models import Complaint, Photo
from common.constants import *

(
    ORDER_TYPE,
    CHOOSE_ORDER,
    NOTIFY_ORDER,
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
        return ORDER_TYPE


async def choose_order_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if not update.callback_query.data.startswith("back"):
            about = update.callback_query.data.replace(" complaint", "")
            context.user_data["complaint_order_type"] = about
        else:
            about = context.user_data["complaint_order_type"]

        orders = parent_to_child_models_mapper[about].get_orders(
            user_id=update.effective_user.id
        )

        keyboard = build_orders_keyboard(
            serials=[
                order.serial for order in orders if not order.complaint_took_care_of
            ]
        )
        if not orders or len(keyboard) == 2:
            await update.callback_query.answer(
                f"لم تقم بأي عملية {order_dict_en_to_ar[about]} بعد ❗️",
                show_alert=True,
            )
            return

        await update.callback_query.edit_message_text(
            text=CHOOSE_ORDERS_TEXT,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        return CHOOSE_ORDER


back_to_choose_order_type = make_complaint


async def choose_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        if not update.callback_query.data.startswith("back"):
            serial = int(update.callback_query.data.replace("serial ", ""))
            context.user_data["complaint_serial"] = serial
        else:
            serial = context.user_data["complaint_serial"]
        about = context.user_data["complaint_order_type"]
        order = parent_to_child_models_mapper[about].get_one_order(
            serial=serial,
        )

        order_text = (
            f"تفاصيل العملية:\n\n"
            f"النوع: <b>{order_dict_en_to_ar[about]}</b>\n"
            f"الرقم التسلسلي: <code>{order.serial}</code>\n"
            f"المبلغ: <b>{order.amount}</b>\n"
            f"وسيلة الدفع: <b>{order.method}</b>\n"
            f"الحالة: <b>{state_dict_en_to_ar[order.state]}</b>\n"
            f"سبب إعادة/رفض: <b>{order.reason if order.reason else 'لا يوجد'}</b>\n\n"
        )

        back_buttons = [
            build_back_button("back_to_choose_order"),
            back_to_user_home_page_button[0],
        ]

        if (
            about == "deposit"
            and order.state == "pending"
            and order.method not in CHECK_DEPOSIT_LIST
        ):
            await update.callback_query.answer(
                text="إيداع قيد التحقق، يقوم البوت بالتحقق بشكل دوري من نجاح العملية، الرجاء التحلي بالصبر.",
                show_alert=True,
            )
            return

        elif order.state == "returned":
            await update.callback_query.edit_message_text(
                text=(
                    order_text
                    + "<b>طلب معاد راجع محادثة البوت وقم بإرفاق المطلوب.\n"
                    + "في حال لم تجدها أعد تقديم الطلب من جديد، مع الأخذ بعين الاعتبار سبب الإعادة.</b>"
                ),
                reply_markup=InlineKeyboardMarkup(back_buttons),
            )
            return

        elif order.state in ["sent", "pending", "checking", "processing"]:
            alert_button = [
                [
                    InlineKeyboardButton(
                        text="إرسال تنبيه🔔",
                        callback_data=f"notify_{order.state}_order_{serial}",
                    )
                ],
                *back_buttons,
            ]
            if order.state in ["sent", "processing"]:
                order_text += "<b>عملية قيد التنفيذ، يمكنك إرسال تذكير بشأنها.</b>"

            elif order.state in ["pending", "checking"]:
                order_text += "<b>عملية قيد التحقق، يمكنك إرسال تذكير بشأنها.</b>"

            await update.callback_query.edit_message_text(
                text=order_text,
                reply_markup=InlineKeyboardMarkup(alert_button),
            )
            return NOTIFY_ORDER

        keyboard = [
            build_back_button("back_to_choose_order"),
            back_to_user_home_page_button[0],
        ]
        await update.callback_query.edit_message_text(
            text=order_text + "<b>أرسل سبب هذه الشكوى</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return COMPLAINT_REASON


back_to_choose_order = choose_order_type


async def complaint_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        context.user_data["reason"] = update.message.text
        comp_info = complaint_stringify_order(
            serial=context.user_data["complaint_serial"],
            order_type=context.user_data["complaint_order_type"],
        )
        complaint_text = (
            f"هل أنت متأكد من أنك تريد إرسال شكوى فيما يخص الطلب:\n\n"
            f"{comp_info}\n"
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


back_to_complaint_reason = choose_order


async def complaint_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == Chat.PRIVATE:
        order_type: str = context.user_data["complaint_order_type"]
        serial = context.user_data["complaint_serial"]
        if update.callback_query.data.startswith("yes"):
            order = parent_to_child_models_mapper[order_type].get_one_order(
                serial=serial
            )

            complaint_text = (
                f"شكوى جديدة:\n\n"
                f"{complaint_stringify_order(serial=serial, order_type=order_type)}\n"
                "سبب الشكوى:\n"
                f"<b>{context.user_data['reason']}</b>\n"
            )
            photos = Photo.get(order_serial=serial, order_type=order_type)

            if order.worker_id:
                context.bot_data["suspended_workers"].add(order.worker_id)

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
            orders = parent_to_child_models_mapper[order_type].get_orders(
                user_id=update.effective_user.id,
            )
            keyboard = build_orders_keyboard(
                serials=[
                    order.serial for order in orders if not order.complaint_took_care_of
                ]
            )
            await update.callback_query.edit_message_text(
                text=CHOOSE_ORDERS_TEXT,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return CHOOSE_ORDER


complaint_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            make_complaint,
            "^make complaint$",
        )
    ],
    states={
        ORDER_TYPE: [
            CallbackQueryHandler(
                choose_order_type,
                "^((deposit)|(busdt)|(withdraw)) complaint$",
            )
        ],
        CHOOSE_ORDER: [
            CallbackQueryHandler(
                choose_order,
                "^serial \d+$",
            )
        ],
        NOTIFY_ORDER: [
            CallbackQueryHandler(
                notify_order,
                "^notify",
            )
        ],
        COMPLAINT_REASON: [
            MessageHandler(
                filters=filters.TEXT & ~filters.COMMAND,
                callback=complaint_reason,
            )
        ],
        COMPLAINT_CONFIRMATION: [
            CallbackQueryHandler(
                complaint_confirmation,
                "^((yes)|(no)) complaint$",
            )
        ],
    },
    fallbacks=[
        CallbackQueryHandler(
            back_to_choose_order_type,
            "^back_to_choose_order_type$",
        ),
        CallbackQueryHandler(
            back_to_complaint_reason,
            "^back_to_complaint_reason$",
        ),
        CallbackQueryHandler(
            back_to_choose_order,
            "^back_to_choose_order$",
        ),
        back_to_user_home_page_handler,
        start_command,
    ],
    name="make_complaint_handler",
    persistent=True,
)
